param([string]$FreeCadPython = 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe', [switch]$SearchDocking)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $FreeCadPython)) { throw 'Set -FreeCadPython to the FreeCAD bundled python.exe' }
$armStages = @()
if ($SearchDocking) { $armStages += 'search_arm_0_docking.py' }
$armStages += @('build_arm_0.py','validate_arm_0.py','export_arm_0.py','report_arm_0.py')
foreach ($armStage in $armStages) {
 & $FreeCadPython (Join-Path $PSScriptRoot $armStage)
 if ($LASTEXITCODE -ne 0) { throw "arm_0 stage failed: $armStage" }
}
