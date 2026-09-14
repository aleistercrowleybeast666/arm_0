"""Measure the user-requested serial wrist against the superseded box wrist."""
import json,importlib.util
import FreeCAD as App
import Part
import build_arm_0 as arm
import check_arm_0 as audit


def Wrist_GetEvidence(root,cfg,parts):
    def Wrist_GetBounds(p,items):
        _,world=arm.Arm0_GetWorldParts(p,[0]*6,items)
        selected=[v for v in world if v['name'].startswith(('J5_','J6_')) and v['role']!='reserve']
        bounds=Part.makeCompound([v['shape'] for v in selected]).BoundBox
        return dict(bounds_mm=[bounds.XMin,bounds.YMin,bounds.ZMin,bounds.XMax,bounds.YMax,bounds.ZMax],size_mm=[bounds.XLength,bounds.YLength,bounds.ZLength]),selected
    archived=root/'mechanical/legacy/v3_box_wrist'
    spec=importlib.util.spec_from_file_location('boxed_wrist_snapshot',archived/'build_arm_0.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    oldcfg=json.loads((archived/'arm_0_parameters.json').read_text(encoding='utf-8-sig'))
    before,_=Wrist_GetBounds(oldcfg['dimensions'],old.Arm0_GetComponents(oldcfg['dimensions']))
    after,world=Wrist_GetBounds(cfg['dimensions'],parts)
    motor5=next(v['shape'] for v in world if v['name']=='J5_CyberGear_Stator')
    motor6=next(v['shape'] for v in world if v['name']=='J6_CyberGear_Stator')
    checks={};failures=[]
    for angle in [-120,-90,-45,0,45,90,120]:
        _,wp=arm.Arm0_GetWorldParts(cfg['dimensions'],[0,0,0,0,angle,0],parts)
        chosen=[v for v in wp if v['name'].startswith(('J5_','J6_')) or v['name']=='J4_DistalOutputHub']
        result=audit.Arm0_CheckParts(chosen,True); checks[str(angle)]=result
        if result['collisions'] or result['clearance_violations']:failures.append('local q5 '+str(angle))
        print('COMPACT WRIST',angle,'collisions',len(result['collisions']),'gaps',len(result['clearance_violations']),flush=True)
    serial_gap=motor6.BoundBox.XMin-motor5.BoundBox.XMax
    if serial_gap<=0:failures.append('motors not separated in extended axial projection')
    tcp=arm.arm_model.Frame_GetChain(cfg['dimensions'],cfg['poses']['CAKE_APPROACH'])['tool'].multVec(App.Vector(cfg['dimensions']['Tool'],0,0))
    cake_error=(tcp-App.Vector(*cfg['cake_center_mm'])).Length
    if cake_error>1e-6:failures.append('cake TCP drift')
    return dict(before=before,after=after,width_reduction_percent=100*(1-after['size_mm'][1]/before['size_mm'][1]),extended_motor_axial_gap_mm=serial_gap,
        Flange_before_mm=35,Flange_after_mm=cfg['dimensions']['Flange'],local_q5_checks=checks,cake_tcp_mm=list(tcp),cake_tcp_error_mm=cake_error,
        note='Motor-before-motor assertion applies to the extended reference pose. J6 moves around J5 during pitch. Seven local angles are samples, not a continuous joint-range certificate. J5 bearing, clamp and cantilever stiffness require hardware/load design.',failures=failures)
