"""Herramientas MCP por stdio, limitadas a CloverPong. Solo Windows."""
import ctypes, ctypes.wintypes as wt, os, re, json, pathlib, threading, time
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent / 'CloverPong'
ROOT.mkdir(exist_ok=True)
LOG = HERE.parent / 'registros'
LOG.mkdir(exist_ok=True)
LOCK = threading.RLock()
K = ctypes.WinDLL('kernel32', use_last_error=True)
K.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID, wt.DWORD, wt.DWORD, wt.HANDLE]
K.CreateFileW.restype = wt.HANDLE
K.CloseHandle.argtypes = [wt.HANDLE]
K.GetFinalPathNameByHandleW.argtypes = [wt.HANDLE, wt.LPWSTR, wt.DWORD, wt.DWORD]
K.GetFileInformationByHandle.argtypes = [wt.HANDLE, wt.LPVOID]
class Info(ctypes.Structure):
    _fields_ = [('attr',wt.DWORD),('ct',wt.FILETIME),('at',wt.FILETIME),('mt',wt.FILETIME),
                ('vol',wt.DWORD),('sizehi',wt.DWORD),('sizelo',wt.DWORD),('links',wt.DWORD),('indexhi',wt.DWORD),('indexlo',wt.DWORD)]
def info(h):
    result = Info()
    if not K.GetFileInformationByHandle(h,ctypes.byref(result)): raise ctypes.WinError(ctypes.get_last_error())
    return result
def final(h):
    b=ctypes.create_unicode_buffer(32768)
    if not K.GetFinalPathNameByHandleW(h,b,len(b),0): raise ctypes.WinError(ctypes.get_last_error())
    return b.value.removeprefix('\\\\?\\')
def handle(path,access,creation=3,directory=False):
    # OPEN_REPARSE_POINT: never follow the final symlink/junction. No FILE_SHARE_DELETE.
    h=K.CreateFileW(str(path),access,3,None,creation,0x00200000 | (0x02000000 if directory else 0),None)
    if h == ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
    return h
# Lock every directory in the root's ancestry against rename/reparse replacement while serving.
GUARDS=[]
for d in reversed([ROOT]+list(ROOT.parents)):
    h=handle(d,0, directory=True)
    if info(h).attr & 0x400: raise RuntimeError('Reparse directory rejected: '+str(d))
    GUARDS.append(h)
ROOT = pathlib.Path(final(GUARDS[-1]))

def path_for(value):
    if not isinstance(value,str) or not value or '\x00' in value: raise PermissionError('Ruta no valida')
    # Flat sandbox: no subdirectories, relative traversal, UNC, device, ADS, or encoded paths.
    value=value.replace('/', '\\')
    if value.lower().startswith(str(ROOT).lower()+'\\'): value=value[len(str(ROOT))+1:]
    if any(c in value for c in '\\/:*?"<>|%') or value in ('.','..') or value.endswith((' ','.')):
        raise PermissionError('Solo archivos directamente dentro de CloverPong')
    if re.match(r'(?i)^(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\.|$)',value): raise PermissionError('Dispositivo no permitido')
    if pathlib.Path(value).suffix.lower() not in ('.html','.css','.js','.json','.txt','.md'):
        raise PermissionError('Extension no permitida')
    return ROOT/value

def fileop(path,content=None,old=None,new=None):
    p=path_for(path)
    writing=content is not None or old is not None
    h=handle(p,0x80000000 | (0x40000000 if writing else 0),4 if content is not None else 3)
    try:
        i=info(h)
        if i.attr & (0x400|0x10) or i.links != 1: raise PermissionError('Enlace, reparse point o directorio bloqueado')
        if os.path.normcase(final(h)) != os.path.normcase(str(p)): raise PermissionError('Ruta final fuera del aislamiento')
        import msvcrt
        fd=msvcrt.open_osfhandle(h,(os.O_RDWR if writing else os.O_RDONLY) | os.O_BINARY); h=None
        with os.fdopen(fd,'r+b' if writing else 'rb') as f:
            if old is not None:
                text=f.read(2_000_001).decode('utf-8')
                if not old or text.count(old)!=1: raise ValueError('El texto a editar debe aparecer exactamente una vez')
                content=text.replace(old,new,1)
            if writing:
                data=content.encode('utf-8')
                if len(data)>2_000_000: raise ValueError('Limite de 2 MB por archivo')
                f.seek(0);f.write(data);f.truncate();f.flush();os.fsync(f.fileno())
                return {'path':str(p),'bytes':len(data),'saved':True}
            data=f.read(2_000_001)
            if len(data)>2_000_000: raise ValueError('Limite de lectura de 2 MB')
            return {'path':str(p),'content':data.decode('utf-8')}
    finally:
        if h is not None: K.CloseHandle(h)

