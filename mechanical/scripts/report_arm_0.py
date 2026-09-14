"""Generate the user-facing V3 report and inventory from measured validation outputs."""
from pathlib import Path
import hashlib
import json
import math


def Report_WriteAll():
    root=Path(__file__).resolve().parents[2]; docdir=root/'mechanical/docs'
    v=json.loads((root/'analysis/v3/validation.json').read_text()); ex=json.loads((root/'analysis/v3/export_checks.json').read_text());cfg=json.loads((root/'mechanical/arm_0_parameters.json').read_text())
    assert not v['failures']
    assert v['geometry_sha256']==hashlib.sha256((root/'mechanical/scripts/build_arm_0.py').read_bytes()).hexdigest()
    for dependency,digest in v['dependency_sha256'].items():
        assert digest==hashlib.sha256((root/'mechanical/scripts'/dependency).read_bytes()).hexdigest(),dependency
    assert v['config_sha256']==hashlib.sha256((root/'mechanical/arm_0_parameters.json').read_bytes()).hexdigest()
    start=v['paths']['STOW_HOME']; unfold=v['paths']['HOME_SAFE_UNFOLD']; old=v['comparison']['legacy_v2'];g=v['gravity'];stow=v['poses']['STOW']['metrics']
    report=['# arm_0 V3：机械拓扑、前折与制造粗模报告','',
        '**正式主文件：[arm_0.FCStd](../freecad/arm_0.FCStd)，文档Label为 `arm_0 | Prototype 0`。** 本轮为物理CAD拓扑重构；源FK函数和六轴转向未修改。当前为静态试装工程粗模，尚非带载制造发布版。','',
        '## Topology','',
        'V2依赖大/小臂中心横向相隔132 mm、长贯穿轴及三个远端电机。V3用子连杆局部双叉包住父关节，主体回到Y=0；J4沿原roll轴线移至近端，J5/J6留在腕部。所有正式几何由本项目独立脚本建立，不导入PAROL6/Thor零件。','',
        '| 关节 | 定子/固定侧 owner | 转子/输出侧 owner | 运动学正角轴向 |','|---|---|---|---|',
        '| J1 | base | yaw | +Z |','| J2 | yaw | upper | 父架局部-Y |','| J3 | upper | fore | 大臂局部-Y |','| J4 | fore | roll | 小臂局部+X |','| J5 | roll | pitch | roll局部-Y |','| J6 | pitch | tool | pitch局部+X |','',
        '电机安装朝向与运动学正角符号分开：J2/J3/J5输出面朝局部+Y。J2/J3代表点和两根中央盒梁均取Y=0；`FoldLane/UpperLane`只保留为锁定零值的历史兼容项。','',
        '## J2','',
        '大臂输出侧叉片直接接短金属hub；对侧叉片用独立短轴颈进入固定轴承支撑。两叉在约80 mm处通过端框并回中央大臂。J2_ThroughShaft已经从正式模型中移除。','',
        '| 指标 | 当前值 |','|---|---|','| 整体关节宽度 | 86 mm（Y=-48…38，含短轴颈外法兰） |','| 子叉片包络 | 83 mm（Y=-45…38） |','| 短轴颈 | Ø19.8×25 mm；含3 mm外法兰总长28 mm，metal |','| 短输出hub | 18 mm轴向范围，metal |','| 对侧轴承 | 20×32×10，GEOMETRIC PLACEHOLDER |','| 支承间距说明 | 输出面到对侧轴承占位中心46 mm；电机内部承载中心未知，未确认真实轴承跨距 |','',
        '![J2双叉与短轴颈](../exports/arm_0_J2_detail.png)','',
        '## J3','',
        'J3定子、前安装支撑和对侧轴承支撑继续属于Rigid_upper。小臂两叉、输出hub和短轴颈属于Rigid_fore。内部隔框承接可拆支撑的紧固载荷，盖板不是唯一承力件。','',
        'J3关节局部宽86 mm，轴颈与轴承占位沿用J2的25 mm和20×32×10。为包住近端J4，叉片局部最大宽104 mm，在约112 mm处并回50 mm中央盒梁。**112 mm超过最初50～80 mm建议**，这是容纳真实电机包络及可拆安装的局部让步；没有恢复整根侧向错层。','',
        '当前前折使用负J3方向，已验证-150°；局部检查中0°、+90°、-90°与-150°没有穿透，-152°/-155°开始发生大臂与J4壳体等冲突。+150°是相反方向的回折，存在多处穿透，明确排除。当前搜索边界[-150°,100°]是CAD约束，不是已选定的实物限位，也不证明边界内任意关节组合都安全。','',
        '![J3与小臂局部叉形](../exports/arm_0_J3_detail.png)','',
        '## J4','',
        '| 指标 | V3 |','|---|---|','| 旧/新输出面距J3 | 290 → 82 mm |','| 新电机轴向包络中心距J3 | 63.75 mm，位于30～80 mm目标区域 |','| 数学J4原点 | 仍在J3之后290 mm；移动的是同一轴线上的执行器 |','| 扭矩管 | OD22 / ID17 / 壁2.5 / 长192 mm，metal，PROVISIONAL |','| 管位置 | 小臂坐标x=90…282 mm |','| 支承 | 近端与远端22.2×32×10轴承占位，带肩座及可拆压盖 |','| 支承中心距 | x=109与267 mm，相距158 mm |','| 接头 | 近端输出适配器、开缝夹紧概念、远端输出hub，均归Rigid_roll |','',
        '轴承和管的0.1 mm径向间隙只用于几何占位。管、接头与末端hub随q4转动；定子和小臂壳保持在Rigid_fore。原生FCStd测试用管上的偏轴见证点确认了该归属。','',
        '角部线槽为8×5 mm，位于Y=12…20、Z=-22…-17，贯穿筋、端框和轴承座。实测对扭矩管间距约9.81 mm、对远端旋转接头约2.81 mm；未检出线槽与实体体积冲突。实际线径、线束弯曲和接插件方向仍需确定。','',
        '![J4远置传动](../exports/arm_0_J4_remote_drive.png)','',
        '| 水平电机自重重力矩下界 | V2 / N·m | V3 / N·m | 变化 / N·m |','|---|---:|---:|---:|',
        f"| J2 | {g['before']['J2_motor_only_lower_bound_Nm']:.4f} | {g['after']['J2_motor_only_lower_bound_Nm']:.4f} | {g['delta_Nm']['J2_motor_only_lower_bound_Nm']:.4f} |",
        f"| J3 | {g['before']['J3_motor_only_lower_bound_Nm']:.4f} | {g['after']['J3_motor_only_lower_bound_Nm']:.4f} | {g['delta_Nm']['J3_motor_only_lower_bound_Nm']:.4f} |",'',
        f"使用CyberGear参考质量下限314 g及水平包络最小力臂。这里只算电机贡献，不含结构/管/线缆/负载。**J2下界仍为{g['after']['J2_motor_only_lower_bound_Nm']:.2f} N·m，超过参考4 N·m额定转矩。**",'',
        '## J5/J6','',
        '经用户确认，Flange由35改为86 mm，其余180/320/290/60/90 mm基线及FK轴序/转向保持。伸直时J5整台电机位于J6后方，两轴垂直；J5转动后J6绕其运动。原来的两层大框均移除。','',
        'J5改用紧凑金属定子支架与独立输出侧轴承座；J6_OnePieceConnector整合夹紧座、单侧6 mm腹板、J6安装环和轴承鼻座。J6工具接头另行拆装，使轴承可装入。轴承仍为15×32×9占位，短轴Ø14.8，J5/J6夹持长12/13 mm；没有完成刚度、预紧或摩擦传扭认证。','',
        f"伸直腕部包围盒XYZ由{' × '.join(f'{x:.2f}' for x in v['compact_wrist']['before']['size_mm'])} mm改为{' × '.join(f'{x:.2f}' for x in v['compact_wrist']['after']['size_mm'])} mm，宽度缩减{v['compact_wrist']['width_reduction_percent']:.1f}%。电机X向包络分离{v['compact_wrist']['extended_motor_axial_gap_mm']:.2f} mm。尺寸包含J5/J6所有物理零件与90 mm工具占位。",'',
        '局部J5角度-120/-90/-45/0/45/90/120°通过抽样实体和间隙检查；这不是整个角域的连续无碰撞认证。CAKE_APPROACH已重算到原目标[500,0,210] mm。旧大框快照见 mechanical/legacy/v3_box_wrist。','',
        '![腕部](../exports/arm_0_wrist.png)','',
        '## Links','',
        '| 主体 | 中心Y | 截面 | 壁 / 筋 |','|---|---:|---|---|','| Upper | 0 mm | 54×64 mm | 4.5 / 4.5 mm |','| Forearm | 0 mm | 50×54 mm | 4.5 / 4.5 mm |','',
        f"大臂在190 mm过渡段内上抬54 mm，约{math.degrees(math.atan2(54,190)):.2f}°；这是实体浅弯，不替代320 mm轴间距。主体最大横向中心偏置为0，关节处才局部加宽。采用空心截面、筋、端框、内部安装隔框和可拆盖板，未把整根连杆做成厚实心块。",'',
        '## Docking','',
        '`front_direction`是可配置水平向量，默认来自J1到工作区方向[1,0,0]。对J3/J4/J5/J6、TCP和主要组件包围盒中心进行前方投影检查；还验证了方向旋转90°后的协变性。','',
        '| 姿态 | J1 / J2 / J3 / J4 / J5 / J6（°） |','|---|---|']
    for name,q in cfg['poses'].items():report.append('| '+name+' | '+' / '.join(f'{x:.4f}'.rstrip('0').rstrip('.') if x else '0' for x in q)+' |')
    report += ['', '| 启动路径 | 最大关节变化 | TCP行程 | 腕部J5行程 | 最大后方越界 | 外部最小间隙 | 采样点 |','|---|---:|---:|---:|---:|---:|---:|']
    for name,data in [('STOW→HOME',start),('HOME→SAFE_UNFOLD',unfold)]:
        report.append(f"| {name} | {data['max_joint_delta_deg']:.1f}° | {data['tcp_path_length_mm']:.2f} mm | {data['wrist_path_length_mm']:.2f} mm | {data['maximum_backward_excursion_mm']:.2f} mm | {data['minimum_external_clearance_mm']:.3f} mm | {data['sample_count']} |")
    report += ['',f"STOW→HOME所有被检查主要中心的最小前方投影为{start['minimum_front_projection_mm']:.2f} mm；HOME→SAFE_UNFOLD为{unfold['minimum_front_projection_mm']:.2f} mm。J1全程不变，没有180°转身解折。SAFE_UNFOLD的400 mm特征长度缩放几何Jacobian条件数约{v['poses']['SAFE_UNFOLD']['jacobian']['condition_number']:.2f}，本次数值筛查没有接近秩亏；不是完整控制安全证明。",'',
        '| STOW与启动比较 | V2后折 | V3前折 |','|---|---:|---:|',
        f"| STOW物理径向包围范围 | {old['stow']['physical_radial_extent_mm']:.2f} mm | {stow['physical_radial_extent_mm']:.2f} mm |",
        f"| STOW物理高度 | {old['stow']['height_mm']:.2f} mm | {stow['height_mm']:.2f} mm |",
        f"| STOW→HOME最大关节变化 | {old['max_joint_delta_deg']:.1f}° | {start['max_joint_delta_deg']:.1f}° |",
        f"| STOW→HOME TCP行程 | {old['tcp_path_length_mm']:.2f} mm | {start['tcp_path_length_mm']:.2f} mm |",
        f"| 启动最大后方越界 | {old['maximum_backward_excursion_mm']:.2f} mm | {start['maximum_backward_excursion_mm']:.2f} mm |",
        '| 启动扫掠总包围盒XYZ | '+' × '.join(f'{x:.1f}' for x in old['swept_size_mm'])+' mm | '+' × '.join(f'{x:.1f}' for x in start['swept_size_mm'])+' mm |','',
        '径向范围用各实体世界包围盒角点保守计算；扫掠是采样全机（含静止底座）的联合包围盒，不是解析扫掠体或体积并集。旧版数据使用真实V2几何和原姿态，只重算运动指标，未重新认证旧路径无碰撞。','',
        '![V3前折](../exports/arm_0_STOW_forward.png)','![V2后折，仅对比](../exports/arm_0_STOW_legacy_backward.png)','',
        '## Naming','',
        '正式入口、文件名、GUI标签、参数、宏和README已统一为arm_0。旧主文件、脚本、STEP、姿态图与试装件移至 `mechanical/legacy/v2/` 并标记SUPERSEDED。当前脚本中剩余旧名称只用于显式加载V2对比源；没有继续指向旧主工程的日常入口。PAROL6、CyberGear、Thor参考名称保持不变。','',
        '## Manufacturing','',
        f"当前输出{len(ex['print_fit'])}个封闭打印候选STL、{len(ex['step_round_trip'])}份实体STEP及七份轻量局部包络。金属件与轴承不混入打印清单。各件尺寸见[文件清单](arm_0_files.md)及[export_checks.json](../../analysis/v3/export_checks.json)。",'',
        '装配顺序、拆卸方向、压盖/叉片先后关系与工具访问见[assembly_concept.md](assembly_concept.md)。电机接口均为REFERENCE-DERIVED / HARDWARE VERIFY，轴承全部为GEOMETRIC PLACEHOLDER，无SELECTED COMPONENT。打印工艺、紧固件长度、金属锁紧和真实预紧仍未释放。','',
        '## Validation','',
        f"FreeCAD原生模型包含{len(v['valid_solids'])}个有效单一实体组件（其中7个为隐藏空间预留），物理组件{sum(x['role']!='reserve' for x in v['valid_solids'])}个。每个姿态/路径采样检查{v['poses']['HOME']['check']['tested_pairs']}组跨刚体对，另查{v['same_rigid']['tested_pairs']}组同刚体零件对。没有按“相邻关节”豁免穿透。",'',
        '所有物理实体交叠体积阈值为0.1 mm³。整体最小实体距离为0，来自明确列出的电机内部面和J1支承预期接触；这些对仍检查穿透。单列的轴承配合按至少0.08 mm检查，当前约0.1 mm；其他外部运动间隙按至少1 mm检查。不能把“外部1 mm”说成全部零件均隔开1 mm。','',
        '四个关键姿态及两段不超过2°步长的插值路径全部通过当前实体检查。**这是连续路径的离散采样检查，不是解析连续碰撞保证**，仍可能漏掉采样间更窄的干涉。线槽分区也通过实体检查。','',
        '| STEP回读 | 有效Solid数量 | 体积误差 / mm³ |','|---|---:|---:|']
    for name,data in ex['step_round_trip'].items():report.append(f"| {name} | {data['solids']} | {data['volume_error_mm3']:.8f} |")
    report += ['', 'STEP除完整有效实体数量外，还逐件验证质心/边界误差小于0.001 mm、相对体积误差小于1e-5；全文件体积误差须同时小于1 mm³和1e-5相对值。布尔曲面数值积分误差按实测值列出。','']
    report += ['', '报告来源：[validation.json](../../analysis/v3/validation.json)、[export_checks.json](../../analysis/v3/export_checks.json)、[docking_search.json](../../analysis/v3/docking_search.json)。候选搜索记录保留过程，最终结论以记录最终脚本与参数哈希的validation为准。局部轴承/电机/壳体仍为简化几何。','',
        '## Remaining Issues','',
        'J2转矩余量、实际CyberGear孔位、接插件、夹紧接头和轴承选型是下一轮优先项。扭矩管远端短夹持、金属件加工、公差链、打印强度、线束动态弯曲和SAFE_UNFOLD→任务路径仍需继续。详细清单见[unresolved_issues.md](unresolved_issues.md)。','',
        '当前结果可用于模型核对和静态打印试装，不能直接声称带载可用。']
    (docdir/'arm_0_v3_review.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    sections={'CAD':[root/'mechanical/freecad/arm_0.FCStd'],
        '参数与脚本':[root/'mechanical/arm_0_parameters.json']+sorted((root/'mechanical/scripts').glob('*arm_0*'))+[root/'mechanical/scripts'/n for n in ['SetArm0Pose.FCMacro','RebuildArm0.FCMacro','ReviewArm0.FCMacro','compact_wrist_review.py']],
        'STEP':sorted((root/'mechanical/exports').glob('arm_0*.step'))+sorted((root/'mechanical/exports/envelope').glob('arm_0*.step')),
        '试装STL':sorted((root/'mechanical/exports/print_fit').glob('*.stl')),
        '原生CAD截图':sorted((root/'mechanical/exports').glob('arm_0*.png')),
        '文档':[root/'README.md',root/'mechanical/README.md']+[docdir/n for n in ['arm_0_v3_review.md','assembly_concept.md','unresolved_issues.md','reference_license_notes.md']],
        '验证':sorted((root/'analysis/v3').glob('*.json'))}
    inventory=['# arm_0 V3 文件清单','','当前主文件为 `mechanical/freecad/arm_0.FCStd`。参考模型不改名；旧版在 `mechanical/legacy/v2/`。','',
        '当前清单本身是 `mechanical/docs/arm_0_files.md`；哈希清单为 `analysis/v3/manifest.json`，两者不参与自循环哈希。','']
    manifest=[]
    for title,paths in sections.items():
        inventory += ['## '+title,'','| 文件 | 字节 |','|---|---:|']
        for path in paths:
            if not path.is_file() or path.name=='manifest.json':continue
            rel=path.relative_to(root).as_posix();data=path.read_bytes()
            inventory.append(f'| [{rel}](../../{rel}) | {len(data)} |');manifest.append(dict(path=rel,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        inventory.append('')
    (docdir/'arm_0_files.md').write_text('\n'.join(inventory),encoding='utf-8')
    (root/'analysis/v3/manifest.json').write_text(json.dumps(dict(files=manifest),indent=2),encoding='utf-8')
    print('Report generated; files',len(manifest))


if __name__=='__main__': Report_WriteAll()
