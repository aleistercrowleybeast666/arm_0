"""Independent coarse CAD; mm/degrees. Run using FreeCAD's bundled Python.

No reference CAD, meshes, or URDF are imported. JSON is the source of truth.
Shapes are regenerated explicitly; Spreadsheet is an editable rebuild input.
"""
from pathlib import Path
from itertools import combinations
import argparse
import json
import math
import FreeCAD as App
import Part


def Arm_LoadConfig(path=None):
    source = Path(path) if path else Path(__file__).resolve().parents[1] / "parameters.json"
    config = json.loads(source.read_text(encoding="utf-8"))
    Arm_ValidateConfig(config)
    return config


def Arm_ValidateConfig(config):
    p = config["dimensions"]
    for key, value in p.items():
        if not math.isfinite(value) or (key != "UpperLane" and value <= 0):
            raise ValueError("Invalid dimension: " + key)
    if p["UpperArm"] <= 140 or p["Forearm"] <= 150:
        raise ValueError("Coarse bracket topology requires longer links")
    if p["MotorDiameter"] > 90 or p["MotorLength"] >= 63:
        raise ValueError("Motor exceeds v1 bracket topology; redesign brackets first")
    if p["Tool"] <= 8 or p["UpperLane"] >= -p["MotorLength"]-2:
        raise ValueError("Insufficient tool or motor mounting allowance")


def Frame_Create(origin=(0, 0, 0), axis=(0, 0, 1), angle=0):
    return App.Placement(App.Vector(*origin), App.Rotation(App.Vector(*axis), angle))


def Frame_GetChain(p, q):
    if len(q) != 6 or not all(math.isfinite(v) for v in q):
        raise ValueError("Expected six finite joint angles")
    yaw = Frame_Create(axis=(0, 0, 1), angle=q[0])
    shoulder = yaw.multiply(Frame_Create((0, 0, p["BaseHeight"])))
    upper = shoulder.multiply(Frame_Create(axis=(0, -1, 0), angle=q[1]))
    elbow = upper.multiply(Frame_Create((p["UpperArm"], 0, 0)))
    fore = elbow.multiply(Frame_Create(axis=(0, -1, 0), angle=q[2]))
    wrist = fore.multiply(Frame_Create((p["Forearm"], p["FoldLane"], 0)))
    roll = wrist.multiply(Frame_Create(axis=(1, 0, 0), angle=q[3]))
    pitch_base = roll.multiply(Frame_Create((p["Wrist"], 0, 0)))
    pitch = pitch_base.multiply(Frame_Create(axis=(0, -1, 0), angle=q[4]))
    flange_base = pitch.multiply(Frame_Create((p["Flange"], 0, 0)))
    tool = flange_base.multiply(Frame_Create(axis=(1, 0, 0), angle=q[5]))
    return {"base": Frame_Create(), "yaw": yaw, "shoulder": shoulder,
            "upper": upper, "elbow": elbow, "fore": fore, "wrist": wrist,
            "roll": roll, "pitch_base": pitch_base, "pitch": pitch,
            "flange_base": flange_base, "tool": tool}


def Shape_MakeCylinder(radius, length, origin, axis):
    return Part.makeCylinder(radius, length, App.Vector(*origin), App.Vector(*axis))


def Shape_MakeBar(start, end, radius):
    a, b = App.Vector(*start), App.Vector(*end)
    direction = b - a
    return Part.makeCylinder(radius, direction.Length, a, direction.normalize())


def Shape_MakeRing(ro, ri, length, origin, axis):
    return Shape_MakeCylinder(ro, length, origin, axis).cut(
        Shape_MakeCylinder(ri, length, origin, axis))


