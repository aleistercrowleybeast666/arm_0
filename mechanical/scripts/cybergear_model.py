"""Measured-reference motor layers. Original mesh kept in a separate Detail document.

Canonical +Z points out; output face Z=0, fixed front flange Z=-3.
Numerical hole positions derive from the third-party STL, NOT a certified drawing.
"""
from pathlib import Path
import json
import math
import FreeCAD as App
import Part
import Mesh


def CyberGear_GetInterface():
    root=Path(__file__).resolve().parents[2]
    loops=json.loads((root/"analysis/stage2/cybergear_plane_loops.json").read_text())
    center=(40.8229898,79.0031928)
    stator=loops["Cybergear - motor-1.STL"]["3.14544094"]
    rotor=loops["Cybergear - rotor-1.STL"]["0.14544068"]
    fixed=[[round(v["center_xz"][i]-center[i],5) for i in range(2)] for v in stator if abs(v["radius"]-1.525)<.005 and v["fit_error_mm"]<.01]
    output=[[round(v["center_xz"][i]-center[i],5) for i in range(2)] for v in rotor if abs(v["radius"]-2.025)<.005 and v["fit_error_mm"]<.01]
    return {"body_diameter":75.0,"body_length":25.0,"total_depth":36.5,"rear_diameter":63.0,
            "rear_length":8.5,"fixed_plane_z":-3.0,"output_diameter":32.0,"output_depth":8.0,
            "fixed_holes_xy":fixed,"output_holes_xy":output,"mesh_to_canonical_translation":[-center[0],-center[1],0.14544068],
            "provenance":"Nominal diameters: CAD.png / manual p3; depth and hole coordinates: third-party STL. Hardware verification required."}


def Solid_Cylinder(radius,length,z=0):
    return Part.makeCylinder(radius,length,App.Vector(0,0,z))


def Solid_CutHoles(shape,centers,diameter,z,length):
    cutters=[Part.makeCylinder(diameter/2,length,App.Vector(x,y,z)) for x,y in centers]
    return shape.cut(Part.makeCompound(cutters)).removeSplitter()


def CyberGear_GetShapes():
    m=CyberGear_GetInterface()
    # Nine radial mounting ears are measured-model interfaces, not generic cylinders.
    body=Solid_Cylinder(37.5,25,-28).fuse(Solid_Cylinder(31.5,8.5,-36.5))
    ears=[Part.makeCylinder(3,25,App.Vector(x,y,-28)) for x,y in m["fixed_holes_xy"]]
    body=body.multiFuse(ears).fuse(Solid_Cylinder(21.5,2,-3))
    body=body.cut(Solid_Cylinder(16.25,8,-8))
    body=Solid_CutHoles(body,m["fixed_holes_xy"],3,-11,8)
    rotor=Solid_Cylinder(16,8,-8).cut(Solid_Cylinder(5,8,-8))
    rotor=Solid_CutHoles(rotor,m["output_holes_xy"],4,-6,6)
    # PROVISIONAL connector reserve, intentionally excluded from physical solid counts.
    cable=Part.makeBox(24,16,14,App.Vector(28,-8,-37))
    return {"stator":body,"rotor":rotor,"cable_reserve":cable}


def CyberGear_BuildDocuments():
    root=Path(__file__).resolve().parents[2]
    info=CyberGear_GetInterface()
    (root/"analysis/stage2/cybergear_interface_data.json").write_text(json.dumps(info,indent=2),encoding="utf-8")
    envelope=App.newDocument("CyberGear_Envelope")
    envelope.Label="CyberGear envelope | output +Z | reference-derived, verify hardware"
    sheet=envelope.addObject("Spreadsheet::Sheet","InterfaceParameters")
    for row,(key,value) in enumerate([(k,v) for k,v in info.items() if isinstance(v,(float,int))],1):
        sheet.set("A"+str(row),key); sheet.set("B"+str(row),str(value))
    for key,shape in CyberGear_GetShapes().items():
        obj=envelope.addObject("PartDesign::Feature","CyberGear_"+key); obj.Shape=shape
        obj.addProperty("App::PropertyString","Role"); obj.Role=key
    for name,z in [("FixedMountFace",-3),("OutputFace",0),("RearFace",-36.5)]:
        obj=envelope.addObject("PartDesign::Feature",name)
        obj.Shape=Part.makeCircle(45,App.Vector(0,0,z))
    axis=envelope.addObject("PartDesign::Feature","OutputAxis")
    axis.Shape=Part.makeLine(App.Vector(0,0,-50),App.Vector(0,0,20))
    envelope.recompute(); envelope.saveAs(str(root/"mechanical/freecad/CyberGear_Envelope.FCStd"))
    detail=App.newDocument("CyberGear_Detail")
    detail.Label="CyberGear Detail | original third-party meshes | REFERENCE ONLY"
    directory=root/"reference/cybergear/upstream/Cybergear model(SOLIDWORKS 2022 & STL)"
    for key in ["motor","rotor"]:
        mesh=Mesh.Mesh(str(directory/("Cybergear - "+key+"-1.STL")))
        placement=App.Placement(App.Vector(*info["mesh_to_canonical_translation"]),App.Rotation(App.Vector(1,0,0),-90))
        mesh.transform(placement.toMatrix())
        obj=detail.addObject("Mesh::Feature","CyberGear_"+key); obj.Mesh=mesh
        obj.addProperty("App::PropertyString","SourceFile"); obj.SourceFile=str(directory/("Cybergear - "+key+"-1.STL"))
    detail.recompute(); detail.saveAs(str(root/"mechanical/freecad/CyberGear_Detail.FCStd"))
    print("CyberGear Detail and Envelope built")


if __name__=="__main__":
    CyberGear_BuildDocuments()
