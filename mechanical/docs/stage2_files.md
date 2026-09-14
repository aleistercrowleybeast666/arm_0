# 第二阶段文件清单

本清单列出本轮新增交付文件和更新入口；不包含FreeCAD自动备份、Python缓存和第一阶段历史产物。
依赖旧有自建运动学脚本 `mechanical/scripts/arm_model.py`，未修改该脚本。参考仓库内容保留在reference，不混入自己的Master。
机器可读大小与SHA256记录见 [deliverable_manifest.json](../../analysis/stage2/deliverable_manifest.json)。
本清单自身为 `mechanical/docs/stage2_files.md`；为避免循环哈希，清单和manifest本身不列入哈希表。

## FreeCAD 主文件

| 文件 | 字节 |
|---|---:|
| [mechanical/freecad/Robot_Master.FCStd](../../mechanical/freecad/Robot_Master.FCStd) | 664352 |
| [mechanical/freecad/CyberGear_Detail.FCStd](../../mechanical/freecad/CyberGear_Detail.FCStd) | 54811 |
| [mechanical/freecad/CyberGear_Envelope.FCStd](../../mechanical/freecad/CyberGear_Envelope.FCStd) | 32149 |
| [mechanical/freecad/PAROL6_reference_assembly.FCStd](../../mechanical/freecad/PAROL6_reference_assembly.FCStd) | 2380583 |

## 参数、脚本与宏

| 文件 | 字节 |
|---|---:|
| [mechanical/master_parameters.json](../../mechanical/master_parameters.json) | 1163 |
| [mechanical/scripts/import_parol6_urdf_to_freecad.py](../../mechanical/scripts/import_parol6_urdf_to_freecad.py) | 4526 |
| [mechanical/scripts/measure_cybergear.py](../../mechanical/scripts/measure_cybergear.py) | 2068 |
| [mechanical/scripts/cybergear_model.py](../../mechanical/scripts/cybergear_model.py) | 4639 |
| [mechanical/scripts/build_robot_master.py](../../mechanical/scripts/build_robot_master.py) | 23761 |
| [mechanical/scripts/check_robot_master.py](../../mechanical/scripts/check_robot_master.py) | 3729 |
| [mechanical/scripts/export_robot_deliverables.py](../../mechanical/scripts/export_robot_deliverables.py) | 6221 |
| [mechanical/scripts/write_stage2_inventory.py](../../mechanical/scripts/write_stage2_inventory.py) | 4433 |
| [mechanical/scripts/build_stage2.ps1](../../mechanical/scripts/build_stage2.ps1) | 567 |
| [mechanical/scripts/SetRobotPose.FCMacro](../../mechanical/scripts/SetRobotPose.FCMacro) | 666 |
| [mechanical/scripts/RebuildRobotMaster.FCMacro](../../mechanical/scripts/RebuildRobotMaster.FCMacro) | 633 |
| [mechanical/scripts/ReviewStage2.FCMacro](../../mechanical/scripts/ReviewStage2.FCMacro) | 3110 |

## STEP

| 文件 | 字节 |
|---|---:|
| [mechanical/exports/Robot_Master_coarse.step](../../mechanical/exports/Robot_Master_coarse.step) | 1604839 |
| [mechanical/exports/J1_base.step](../../mechanical/exports/J1_base.step) | 319051 |
| [mechanical/exports/J2_shoulder.step](../../mechanical/exports/J2_shoulder.step) | 189429 |
| [mechanical/exports/J3_upper_elbow.step](../../mechanical/exports/J3_upper_elbow.step) | 513500 |
| [mechanical/exports/envelope/base_envelope.step](../../mechanical/exports/envelope/base_envelope.step) | 29927 |
| [mechanical/exports/envelope/forearm_envelope.step](../../mechanical/exports/envelope/forearm_envelope.step) | 40940 |
| [mechanical/exports/envelope/shoulder_envelope.step](../../mechanical/exports/envelope/shoulder_envelope.step) | 53099 |
| [mechanical/exports/envelope/tool_envelope.step](../../mechanical/exports/envelope/tool_envelope.step) | 12827 |
| [mechanical/exports/envelope/upper_arm_envelope.step](../../mechanical/exports/envelope/upper_arm_envelope.step) | 65206 |
| [mechanical/exports/envelope/wrist_envelope.step](../../mechanical/exports/envelope/wrist_envelope.step) | 24084 |
| [mechanical/exports/envelope/wrist_pitch_envelope.step](../../mechanical/exports/envelope/wrist_pitch_envelope.step) | 18221 |

## 试装 STL

| 文件 | 字节 |
|---|---:|
| [mechanical/exports/print_fit/J1_BaseTray.stl](../../mechanical/exports/print_fit/J1_BaseTray.stl) | 299684 |
| [mechanical/exports/print_fit/J1_BearingSeat.stl](../../mechanical/exports/print_fit/J1_BearingSeat.stl) | 118884 |
| [mechanical/exports/print_fit/J1_MotorMount.stl](../../mechanical/exports/print_fit/J1_MotorMount.stl) | 192284 |
| [mechanical/exports/print_fit/J1_RotatingPlatform.stl](../../mechanical/exports/print_fit/J1_RotatingPlatform.stl) | 116884 |
| [mechanical/exports/print_fit/J2_BearingRetainer.stl](../../mechanical/exports/print_fit/J2_BearingRetainer.stl) | 63684 |
| [mechanical/exports/print_fit/J2_LeftMotorCheek.stl](../../mechanical/exports/print_fit/J2_LeftMotorCheek.stl) | 165284 |
| [mechanical/exports/print_fit/J2_RightBearingCheek.stl](../../mechanical/exports/print_fit/J2_RightBearingCheek.stl) | 95184 |
| [mechanical/exports/print_fit/J3_BearingRetainer.stl](../../mechanical/exports/print_fit/J3_BearingRetainer.stl) | 63684 |
| [mechanical/exports/print_fit/J3_FixedMotorPlate.stl](../../mechanical/exports/print_fit/J3_FixedMotorPlate.stl) | 192284 |
| [mechanical/exports/print_fit/J3_RemovableBearingCheek.stl](../../mechanical/exports/print_fit/J3_RemovableBearingCheek.stl) | 94784 |
| [mechanical/exports/print_fit/Upper_MainShell_Distal.stl](../../mechanical/exports/print_fit/Upper_MainShell_Distal.stl) | 292084 |
| [mechanical/exports/print_fit/Upper_MainShell_Proximal.stl](../../mechanical/exports/print_fit/Upper_MainShell_Proximal.stl) | 326884 |
| [mechanical/exports/print_fit/Upper_RemovableLid.stl](../../mechanical/exports/print_fit/Upper_RemovableLid.stl) | 83784 |

