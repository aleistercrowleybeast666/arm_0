# 第一阶段参考审查

检查日期：2026-09-14。原 `reference` 目录为空。普通网络克隆失败后，经授权网络重试完成两个 shallow clone（depth=1）；未删除或覆盖已有用户文件。只含当前版本与浅历史，不含完整提交历史。

## 已实际获取的来源

| 参考源 | 上游 / 本地位置 | 固定提交 |
|---|---|---|
| PAROL6 | https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm / `reference/PAROL6` | `3892e9c85c1f6d8041cda01c47c9db9d18b30ad8` |
| Thor | https://github.com/AngelLM/Thor / `reference/Thor` | `286b081fe6f056d87c379b884781ef77ff6a0159` |

本轮读取 README、许可证、目录清单、PAROL6 BOM 与 URDF 开头，检查 Thor 一个 FreeCAD 文件的 Document.xml 对象结构。未逐页评审全部装配 PDF，也未对全部原始零件作几何审计。完整文件类型统计见 `analysis/reference_inventory.json`。

## PAROL6

7856 个受检查文件，其中 52 个 STL、1 个 URDF、2 个 STEP、5 个 PDF；大量其他文件属于控制软件依赖和文档资源。

- `STL/`：机械分件；其中 `mounting plates/big_base.STEP`、`small_base.STEP` 只是安装板，不能误称为完整整臂 STEP。
- `PAROL6_URDF/PAROL6/urdf/PAROL6.urdf`：关节、link、惯量及网格引用；可研究六轴串联表达方式。原尺寸、零点、限位、质量不能直接移植。
- `BOM/BOM.md`、`BOM_PDF_Legacy.pdf`：采购分类。BOM 包含 NEMA17 步进电机、行星减速器、皮带等，与本项目 CyberGear 方案不同。
- `Building instructions/Parol building instructions.pdf`、小打印平台改装 PDF、`PETG_printing.md`：可供人工继续研究装配次序和维护空间。
- `Print table/`：打印分件参考；不作为本项目制造材料和强度依据。

适合借鉴：底座—肩—肘—前臂—腕—工具的分段逻辑、工业串联构型、折叠概念。没有导入其 STL、URDF 或任何原始 CAD 到我们的机械文件。

## Thor

236 个文件；79 个 FCStd、72 个 STEP、72 个 STL。

- `freecad-src/`：原生特征树；抽查 `Art2BodyA.fcstd`，内含 1 个 Spreadsheet、22 个 Sketch、2 个 Body、Pad/Pocket、Datum 等。这支持借鉴参数入口和分件组织方式；并非认定所有零件都由统一主参数完全驱动。
- `step/`、`stl/`：交换实体与打印网格；`mods/` 是变体；`doc/` 主要是说明图片/标识，不应误称为完整装配手册目录。
- 当前仓库没有 URDF，README 指向独立 Thor-ROS 仓库；本轮未克隆该仓库。
- BOM 与装配链接在 README，指向 https://thor.angel-lm.com/documentation/bom/ 和 https://thor.angel-lm.com/documentation/assembly/ 。未声称已下载这些页面的全部装配资料。

适合借鉴：按关节拆分 FreeCAD 源文件、Spreadsheet + Sketch/Body 的工程组织。步进电机、打印齿轮、GT2 传动、原尺寸与外壳均未沿用。

## 许可证与独立重建边界

PAROL6 根 LICENSE 是 GPLv3；README 最下方同样声明 GPLv3。徽章的 alt 文本出现 MIT 字样，不能据此将其认定为 MIT 项目。Thor 根 LICENSE 是 CC BY-SA 4.0。

两者不能简单归纳为“禁止商用”：GPLv3 包含传播修改版本、源码与许可条件；CC BY-SA 4.0 允许商业使用，但对受其约束的共享/改编材料要求署名、标注修改和相同方式共享。范围应结合实际使用的文件与交付方式评估，不能以重画或重命名推断义务消失。

原文依据：[PAROL6 LICENSE](https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm/blob/main/LICENSE)、[Thor LICENSE](https://github.com/AngelLM/Thor/blob/main/LICENSE)、[CC 官方条款摘要](https://creativecommons.org/licenses/by-sa/4.0/)。商业发布前仍需核实拟使用素材及相关权利；本轮不作最终法律清权结论。

**参考来源**：上述仓库的构型与文件组织信息。**我们自行重建的结构**：参数、运动链、145 mm 双侧主梁间隔、肩部 dog-leg、J3 定子归属、外置 J5 与回绕 J6 支架、所有基础几何、验证与导出脚本。脚本不读取 reference CAD/mesh/URDF；正式导出仅含本项目生成几何。参考目录保留上游 LICENSE，不把上游文件混入正式 STEP/FCStd。

Y-arm 尚未取得；CyberGear 用户装配来源与完整性未确认，详见对应预留目录 README。
