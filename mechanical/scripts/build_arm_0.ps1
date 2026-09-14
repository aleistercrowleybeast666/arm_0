param([string]$FreeCadPython = 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe', [switch]$SearchDocking)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $FreeCadPython)) { throw 'Set -FreeCadPython to the FreeCAD bundled python.exe' }
if ($SearchDocking) { throw 'Prototype 0 poses are frozen. This review workflow does not run a docking search.' }
& $FreeCadPython (Join-Path $PSScriptRoot 'handoff_arm_0.py') --validate
if ($LASTEXITCODE -ne 0) { throw 'arm_0 validation/export failed; no handoff release.' }
Write-Output 'Geometry exported. Generate CSV with tables_arm_0.mjs, render ReviewArm0.FCMacro, commit source, then run pack_arm_0.py. ZIP remains ignored.'
