"""Adapta exclusivamente el GGUF oficial verificado para llama.cpp b12144."""
import argparse
import hashlib
import math
import os
from pathlib import Path
import shutil
import struct

SHA256 = '4d439bb832487fbb91d0a739a5746cf3089bde4137c17050576b24e6dba3539c'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def adapt(source, destination=None, reference=None):
    if digest(source) != SHA256:
        raise ValueError('El SHA256 no corresponde al Q4_K_M oficial de esta guía. No se ha modificado nada.')
    with source.open('rb') as f:
        def read(n):
            data = f.read(n)
            if len(data) != n:
                raise ValueError('GGUF truncado')
            return data
        def scalar(fmt):
            return struct.unpack('<' + fmt, read(struct.calcsize('<' + fmt)))[0]
        def string():
            return read(scalar('Q')).decode('utf-8')
        def value(kind):
            if kind == 8:
                return string()
            if kind == 9:
                subtype, count = scalar('I'), scalar('Q')
                return [value(subtype) for _ in range(count)]
            return scalar({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}[kind])
        if read(4) != b'GGUF':
            raise ValueError('No es GGUF')
        version, nt, nk = scalar('I'), scalar('Q'), scalar('Q')
        start = f.tell()
        metadata = {}
        for _ in range(nk):
            key = string()
            metadata[key] = value(scalar('I'))
        end = f.tell()
        f.seek(start)
        raw_metadata = read(end-start)
        items = []
        for _ in range(nt):
            start = f.tell()
            name = string()
            dims = [scalar('Q') for _ in range(scalar('I'))]
            kind, offset = scalar('I'), scalar('Q')
            end = f.tell()
            f.seek(start)
            items.append((name, dims, kind, offset, read(end-start)))
        alignment = metadata.get('general.alignment', 32)
        base = (f.tell()+alignment-1)//alignment*alignment
        kept, newoff = [], 0
        for i, (name, dims, kind, offset, raw) in enumerate(items):
            size = (items[i+1][3] if i+1 < len(items) else source.stat().st_size-base)-offset
            if '.ssm_bd_' not in name and not name.endswith('.ssm_conv1d.weight_right'):
                kept.append((name,dims,kind,offset,size,raw[:-8]+struct.pack('<Q',newoff)))
                newoff += size
        if nt-len(kept) != 120 or len(kept) != 733:
            raise ValueError('Distribución de tensores inesperada')
        key = b'clover_moe.expert_shared_count'
        header = b'GGUF'+struct.pack('<IQQ',version,len(kept),nk+1)+raw_metadata
        header += struct.pack('<Q',len(key))+key+struct.pack('<II',4,1)
        header += b''.join(item[5] for item in kept)
        header += b'\0' * ((-len(header)) % alignment)
        def chunks():
            yield header
            transformed = 0
            for name,dims,kind,offset,size,_ in kept:
                f.seek(base+offset)
                if name.endswith('.ssm_a'):
                    if kind != 0:
                        raise ValueError('ssm_a debe ser F32')
                    count = math.prod(dims)
                    vals = struct.unpack('<'+'f'*count, read(count*4))
                    yield struct.pack('<'+'f'*count, *[-math.exp(x) for x in vals])
                    size -= count*4
                    transformed += 1
                while size:
                    data = read(min(size, 16*1024*1024))
                    yield data
                    size -= len(data)
            if transformed != 30:
                raise ValueError('Número inesperado de tensores ssm_a')
        if reference:
            with reference.open('rb') as expected:
                for chunk in chunks():
                    if expected.read(len(chunk)) != chunk:
                        raise ValueError('La adaptación difiere de la copia de referencia')
                if expected.read(1):
                    raise ValueError('La referencia contiene datos adicionales')
            print('OK: adaptación idéntica byte a byte a la copia AR existente; solo lectura.')
        else:
            if source.resolve() == destination.resolve() or destination.exists():
                raise ValueError('El destino ya existe. No se sobrescribe.')
            temporary = destination.with_suffix('.gguf.part')
            with temporary.open('xb') as out:
                for chunk in chunks():
                    out.write(chunk)
            os.rename(temporary, destination)
            print('Modelo AR preparado:', destination)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('origen', type=Path)
    p.add_argument('--verificar-con', type=Path)
    args = p.parse_args()
    target = args.origen.with_name(args.origen.stem+'-AR.gguf')
    try:
        if not args.verificar_con:
            free = shutil.disk_usage(args.origen.parent).free
            if free < args.origen.stat().st_size:
                raise ValueError('Hace falta espacio para una segunda copia del modelo.')
        adapt(args.origen, target, args.verificar_con)
    except (OSError, ValueError) as exc:
        p.exit(1, str(exc)+'\n')