def schema(name,description,properties,required):
    return {'name':name,'description':description,'inputSchema':{'type':'object','properties':properties,'required':required,'additionalProperties':False}}
STR={'type':'string'}
TOOLS=[schema('list_files','Lista los archivos de CloverPong y su ruta absoluta. No hay acceso a otras carpetas.',{},[]),
       schema('read_file','Lee un archivo UTF-8 directamente dentro de CloverPong.',{'path':STR},['path']),
       schema('write_file','Crea o reemplaza un archivo UTF-8 dentro de CloverPong. Devuelve su ruta absoluta.',{'path':STR,'content':STR},['path','content']),
       schema('edit_file','Reemplaza una unica aparicion exacta de texto dentro de un archivo de CloverPong.',{'path':STR,'old_text':STR,'new_text':STR},['path','old_text','new_text'])]
def audit(event):
    with (LOG/'herramientas.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'time':time.time(),**event},ensure_ascii=False)+'\n')
def call(name,args):
    with LOCK:
        try:
            if name=='list_files':
                result={'root':str(ROOT),'files':[p.name for p in ROOT.iterdir() if p.is_file() and not p.is_symlink()]}
            elif name=='read_file': result=fileop(args['path'])
            elif name=='write_file': result=fileop(args['path'],content=args['content'])
            elif name=='edit_file': result=fileop(args['path'],old=args['old_text'],new=args['new_text'])
            else: raise PermissionError('Herramienta no permitida')
            audit({'tool':name,'args':args,'result':result,'ok':True})
            return {'content':[{'type':'text','text':json.dumps(result,ensure_ascii=False)}]}
        except Exception as e:
            audit({'tool':name,'args':args,'ok':False,'error':str(e)})
            return {'isError':True,'content':[{'type':'text','text':str(e)}]}

if __name__=='__main__':
    if '--stdio' in sys.argv:
        # Native llama.cpp MCP: no HTTP proxy, no general-purpose built-in tools.
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')
        for line in sys.stdin:
            try:
                msg=json.loads(line)
                if 'id' not in msg: continue
                method=msg.get('method');id=msg['id']
                if method=='initialize': result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'CloverPong aislado','version':'1.1'}}
                elif method=='tools/list': result={'tools':TOOLS}
                elif method=='tools/call': result=call(msg['params']['name'],msg['params'].get('arguments',{}))
                elif method=='ping': result={}
                else:
                    print(json.dumps({'jsonrpc':'2.0','id':id,'error':{'code':-32601,'message':'Metodo no disponible'}}),flush=True);continue
                print(json.dumps({'jsonrpc':'2.0','id':id,'result':result},ensure_ascii=True),flush=True)
            except Exception as e:
                print(json.dumps({'jsonrpc':'2.0','id':msg.get('id'),'error':{'code':-32603,'message':str(e)}}),flush=True)
    elif '--selftest' in sys.argv:
        result=[]
        # An actual writable sentinel outside the allowed directory must remain untouched.
        sentinel=LOG/'sentinel.txt';sentinel.write_text('UNCHANGED',encoding='utf-8')
        bad=['../CloverStudio/registros/sentinel.txt',str(sentinel),'C:\\fuera\\private.txt','\\\\localhost\\C$\\outside.txt','index.html:stream','NUL.txt','..\\escape.txt','sub\\a.txt','%2e%2e%5cescape.txt','file.txt.']
        for p in bad:
            r=call('write_file',{'path':p,'content':'MUST NOT WRITE'});assert r.get('isError'),p;result.append({'path':p,'blocked':True})
        link=ROOT/'hardlink-test.txt';os.link(sentinel,link)
        try:
            for tool,args in [('read_file',{'path':link.name}),('write_file',{'path':link.name,'content':'MUST NOT WRITE'}),('edit_file',{'path':link.name,'old_text':'UNCHANGED','new_text':'BAD'})]:
                assert call(tool,args).get('isError');result.append({'case':'hardlink '+tool,'blocked':True})
        finally:link.unlink()
        assert sentinel.read_text()=='UNCHANGED'
        call('write_file',{'path':'control.txt','content':'uno'})
        assert not call('edit_file',{'path':'control.txt','old_text':'uno','new_text':'dos'}).get('isError')
        assert json.loads(call('read_file',{'path':'control.txt'})['content'][0]['text'])['content']=='dos'
        (LOG/'aislamiento.json').write_text(json.dumps({'negative_tests':result,'outside_sentinel':'UNCHANGED','inside_read_write_edit':'PASS'},indent=2),encoding='utf-8')
        print('PASS: 13 escapes blocked; real hardlink blocked; inside read/write/edit verified')
    else:
        raise SystemExit("Usa --stdio o --selftest")
