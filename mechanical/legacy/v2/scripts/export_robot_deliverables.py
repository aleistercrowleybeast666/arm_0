"""Export low-complexity rigid-link envelopes, fit-test STLs, and audit round trips."""
from pathlib import Path
import json
import hashlib
import FreeCAD as App
import Part
import Mesh
import MeshPart
import build_robot_master as robot


def Robot_ExportDeliverables():
    root=Path(__file__).resolve().parents[2]
    cfg=robot.Robot_LoadConfig(); p=cfg["dimensions"]; parts=robot.Robot_GetComponents(p)
    export=root/"mechanical/exports"
    fit=export/"print_fit"; fit.mkdir(exist_ok=True)
    env=export/"envelope"; env.mkdir(exist_ok=True)
    report={"print_fit":[],"envelopes":[],"step_round_trip":{},"invariants":{}}
    for item in parts:
        if item["role"]!="printed" or item["assembly"] not in ["J1","J2","J3"]: continue
        shape=item["shape"]; bbox=shape.BoundBox
        mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,AngularDeflection=.2,Relative=False)
        path=fit/(item["name"]+".stl"); mesh.write(str(path))
        reloaded=Mesh.Mesh(str(path))
        record={"name":item["name"],"assembly":item["assembly"],"bounds_mm":[bbox.XLength,bbox.YLength,bbox.ZLength],
                "valid_solid":shape.isValid() and len(shape.Solids)==1,"closed_mesh":reloaded.isSolid(),"triangles":reloaded.CountFacets,
                "release":"FIT / ASSEMBLY ONLY. Material, orientation, hardware interfaces and loads require verification."}
        report["print_fit"].append(record)
        assert record["valid_solid"] and record["closed_mesh"],item["name"]
    names={"base":"base_envelope","yaw":"shoulder_envelope","upper":"upper_arm_envelope","fore":"forearm_envelope",
           "roll":"wrist_envelope","pitch":"wrist_pitch_envelope","tool":"tool_envelope"}
    for owner,name in names.items():
        chosen=[v for v in parts if v["owner"]==owner and v["role"]!="reserve"]
        boxes=[]
        for component in chosen:
            b=component["shape"].BoundBox
            boxes.append(robot.Shape_Box(b.XLength,b.YLength,b.ZLength,b.XMin,b.YMin,b.ZMin))
        shape=Part.makeCompound(boxes)
        robot.Robot_ExportWorldParts([{"name":name,"shape":shape,"role":"envelope"}],env/(name+".step"))
        report["envelopes"].append({"file":name+".step","frame":owner,"primitives":len(boxes),"faces":len(shape.Faces),
                                   "kind":"conservative per-component local AABBs, NOT exact collision bodies","included":[v["name"] for v in chosen]})
    _,world=robot.Robot_GetWorldParts(p,cfg["poses"]["HOME"],parts)
    for file,selection in [("Robot_Master_coarse.step",[v for v in world if v["role"]!="reserve"]),
                            ("J1_base.step",[v for v in world if v["assembly"]=="J1" and v["role"]!="reserve"]),
                            ("J2_shoulder.step",[v for v in world if v["assembly"]=="J2" and v["role"]!="reserve"]),
                            ("J3_upper_elbow.step",[v for v in world if v["assembly"]=="J3" and v["role"]!="reserve"])]:
        shape=Part.read(str(export/file)); expected=sum(v["shape"].Volume for v in selection)
        record={"valid":shape.isValid(),"solids":len(shape.Solids),"expected_solids":sum(len(v["shape"].Solids) for v in selection),
                "volume_error_mm3":abs(shape.Volume-expected)}
        assert record["valid"] and record["volume_error_mm3"]<.01
        assert record["solids"]==record["expected_solids"]
        report["step_round_trip"][file]=record
    doc=App.openDocument(str(root/"mechanical/freecad/Robot_Master.FCStd"))
    before=doc.J3_CyberGear_Stator.Placement
    robot.Robot_SetPose(doc,"STOW",cfg)
    after=doc.J3_CyberGear_Stator.Placement
    q=list(cfg["poses"]["STOW"]); cfg["poses"]["CHECK_J3_ONLY"]=[*q[:2],q[2]-15,*q[3:]]
    fixed=doc.J3_CyberGear_Stator.Placement
    robot.Robot_SetPose(doc,"CHECK_J3_ONLY",cfg)
    assert fixed.isSame(doc.J3_CyberGear_Stator.Placement,1e-8)
    distances={}
    for i,key in [(2,"UpperArm"),(3,"Forearm"),(4,"Wrist"),(5,"Flange")]:
        a=doc.getObject("Axis_J"+str(i)).AxisOrigin; b=doc.getObject("Axis_J"+str(i+1)).AxisOrigin
        distances[key]=(b-a).Length; assert abs(distances[key]-p[key])<1e-7
    assert len([o for o in doc.Objects if o.TypeId=="PartDesign::Body" and o.Role=="motor"])==6
    report["invariants"]={"J3_stator_fixed_on_J3_change":True,"six_motor_stators":True,"center_distances_mm":distances}
    App.closeDocument(doc.Name)
    # A conservative motor-only gravity screening, not a dynamics or payload calculation.
    _,extended=robot.Robot_GetWorldParts(p,[0]*6,parts)
    lower_bounds={}
    for joint in [3,4,5,6]:
        objects=[v for v in extended if v["name"] in [f"J{joint}_CyberGear_Stator",f"J{joint}_CyberGear_Rotor"]]
        lower_bounds[f"J{joint}"]=min(v["shape"].BoundBox.XMin for v in objects)/1000
    report["gravity_screen"]={"mass_lower_kg_per_motor":.314,"source":"repository manual p5: 317g +/-3g; p4 rated 4Nm",
        "minimum_x_levers_m":lower_bounds,"motor_only_J2_lower_bound_Nm":.314*9.81*sum(lower_bounds.values()),
        "rated_Nm":4,"caveat":"Uses reference envelope bounds at horizontal full extension; excludes all structures/tool and assumes model contains each motor mass. Requires J2 gearing/counterbalance/reselection study before powered prototype."}
    report["config_sha256"]=hashlib.sha256((root/"mechanical/master_parameters.json").read_bytes()).hexdigest()
    (root/"analysis/stage2/deliverable_checks.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    bridge={"schema":"ArmDesigner candidate bridge v2 (not tested against ArmDesigner)","units":"mm / deg","frames":names,
            "parameters":p,"envelope_semantics":"Each STEP is local to named rigid frame. Use provided world placements, not all at world origin.","poses":{}}
    for name,q in robot.Robot_LoadConfig()["poses"].items():
        frames,_=robot.Robot_GetWorldParts(p,q,parts)
        bridge["poses"][name]={owner:{"translation_mm":list(frames[owner].Base),"quaternion_xyzw":list(frames[owner].Rotation.Q)} for owner in names}
    (root/"analysis/stage2/armdesigner_bridge_v2.json").write_text(json.dumps(bridge,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__=="__main__": Robot_ExportDeliverables()
