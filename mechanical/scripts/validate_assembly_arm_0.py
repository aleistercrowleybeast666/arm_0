"""V4 assembled fasteners and service access diagnostics. No adjacent-link penetration exemption."""
from pathlib import Path
from itertools import combinations
import json,math,sys,time
import FreeCAD as App
import build_arm_0 as arm
from fasteners_arm_0 import Fastener_Apply,Fastener_GetPlan
from check_arm_0 import Pair_GetInterfaceClass


def Assembly_CheckParts(parts,clearances=True,same=None,cache=None,frames=None):
    physical=[v for v in parts if v['role']!='reserve'];data=[]
    for v in physical:
        b=v['shape'].BoundBox;data.append((v,(b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax)))
    hits=[];gaps=[];pairs=0;closest=1e9;closest_pair=[];relative={}
    if cache is not None:
        for a in frames:
            for b in frames:
                t=frames[a].inverse().multiply(frames[b]);relative[a,b]=tuple(round(x,10) for x in list(t.Base)+list(t.Rotation.Q))
    for (a,ba),(b,bb) in combinations(data,2):
        equal=a['owner']==b['owner']
        if same is not None and equal!=same:continue
        pairs+=1;ds=[max(0,ba[k]-bb[k+3],bb[k]-ba[k+3]) for k in range(3)]
        lower=sum(x*x for x in ds)**.5
        key=(a['name'],b['name'],relative[a['owner'],b['owner']]) if cache is not None else None
        memo=cache.setdefault(key,{}) if cache is not None else {}
        if lower<1e-7:
            if 'volume' not in memo:memo['volume']=a['shape'].common(b['shape']).Volume
            volume=memo['volume']
            if volume>.1:hits.append(dict(pair=[a['name'],b['name']],volume_mm3=round(volume,5)))
        if clearances and not equal and lower<max(closest,1.00001):
            kind=Pair_GetInterfaceClass(a,b);threshold=0 if 'contact' in kind else .08 if kind=='running_fit' else 1
            if 'distance' not in memo:memo['distance']=a['shape'].distToShape(b['shape'])[0]
            distance=memo['distance']
            if kind=='external' and distance<closest:closest=distance;closest_pair=[a['name'],b['name']]
            if distance+1e-6<threshold:gaps.append(dict(pair=[a['name'],b['name']],distance_mm=distance,required_mm=threshold))
    return dict(tested_pairs=pairs,collisions=hits,clearance_violations=gaps,external_minimum_mm=closest if closest<1e9 else '>=1.0',minimum_pair=closest_pair)


