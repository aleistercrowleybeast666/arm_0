"""Research-only reconstruction from upstream URDF, preserving link/joint names."""
from pathlib import Path
import xml.etree.ElementTree as ET
import math
import json
import FreeCAD as App
import Part
import Mesh


def Urdf_GetOrigin(element):
    if element is None:
        return App.Placement()
    xyz = [float(x)*1000 for x in element.get("xyz", "0 0 0").split()]
    roll, pitch, yaw = [math.degrees(float(x)) for x in element.get("rpy", "0 0 0").split()]
    return App.Placement(App.Vector(*xyz), App.Rotation(yaw, pitch, roll))


def Parol_BuildReference():
    root = Path(__file__).resolve().parents[2]
    package = root / "reference/PAROL6/PAROL6_URDF/PAROL6"
    source = package / "urdf/PAROL6.urdf"
    xml = ET.parse(source).getroot()
    doc = App.newDocument("PAROL6_reference_assembly")
    doc.Label = "PAROL6 reference only | upstream GPLv3 | URDF zero pose"
    joint_group = doc.addObject("App::DocumentObjectGroup", "URDF_Joints")
    transforms = {"world": App.Placement()}
    pending = list(xml.findall("joint"))
    joint_report = []
    while pending:
        progress = False
        for joint in pending[:]:
            parent, child = joint.find("parent").get("link"), joint.find("child").get("link")
            if parent not in transforms:
                continue
            local = Urdf_GetOrigin(joint.find("origin"))
            transforms[child] = transforms[parent].multiply(local)
            axis = App.Vector(*[float(x) for x in joint.find("axis").get("xyz").split()]) if joint.find("axis") is not None else App.Vector(0,0,1)
            obj = doc.addObject("PartDesign::Feature", "Joint_"+joint.get("name"))
            obj.Label = joint.get("name")
            origin = transforms[child].Base
            world_axis = transforms[child].Rotation.multVec(axis)
            obj.Shape = Part.makeLine(origin-world_axis*35, origin+world_axis*35)
            for prop, value in [("JointName",joint.get("name")),("JointType",joint.get("type")),("ParentLink",parent),("ChildLink",child)]:
                obj.addProperty("App::PropertyString",prop,"URDF"); setattr(obj,prop,value)
            obj.addProperty("App::PropertyVector","LocalAxis","URDF"); obj.LocalAxis=axis
            obj.addProperty("App::PropertyPlacement","JointOrigin","URDF"); obj.JointOrigin=local
            joint_group.addObject(obj)
            joint_report.append({"name":joint.get("name"),"parent":parent,"child":child,
                                 "origin_world_mm":list(origin),"axis_world":list(world_axis)})
            pending.remove(joint); progress=True
        if not progress:
            raise ValueError("URDF cycle or missing parent")
    mesh_report=[]
    for link in xml.findall("link"):
        name=link.get("name")
        group=doc.addObject("App::Part","Link_"+name); group.Label=name
        group.Placement=transforms[name]
        group.addProperty("App::PropertyString","UrdfLinkName"); group.UrdfLinkName=name
        for i,visual in enumerate(link.findall("visual")):
            mesh_element=visual.find("geometry/mesh")
            if mesh_element is None:
                continue
            uri=mesh_element.get("filename")
            if not uri.startswith("package://parol6/"):
                raise ValueError("Unexpected mesh URI: "+uri)
            path=package/uri.removeprefix("package://parol6/")
            mesh=Mesh.Mesh(str(path))
            scale=[float(x)*1000 for x in mesh_element.get("scale","1 1 1").split()]
            matrix=App.Matrix(); matrix.scale(*scale); mesh.transform(matrix)
            obj=doc.addObject("Mesh::Feature",name+"_visual_"+str(i)); obj.Mesh=mesh
            group.addObject(obj); obj.Placement=Urdf_GetOrigin(visual.find("origin"))
            obj.addProperty("App::PropertyString","SourceMesh","Provenance"); obj.SourceMesh=str(path)
            mesh_report.append({"link":name,"file":str(path.relative_to(root)),"stl_scale_to_mm":scale,"facets":mesh.CountFacets})
    doc.recompute()
    target=root/"mechanical/freecad/PAROL6_reference_assembly.FCStd"
    doc.saveAs(str(target))
    report={"urdf":str(source.relative_to(root)),"pose":"all joint angles zero","joints":joint_report,"meshes":mesh_report,
            "note":"STL numbers and URDF xyz both in meters; both scaled to mm. Reference geometry excluded from arm_0."}
    (root/"analysis/stage2/parol6_import.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(target)
    return doc


if __name__=="__main__":
    Parol_BuildReference()
