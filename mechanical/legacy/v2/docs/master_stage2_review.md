# 第二阶段：机械 CAD Master 使用与验证

本轮产物为独立建模的工程粗模：J1～J3可进行模型核对、切片和静态打印试装，J4～J6为装配占位。尚不能作为带载电动样机的制造发布版本。

## 打开与操作

用 FreeCAD 1.1.3 打开 [Robot_Master.FCStd](../freecad/Robot_Master.FCStd)。默认保存 HOME。模型含六根 Axis_J1…J6、六个 Origin_J1…J6、MasterParameters 表格、PoseController、按总成分组的独立 Body；共41个物理组件对象，另有6个可隐藏的线缆预留体。

1. 切换姿态：选择 PoseController，在属性 CurrentPose 中选择 HOME、STOW、SAFE_UNFOLD 或 CAKE_APPROACH，然后运行 [SetRobotPose.FCMacro](../scripts/SetRobotPose.FCMacro)。单改下拉框不会自动更新实体。
2. 改尺寸：编辑 MasterParameters 后运行 [RebuildRobotMaster.FCMacro](../scripts/RebuildRobotMaster.FCMacro)，创建新的 CUSTOM 文档，再另存为。修改表格后必须先重建几何，再切姿态；表格不会自动驱动所有布尔实体，也不会写回 JSON。
3. 批量主入口：[master_parameters.json](../master_parameters.json)。重建脚本会覆盖其管理的同名输出，人工修改请另存新文件。
4. PowerShell 在 Arm 根目录运行 `& .\mechanical\scripts\build_stage2.ps1`，依次重建参考、Master、静态检查、STEP回读和STL。截图单独运行 [ReviewStage2.FCMacro](../scripts/ReviewStage2.FCMacro)。此截图宏打开并保存四份生成文档，运行完关闭该 FreeCAD 窗口，宜使用独立进程。

这些 Body 有命名的建模阶段与最终 Tip，但不是全部由可交互草图约束驱动。尺寸变化通过 Python 重建；局部人工修改应保存在副本中。

## 参考与电机接口

- PAROL6：URDF中 xyz、rpy、关节层级和轴向完整解析；网格和位移由米转毫米。已重建7个网格连杆及world，独立 App::Part 保留link/joint名，可分别隐藏。[参考装配](../freecad/PAROL6_reference_assembly.FCStd) / [分析](PAROL6_reference_review.md)。
- Thor：实际存在 `freecad-src/Assembly.FCStd`，六个总成链接可解析；其中Art4/Art56聚合包围盒含异常极大值，未据此宣称全装配几何验证通过。官方装配网页请求超时，已记录限制。[分析](Thor_reference_review.md)。
- CyberGear：已克隆到原有目录内的 `reference/cybergear/upstream`，保留原README和用户SLDASM。用上游两份STL组成 [Detail](../freecad/CyberGear_Detail.FCStd)，结合说明书图纸与STL平面孔环提取建立 [Envelope](../freecad/CyberGear_Envelope.FCStd)。没有上游STEP，未声称已直接读取SolidWorks装配。

电机原点定义为输出面中心，局部+Z为输出方向。定子主体Ø75、长度25，后盖Ø63、厚8.5，固定止口Ø43；相对输出面，定子后端为Z=-36.5。前面9-M3固定接口与输出6-M4接口分开建模，输出盘Ø32。说明书标称、网格测量、简化和假设逐项区分，见 [cybergear_interface.md](cybergear_interface.md)。线缆24×16×14预留体的朝向仍是假设；Detail可辅助核对孔位，不能取代实物测量或厂家工程图。

PAROL6/Thor几何未进入我们的Master。来源与许可证事实见 [reference_license_notes.md](reference_license_notes.md)；CyberGear仓库未发现LICENSE，不推定有商业再分发许可。

## 六轴、归属和实体构型

| 关节 | 定子所属刚体 | 转子驱动 | 轴向约定 |
|---|---|---|---|
| J1 | 地面底座 base | 肩架 yaw | 世界+Z |
| J2 | 肩架 yaw | 大臂 upper | 肩架局部-Y |
| J3 | 大臂 upper | 小臂 fore | 大臂局部-Y |
| J4 | 小臂 fore | 腕roll | 小臂局部+X |
| J5 | 腕roll | 腕pitch | roll局部-Y |
| J6 | 腕pitch | 工具 tool | pitch局部+X |

表中为运动学正角轴向；J2/J3/J5的电机输出面朝局部+Y，与正角轴向相反。后续控制坐标映射需明确此符号，当前不涉及控制代码。

BaseHeight=180、UpperArm=320、Forearm=290、Wrist=60、Flange=35、Tool=90 mm，MotorCount=6。用本工作区第一阶段的自身运动学框架，实际检查Master轴线代表点之间的320/290/60/35 mm。

J2、J3是沿Y方向的轴线；其尺寸代表点取y=70 mm，不等于电机输出面中心所在的y=0平面。J1代表点在地面，其实际输出面在z=90 mm。这些是同一轴线上的不同点，不增加虚构的连杆长度。J2高度为180 mm。零角完全伸展时TCP为(795,70,180) mm。

本工作区没有可用于交叉核验的ArmDesigner源码，因此只确认提供的基线尺寸和本地运动学，未声称已完成与ArmDesigner的零位、符号、坐标系回归。