def Arm_GetGeometry(p, q):
    """Parts contain explicit stator ownership; adjacency is NOT collision-exempt."""
    f = Frame_GetChain(p, q)
    r, ml = p["MotorDiameter"] / 2, p["MotorLength"]
    u, l, lane, rail = p["UpperArm"], p["Forearm"], p["FoldLane"], p["UpperLane"]
    w, fl, tool = p["Wrist"], p["Flange"], p["Tool"]
    parts = []

    def Part_Add(name, owner, shape, frame, kind="structure"):
        shape.Placement = f[frame].multiply(shape.Placement)
        parts.append({"name": name, "owner": owner, "kind": kind, "shape": shape})

    # First: all six motor envelopes. No housing is designed before these.
    Part_Add("Motor_J1", "ground", Shape_MakeCylinder(r, ml, (0, 0, 25), (0, 0, 1)), "base", "motor")
    Part_Add("Motor_J2", "yaw", Shape_MakeCylinder(r, ml, (0, -ml-2, 0), (0, 1, 0)), "shoulder", "motor")
    Part_Add("Motor_J3", "upper", Shape_MakeCylinder(r, ml, (u, -ml-2, 0), (0, 1, 0)), "upper", "motor")
    Part_Add("Motor_J4", "fore", Shape_MakeCylinder(r, ml, (-ml-10, 0, 0), (1, 0, 0)), "wrist", "motor")
    Part_Add("Motor_J5", "roll", Shape_MakeCylinder(r, ml, (w, -r-10-ml, 0), (0, 1, 0)), "roll", "motor")
    # J6 front face is exactly the flange datum; preserve the full 90 mm tool length.
    Part_Add("Motor_J6", "pitch", Shape_MakeCylinder(r, ml, (fl-ml, 0, 0), (1, 0, 0)), "pitch", "motor")

    Part_Add("Base_Plate", "ground", Shape_MakeCylinder(95, 15, (0, 0, 0), (0, 0, 1)), "base")
    Part_Add("J1_Mount", "ground", Shape_MakeCylinder(r+3, 10, (0, 0, 15), (0, 0, 1)), "base")
    Part_Add("Base_Shell", "ground", Shape_MakeRing(70, r+6, 70, (0, 0, 15), (0, 0, 1)), "base")
    Part_Add("J1_Shaft", "yaw", Shape_MakeCylinder(12, 88-25-ml, (0, 0, 25+ml), (0, 0, 1)), "yaw", "interface")
    Part_Add("J1_Output", "yaw", Shape_MakeCylinder(42, 12, (0, 0, 88), (0, 0, 1)), "yaw")
    Part_Add("Shoulder_Column", "yaw", Part.makeBox(30, 24, p["BaseHeight"]-100,
             App.Vector(-15, -80, 100)), "yaw")
    Part_Add("Shoulder_Foot", "yaw", Shape_MakeBar((0, 0, 100), (0, -68, 100), 12), "yaw")
    Part_Add("J2_Mount", "yaw", Shape_MakeCylinder(r+3, 13, (0, -ml-15, 0), (0, 1, 0)), "shoulder")
    Part_Add("J2_Output", "upper", Shape_MakeCylinder(16, 16, (0, 0, 0), (0, 1, 0)), "upper")
    Part_Add("J2_Shaft", "upper", Shape_MakeCylinder(10, 2, (0, -2, 0), (0, 1, 0)), "upper", "interface")
    Part_Add("Upper_RootArm", "upper", Shape_MakeBar((0, 10, 0), (60, 10, 0), 8), "upper")
    Part_Add("Upper_Dogleg", "upper", Shape_MakeBar((60, 10, 0), (60, rail, 0), 8), "upper")
    Part_Add("Upper_Rail", "upper", Part.makeBox(u-60, p["RailWidth"], p["RailHeight"],
             App.Vector(60, rail-p["RailWidth"]/2, -p["RailHeight"]/2)), "upper")
    Part_Add("J3_Mount", "upper", Shape_MakeCylinder(r+3, -ml-2-(rail-10), (u, rail-10, 0), (0, 1, 0)), "upper")
    Part_Add("J3_Output", "fore", Shape_MakeCylinder(16, lane+10, (0, 0, 0), (0, 1, 0)), "fore")
    Part_Add("J3_Shaft", "fore", Shape_MakeCylinder(10, 2, (0, -2, 0), (0, 1, 0)), "fore", "interface")
    Part_Add("Fore_Rail", "fore", Part.makeBox(l-65, p["RailWidth"], p["RailHeight"],
             App.Vector(0, lane-p["RailWidth"]/2, -p["RailHeight"]/2)), "fore")
    Part_Add("J4_Mount", "fore", Shape_MakeCylinder(r+3, 8, (-ml-18, 0, 0), (1, 0, 0)), "wrist")
    Part_Add("J4_Output", "roll", Shape_MakeCylinder(15, 12, (-8, 0, 0), (1, 0, 0)), "roll")
    Part_Add("J4_Shaft", "roll", Shape_MakeCylinder(8, 2, (-10, 0, 0), (1, 0, 0)), "roll", "interface")
    Part_Add("Wrist_SideArm", "roll", Shape_MakeBar((0, 0, 0), (0, -r-ml-18, 0), 6), "roll")
    Part_Add("Wrist_LongArm", "roll", Shape_MakeBar((0, -r-ml-18, 0), (w, -r-ml-18, 0), 6), "roll")
    Part_Add("J5_Mount", "roll", Shape_MakeCylinder(r+3, 8, (w, -r-ml-18, 0), (0, 1, 0)), "roll")
    Part_Add("J5_Output", "pitch", Shape_MakeCylinder(10, 3, (0, -r-8, 0), (0, 1, 0)), "pitch")
    Part_Add("J5_Shaft", "pitch", Shape_MakeCylinder(8, 2, (0, -r-10, 0), (0, 1, 0)), "pitch", "interface")
    rear = fl-ml
    Part_Add("Wrist_OutputSide", "pitch", Part.makeBox(10-(rear-12), 3, 24,
             App.Vector(rear-12, -r-8, -12)), "pitch")
    Part_Add("Wrist_OutputBack", "pitch", Part.makeBox(6, r+8, 24,
             App.Vector(rear-12, -r-8, -12)), "pitch")
    Part_Add("J6_Mount", "pitch", Shape_MakeCylinder(r+3, 6, (rear-6, 0, 0), (1, 0, 0)), "pitch")
    Part_Add("Tool_Flange", "tool", Shape_MakeCylinder(28, 6, (0, 0, 0), (1, 0, 0)), "tool")
    Part_Add("Tool_Placeholder", "tool", Shape_MakeCylinder(10, tool-6, (6, 0, 0), (1, 0, 0)), "tool")
    return f, parts


