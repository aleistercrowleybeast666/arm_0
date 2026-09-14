param([string]$FreeCadPython = 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $FreeCadPython)) { throw 'Set -FreeCadPython to FreeCAD bundled python.exe' }
& $FreeCadPython (Join-Path $PSScriptRoot 'arm_model.py')
if ($LASTEXITCODE -ne 0) { throw 'FreeCAD build failed' }