- J1：Ø210开口底座，4 mm壁/径向筋，带嵌件孔的安装柱，可拆电机板、带肩支承座及旋转平台。
- J2：左右支撑板、安装脚/筋，左侧电机，右侧带肩轴承座及压盖，大臂接口与金属贯穿轴构成双侧支承。
- J3：定子固定在大臂末端壳体，可拆前固定板和对侧轴承板；动侧为输出hub、轴和小臂根部。单独改变q3的检查确认定子不动。
- 大臂：4 mm壁与筋的盒壳，24/90 mm过渡形成约14.93°浅弯；X=180处拆为两段，用4-M4连接，盖板可拆。J2→J3始终320 mm。
- 折叠：大臂主壳中心y=-62，小臂y=+70，两者横向相隔132 mm。以侧向错层、局部让位及短支架实现回折，宽度仍待优化。
- J4～J6：独立定子/转子、安装占位与局部让位，保持60/35 mm轴间距及90 mm工具长度；未完成腕部制造细节。

## 最终几何检查

报告：[master_checks.json](../../analysis/stage2/master_checks.json)、[deliverable_checks.json](../../analysis/stage2/deliverable_checks.json)、[STOW余量检查](../../analysis/stage2/stow_margin_check.json)。测试采用包围盒筛选后BRep交集，交叠体积阈值0.1 mm³；接触不作为穿透。结果限于当前简化实体和列出的离散姿态。

| 姿态 | J1/J2/J3/J4/J5/J6（度） | 跨刚体穿透 | 线缆预留冲突 |
|---|---|---|---|
| HOME | 0 / 45 / 65 / 0 / -80 / 0 | 未检出 | 未检出 |
| STOW | 0 / 75 / 165 / 180 / 90 / 0 | 未检出 | 未检出 |
| SAFE_UNFOLD | 0 / 75 / 90 / 180 / 90 / 0 | 未检出 | 未检出 |
| CAKE_APPROACH | 0 / 57.9412 / -77.3316 / 0 / -70.6096 / 0 | 未检出 | 未检出 |

每个姿态检查688组跨刚体组件对，另外检查132组同刚体零件对，均未检出大于阈值的实体穿透。六电机定子简化外形之间最小距离约19.93 mm，发生在J5/J6；这不是所有机械件的最小间隙。线缆预留检查只针对其他刚体，不包括本刚体内部走线。STOW肩部对侧轴承支撑到J4壳体约9.24 mm。

STOW采用J3=165°：试过的168°、170°已有肩部支撑与J4壳体穿透，175°出现多处肩/腕/平台冲突，不能把175°当作可用姿态。小臂可以向大臂一侧折回，腕部仍影响最终收纳范围。没有做连续路径扫掠、线束弯曲仿真、限位开关或真实螺钉工具包络验证；SAFE_UNFOLD只是姿态名称，不是已验证安全轨迹。第一阶段的轨迹结论不能沿用。

15个打印候选实体均为有效单一Solid；本轮重点导出其中J1～J3的13个封闭STL用于试装。完整STEP回读得到41个有效Solid，总体积差约0.00464 mm³；J1/J2/J3子STEP分别为9/8/11个Solid。四份STEP均通过有效性、实体数量和体积回读检查。

## 制造性与未完成工作

主体壁4 mm、筋4 mm、盖4 mm，局部电机板6 mm、平台8 mm；M3/M4/M5通孔3.4/4.5/5.5，嵌件预孔、轴承座和同轴配合均标PROVISIONAL。J2/J3轴承20×42×12占位带肩和压盖，J1支承80×100×10占位未定具体轴承类型。金属轴与输出件不能随意改成打印承力件。

电机从哪一侧装、螺钉访问、轴承安装、子连杆连接及拆卸顺序见 [assembly_concept.md](assembly_concept.md)。轴锁紧、轴承预紧、螺钉有效啮合、打印材料/方向和最终加工图仍需设计，完整待办见 [unresolved_issues.md](unresolved_issues.md)。

**J2转矩是当前首要结构约束。** 以说明书质量下限314 g及参考包络的最小水平力臂，只计J3～J6四个电机，完全水平伸展时J2重力矩下界为6.627 N·m，已高于4 N·m额定转矩。尚未加入壳体、轴、工具或负载。此为保守的电机自重筛查，不是完整载荷计算；需要研究J2减速、配重/弹簧或电机重选后再进行带电带载样机。

## 导出与接续

[完整STEP](../exports/Robot_Master_coarse.step)及J1/J2/J3子总成使用HOME世界坐标；[envelope目录](../exports/envelope/)中的7个STEP则分别位于各自刚体局部坐标。
envelope是每组件的保守AABB盒，不是精确碰撞面；盒之间可能产生保守误报。使用 [armdesigner_bridge_v2.json](../../analysis/stage2/armdesigner_bridge_v2.json) 中各姿态的translation与xyzw四元数放置，不能将七份局部STEP全叠在世界原点。尚未修改或接入ArmDesigner。

全部新增CAD、脚本、导出、文档、截图和验证记录见 [stage2_files.md](stage2_files.md)。当前Arm不是Git仓库，没有初始化；三份上游来源保留在reference，第一阶段文件与用户原SLDASM保留。