def Arm_GetAxes(p, f):
    lane = p["FoldLane"]
    # Axis line representative points use the forearm lane for exact center distances.
    specs = [("J1", "base", (0,0,0), (0,0,1)),
             ("J2", "shoulder", (0,lane,0), (0,-1,0)),
             ("J3", "elbow", (0,lane,0), (0,-1,0)),
             ("J4", "wrist", (0,0,0), (1,0,0)),
             ("J5", "pitch_base", (0,0,0), (0,-1,0)),
             ("J6", "flange_base", (0,0,0), (1,0,0))]
    axes = []
    for name, frame, point, direction in specs:
        axes.append({"name": name, "origin_mm": list(f[frame].multVec(App.Vector(*point))),
                     "axis_world": list(f[frame].Rotation.multVec(App.Vector(*direction))),
                     "quaternion_xyzw": list(f[frame].Rotation.Q)})
    return axes


def Arm_CheckGeometry(parts, full=False):
    collisions, near = [], []
    pairs = 0
    min_motor = {"distance_mm": 1e9, "pair": []}
    for a, b in combinations(parts, 2):
        motor_pair = a["kind"] == b["kind"] == "motor"
        if not full and not motor_pair:
            continue
        if a["owner"] == b["owner"] and not motor_pair:
            continue
        pairs += 1
        sa, sb = a["shape"], b["shape"]
        ba, bb = sa.BoundBox, sb.BoundBox
        gap2 = sum(max(0, getattr(ba, ax+"Min")-getattr(bb, ax+"Max"),
                       getattr(bb, ax+"Min")-getattr(ba, ax+"Max"))**2 for ax in "XYZ")
        if not motor_pair and gap2 >= 25:
            continue
        distance = sa.distToShape(sb)[0]
        if motor_pair and distance < min_motor["distance_mm"]:
            min_motor = {"distance_mm": round(distance, 5), "pair": [a["name"], b["name"]]}
        if distance < 1e-6:
            volume = sa.common(sb).Volume
            if volume > 0.01:
                collisions.append({"pair": [a["name"], b["name"]], "volume_mm3": round(volume, 3)})
        elif distance < 5:
            near.append({"pair": [a["name"], b["name"]], "distance_mm": round(distance, 3)})
    return {"tested_pairs": pairs, "collisions": collisions, "clearance_under_5mm": near,
            "min_motor_clearance": min_motor,
            "invalid_shapes": [a["name"] for a in parts if not a["shape"].isValid()]}


