# arm_0 当前文件入口

- mechanical/freecad/arm_0.FCStd：我们自己的正式主CAD，Prototype 0。
- mechanical/exports/arm_0.step：当前HOME整机；同目录四姿态与J2/J3/J4/腕部PNG由ReviewArm0.FCMacro生成。
- mechanical/arm_0_parameters.json：冻结尺寸/姿态与图片来源硬件参数。
- mechanical/docs/fastener_schedule.csv、arm_0_BOM.csv：当前紧固件接口和物料表。
- mechanical/docs/assembly_manifest.csv、joint_datums.csv、parameter_summary.csv：SolidWorks重装与轴基准。
- analysis/v4/assembly_validation.json：本轮含紧固件的完整几何/拆装检查；同目录handoff_export_checks.json记录STEP回读。
- mechanical/handoff/solidworks：白名单交接暂存目录，Git忽略。
- dist/arm_0_SW_handoff_20260914.zip及.sha256：首次审图ZIP及哈希，Git忽略，单独交接。

reference目录、PAROL6参考装配和CyberGear原始详细参考仅供本地参考；不是我们自己的机械臂，也不进入Git或ZIP。旧版几何、旧搜索与analysis/v3等历史报告保留用于追溯，不应用于本轮改动后的紧固装配。当前检查以analysis/v4为准。
