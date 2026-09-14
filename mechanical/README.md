# Arm 机械工程

**当前入口：[第二阶段 CAD 使用与验证报告](docs/master_stage2_review.md)**。
请打开 `freecad/Robot_Master.FCStd`；第二阶段参数入口是 `master_parameters.json` / MasterParameters 表格。
全部新增文件见 [第二阶段文件清单](docs/stage2_files.md)，装配步骤见 [assembly_concept.md](docs/assembly_concept.md)。

以下保留第一阶段历史说明；其占位电机、姿态、碰撞结果和 `parameters.json` 不适用于当前 Robot_Master。

# 第一阶段历史记录

建议先看 `exports/layout_preview.png`，再在 FreeCAD 中打开 `freecad/Arm_v1_STOW.FCStd` 或 `Arm_v1_HOME.FCStd`。

```text
Arm/
  reference/                 上游参考与用户模型入口，不参与正式 CAD 生成
    PAROL6/                  已克隆，保留 GPLv3 LICENSE
    Thor/                    已克隆，保留 CC BY-SA 4.0 LICENSE
    y_arm/                   等待用户补充
    cybergear/               原始电机模型状态与 STEP 接口说明
  mechanical/
    parameters.json          总参数入口（mm / deg）
    freecad/                 HOME / STOW / SAFE_UNFOLD / EXTENDED / CAKE_APPROACH
    scripts/                 生成、检查、预览及 FreeCAD 宏
    exports/                 STEP 与预览图
    docs/                    参考审查、构型、验证与人工接续
  analysis/                  原始检查 JSON、参考清单、回导数据
```

## 使用

在 Arm 根目录 PowerShell 运行：

```powershell
& .\mechanical\scripts\build.ps1
& 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe' .\mechanical\scripts\validate_layout.py
& 'D:\Program Files\FreeCAD_1.1.3-Windows-x86_64-py311\bin\python.exe' .\mechanical\scripts\render_preview.py
```

主机已用 FreeCAD 1.1.3 自带 Python 3.11 实际生成。普通系统 Python 没有 FreeCAD 模块。更换安装位置时，给 build.ps1 的 `-FreeCadPython` 传入自带 python.exe。

FreeCAD GUI：菜单 宏 → 宏 → 选择 `scripts/BuildArm.FCMacro`，生成 HOME；打开已有模型后可修改 MasterParameters，并运行 `RebuildFromSheet.FCMacro` 生成新的未保存 CUSTOM 文档。**Spreadsheet 修改不会自动驱动实体，必须显式重建**。JSON 是批量生成的主入口，CUSTOM 表格修改不会写回 JSON。

运行 build 会更新脚本管理的同名 FCStd 和 STEP；FreeCAD 可能保留 FCStd1 备份。人工修改版本请“另存为”到新名称，避免被重建覆盖。每次改参数后必须重新运行验证，不能沿用旧报告。

本版没有导入参考 CAD；不含最终孔位、制造图、真实电机、控制程序或承载认证。详见 `docs/concept_layout.md` 和 `docs/handoff.md`。
