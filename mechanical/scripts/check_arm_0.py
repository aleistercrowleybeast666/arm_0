"""V3 geometric auditing. Never exempt adjacent joints from penetration checks."""
from pathlib import Path
from itertools import combinations
import json
import math
import hashlib
import FreeCAD as App
import Part
import build_arm_0 as arm


def Pair_GetGap(a,b):
    return sum(max(0,getattr(a,k+'Min')-getattr(b,k+'Max'),getattr(b,k+'Min')-getattr(a,k+'Max'))**2 for k in 'XYZ')**.5


def Pair_GetInterfaceClass(a,b):
    names={a['name'],b['name']}
    if any(names=={f'J{i}_CyberGear_Stator',f'J{i}_CyberGear_Rotor'} for i in range(1,7)):
        return 'motor_internal_contact'
    if names=={'J1_BearingPlaceholder','J1_OutputHub'}: return 'bearing_axial_contact'
    fits=[('J1_BearingSeat','J1_OutputHub')]
    for j,fixed in [(2,'J2_OppositeBearingPedestal'),(3,'J3_FixedBearingSupport')]:
        fits += [(fixed,f'J{j}_ShortBearingStub'),(f'J{j}_BearingRetainer',f'J{j}_ShortBearingStub'),(f'J{j}_BearingPlaceholder',f'J{j}_ShortBearingStub')]
    for side in ['Proximal','Distal']:
        fits += [(f'J4_{side}BearingHousing','J4_TorqueTube'),(f'J4_{side}Bearing','J4_TorqueTube'),(f'J4_{side}BearingRetainer','J4_TorqueTube')]
    fits += [('J5_OutputSupportBearing','J5_ShortOutputHub'),('J5_CompactStatorSupport','J5_ShortOutputHub'),('J5_RemovableBearingSeat','J5_ShortOutputHub'),('J6_OnePieceConnector','J6_ShortOutputHub'),('J6_OutputBearing','J6_ShortOutputHub')]
    return 'running_fit' if any(names==set(pair) for pair in fits) else 'external'


def Arm0_CheckParts(parts,distances=False,same_only=False,clearance_only=False):
    physical=[v for v in parts if v['role']!='reserve']; collisions=[]; near=[]; min_gap=float('inf'); min_pair=None; pairs=0; external_min=float('inf'); violations=[]
    for a,b in combinations(physical,2):
        same=a['owner']==b['owner']
        if same_only!=same: continue
        pairs+=1; sa,sb=a['shape'],b['shape']; gap=Pair_GetGap(sa.BoundBox,sb.BoundBox)
        if gap<1e-6:
            volume=sa.common(sb).Volume
            if volume>.1: collisions.append(dict(pair=[a['name'],b['name']],volume_mm3=round(volume,4)))
        kind=Pair_GetInterfaceClass(a,b)
        threshold=0 if 'contact' in kind else .08 if kind=='running_fit' else 1.0
        if (distances and gap<max(external_min,2)) or (clearance_only and gap<threshold):
            distance=sa.distToShape(sb)[0]
            if distance<min_gap: min_gap=distance; min_pair=[a['name'],b['name']]
            if kind=='external': external_min=min(external_min,distance)
            if distance+1e-6<threshold: violations.append(dict(pair=[a['name'],b['name']],distance_mm=distance,required_mm=threshold))
            if distance<2: near.append(dict(pair=[a['name'],b['name']],distance_mm=distance,interface=kind))
    return dict(tested_pairs=pairs,collisions=collisions,minimum_clearance_mm=min_gap if distances else None,minimum_pair=min_pair,near_pairs=near,external_minimum_mm=external_min if distances else None,clearance_violations=violations)


def Arm0_Diagnose():
    cfg=arm.Arm0_LoadConfig(); p=cfg['dimensions']; parts=arm.Arm0_GetComponents(p); result={}
    for name,q in cfg['poses'].items():
        _,world=arm.Arm0_GetWorldParts(p,q,parts); check=Arm0_CheckParts(world)
        result[name]=check; print(name,json.dumps(check),flush=True)
    _,world=arm.Arm0_GetWorldParts(p,[0]*6,parts)
    result['same_rigid']=Arm0_CheckParts(world,same_only=True)
    print('SAME',json.dumps(result['same_rigid']),flush=True)
    (Path(__file__).resolve().parents[2]/'analysis/v3/diagnostic.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


if __name__=='__main__': Arm0_Diagnose()
