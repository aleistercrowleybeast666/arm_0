"""Search forward docking, with geometry and <=2 degree joint-interpolated paths."""
from pathlib import Path
from itertools import product
import math
import json
import FreeCAD as App
import build_arm_0 as arm
import check_arm_0 as audit


def Front_GetUnit(cfg):
    x,y=cfg['front_direction'][:2]; length=math.hypot(x,y)
    if length<1e-9: raise ValueError('front_direction must have nonzero horizontal length')
    return (x/length,y/length,0)


def Pose_GetMetrics(cfg,q,parts):
    p=cfg['dimensions']; front=Front_GetUnit(cfg); frames,world=arm.Arm0_GetWorldParts(p,q,parts)
    physical=[v for v in world if v['role']!='reserve']; boxes=[v['shape'].BoundBox for v in physical]
    bounds=[min(getattr(b,k+'Min') for b in boxes) for k in 'XYZ']+[max(getattr(b,k+'Max') for b in boxes) for k in 'XYZ']
    tcp=frames['tool'].multVec(App.Vector(p['Tool'],0,0)); wrist=frames['pitch_base'].Base
    landmarks={'J3':frames['elbow'].Base,'J4':frames['wrist'].Base,'J5':wrist,'J6':frames['tool'].Base,'TCP':tcp}
    for v in physical:
        if v['owner'] in ['fore','roll','pitch','tool']: landmarks[v['name']]=v['shape'].BoundBox.Center
    projections={k:pt.x*front[0]+pt.y*front[1] for k,pt in landmarks.items()}
    radial=max(math.hypot(x,y) for b in boxes for x in [b.XMin,b.XMax] for y in [b.YMin,b.YMax])
    margin=min(min(angle-lo,hi-angle) for angle,(lo,hi) in zip(q,cfg['mechanical_limits_deg']))
    return dict(q=q,tcp_mm=list(tcp),wrist_mm=list(wrist),bounds_mm=bounds,physical_radial_extent_mm=radial,height_mm=bounds[5]-bounds[2],
        minimum_front_projection_mm=min(projections.values()),backward_excursion_mm=max(0,-min(projections.values())),front_projections_mm=projections,joint_margin_deg=margin),world


def Path_GetSamples(a,b,step=2):
    n=max(1,math.ceil(max(abs(y-x) for x,y in zip(a,b))/step))
    return [[x+(y-x)*i/n for x,y in zip(a,b)] for i in range(n+1)]


def Path_Check(cfg,a,b,parts,detailed=False):
    records=[]; first=None
    for i,q in enumerate(Path_GetSamples(a,b,cfg['path_step_deg'])):
        metrics,world=Pose_GetMetrics(cfg,q,parts)
        check=audit.Arm0_CheckParts(world,distances=detailed,clearance_only=not detailed)
        valid=not check['collisions'] and not check['clearance_violations'] and metrics['minimum_front_projection_mm']>=-cfg['backward_allowance_mm'] and metrics['bounds_mm'][2]>=-1e-6 and metrics['joint_margin_deg']>=0
        if not valid and first is None: first=dict(sample=i,q=q,collisions=check['collisions'],clearance_violations=check['clearance_violations'],minimum_front_projection_mm=metrics['minimum_front_projection_mm'])
        records.append(dict(sample=i,metrics=metrics,check=check))
        if first and not detailed: break
    tcp=sum(math.dist(x['metrics']['tcp_mm'],y['metrics']['tcp_mm']) for x,y in zip(records,records[1:]))
    wrist=sum(math.dist(x['metrics']['wrist_mm'],y['metrics']['wrist_mm']) for x,y in zip(records,records[1:]))
    bounds=[min(v['metrics']['bounds_mm'][k] for v in records) for k in range(3)]+[max(v['metrics']['bounds_mm'][k] for v in records) for k in range(3,6)]
    ext=[v['check']['external_minimum_mm'] for v in records if v['check']['external_minimum_mm'] is not None]
    return dict(valid=first is None,first_failure=first,max_joint_delta_deg=max(abs(y-x) for x,y in zip(a,b)),tcp_path_length_mm=tcp,wrist_path_length_mm=wrist,
        maximum_backward_excursion_mm=max(v['metrics']['backward_excursion_mm'] for v in records),minimum_front_projection_mm=min(v['metrics']['minimum_front_projection_mm'] for v in records),
        swept_bounds_mm=bounds,swept_size_mm=[bounds[k+3]-bounds[k] for k in range(3)],sample_count=len(records),step_deg=cfg['path_step_deg'],minimum_external_clearance_mm=min(ext) if ext else None,samples=records)


def Docking_Search():
    root=Path(__file__).resolve().parents[2]; cfg=arm.Arm0_LoadConfig(); p=cfg['dimensions']; parts=arm.Arm0_GetComponents(p)
    front=Front_GetUnit(cfg); yaw=math.degrees(math.atan2(front[1],front[0])); candidates=[]
    for j2,j3 in product([45,50,55,60,65,70,75],[-150,-147,-144,-140]):
        q=[yaw,j2,j3,0,-j2-j3,0]; metrics,world=Pose_GetMetrics(cfg,q,parts)
        if metrics['minimum_front_projection_mm']<-cfg['backward_allowance_mm'] or metrics['bounds_mm'][2]<0 or metrics['joint_margin_deg']<0:
            candidates.append(dict(metrics=metrics,accepted=False,reason='front / floor / joint bounds'));continue
        check=audit.Arm0_CheckParts(world,clearance_only=True)
        accepted=not check['collisions'] and not check['clearance_violations']
        candidates.append(dict(metrics=metrics,accepted=accepted,check=check))
        print('candidate',q,'PASS' if accepted else 'FAIL',round(metrics['physical_radial_extent_mm'],2),flush=True)
    viable=sorted([v for v in candidates if v['accepted']],key=lambda v:(v['metrics']['backward_excursion_mm'],v['metrics']['physical_radial_extent_mm'],v['metrics']['height_mm']))
    attempts=[]; selected=None
    safe=[yaw,50,-110,0,60,0]
    for candidate in viable:
        stow=candidate['metrics']['q']
        for dj2,dj3 in [(-3,8),(-2,6),(0,8),(-2,10)]:
            home=[yaw,stow[1]+dj2,stow[2]+dj3,0,-stow[1]-dj2-stow[2]-dj3,0]
            startup=Path_Check(cfg,stow,home,parts)
            unfold=Path_Check(cfg,home,safe,parts) if startup['valid'] else None
            attempts.append(dict(stow=stow,home=home,startup=startup,unfold=unfold))
            print('path attempt',stow,home,startup['valid'],unfold['valid'] if unfold else None,flush=True)
            if startup['valid'] and unfold['valid']:
                selected=dict(STOW=stow,HOME=home,SAFE_UNFOLD=safe,CAKE_APPROACH=cfg['poses']['CAKE_APPROACH']);break
        if selected: break
    report=dict(search_space='J2 grid, negative J3 forward folding, q4=0, tool horizontal; bounded search, not global optimum',candidates=candidates,path_attempts=attempts,selected=selected)
    (root/'analysis/v3/docking_search.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not selected: raise RuntimeError('No forward docking candidate satisfies geometry and sampled paths')
    cfg['poses']=selected
    (root/'mechanical/arm_0_parameters.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    print('SELECTED',json.dumps(selected),flush=True)


if __name__=='__main__': Docking_Search()
