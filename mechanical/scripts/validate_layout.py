"""Sample envelope interference, paths, geometric reach, and ownership invariants."""
from pathlib import Path
import json
import math
import arm_model as arm
import FreeCAD as App


def Task_SolveDownward(p, x, z):
    # At J4=0, wrist offset follows the forearm; flange+tool point vertically down.
    a, b = p["UpperArm"], p["Forearm"] + p["Wrist"]
    dz = z + p["Flange"] + p["Tool"] - p["BaseHeight"]
    cosine = (x*x + dz*dz - a*a - b*b)/(2*a*b)
    if abs(cosine) > 1:
        raise ValueError("Target unreachable for downward tool")
    elbow = -math.acos(cosine)
    shoulder = math.atan2(dz,x)-math.atan2(b*math.sin(elbow), a+b*math.cos(elbow))
    q2, q3 = math.degrees(shoulder), math.degrees(elbow)
    return [0, q2, q3, 0, -90-q2-q3, 0]


def Sample_Check(p, q):
    f, parts = arm.Arm_GetGeometry(p,q)
    check = arm.Arm_CheckGeometry(parts, full=True)
    return {"q_deg": q, "collisions": check["collisions"],
            "min_motor_clearance": check["min_motor_clearance"],
            "minimum_z_mm": min(v["shape"].BoundBox.ZMin for v in parts),
            "tcp_mm": list(f["tool"].multVec(App.Vector(p["Tool"],0,0)))}


def Layout_RunValidation():
    root = Path(__file__).resolve().parents[2]
    c = arm.Arm_LoadConfig(); p = c["dimensions"]
    result = {"method": "OCCT BRep pair intersections >0.01 mm^3; same rigid-link structure excluded; all motor pairs included. Samples are not continuous swept-volume proof.",
              "sweeps": {}, "paths": {}, "task_points": {}}
    for name, roll, pitch in [("wrist_inboard",0,-90), ("wrist_outboard",180,90)]:
        samples = []
        for j3 in range(90,201,2):
            samples.append(Sample_Check(p,[0,75,j3,roll,pitch,0]))
        result["sweeps"][name] = samples
        print("Completed",name,flush=True)
    waypoints = [("STOW",c["poses"]["STOW"]), ("SAFE_UNFOLD",c["poses"]["SAFE_UNFOLD"]),
                 ("WRIST_NEUTRAL",[0,75,90,180,0,0]),
                 ("WRIST_TURNED",[0,75,90,0,0,0]), ("HOME",c["poses"]["HOME"])]
    for (na,qa),(nb,qb) in zip(waypoints, waypoints[1:]):
        count = math.ceil(max(abs(a-b) for a,b in zip(qa,qb))/3)
        samples = [Sample_Check(p,[a+(b-a)*i/count for a,b in zip(qa,qb)]) for i in range(count+1)]
        result["paths"][na+"_to_"+nb] = samples
        print("Completed path",na,nb,flush=True)
    for name,x in [("cake_near",400), ("cake_center",500), ("cake_far",600),
                   ("radius_650",math.sqrt(650**2-p["FoldLane"]**2))]:
        q = Task_SolveDownward(p,x,210)
        result["task_points"][name] = Sample_Check(p,q)
        if name == "cake_center":
            c["poses"]["CAKE_APPROACH"] = q
            doc,*_ = arm.Arm_BuildDocument(c,"CAKE_APPROACH")
            App.closeDocument(doc.Name)
    f0,parts0 = arm.Arm_GetGeometry(p,c["poses"]["STOW"])
    q = list(c["poses"]["STOW"]); q[2] -= 20
    f1,parts1 = arm.Arm_GetGeometry(p,q)
    a = next(v["shape"] for v in parts0 if v["name"] == "Motor_J3")
    b = next(v["shape"] for v in parts1 if v["name"] == "Motor_J3")
    assert (a.CenterOfMass-b.CenterOfMass).Length < 1e-8, "J3 stator must stay with upper arm"
    assert a.Placement.Rotation.isSame(b.Placement.Rotation,1e-8)
    axes = arm.Arm_GetAxes(p,f0)
    centers = [App.Vector(*x["origin_mm"]) for x in axes]
    for index,length in [(1,p["UpperArm"]),(2,p["Forearm"]),(3,p["Wrist"]),(4,p["Flange"])]:
        assert abs((centers[index+1]-centers[index]).Length-length) < 1e-6
    result["invariants"] = {"J3_stator_fixed_to_upper": True, "center_distances_match": True}
    (root/"analysis"/"motion_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    compact = {"sweeps":{},"paths":{},"task_points":{}}
    for category in ["sweeps","paths"]:
        for name,samples in result[category].items():
            bad = [x for x in samples if x["collisions"] or x["minimum_z_mm"] < -1e-6]
            compact[category][name] = {"sample_count":len(samples),"bad_samples":len(bad),"first_bad":bad[0] if bad else None,
                                     "min_motor_clearance_mm":min(x["min_motor_clearance"]["distance_mm"] for x in samples)}
    compact["task_points"] = result["task_points"]
    (root/"analysis"/"validation_summary.json").write_text(json.dumps(compact,indent=2),encoding="utf-8")
    print(json.dumps(compact,indent=2),flush=True)


if __name__ == "__main__":
    Layout_RunValidation()