def Assembly_RunDiagnostic():
    root=Path(__file__).resolve().parents[2];cfg=arm.Arm0_LoadConfig();base=arm.Arm0_GetComponents(cfg['dimensions'],False);parts,plan=Fastener_Apply(base,cfg['dimensions'])
    print('COMPONENTS',len(parts),'INTERFACES',len(plan),flush=True)
    _,world=arm.Arm0_GetWorldParts(cfg['dimensions'],cfg['poses']['HOME'],parts)
    result=Assembly_CheckParts(world,True)
    service=Assembly_CheckService(parts,plan)
    (root/'analysis/v4/service_diagnostic.json').write_text(json.dumps(service,indent=2),encoding='utf-8')
    print('SERVICE',[(v['id'],v['blockers']) for v in service if v['blockers']],flush=True)
    (root/'analysis/v4/diagnostic.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('HITS',len(result['collisions']),'GAPS',len(result['clearance_violations']),flush=True)
    for x in result['collisions']:print(x,flush=True)
    for x in result['clearance_violations']:print('GAP',x,flush=True)



def Assembly_CheckService(parts,plan):
    reports=[];rank={n:i for i,n in enumerate(['base','yaw','upper','fore','roll','pitch','tool'])}
    for rec in plan:
        blocked=[];removed=set(rec['remove']);owner=rec['owner']
        # Service on a detached rigid subassembly; adjacent links removed first.
        remaining=[v for v in parts if v['owner']==owner and v['role']!='reserve' and v['name'] not in removed and v.get('fastener_id')!=rec['id'] and not any(m in removed for m in v.get('mates',[]))]
        for i,inst in enumerate(rec['instances'],1):
            for v in remaining:
                if inst['tool'].BoundBox.intersect(v['shape'].BoundBox):
                    vol=inst['tool'].common(v['shape']).Volume
                    if vol>.1:blocked.append(dict(instance=i,part=v['name'],kind='driver',volume_mm3=vol))
            if inst['nut'] is not None:
                # Sweep a conservative nut bounding box along the stated extraction path.
                n=inst['nut'];d=App.Vector(*inst['nut_entry'])*12;b=n.BoundBox
                lo=[min(getattr(b,k+'Min'),getattr(b,k+'Min')+d[t]) for t,k in enumerate('XYZ')]
                hi=[max(getattr(b,k+'Max'),getattr(b,k+'Max')+d[t]) for t,k in enumerate('XYZ')]
                sweep=arm.Shape_Box(*[hi[t]-lo[t] for t in range(3)],*lo)
                for v in remaining:
                    if v['name']==rec['a'] and rec['a'].endswith('RemovableCover'):continue
                    if sweep.BoundBox.intersect(v['shape'].BoundBox):
                        vol=sweep.common(v['shape']).Volume
                        if vol>.1:blocked.append(dict(instance=i,part=v['name'],kind='nut_extraction',volume_mm3=vol))
        reports.append(dict(id=rec['id'],serviceable=not blocked,stage='Detached rigid subassembly; remove listed covers/components and interface bolts before nut extraction',remove=[n for n in rec['remove'] if n=='CHILD_LINKS' or any(v['name']==n and v['owner']==owner for v in parts)],blockers=blocked))
    return reports


def Assembly_RunValidation(parts=None,plan=None):
    import hashlib
    import search_arm_0_docking as docking
    root=Path(__file__).resolve().parents[2];cfg=arm.Arm0_LoadConfig();p=cfg['dimensions']
    if parts is None:parts,plan=Fastener_Apply(arm.Arm0_GetComponents(p,False),p)
    result=dict(schema='arm_0.assembly_validation.v4',baseline_commit=cfg['freeze_review_baseline_commit'],config_sha256=hashlib.sha256((root/'mechanical/arm_0_parameters.json').read_bytes()).hexdigest(),poses={},paths={},policy='Every physical solid including bolts/nuts/washers. Penetration >0.1 mm3 fails including same link; external gap >=1 mm; exact legacy bearing fit/contact classes only. Tools static service checks, not motion bodies. Bench anchors intentionally extend below base.',physical_components=sum(v['role']!='reserve' for v in parts),interfaces=len(plan))
    result['same_rigid']=Assembly_CheckParts(parts,False,True)
    result['removed_access_chips_mm3']={v['name']:v['removed_access_chips_mm3'] for v in parts if v.get('removed_access_chips_mm3')}
    result['geometry_sources_sha256']={n:hashlib.sha256((root/'mechanical/scripts'/n).read_bytes()).hexdigest() for n in ['build_arm_0.py','geometry_arm_0.py','wrist_arm_0.py','fasteners_arm_0.py','arm_model.py']}
    duct=next(v['shape'] for v in parts if v['name']=='Forearm_CableDuctReserve');_,zero=arm.Arm0_GetWorldParts(p,[0]*6,parts)
    # Duct is fore-local; compare in the same zero-pose world frame.
    _,local_zero=arm.Arm0_GetWorldParts(p,[0]*6,[v for v in parts if v['name']=='Forearm_CableDuctReserve']);duct=local_zero[0]['shape']
    result['cable_duct_conflicts']=[]
    for v in zero:
        if v['role']!='reserve' and duct.BoundBox.intersect(v['shape'].BoundBox):
            volume=duct.common(v['shape']).Volume
            if volume>.1:result['cable_duct_conflicts'].append(dict(part=v['name'],volume_mm3=volume))
    result['service']=Assembly_CheckService(parts,plan)
    (root/'analysis/v4/service_diagnostic.json').write_text(json.dumps(result['service'],indent=2),encoding='utf-8')
    print('SERVICE',sum(not v['serviceable'] for v in result['service']),flush=True)
    cache={};pair_cache={}
    def Check(q):
        key=tuple(round(a,8) for a in q)
        if key not in cache:
            metrics,world=docking.Pose_GetMetrics(cfg,q,parts);frames=arm.arm_model.Frame_GetChain(p,q);check=Assembly_CheckParts(world,True,False,pair_cache,frames)
            # Only laboratory bench anchors may occupy the fixture below z=0.
            body=[v for v in world if v['role']!='reserve' and v.get('fastener_id')!='F-J1-001']
            floor=min(v['shape'].BoundBox.ZMin for v in body)
            cache[key]=dict(metrics=metrics,check=check,robot_floor_z_mm=floor,valid=not check['collisions'] and not check['clearance_violations'] and floor>=-1e-6 and metrics['joint_margin_deg']>=0)
        return cache[key]
    for name,q in cfg['poses'].items():
        result['poses'][name]=Check(q);print('POSE',name,'hits',len(result['poses'][name]['check']['collisions']),'gaps',len(result['poses'][name]['check']['clearance_violations']),flush=True)
    for label,a,b in [('STOW_HOME','STOW','HOME'),('HOME_SAFE_UNFOLD','HOME','SAFE_UNFOLD')]:
        samples=docking.Path_GetSamples(cfg['poses'][a],cfg['poses'][b],2);records=[]
        for i,q in enumerate(samples):
            rec=Check(q);records.append(rec);print('PATH',label,i+1,'/',len(samples),'valid',rec['valid'],flush=True)
        result['paths'][label]=dict(sample_count=len(samples),maximum_sample_step_deg=max(max(abs(x-y) for x,y in zip(v,u)) for v,u in zip(samples,samples[1:])),valid=all(r['valid'] and r['metrics']['minimum_front_projection_mm']>=-cfg['backward_allowance_mm'] for r in records),samples=records)
    result['valid_geometry']=not result['cable_duct_conflicts'] and not result['same_rigid']['collisions'] and all(v['valid'] for v in result['poses'].values()) and all(v['valid'] for v in result['paths'].values())
    result['cache_policy']='Per-run exact solid results reused only for same named pair at the same relative rigid placement (roundoff 1e-10); all pose and path records retained.'
    result['unserviceable_interfaces']=sum(not v['serviceable'] for v in result['service'])
    result['release']='PRELIMINARY REVIEW ONLY / NOT PRODUCTION';result['valid']=result['valid_geometry'] and result['unserviceable_interfaces']==0
    (root/'analysis/v4/assembly_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('VALIDATION',result['valid'],'GEOMETRY',result['valid_geometry'],'SERVICE_FAILURES',result['unserviceable_interfaces'],flush=True)
    return result


if __name__=='__main__':
    if '--full' in sys.argv:sys.exit(0 if Assembly_RunValidation()['valid'] else 1)
    else:Assembly_RunDiagnostic()
