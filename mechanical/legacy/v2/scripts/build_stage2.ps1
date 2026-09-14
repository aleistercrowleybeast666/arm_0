param([string]$FreeCadPython = 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $FreeCadPython)) { throw 'Set -FreeCadPython to the FreeCAD bundled python.exe' }
foreach ($stageScript in @('measure_cybergear.py','import_parol6_urdf_to_freecad.py','cybergear_model.py','build_robot_master.py','check_robot_master.py','export_robot_deliverables.py')) {
    & $FreeCadPython (Join-Path $PSScriptRoot $stageScript)
    if ($LASTEXITCODE -ne 0) { throw "Stage failed: $stageScript" }
}