## 文档

| 文件 | 字节 |
|---|---:|
| [mechanical/docs/master_stage2_review.md](../../mechanical/docs/master_stage2_review.md) | 9270 |
| [mechanical/docs/cybergear_interface.md](../../mechanical/docs/cybergear_interface.md) | 4392 |
| [mechanical/docs/PAROL6_reference_review.md](../../mechanical/docs/PAROL6_reference_review.md) | 4231 |
| [mechanical/docs/Thor_reference_review.md](../../mechanical/docs/Thor_reference_review.md) | 2461 |
| [mechanical/docs/reference_license_notes.md](../../mechanical/docs/reference_license_notes.md) | 1863 |
| [mechanical/docs/assembly_concept.md](../../mechanical/docs/assembly_concept.md) | 6407 |
| [mechanical/docs/unresolved_issues.md](../../mechanical/docs/unresolved_issues.md) | 2954 |

## 原生 CAD 截图

| 文件 | 字节 |
|---|---:|
| [mechanical/exports/Robot_HOME.png](../../mechanical/exports/Robot_HOME.png) | 40255 |
| [mechanical/exports/Robot_STOW.png](../../mechanical/exports/Robot_STOW.png) | 76950 |
| [mechanical/exports/Robot_SAFE_UNFOLD.png](../../mechanical/exports/Robot_SAFE_UNFOLD.png) | 76634 |
| [mechanical/exports/Robot_CAKE_APPROACH.png](../../mechanical/exports/Robot_CAKE_APPROACH.png) | 49525 |
| [mechanical/exports/CyberGear_Detail.png](../../mechanical/exports/CyberGear_Detail.png) | 26757 |
| [mechanical/exports/CyberGear_Envelope.png](../../mechanical/exports/CyberGear_Envelope.png) | 38187 |
| [mechanical/exports/PAROL6_reference_assembly.png](../../mechanical/exports/PAROL6_reference_assembly.png) | 62522 |

## 验证与来源读取记录

| 文件 | 字节 |
|---|---:|
| [analysis/stage2/armdesigner_bridge_v2.json](../../analysis/stage2/armdesigner_bridge_v2.json) | 8936 |
| [analysis/stage2/cybergear-04.png](../../analysis/stage2/cybergear-04.png) | 174951 |
| [analysis/stage2/cybergear-05.png](../../analysis/stage2/cybergear-05.png) | 238051 |
| [analysis/stage2/cybergear-06.png](../../analysis/stage2/cybergear-06.png) | 169031 |
| [analysis/stage2/cybergear_dims-03.png](../../analysis/stage2/cybergear_dims-03.png) | 511490 |
| [analysis/stage2/cybergear_interface_data.json](../../analysis/stage2/cybergear_interface_data.json) | 1214 |
| [analysis/stage2/cybergear_manual.txt](../../analysis/stage2/cybergear_manual.txt) | 33229 |
| [analysis/stage2/cybergear_mesh_bounds.json](../../analysis/stage2/cybergear_mesh_bounds.json) | 525 |
| [analysis/stage2/cybergear_plane_loops.json](../../analysis/stage2/cybergear_plane_loops.json) | 7591 |
| [analysis/stage2/deliverable_checks.json](../../analysis/stage2/deliverable_checks.json) | 9165 |
| [analysis/stage2/environment.json](../../analysis/stage2/environment.json) | 630 |
| [analysis/stage2/gui_review.log](../../analysis/stage2/gui_review.log) | 106 |
| [analysis/stage2/master_checks.json](../../analysis/stage2/master_checks.json) | 4716 |
| [analysis/stage2/parol6_fold-056.png](../../analysis/stage2/parol6_fold-056.png) | 185951 |
| [analysis/stage2/parol6_import.json](../../analysis/stage2/parol6_import.json) | 3915 |
| [analysis/stage2/parol6_manual.txt](../../analysis/stage2/parol6_manual.txt) | 26126 |
| [analysis/stage2/parol6_upper-053.png](../../analysis/stage2/parol6_upper-053.png) | 111331 |
| [analysis/stage2/parol6_wrist-026.png](../../analysis/stage2/parol6_wrist-026.png) | 133581 |
| [analysis/stage2/stow_margin_check.json](../../analysis/stage2/stow_margin_check.json) | 3734 |
| [analysis/stage2/thor_assembly_check.json](../../analysis/stage2/thor_assembly_check.json) | 1487 |

## 更新的历史入口

| 文件 | 字节 |
|---|---:|
| [mechanical/README.md](../../mechanical/README.md) | 2737 |
| [reference/cybergear/README.md](../../reference/cybergear/README.md) | 2291 |