def Arm_BuildDocument(config, pose_name, q=None, save=True):
    Arm_ValidateConfig(config)
    p = config["dimensions"]
    q = config["poses"][pose_name] if q is None else q
    f, parts = Arm_GetGeometry(p, q)
    doc = App.newDocument("Arm_" + pose_name)
    doc.Label = "ARM v1 | " + pose_name + " | ENVELOPES ONLY"
    sheet = doc.addObject("Spreadsheet::Sheet", "MasterParameters")
    sheet.set("A1", "Parameter"); sheet.set("B1", "Value (mm / deg)")
    for row, (key, val) in enumerate(list(p.items()) + [("Joint"+str(i+1)+"Angle", v) for i,v in enumerate(q)], 2):
        sheet.set("A"+str(row), key); sheet.set("B"+str(row), str(val)); sheet.setAlias("B"+str(row), key)
    sheet.set("D1", "Edit then run RebuildFromSheet.FCMacro; no live shape expressions")
    groups = {}
    for key in ("ground", "yaw", "upper", "fore", "roll", "pitch", "tool"):
        groups[key] = doc.addObject("App::DocumentObjectGroup", "Link_"+key)
    colors = {"ground": (0.27,0.32,0.40), "yaw": (0.50,0.57,0.64), "upper": (0.12,0.42,0.64),
              "fore": (0.1,0.66,0.63), "roll": (0.54,0.58,0.64), "pitch": (0.60,0.64,0.71), "tool": (0.84,0.33,0.24)}
    objects = []
    for part in parts:
        obj = doc.addObject("PartDesign::Feature", part["name"])
        obj.Shape = part["shape"]
        obj.addProperty("App::PropertyString", "RigidOwner", "Design"); obj.RigidOwner = part["owner"]
        obj.addProperty("App::PropertyString", "Role", "Design"); obj.Role = part["kind"]
        groups[part["owner"]].addObject(obj)
        if App.GuiUp:
            obj.ViewObject.ShapeColor = (0.92,0.60,0.13) if part["kind"] == "motor" else colors[part["owner"]]
            obj.ViewObject.LineColor = (0.12,0.15,0.20)
        objects.append(obj)
    skeleton = doc.addObject("App::DocumentObjectGroup", "MasterSkeleton")
    axes = Arm_GetAxes(p, f)
    for axis in axes:
        obj = doc.addObject("PartDesign::Feature", "Axis_"+axis["name"])
        pos = App.Vector(*axis["origin_mm"]); vec = App.Vector(*axis["axis_world"])
        obj.Shape = Part.makeLine(pos-vec*105, pos+vec*105)
        obj.addProperty("App::PropertyVector", "AxisDirection", "Kinematics"); obj.AxisDirection = vec
        obj.addProperty("App::PropertyVector", "AxisOrigin", "Kinematics"); obj.AxisOrigin = pos
        skeleton.addObject(obj)
        if App.GuiUp:
            obj.ViewObject.LineColor = (0.95,0.2,0.25); obj.ViewObject.LineWidth = 2
    skeleton_shape = Part.makePolygon([App.Vector(*a["origin_mm"]) for a in axes[1:]] +
                                      [f["tool"].multVec(App.Vector(p["Tool"],0,0))])
    line = doc.addObject("PartDesign::Feature", "Centerline"); line.Shape = skeleton_shape; skeleton.addObject(line)
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric(); Gui.activeDocument().activeView().fitAll()
    root = Path(__file__).resolve().parents[1]
    if save:
        doc.saveAs(str(root / "freecad" / ("Arm_v1_"+pose_name+".FCStd")))
        Part.export(objects, str(root / "exports" / ("Arm_v1_"+pose_name+".step")))
    return doc, f, parts, axes


def Arm_RunBatch(config):
    root = Path(__file__).resolve().parents[1]
    for sub in ("freecad", "exports", "docs"):
        (root/sub).mkdir(exist_ok=True)
    output = root.parent / "analysis"; output.mkdir(exist_ok=True)
    reports, bridge = {}, {"units": {"length": "mm", "angle": "deg"}, "poses": {}}
    for name, q in config["poses"].items():
        doc, f, parts, axes = Arm_BuildDocument(config, name)
        reports[name] = Arm_CheckGeometry(parts, full=True)
        reports[name]["angles_deg"] = q
        reports[name]["tcp_mm"] = list(f["tool"].multVec(App.Vector(config["dimensions"]["Tool"],0,0)))
        reports[name]["minimum_z_mm"] = min(a["shape"].BoundBox.ZMin for a in parts)
        bridge["poses"][name] = {"angles_deg": q, "axes": axes, "tcp_mm": reports[name]["tcp_mm"]}
        App.closeDocument(doc.Name)
        print(name, "collisions", len(reports[name]["collisions"]), flush=True)
    (output/"pose_checks.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    (output/"armdesigner_bridge.json").write_text(json.dumps(bridge, indent=2), encoding="utf-8")
    return reports


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    args = parser.parse_args()
    Arm_RunBatch(Arm_LoadConfig(args.config))
