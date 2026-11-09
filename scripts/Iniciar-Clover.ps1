param([switch]$Archivos)
$ErrorActionPreference = 'Stop'
$base = Split-Path $PSScriptRoot
$exe = Join-Path $base 'motor\llama-server.exe'
$model = Join-Path $base 'modelos\Clover-35B-A3B-Preview-Q4_K_M-AR.gguf'
if (!(Test-Path -LiteralPath $exe)) { throw 'Falta motor\llama-server.exe. Sigue instalacion-windows.md.' }
if (!(Test-Path -LiteralPath $model)) { throw 'Falta el modelo AR. Ejecuta primero preparar-modelo-ar.py.' }
$ErrorActionPreference = 'Continue'
$version = (& $exe --version 2>&1 | Out-String)
$versionExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($versionExit -ne 0) { throw 'No se puede ejecutar llama-server.exe. Comprueba las DLL y el controlador NVIDIA.' }
if ($version -notmatch 'build 12144, commit 69ee2ecc0') { throw 'Esta guía está comprobada con b12144 (69ee2ecc0).' }
if (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue) { throw '8080 ya está ocupado. Cierra el otro servidor antes de continuar.' }
$arguments = @('--model',$model,'--alias','Clover-35B-A3B-Q4_K_M','--host','127.0.0.1','--port','8080',
    '--ctx-size','65536','--parallel','1','--n-gpu-layers','all','--n-cpu-moe','36','--fit','off',
    '--fit-target','768','--flash-attn','on','--batch-size','256','--ubatch-size','128',
    '--cache-type-k','f16','--cache-type-v','f16')
if ($Archivos) {
    $python = (Get-Command python.exe -ErrorAction Stop).Source
    & $python -c "import sys; assert sys.version_info >= (3,11)"
    if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.11 o posterior y comprueba python --version.' }
    $config = Join-Path $base 'mcp-local.json'
    @{ mcpServers = @{ CloverPong = @{ command=$python; args=@((Join-Path $PSScriptRoot 'archivos-restringidos.py'),'--stdio') } } } |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $config -Encoding UTF8
    $arguments[3] = 'Clover-Archivos-64K'
    $arguments += @('--mcp-servers-config',$config)
}
Write-Host 'Cuando aparezca listening on, abre http://127.0.0.1:8080/ . Para detener: Ctrl+C.'
& $exe @arguments
if ($LASTEXITCODE -ne 0) { throw 'El servidor se ha detenido con un error. Revisa las últimas líneas de esta ventana.' }
