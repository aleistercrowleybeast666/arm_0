"""Final arm_0 evidence: sampled startup paths, CAD invariants, gravity screen and V2 comparison."""
from pathlib import Path
import json
import math
import hashlib
import importlib.util
import FreeCAD as App
import Part
import numpy as np
import build_arm_0 as arm
import check_arm_0 as audit
import search_arm_0_docking as docking


def Jacobian_GetCondition(p,q):
    frames=arm.arm_model.Frame_GetChain(p,q); axes=arm.arm_model.Arm_GetAxes(p,frames)
    tcp=frames['tool'].multVec(App.Vector(p['Tool'],0,0)); columns=[]
    for axis in axes:
        direction=App.Vector(*axis['axis_world']); point=App.Vector(*axis['origin_mm'])
        v=direction.cross(tcp-point); columns.append(list(v)+list(direction*400))
    singular=np.linalg.svd(np.array(columns).T,compute_uv=False)
    return dict(characteristic_length_mm=400,singular_values_mm_per_rad=singular.tolist(),condition_number=float(singular[0]/singular[-1]),note='Scaled geometric Jacobian screen; not a dynamics/control certification')


def Geometry_GetGravity(p,parts):
    _,world=arm.Arm0_GetWorldParts(p,[0]*6,parts); records={}
    for j in [3,4,5,6]:
        chosen=[v['shape'] for v in world if v['name'] in [f'J{j}_CyberGear_Stator',f'J{j}_CyberGear_Rotor']]
        records[str(j)]=min(v.BoundBox.XMin for v in chosen)/1000
    return dict(minimum_x_m=records,J2_motor_only_lower_bound_Nm=.314*9.81*sum(records.values()),J3_motor_only_lower_bound_Nm=.314*9.81*sum(records[str(j)]-.320 for j in [4,5,6]))


def Legacy_GetComparison(root):
    path=root/'mechanical/legacy/v2/scripts/build_robot_master.py'
    spec=importlib.util.spec_from_file_location('arm_legacy_v2',path); legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    cfg=json.loads((root/'mechanical/legacy/v2/master_parameters.json').read_text(encoding='utf-8-sig'));p=cfg['dimensions'];parts=legacy.Robot_GetComponents(p)
    cfg.update(front_direction=[1,0,0],backward_allowance_mm=20,mechanical_limits_deg=[[-180,180]]*6,path_step_deg=2)
    stow=cfg['poses']['STOW'];home=cfg['poses']['HOME'];samples=[]
    for q in docking.Path_GetSamples(stow,home,2): samples.append(docking.Pose_GetMetrics(cfg,q,parts)[0])
    bounds=[min(v['bounds_mm'][k] for v in samples) for k in range(3)]+[max(v['bounds_mm'][k] for v in samples) for k in range(3,6)]
    return dict(stow=samples[0],home=samples[-1],max_joint_delta_deg=max(abs(a-b) for a,b in zip(stow,home)),
        tcp_path_length_mm=sum(math.dist(a['tcp_mm'],b['tcp_mm']) for a,b in zip(samples,samples[1:])),
        wrist_path_length_mm=sum(math.dist(a['wrist_mm'],b['wrist_mm']) for a,b in zip(samples,samples[1:])),
        maximum_backward_excursion_mm=max(v['backward_excursion_mm'] for v in samples),swept_bounds_mm=bounds,swept_size_mm=[bounds[k+3]-bounds[k] for k in range(3)],
        note='Original V2 geometry and V2 poses; motion metrics only, not re-certified collision-free',gravity=Geometry_GetGravity(p,parts))


