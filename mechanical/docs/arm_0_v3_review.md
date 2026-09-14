# arm_0 Prototype 0：冻结拓扑与首次审图

主工程为arm_0.FCStd，标签arm_0 | Prototype 0。本轮沿用V3拓扑并整理紧固、局部避空和交接文件，不重新搜索姿态。当前基线180/320/290/60/86/90 mm，UpperLane=FoldLane=0；J5→J6=86 mm。

| 关节 | 父刚体 | 子刚体 | 正角轴 |
|---|---|---|---|
| J1 | base | yaw | +Z |
| J2 | yaw | upper | 局部-Y |
| J3 | upper | fore | 局部-Y |
| J4 | fore | roll | 局部+X |
| J5 | roll | pitch | 局部-Y |
| J6 | pitch | tool | 局部+X |

J2为大臂子叉包住父关节，J3为小臂子叉包住父关节，均为短输出hub与对侧短轴颈。定子分别固定在yaw和upper。主体为空心居中盒梁，盖板可拆，内部筋与壳体整体打印。

J4电机包络中心在J3后63.75 mm、输出面82 mm；数学J4轴原点仍在小臂末端290 mm。金属扭矩管OD22/ID17/长192 mm位于小臂x=90…282，旋转管与端部接头属于roll，壳体和两处轴承属于fore。8×5 mm角部线槽独立预留。

J5/J6伸直时前后排列，通过一体金属连接件和独立工具接头形成紧凑腕部。轴承和夹紧仍为几何占位；不得将金属连接件替换为普通打印材料。局部新增标准螺钉头凹座、螺母槽和轴承座安装耳，不改变上述轴系。

| 姿态 | 六轴角度 / deg |
|---|---|
| STOW | 0,55,-150,0,95,0 |
| HOME | 0,52,-142,0,90,0 |
| SAFE_UNFOLD | 0,50,-110,0,60,0 |
| CAKE_APPROACH | 见parameter_summary.csv；TCP目标500,0,210 mm |

实体、紧固件、同刚体和跨刚体的检查及两条启动路径结果以assembly_validation.json为准。两路径为STOW→HOME和HOME→SAFE_UNFOLD，最大步长2°；不代表任意关节组合、采样间隙或完整任务路径都通过。

![HOME](../exports/arm_0_HOME.png)
![STOW](../exports/arm_0_STOW.png)
![SAFE_UNFOLD](../exports/arm_0_SAFE_UNFOLD.png)
![CAKE_APPROACH](../exports/arm_0_CAKE_APPROACH.png)
![J2](../exports/arm_0_J2_detail.png)
![J3](../exports/arm_0_J3_detail.png)
![J4](../exports/arm_0_J4_remote_drive.png)
![J5/J6](../exports/arm_0_wrist.png)

首次审图仍需处理：J2载荷裕量不足、实际轴承选择、金属件刚度/疲劳、公差/预紧、夹紧传扭、所有螺钉长度、实际电机孔深、打印材料与方向。STEP和STL只是审图/静态试装候选，不是生产发布。
