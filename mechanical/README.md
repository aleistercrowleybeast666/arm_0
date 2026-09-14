# arm_0 机械工程

正式主文件：[arm_0.FCStd](freecad/arm_0.FCStd)。参数：[arm_0_parameters.json](arm_0_parameters.json)。

请先看 [V3 拓扑与验证报告](docs/arm_0_v3_review.md)，再看 [装配顺序](docs/assembly_concept.md) 和 [待解决问题](docs/unresolved_issues.md)。

V3入口是 `scripts/build_arm_0.ps1`、`scripts/build_arm_0.py`、`scripts/SetArm0Pose.FCMacro`、`scripts/RebuildArm0.FCMacro`。所有操作方式见根目录README。

[legacy/v2](legacy/v2/README.md)为旧侧向错层模型，已SUPERSEDED。旧版参数、导出与报告保留用于比较。`Arm_v1_*`、`parameters.json`、`build.ps1`和对应第一阶段脚本为历史，不是当前重建入口。

PAROL6、CyberGear详细网格、Thor是参考，保持原名且不混入我们的主装配。

当前腕部为J5后置、J6前置的一体连接件方案，Flange已按用户确认从35改为86 mm。旧大框腕部快照见 [legacy/v3_box_wrist](legacy/v3_box_wrist/README.md)。
