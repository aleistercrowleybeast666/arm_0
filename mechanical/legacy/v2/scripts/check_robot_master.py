"""Stage-2 BRep interference and export audits; does not treat no overlap as load safety."""
from pathlib import Path
from itertools import combinations
import json
import hashlib
import FreeCAD as App
import Part
import build_robot_master as robot


def Pair_GetBoxGap(a,b):
    return sum(max(0,getattr(a,k+"Min")-getattr(b,k+"Max"),getattr(b,k+"Min")-getattr(a,k+"Max"))**2 for k in "XYZ")**.5


def Robot_CheckParts(parts,check_rigid_overlaps=False):
    collisions=[]; min_motor=1e9; min_pair=[]; cable=[]
    pairs=0
    for a,b in combinations(parts,2):
        if a["role"]=="reserve" or b["role"]=="reserve":
            reserve,physical=(a,b) if a["role"]=="reserve" else (b,a)
            if physical["role"]=="reserve" or reserve["owner"]==physical["owner"]: continue
            if Pair_GetBoxGap(a["shape"].BoundBox,b["shape"].BoundBox)==0:
                volume=a["shape"].common(b["shape"]).Volume
                if volume>.1: cable.append({"pair":[a["name"],b["name"]],"volume_mm3":round(volume,3)})
            continue
        same=a["owner"]==b["owner"]
        if same and not check_rigid_overlaps: continue
        if check_rigid_overlaps and not same: continue
        pairs+=1
        sa,sb=a["shape"],b["shape"]
        motor=a["role"]==b["role"]=="motor"
        if motor:
            distance=sa.distToShape(sb)[0]
            if distance<min_motor: min_motor=distance; min_pair=[a["name"],b["name"]]
        if Pair_GetBoxGap(sa.BoundBox,sb.BoundBox)>1e-5: continue
        volume=sa.common(sb).Volume
        if volume>.1:
            collisions.append({"pair":[a["name"],b["name"]],"volume_mm3":round(volume,3),"roles":[a["role"],b["role"]]})
    return {"tested_pairs":pairs,"collisions":collisions,"cable_reserve_conflicts":cable,
            "minimum_motor_distance_mm":min_motor if min_motor<1e9 else None,"minimum_motor_pair":min_pair}


def Robot_RunChecks():
    root=Path(__file__).resolve().parents[2]
    cfg=robot.Robot_LoadConfig(); p=cfg["dimensions"]; components=robot.Robot_GetComponents(p)
    result={"poses":{},"printed_part_validity":[],"freecad_version":App.Version(),
            "config_sha256":hashlib.sha256((root/"mechanical/master_parameters.json").read_bytes()).hexdigest(),
            "geometry_script_sha256":hashlib.sha256((root/"mechanical/scripts/build_robot_master.py").read_bytes()).hexdigest()}
    for c in components:
        if c["role"]=="printed":
            result["printed_part_validity"].append({"name":c["name"],"valid":c["shape"].isValid(),"solids":len(c["shape"].Solids),"volume_mm3":c["shape"].Volume})
    for name,q in cfg["poses"].items():
        frames,parts=robot.Robot_GetWorldParts(p,q,components)
        check=Robot_CheckParts(parts)
        check["angles_deg"]=q
        check["minimum_z_mm"]=min(x["shape"].BoundBox.ZMin for x in parts if x["role"]!="reserve")
        check["tcp_mm"]=list(frames["tool"].multVec(App.Vector(p["Tool"],0,0)))
        result["poses"][name]=check
        print(name,json.dumps(check),flush=True)
    _,zero=robot.Robot_GetWorldParts(p,[0]*6,components)
    result["same_rigid_overlaps"]=Robot_CheckParts(zero,True)
    (root/"analysis/stage2/master_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("RIGID",json.dumps(result["same_rigid_overlaps"]),flush=True)
    if any(v["collisions"] for v in result["poses"].values()) or result["same_rigid_overlaps"]["collisions"]:
        raise RuntimeError("Physical interference detected; see analysis/stage2/master_checks.json")
    if any(not v["valid"] or v["solids"]!=1 for v in result["printed_part_validity"]):
        raise RuntimeError("Printed part is not a single valid solid")


if __name__=="__main__": Robot_RunChecks()
