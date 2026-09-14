"""Whitelist SolidWorks review export. Run with the bundled FreeCAD Python."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,re
from collections import Counter
import FreeCAD as App
import Part,Mesh,MeshPart
import build_arm_0 as arm
from fasteners_arm_0 import Fastener_Apply,Shape_GetHex
from validate_assembly_arm_0 import Assembly_RunValidation


def Step_CheckRoundTrip(path,reference):
    imported=Part.read(str(path));original=[v['shape'].Solids[0] for v in reference];remaining=[(x,x.CenterOfMass) for x in imported.Solids];rows=[]
    assert imported.isValid() and len(remaining)==len(original),(str(path),'topology')
    for part,shape in zip(reference,original):
        center=shape.CenterOfMass;entry=min(remaining,key=lambda x:(x[1]-center).Length);remaining.remove(entry);other=entry[0]
        dv=abs(other.Volume-shape.Volume)/shape.Volume;dc=(other.CenterOfMass-shape.CenterOfMass).Length
        db=max(abs(getattr(other.BoundBox,k)-getattr(shape.BoundBox,k)) for k in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
        assert other.isValid() and dv<1e-5 and dc<.001 and db<.001,(path.name,part['name'],dv,dc,db)
        rows.append(dict(name=part['name'],relative_volume_error=dv,center_error_mm=dc,bounds_error_mm=db))
    vol=sum(s.Volume for s in original);error=abs(imported.Volume-vol)
    assert error<1 and error/vol<1e-5,(path.name,error)
    header=path.read_text(encoding='utf-8',errors='replace')[:3000];schema=re.search(r'FILE_SCHEMA\s*\(\((.*?)\)\)',header,re.S)
    return dict(file=path.name,valid=True,solids=len(original),volume_error_mm3=error,schema=schema.group(1) if schema else 'UNKNOWN',parts=rows)


def Catalog_GetParts():
    from fasteners_arm_0 import Hardware_GetDimensions
    result=[]
    for size in [3,4,5]:
        d=Hardware_GetDimensions(size)
        for kind,h in [('HexNut',d['nut_h']),('LockNut',d['lock_h'])]:
            shape=Shape_GetHex(d['af'],h,(0,0,0),(0,0,1)).cut(Part.makeCylinder((size+.1)/2,h))
            result.append(dict(name=f'M{size}_{kind}_CATALOG',shape=shape,role='hardware_placeholder',owner='catalog',assembly='CATALOG',note='Uninstalled standard envelope; supplier verification required'))
    block=arm.Shape_Box(22,10,10,0,-5,-5)
    # Nominal first-direction edge L3 from image; front offset inferred by symmetry.
    # 3 mm visual hole depth is expressly not a machining dimension.
    for x in [9,17]:block=block.cut(Part.makeCylinder(1.65,3,App.Vector(x,0,5),App.Vector(0,0,-1)))
    for x in [5,13]:block=block.cut(Part.makeCylinder(1.65,3,App.Vector(x,-5,0),App.Vector(0,1,0)))
    result.append(dict(name='FourWayNutBlock_PLACEHOLDER',shape=block,role='hardware_placeholder',owner='catalog',assembly='CATALOG',note='2-M4*8-H10*22 / image nominal 22x10x10, pitch8, L3=5; hole depth 3 is visual only, front offset inferred; MEASURE SCHOOL HARDWARE; installed qty0'))
    return result


def Handoff_PrepareTables(root,cfg,parts,plan,manifest,datums):
    tables={};headers=['Fastener_ID','Joint','Part_A','Part_B','Screw_Size','Qty','Screw_Type','Part_A_Hole','Receiver_Type','Nut_Type','Washer','Insertion_Direction','Tool_Access_Direction','Tool','Serviceable','Status','Notes'];rows=[]
    validation=json.loads((root/'analysis/v4/assembly_validation.json').read_text(encoding='utf-8'));service={v['id']:v for v in validation['service']}
    for r in plan:
        rows.append([r['id'],r['joint'],r['a'],r['b'],'M'+str(r['size']),len(r['points']),'ISO4762 envelope / length TBD',f"THROUGH diameter {r['size']+(.4 if r['size']==3 else .5):.1f} mm",r['receiver'],r['receiver'] if 'NUT' in r['receiver'] else 'NONE','Both ends' if r['washer'] else 'None / direct seat',str(r['axis'])+' in '+r['owner'],str(tuple(-x for x in r['axis']))+' in '+r['owner'],'Hex key '+str({3:2.5,4:3,5:4}[r['size']])+' mm', 'YES / staged' if service[r['id']]['serviceable'] else 'REVIEW BLOCKED','PROVISIONAL / LENGTH TBD / HARDWARE VERIFY',r['note']+' | removal prerequisites: detached rigid subassembly; '+', '.join(r['remove'])+' | Nut entry '+str(r['nut_entry'])])
    tables['fastener_schedule.csv']=[headers]+rows
    bom=[['Item_ID','Part_Name','Qty','Category','Material','Manufacturing_Method','Fastener_Size','Selected_Component','Status','Notes']];i=0
    for v in parts:
        if v['role'] in ['reserve','hardware_placeholder']:continue
        i+=1;role=v['role'];bom.append([f'B-{i:03d}',v['name'],1,role,'TBD polymer' if role=='printed' else 'TBD metal','FDM candidate' if role=='printed' else 'Machining TBD' if role=='metal' else 'Purchased reference','', 'CyberGear reference' if role in ['motor','rotor'] else 'TBD','HARDWARE_VERIFY' if role in ['motor','rotor'] else 'PLACEHOLDER' if role=='bearing' else 'PROVISIONAL',v.get('note','')+(' | Stator/rotor are two shapes of ONE motor, not two purchased motors' if role in ['motor','rotor'] else '')])
    counts=Counter((v['size'],v['hardware_kind']) for v in parts if v['role']=='hardware_placeholder')
    for (size,kind),qty in sorted(counts.items()):
        i+=1;bom.append([f'B-{i:03d}',f'M{size}_{kind}',qty,'FASTENER','Steel TBD','Purchased',f'M{size}','TBD supplier','HARDWARE_VERIFY','Installed envelopes; bolt length TBD; each instance traced by fastener_schedule; washer envelope is provisional'])
    i+=1;bom.append([f'B-{i:03d}','FourWayNutBlock',0,'CATALOG','Metal TBD','Purchased','M4','2-M4*8-H10*22','PROVISIONAL / IMAGE SPECIFICATION','User will purchase fifth row. 90 degree independent-plate connections only. Current interfaces are parallel stacks or integral ribs, installed0. Hole depths TBD.'])
    tables['arm_0_BOM.csv']=bom
    tables['assembly_manifest.csv']=[list(manifest[0])]+[list(v.values()) for v in manifest]
    tables['joint_datums.csv']=[list(datums[0])]+[list(v.values()) for v in datums]
    params=[['Parameter','Value','Unit','Status','Notes']]
    for k,v in cfg['dimensions'].items():
        if (k in cfg['deprecated_parameters'] or k in cfg.get('reserved_parameters',[])) and k not in cfg['confirmed_baseline'] and k not in ['FoldLane','UpperLane']:continue
        params.append([k,v,'count' if k=='MotorCount' else 'mm','CONFIRMED_BASELINE' if k in cfg['confirmed_baseline'] or k in ['FoldLane','UpperLane'] else 'PROVISIONAL','Frozen joint origins; local detailed dimensions provisional'])
    for k,v in cfg['school_hardware'].items():
        if k.startswith('nut_block_'):params.append([k,'TBD' if v is None else v,'mm or thread','HARDWARE_VERIFY' if v is None else 'PROVISIONAL','User image fifth row; not measured'])
    for k,v in cfg['poses'].items():params.append([k,str(v),'deg','CONFIRMED_BASELINE','No pose search or optimization this round'])
    params.append(['Bearing_selection','TBD','','PLACEHOLDER','Geometric envelopes only'])
    tables['parameter_summary.csv']=params
    holes=[['Feature','Part','Purpose','Interface','Status']]
    for r in plan:holes.append([f"{r['size']+(.4 if r['size']==3 else .5):.1f} mm through pattern",r['a'],'Fastener clearance',r['id'],'REVIEW'])
    holes += [['Bearing bores / tube passage','Bearing seats and hubs','Bearing fit / rotating tube','NON_FASTENER','PLACEHOLDER'],['Central / corner cable openings','Central beams and wrists','Cable / service route','NON_FASTENER','PROVISIONAL'],['Motor interface tapped holes','CyberGear references','9-M3 fixed / 6-M4 output','CYBERGEAR_THREAD','HARDWARE_VERIFY'],['Clamp lower half tap','J4_DistalOutputHub','M3 metal clamp thread','F-J4-010','HARDWARE_VERIFY']]
    tables['hole_function_register.csv']=holes
    (root/'analysis/v4/tables_input.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf-8')
    return counts


def Handoff_Export(parts=None,plan=None):
    root=Path(__file__).resolve().parents[2];cfg=arm.Arm0_LoadConfig();p=cfg['dimensions'];stage=root/'mechanical/handoff/solidworks'
    if parts is None:parts,plan=Fastener_Apply(arm.Arm0_GetComponents(p,False),p)
    validation=Assembly_RunValidation(parts,plan) if '--validate' in sys.argv else json.loads((root/'analysis/v4/assembly_validation.json').read_text(encoding='utf-8'))
    assert validation['valid'],'Geometry and staged service validation must pass before export'
    categories={'printed':'PRINTED','metal':'METAL','motor':'MOTOR_REFERENCE','rotor':'MOTOR_REFERENCE','bearing':'BEARING_PLACEHOLDER','hardware_placeholder':'HARDWARE_PLACEHOLDER'}
    for d in ['01_ASSEMBLY','03_PRINT_STL','04_DOCS','05_IMAGES']+['02_PARTS_STEP/'+x for x in categories.values()]: (stage/d).mkdir(parents=True,exist_ok=True)
    if '--reuse-native' not in sys.argv:
        doc,_=arm.Arm0_BuildDocument(cfg,False,parts)
        group=doc.addObject('App::DocumentObjectGroup','UninstalledHardwareCatalog')
        for cat in Catalog_GetParts():
            obj=doc.addObject('PartDesign::Feature',cat['name']);obj.Shape=cat['shape'];group.addObject(obj)
            obj.addProperty('App::PropertyString','ReferenceStatus');obj.ReferenceStatus=cat['note'];obj.addProperty('App::PropertyInteger','InstalledQuantity');obj.InstalledQuantity=0
        doc.recompute();doc.saveAs(str(root/'mechanical/freecad/arm_0.FCStd'));App.closeDocument(doc.Name)
    else:
        # Resume export after an export-only failure without overwriting reviewed GUI styling.
        assert validation['config_sha256']==hashlib.sha256((root/'mechanical/arm_0_parameters.json').read_bytes()).hexdigest()
        for name,digest in validation['geometry_sources_sha256'].items():assert hashlib.sha256((root/'mechanical/scripts'/name).read_bytes()).hexdigest()==digest
        doc=App.openDocument(str(root/'mechanical/freecad/arm_0.FCStd'))
        for part in parts:
            body=doc.getObject(part['name']);native=body.Tip.Shape
            assert body.FrameKey==part['owner'] and native.isValid() and len(native.Solids)==1
            assert abs(native.Volume-part['shape'].Volume)/part['shape'].Volume<1e-8,part['name']
            assert max(abs(getattr(native.BoundBox,k)-getattr(part['shape'].BoundBox,k)) for k in ['XMin','XMax','YMin','YMax','ZMin','ZMax'])<.001,part['name']
        App.closeDocument(doc.Name)
    shutil.copy2(root/'mechanical/freecad/arm_0.FCStd',stage/'01_ASSEMBLY/arm_0.FCStd')
    checks=[];manifest=[];frames,home=arm.Arm0_GetWorldParts(p,cfg['poses']['HOME'],parts)
    for pose,filename in [('HOME','arm_0_HOME.step'),('STOW','arm_0_STOW_reference.step')]:
        _,world=arm.Arm0_GetWorldParts(p,cfg['poses'][pose],parts);physical=[v for v in world if v['role']!='reserve'];path=stage/'01_ASSEMBLY'/filename
        arm.Arm0_ExportParts(physical,path);checks.append(Step_CheckRoundTrip(path,physical))
        if pose=='HOME':shutil.copy2(path,root/'mechanical/exports/arm_0.step')
    arm.Arm0_ExportParts([v for v in parts if v['name']=='J6_OnePieceConnector'],root/'mechanical/exports/arm_0_J6_OnePieceConnector.step')
    for joint in ['J1','J2','J3']:
        arm.Arm0_ExportParts([v for v in home if v['assembly']==joint],root/'mechanical/exports'/('arm_0_'+joint+'.step'))
    arm.Arm0_ExportParts([v for v in home if v['assembly'] in ['J5','J6']],root/'mechanical/exports/arm_0_wrist.step')
    for index,v in enumerate([x for x in parts if x['role']!='reserve']+Catalog_GetParts(),1):
        local=dict(v);c=v['shape'].Solids[0].CenterOfMass;shape=v['shape'].copy();shape.translate(-c);local['shape']=shape
        category=categories[v['role']];rel='02_PARTS_STEP/'+category+'/'+v['name']+'.step';path=stage/rel
        arm.Arm0_ExportParts([local],path);checks.append(Step_CheckRoundTrip(path,[local]))
        placement=App.Placement(c,App.Rotation()) if v['owner']=='catalog' else frames[v['owner']].multiply(App.Placement(c,App.Rotation()))
        xyz=list(placement.Base);quat=list(placement.Rotation.Q)
        manifest.append(dict(part_name=v['name'],step_file=rel,quantity=0 if v['owner']=='catalog' else 1,category=category,role=v['role'],rigid_link=v['owner'],subassembly=v['assembly'],HOME_tx_mm=xyz[0],HOME_ty_mm=xyz[1],HOME_tz_mm=xyz[2],HOME_qx=quat[0],HOME_qy=quat[1],HOME_qz=quat[2],HOME_qw=quat[3],reference_status='PLACEHOLDER' if v['role'] in ['bearing','hardware_placeholder'] else 'HARDWARE_VERIFY' if v['role'] in ['motor','rotor'] else 'PROVISIONAL',notes=v.get('note','')+' | origin: part centroid, axes parallel rigid frame'))
        if v['role']=='printed':
            mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,AngularDeflection=.2,Relative=False);stl=stage/'03_PRINT_STL'/(v['name']+'.stl');mesh.write(str(stl));assert Mesh.Mesh(str(stl)).isSolid(),v['name']
            shutil.copy2(stl,root/'mechanical/exports/print_fit'/stl.name)
        if index%50==0:print('LOCAL STEP',index,flush=True)
    datums=[];parents=['base','yaw','upper','fore','roll','pitch'];children=['yaw','upper','fore','roll','pitch','tool']
    for i,a in enumerate(arm.arm_model.Arm_GetAxes(p,frames)):
        datums.append(dict(joint=a['name'],parent=parents[i],child=children[i],origin_x_mm=a['origin_mm'][0],origin_y_mm=a['origin_mm'][1],origin_z_mm=a['origin_mm'][2],axis_x=a['axis_world'][0],axis_y=a['axis_world'][1],axis_z=a['axis_world'][2],reference_pose='HOME',angle_deg=cfg['poses']['HOME'][i],status='CONFIRMED_BASELINE',dimension_chain='180/320/290/60/86/90 mm; offsets0'))
    counts=Handoff_PrepareTables(root,cfg,parts,plan,manifest,datums)
    report=dict(step_files=len(checks),part_step_files=len(manifest),installed_parts=sum(v['quantity'] for v in manifest),catalog_parts=sum(v['quantity']==0 for v in manifest),printed_stl=sum(v['role']=='printed' for v in parts),fastener_instances=sum(len(v['points']) for v in plan),hardware_components=sum(v['role']=='hardware_placeholder' for v in parts),counts={f'M{s}_{k}':n for (s,k),n in counts.items()},round_trips=checks)
    (root/'analysis/v4/handoff_export_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('EXPORT COMPLETE',json.dumps({k:v for k,v in report.items() if k!='round_trips'}),flush=True)


if __name__=='__main__':Handoff_Export()
