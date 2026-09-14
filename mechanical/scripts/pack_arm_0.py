"""Pack only audited SolidWorks handoff files; downloaded references never enter the whitelist."""
from pathlib import Path
import csv,json,hashlib,zipfile,shutil,subprocess,re


def Hash_Get(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def Handoff_Pack():
    root=Path(__file__).resolve().parents[2];stage=root/'mechanical/handoff/solidworks';dist=root/'dist';dist.mkdir(exist_ok=True)
    validation=json.loads((root/'analysis/v4/assembly_validation.json').read_text(encoding='utf-8'));exports=json.loads((root/'analysis/v4/handoff_export_checks.json').read_text(encoding='utf-8'))
    assert validation['valid'],'Fix geometry and service failures before packaging'
    assert validation['config_sha256']==Hash_Get(root/'mechanical/arm_0_parameters.json'),'Stale configuration validation'
    for n,h in validation['geometry_sources_sha256'].items():assert Hash_Get(root/'mechanical/scripts'/n)==h,'Stale geometry validation: '+n
    for r in json.loads((root/'analysis/v4/table_checks.json').read_text(encoding='utf-8')):assert r['sha256']==Hash_Get(root/'mechanical/docs'/r['file']),'CSV changed after verification'
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    manifest=list(csv.DictReader((root/'mechanical/docs/assembly_manifest.csv').read_text(encoding='utf-8-sig').splitlines()))
    fast=list(csv.DictReader((root/'mechanical/docs/fastener_schedule.csv').read_text(encoding='utf-8-sig').splitlines()))
    receivers={'CYBERGEAR_THREAD','METAL_TAPPED_THREAD','HEX_NUT','LOCK_NUT','FOUR_WAY_NUT_BLOCK'}
    assert len({r['Fastener_ID'] for r in fast})==len(fast) and all(r['Receiver_Type'] in receivers for r in fast)
    images=['arm_0_'+n+'.png' for n in ['HOME','STOW','SAFE_UNFOLD','CAKE_APPROACH','J2_detail','J3_detail','J4_remote_drive','wrist']]
    documents=['fastener_schedule.csv','arm_0_BOM.csv','assembly_manifest.csv','joint_datums.csv','parameter_summary.csv','hole_function_register.csv','hardware_to_measure.md','fastener_envelope_sources.md','arm_0_v3_review.md','assembly_concept.md','unresolved_issues.md','review_checklist.md']
    for name in documents:
        src=root/'mechanical/docs'/name;dest=stage/'04_DOCS'/name
        if name.endswith('.md'):
            text=src.read_text(encoding='utf-8-sig').replace('../exports/','../05_IMAGES/').replace('../freecad/','../01_ASSEMBLY/')
            assert not re.search(r'Flange\s*(?:=|为|：|:)\s*35|35\s*mm腕距|legacy_backward|热熔嵌件连接',text,re.I),name
            dest.write_text(text,encoding='utf-8')
        else:shutil.copy2(src,dest)
    for name in images:shutil.copy2(root/'mechanical/exports'/name,stage/'05_IMAGES'/name)
    shutil.copy2(root/'mechanical/freecad/arm_0.FCStd',stage/'01_ASSEMBLY/arm_0.FCStd')
    reports=['assembly_validation.json','handoff_export_checks.json','table_checks.json','freeze_audit.json']
    for name in reports:shutil.copy2(root/'analysis/v4'/name,stage/'04_DOCS'/name)
    schema=exports['round_trips'][0]['schema'];ap='AP214 (AUTOMOTIVE_DESIGN)' if 'AUTOMOTIVE_DESIGN' in schema else schema
    readme=f'''# arm_0 SolidWorks 首次审图交接

代码提交：`{sha}`。文件生成于2026-09-14，单位mm。基线180/320/290/60/86/90 mm；J5→J6=86 mm，UpperLane=FoldLane=0。STEP文件头实际FILE_SCHEMA为 `{schema}`，对应{ap}；没有宣称导出AP242。

## 从这里打开

先打开 `01_ASSEMBLY/arm_0_HOME.step`。SolidWorks导入选项与许可证版本可能不同：导入后执行 Import Diagnostics（导入诊断），检查实体数、坏面和单位。若识别为装配，另存为SLDASM；若导入为多实体零件，使用保存实体/单件STEP重建装配。以 `04_DOCS/assembly_manifest.csv` 的HOME位移和四元数xyzw恢复每个零件。不要把所有本地原点零件直接重叠后当成正确装配。

`arm_0_STOW_reference.step`仅为冻结收纳姿态参考；主装配以HOME为准。`arm_0.FCStd`供FreeCAD查看和溯源，FreeCAD特征树不会经STEP自动转换为SolidWorks可编辑历史。当前项目的脚本生成参数和特征也不能被视为原生SolidWorks草图、配合或加工图。

## 文件约定

- `02_PARTS_STEP`按打印、金属、电机参考、轴承占位、五金占位分类。每个文件为独立有效实体，原点移至自身质心，轴向保持所属刚体方向；manifest给出恢复HOME的完整变换。
- `03_PRINT_STL`仅有{exports['printed_stl']}个打印结构试装候选，不含电机/轴承/金属件/螺母/空间预留。STL为mm，需在切片器核对单位。
- `04_DOCS/joint_datums.csv`提供HOME六轴原点、轴向与父子关系；parameter_summary区分CONFIRMED_BASELINE、PROVISIONAL、HARDWARE_VERIFY、PLACEHOLDER。
- 紧固件表{len(fast)}个接口；所有采购螺钉长度TBD。包络轴长包含夹层和保守占用，不是已核定的采购长度。六个电机各分定子与转子两参考实体；BOM按6个完整电机计数。
- FourWayNutBlock候选按用户指定第五行2-M4×8-H10×22，仅供两块独立板材90°连接。图片标称22×10×10、M4、两对孔距8、L3=5；孔深/交孔待实测。当前安装0；独立CATALOG件不能加入运动装配。示意盲孔3 mm不可用于加工。
- `05_IMAGES`为当前四姿态和四个局部原生CAD截图，没有历史反折或旧腕部图。

## 检查与状态

所有STEP都已重新读取并检查实体有效性、数量、体积、质心和包围盒。容差：整文件体积误差<1 mm³且相对<1e-5；每实体体积相对<1e-5、质心和边界误差<0.001 mm。布尔/圆锥积分噪声与几何位置误差分别记录。详情见handoff_export_checks.json。

四冻结姿态、STOW→HOME及HOME→SAFE_UNFOLD以≤2°采样，包含实际螺钉头、螺母与垫圈占位；工具仅作静态分阶段维修检查。离散检查不证明采样间或其他姿态连续无碰撞。电机接口、轴承选型、台面厚度、螺钉长度、金属强度/公差/预紧、打印材料与所有夹紧传扭仍需验证。本包只用于首次审图和静态试装准备，不是生产文件。

SHA256SUMS列出本目录内除清单自身外的所有交接文件哈希。ZIP经重新打开验证CRC、白名单和逐文件SHA256。下载的PAROL6/Thor、上游CAD/STL、参考资料、Git、历史版本、日志和缓存不在包内。ZIP单独交接，未提交Git。
'''
    (stage/'README_SOLIDWORKS.md').write_text(readme,encoding='utf-8')
    (stage/'HANDOFF_STATUS.md').write_text(f'''# 首次审图状态

CONFIRMED_BASELINE：六轴拓扑、180/320/290/60/86/90 mm、主体Y=0、四冻结姿态。代码提交{sha}。

PROVISIONAL：局部壁厚、凹座、螺母槽、金属连接件、扭矩管及夹紧；M4连接块按图片选型，非实测。当前不装连接块，普通夹层用螺钉和防松螺母。

HARDWARE_VERIFY：全部螺钉长度、电机螺纹/止口、台厚、实际标准件、连接块孔深/交孔、材料/公差/预紧、拆装工具与强度。

PLACEHOLDER：轴承、标准五金包络、独立未安装目录件。

验证几何通过：{validation['valid_geometry']}；静态分阶段拆装未通过接口：{validation['unserviceable_interfaces']}。实体STEP回读{exports['step_files']}个、单件STEP {exports['part_step_files']}个、打印STL {exports['printed_stl']}个。这些检查不构成生产或承载批准。
''',encoding='utf-8')
    allowed={'README_SOLIDWORKS.md','HANDOFF_STATUS.md','01_ASSEMBLY/arm_0_HOME.step','01_ASSEMBLY/arm_0_STOW_reference.step','01_ASSEMBLY/arm_0.FCStd'}
    allowed.update(r['step_file'] for r in manifest)
    allowed.update('03_PRINT_STL/'+r['part_name']+'.stl' for r in manifest if r['category']=='PRINTED')
    allowed.update('04_DOCS/'+n for n in documents+reports);allowed.update('05_IMAGES/'+n for n in images)
    assert all((stage/n).is_file() for n in allowed)
    hashes={n:Hash_Get(stage/n) for n in sorted(allowed)}
    (stage/'SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in hashes.items()),encoding='utf-8');allowed.add('SHA256SUMS')
    zip_path=dist/'arm_0_SW_handoff_20260914.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in sorted(allowed):z.write(stage/n,n)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None and set(z.namelist())==allowed
        for n,h in hashes.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
        assert not any(re.search(r'(^|/)(reference|legacy|\.git|__pycache__)(/|$)|PAROL6|Thor|legacy_backward|\.log$',n,re.I) for n in z.namelist())
    digest=Hash_Get(zip_path);(dist/(zip_path.name+'.sha256')).write_text(digest+'  '+zip_path.name+'\n',encoding='ascii')
    result=dict(path=str(zip_path),size_bytes=zip_path.stat().st_size,sha256=digest,git_commit=sha,files=len(allowed),crc=True,file_hashes=True,whitelist=True)
    (dist/'handoff_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':Handoff_Pack()