def Arm0_RunValidation():
    root=Path(__file__).resolve().parents[2]; cfg=arm.Arm0_LoadConfig(); p=cfg['dimensions'];parts=arm.Arm0_GetComponents(p)
    result=dict(freecad_version=App.Version(),config_sha256=hashlib.sha256((root/'mechanical/arm_0_parameters.json').read_bytes()).hexdigest(),
        geometry_sha256=hashlib.sha256((root/'mechanical/scripts/build_arm_0.py').read_bytes()).hexdigest(),poses={},paths={},valid_solids=[],interface_policy='All physical solids checked for penetration >0.1 mm3. Minimum external gap 1 mm. Exact listed bearing fits 0.08 mm; six motor internal contact pairs and J1 bearing axial contact permit touching only. No adjacency penetration exemption.')
    for part in parts:
        s=part['shape']; row=dict(name=part['name'],owner=part['owner'],role=part['role'],valid=s.isValid(),solids=len(s.Solids),volume_mm3=s.Volume,bounds_mm=[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin,s.BoundBox.XMax,s.BoundBox.YMax,s.BoundBox.ZMax])
        assert row['valid'] and row['solids']==1,part['name']; result['valid_solids'].append(row)
    for name,q in cfg['poses'].items():
        metrics,world=docking.Pose_GetMetrics(cfg,q,parts); check=audit.Arm0_CheckParts(world,True)
        result['poses'][name]=dict(metrics=metrics,check=check,jacobian=Jacobian_GetCondition(p,q))
        print('POSE',name,'collisions',len(check['collisions']),'gap_failures',len(check['clearance_violations']),flush=True)
    for label,a,b in [('STOW_HOME','STOW','HOME'),('HOME_SAFE_UNFOLD','HOME','SAFE_UNFOLD')]:
        print('PATH START',label,flush=True)
        result['paths'][label]=docking.Path_Check(cfg,cfg['poses'][a],cfg['poses'][b],parts,True)
        print('PATH END',label,result['paths'][label]['valid'],flush=True)
        (root/'analysis/v3/validation_partial.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    _,zero=arm.Arm0_GetWorldParts(p,[0]*6,parts); result['same_rigid']=audit.Arm0_CheckParts(zero,same_only=True)
    # The static cable route must be empty of physical solids, including the rotating drive.
    duct=next(v['shape'] for v in zero if v['name']=='Forearm_CableDuctReserve');duct_hits=[]
    for part in zero:
        if part['role']=='reserve':continue
        if duct.BoundBox.intersect(part['shape'].BoundBox):
            volume=duct.common(part['shape']).Volume
            if volume>.1:duct_hits.append(dict(name=part['name'],volume_mm3=volume))
    result['cable_partition']=dict(cross_section_mm=[8,5],physical_conflicts=duct_hits,rotating_clearance_mm={name:duct.distToShape(next(v['shape'] for v in zero if v['name']==name))[0] for name in ['J4_TorqueTube','J4_DistalOutputHub','J4_DistalBearing']})
    # Native document ownership test, with an off-axis witness on the rotating tube.
    doc=App.openDocument(str(root/'mechanical/freecad/arm_0.FCStd'))
    arm.Arm0_SetPose(doc,'STOW',cfg); original=doc.J3_CyberGear_Stator.Placement
    cfg['poses']['CHECK_J3']=list(cfg['poses']['STOW']);cfg['poses']['CHECK_J3'][2]+=7
    arm.Arm0_SetPose(doc,'CHECK_J3',cfg); assert original.isSame(doc.J3_CyberGear_Stator.Placement,1e-8)
    motor=doc.J4_CyberGear_Stator.Placement; tube=doc.J4_TorqueTube.Placement
    cfg['poses']['CHECK_J4']=list(cfg['poses']['CHECK_J3']);cfg['poses']['CHECK_J4'][3]+=30
    arm.Arm0_SetPose(doc,'CHECK_J4',cfg)
    assert motor.isSame(doc.J4_CyberGear_Stator.Placement,1e-8)
    witness=App.Vector(-100,9,0); assert (tube.multVec(witness)-doc.J4_TorqueTube.Placement.multVec(witness)).Length>1
    distances={}
    for j,key in [(2,'UpperArm'),(3,'Forearm'),(4,'Wrist'),(5,'Flange')]:
        a=doc.getObject(f'Axis_J{j}').AxisOrigin;b=doc.getObject(f'Axis_J{j+1}').AxisOrigin
        distances[key]=(b-a).Length; assert abs(distances[key]-p[key])<1e-7
    result['invariants']=dict(center_distances_mm=distances,J3_stator_fixed_on_upper=True,J4_stator_fixed_on_fore=True,J4_tube_rotates_with_roll=True,actuator_count=sum(v['role']=='motor' for v in parts),legacy_through_shafts_absent=not any('ThroughShaft' in v['name'] for v in parts))
    App.closeDocument(doc.Name)
    result['j3_proximal_checks']={}
    for angle in [0,90,-90,-150,-152,-155,150]:
        _,world=arm.Arm0_GetWorldParts(p,[0,65,angle,0,75,0],parts)
        selected=[v for v in world if v['name'] in ['Upper_CentralBox','J3_StatorMount','J3_FixedBearingSupport','J3_CyberGear_Stator','J4_CyberGear_Stator','J4_ProximalStatorHousing','J3_OutputForkCheek','J3_OppositeForkCheek']]
        result['j3_proximal_checks'][str(angle)]=audit.Arm0_CheckParts(selected,True)
        print('J3 LOCAL',angle,len(result['j3_proximal_checks'][str(angle)]['collisions']),flush=True)
    legacy=Legacy_GetComparison(root);after=Geometry_GetGravity(p,parts)
    result['comparison']=dict(legacy_v2=legacy,forward_v3=result['paths']['STOW_HOME'])
    result['gravity']=dict(mass_lower_kg=.314,source='CyberGear reference manual: 317 +/-3 g, nominal rated 4 Nm; source provenance in cybergear_interface.md',before=legacy['gravity'],after=after,
        delta_Nm={j:after[j]-legacy['gravity'][j] for j in ['J2_motor_only_lower_bound_Nm','J3_motor_only_lower_bound_Nm']},note='Horizontal motor-mass-only bound; excludes torque tube, metal hubs, printed parts, cables and payload. Does not establish a usable payload.')
    # Rotation covariance for front-direction abstraction, with no FK algorithm changes.
    fresh=arm.Arm0_LoadConfig();a=docking.Pose_GetMetrics(fresh,fresh['poses']['STOW'],parts)[0]
    rotated=json.loads(json.dumps(fresh));rotated['front_direction']=[0,1,0];q=list(fresh['poses']['STOW']);q[0]+=90
    b=docking.Pose_GetMetrics(rotated,q,parts)[0]
    assert abs(a['minimum_front_projection_mm']-b['minimum_front_projection_mm'])<1e-6
    result['front_direction_covariance_check']=True
    from compact_wrist_review import Wrist_GetEvidence
    result['compact_wrist']=Wrist_GetEvidence(root,cfg,parts)
    failures=[]
    if result['compact_wrist']['failures']: failures.append('compact wrist')
    if result['cable_partition']['physical_conflicts']:failures.append('cable partition')
    for name,v in result['poses'].items():
        if v['check']['collisions'] or v['check']['clearance_violations']: failures.append(name)
    if result['same_rigid']['collisions']: failures.append('same_rigid')
    for name,v in result['paths'].items():
        if not v['valid']: failures.append(name)
    if result['poses']['SAFE_UNFOLD']['jacobian']['condition_number']>100: failures.append('SAFE_UNFOLD Jacobian')
    result['failures']=failures
    result['dependency_sha256']={name:hashlib.sha256((root/'mechanical/scripts'/name).read_bytes()).hexdigest() for name in ['geometry_arm_0.py','wrist_arm_0.py','arm_model.py','cybergear_model.py']}
    (root/'analysis/v3/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if failures: raise RuntimeError('Validation failed: '+str(failures))
    print('V3 VALIDATION PASS',flush=True)


if __name__=='__main__': Arm0_RunValidation()
