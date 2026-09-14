# 人工接续与回导约定

1. 打开 HOME/STOW 原生 FCStd；树中有 MasterParameters、MasterSkeleton 及 ground/yaw/upper/fore/roll/pitch/tool 七个刚体组。六电机各为独立对象，可检查其 RigidOwner 属性。
2. 用 SolidWorks 检查根目录 SLDASM 是否缺件/含虚拟件，导出完整 STEP，确认 CyberGear 实际型号、外径、轴向长度、连接器、输出面和重量。按 `reference/cybergear/README.md` 放置；本轮模型只是 Ø80×50 假设。
3. 保持320/290中心距，完善肩/肘独立轴承、轴和安装孔，核对145 mm主梁侧向间隔能否缩小。当前细杆、薄板、短轴只是力流连接示意，未定壁厚与材料。
4. 确认蛋糕平台坐标、尺寸、工具形状/重量、工作姿态、速度、急停及最大载荷，再做静力矩、加速度、刚度、疲劳、温升与底座倾覆分析。本轮未指定材料或真实质量，不能给出有效负载结论。
5. 测量线缆弯曲半径、接头朝向及J3/J4可用角度，设置真实止挡和标定零位。验证连续扫掠与完整任务路径，特别是深折叠和从HOME切换到负J3的蛋糕姿态。
6. 参数/真实实体每次变化都重新生成检查；5 mm电机间隙目标不包含线束，接口面的接触/2 mm转接间隙属于粗模接头，需逐一审核。

## ArmDesigner 接口

`analysis/armdesigner_bridge.json` 含四个主姿态的六轴世界坐标、方向、上游帧 quaternion_xyzw 和 TCP；`analysis/motion_checks.json` 还包含蛋糕姿态和展开路径。参数从 `mechanical/parameters.json` 读取。

这是数据交换准备文件，未修改 ArmDesigner，也不声称已兼容其既有 schema。本工作区没有 ArmDesigner 源码，后续需映射它的角度正负、零位、单位和旋转约定。不要复用参考 URDF 的惯量或限位。

运动链（列向量、左乘父帧，长度mm）：

```text
Rz(q1)
T(0,0,BaseHeight) Ry(-q2)
T(UpperArm,0,0) Ry(-q3)
T(Forearm,FoldLane,0) Rx(q4)
T(Wrist,0,0) Ry(-q5)
T(Flange,0,0) Rx(q6)
T(Tool,0,0) → TCP
```

大臂实体偏置 UpperLane 影响碰撞几何；FoldLane同时影响运动学。主骨架的J2/J3基准点位于各自轴线上y=FoldLane位置，其方向数据是关节转动轴而非电机型号输出符号约定。电机实际转向、减速比和编码器单位需另行标定。

## 本轮未完成

- 真实CyberGear导入和孔位匹配；Y-arm参考审查。
- 支承轴承、真实转子/输出法兰、紧固件与装配公差；不存在最终可制造BOM。
- 六轴完整自由度空间与连续碰撞、环境障碍及食品接触工具设计。
- 连续扭矩/热、材料强度和刚度；没有把“几何可达”当成“650mm处可带载作业”。
- 最终工业外观、工艺、工程图和控制器安全路径。
