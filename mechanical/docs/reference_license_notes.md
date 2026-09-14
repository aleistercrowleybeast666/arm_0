# 第二阶段参考来源与许可证事实

记录日期2026-09-14。本文件只列来源、已看到的许可声明和待核对点，不作法律结论。

| 来源 | 当前本地版本 | 许可证事实 |
|---|---|---|
| PAROL6 | 3892e9c85c1f6d8041cda01c47c9db9d18b30ad8 | 根LICENSE为GPLv3；不能因README徽章alt残留MIT字样当作MIT |
| Thor | 286b081fe6f056d87c379b884781ef77ff6a0159 | 根LICENSE为CC BY-SA 4.0 |
| freezeLUO/CyberGear | db450fa86455ab1edd0c744fc6aef4e810573014 | 未找到LICENSE文件；README描述3D模型用途，但未给出完整明确的模型商业使用/改编/再分发许可条款 |
| 根目录用户SLDASM | 原文件保留 | 来源、版本与使用授权未知 |
| Y-arm | 尚未提供 | 未取得文件与许可证 |

仓库：[PAROL6](https://github.com/Source-Robotics/PAROL6-Desktop-robot-arm)、[Thor](https://github.com/AngelLM/Thor)、[CyberGear](https://github.com/freezeLUO/CyberGear)。

研究层：`PAROL6_reference_assembly.FCStd`包含上游网格，`CyberGear_Detail.FCStd`包含第三方定子和转子网格。这些是明确标记的参考文件，不混入我们的STEP装配。

独立重建层：Robot_Master中的底座、双侧肩架、盒形分段大臂、盖板、yoke、轴承座、紧固接口及腕部占位均由本项目脚本生成；没有缩放、改名或导入PAROL6/Thor原始零件。

CyberGear Envelope虽用基础实体独立生成，接口数值和孔中心来自该仓库的尺寸图/网格测量。独立编写脚本不自动等于来源权利问题已经解决；商业发布时仍需核查模型/数据的来源与可使用范围，必要时改用厂家正式提供或实测确认的接口资料。未知许可证不能直接写成“自由商用”。

本轮未重新许可参考仓库、未删除其LICENSE，也未将参考几何作为本项目原创零件发布。
