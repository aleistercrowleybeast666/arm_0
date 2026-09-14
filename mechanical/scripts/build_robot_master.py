"""Independent stage-2 CAD. Structured Bodies, open shells, seats, ribs and fasteners.

No PAROL6/Thor geometry enters this model. CyberGear is independently simplified
from drawing/mesh interface measurements; detailed source meshes remain separate.
"""
from pathlib import Path
import json
import math
import argparse
import FreeCAD as App
import Part
import arm_model
from cybergear_model import CyberGear_GetShapes, CyberGear_GetInterface, Solid_CutHoles


def Robot_LoadConfig():
    return json.loads((Path(__file__).resolve().parents[1]/"master_parameters.json").read_text(encoding="utf-8"))


def Shape_Box(dx,dy,dz,x,y,z):
    return Part.makeBox(dx,dy,dz,App.Vector(x,y,z))


def Shape_Cylinder(r,h,origin=(0,0,0),axis=(0,0,1)):
    return Part.makeCylinder(r,h,App.Vector(*origin),App.Vector(*axis))


def Shape_Ring(ro,ri,h,origin=(0,0,0),axis=(0,0,1)):
    return Shape_Cylinder(ro,h,origin,axis).cut(Shape_Cylinder(ri,h,origin,axis))


def Shape_Orient(shape,origin,axis):
    result=shape.copy()
    result.Placement=App.Placement(App.Vector(*origin),App.Rotation(App.Vector(0,0,1),App.Vector(*axis))).multiply(shape.Placement)
    return result


def Pattern_GetCircle(radius,count=4,start=45):
    return [(radius*math.cos(math.radians(start+360*i/count)),radius*math.sin(math.radians(start+360*i/count))) for i in range(count)]


def Shape_Profile(points,y,length):
    wire=Part.makePolygon([App.Vector(x,y,z) for x,z in points]+[App.Vector(points[0][0],y,points[0][1])])
    return Part.Face(wire).extrude(App.Vector(0,length,0))


def Shape_MotorPlate(p):
    m=CyberGear_GetInterface()
    blank=Shape_Ring(52,22,6,(0,0,-3))
    holes=Solid_CutHoles(blank,m["fixed_holes_xy"],p["m3_clearance"],-3,6)
    holes=Solid_CutHoles(holes,Pattern_GetCircle(47),p["m3_clearance"],-3,6)
    return blank,holes


def Shape_OutputAdapter(p):
    blank=Shape_Ring(19,8.2,8)
    return Solid_CutHoles(blank,CyberGear_GetInterface()["output_holes_xy"],p["m4_clearance"],0,8)


def Robot_GetComponents(p):
    m=CyberGear_GetInterface(); motors=CyberGear_GetShapes()
    u,l,h,lane,rail=p["UpperArm"],p["Forearm"],p["BaseHeight"],p["FoldLane"],p["UpperLane"]
    w,fl,t=p["Wrist"],p["Flange"],p["Tool"]
    wall,rib=p["link_wall"],p["rib_thickness"]
    components=[]

    def Component_Add(name,owner,shape_or_stages,role="printed",assembly=""):
        stages=shape_or_stages if isinstance(shape_or_stages,list) else [("Form",shape_or_stages)]
        if stages[-1][1].isNull() or not stages[-1][1].isValid():
            raise ValueError("Invalid CAD: "+name)
        components.append({"name":name,"owner":owner,"stages":stages,"shape":stages[-1][1],"role":role,"assembly":assembly})

    # STEP 1: six stators, six rotors and connector direction reserves, before shells.
    motor_specs=[(1,"base","yaw",(0,0,90),(0,0,90),(0,0,1)),
                 (2,"yaw","upper",(0,0,h),(0,0,0),(0,1,0)),
                 (3,"upper","fore",(u,0,0),(0,0,0),(0,1,0)),
                 (4,"fore","roll",(l,lane,0),(0,0,0),(1,0,0)),
                 (5,"roll","pitch",(w,-58,0),(0,-58,0),(0,1,0)),
                 (6,"pitch","tool",(fl,0,0),(0,0,0),(1,0,0))]
    for number,stator_owner,rotor_owner,stator_origin,rotor_origin,axis in motor_specs:
        assembly="J"+str(number)
        Component_Add(assembly+"_CyberGear_Stator",stator_owner,Shape_Orient(motors["stator"],stator_origin,axis),"motor",assembly)
        Component_Add(assembly+"_CyberGear_Rotor",rotor_owner,Shape_Orient(motors["rotor"],rotor_origin,axis),"rotor",assembly)
        Component_Add(assembly+"_CableReserve",stator_owner,Shape_Orient(motors["cable_reserve"],stator_origin,axis),"reserve",assembly)

    # J1 open tray, radial webs, service cable exit; detachable motor mounting plate.
    radius=p["J1_base_radius"]
    blank=Shape_Cylinder(radius,87)
    hollow=blank.cut(Shape_Cylinder(radius-wall,83,(0,0,wall)))
    webs=[]
    for angle in [45,135,225,315]:
        web=Shape_Box(radius-45, rib,83,45,-rib/2,wall)
        web.rotate(App.Vector(),App.Vector(0,0,1),angle); webs.append(web)
    reinforced=hollow.multiFuse(webs)
    for x,y in Pattern_GetCircle(47):
        reinforced=reinforced.fuse(Shape_Cylinder(5,8,(x,y,79)))
    for x,y in Pattern_GetCircle(57):
        reinforced=reinforced.fuse(Shape_Cylinder(5,11,(x,y,79)))
    holes=[]
    for x,y in Pattern_GetCircle(radius-13,4,0):
        holes.append(Shape_Cylinder(p["m5_clearance"]/2,wall,(x,y,0)))
    for x,y in Pattern_GetCircle(47):
        holes.append(Shape_Cylinder(p["insert_pilot_diameter"]/2,p["insert_depth"],(x,y,87-p["insert_depth"])))
    for x,y in Pattern_GetCircle(57):
        holes.append(Shape_Cylinder(p["insert_pilot_diameter"]/2,p["insert_depth"],(x,y,90-p["insert_depth"])))
    cable_cut=Shape_Box(20,p["cable_channel"],18,radius-15,-p["cable_channel"]/2,48)
    final=reinforced.cut(Part.makeCompound(holes+[cable_cut])).removeSplitter()
    Component_Add("J1_BaseTray","base",[("OuterForm",blank),("OpenCavity",hollow),("RadialRibs",reinforced),("MountAndCableCuts",final)],assembly="J1")
    plate0,plate=Shape_MotorPlate(p)
    Component_Add("J1_MotorMount","base",[("Plate",Shape_Orient(plate0,(0,0,90),(0,0,1))),
                  ("BoltHoles",Shape_Orient(plate,(0,0,90),(0,0,1)))],assembly="J1")
    bearing_seat=Shape_Ring(62,40.2,3,(0,0,93)).fuse(Shape_Ring(62,50.1,10,(0,0,96)))
    bearing_seat=bearing_seat.fuse(Shape_Ring(62,52.15,3,(0,0,90)))
    for x,y in Pattern_GetCircle(57): bearing_seat=bearing_seat.cut(Shape_Cylinder(p["m3_clearance"]/2,16,(x,y,90)))
    Component_Add("J1_BearingSeat","base",bearing_seat,assembly="J1")
    Component_Add("J1_BearingPlaceholder","base",Shape_Ring(50,40,10,(0,0,96)),"bearing","J1")
    Component_Add("J1_OutputAdapter","yaw",Shape_Orient(Shape_OutputAdapter(p),(0,0,90),(0,0,1)),"metal","J1")
    hub=Shape_Ring(19,8.2,8,(0,0,98)).fuse(Shape_Ring(39.9,32,10,(0,0,96)))
    bridge=Shape_Ring(40,8.2,4,(0,0,106))
    for x,y in Pattern_GetCircle(25): bridge=bridge.cut(Shape_Cylinder(p["m4_clearance"]/2,4,(x,y,106)))
    Component_Add("J1_OutputHub","yaw",hub.fuse(bridge),"metal","J1")
    plinth=Shape_Box(112,165,8,-56,-48,110)
    window=Shape_Box(64,55,8,-32,30,110)
    plinth_cut=plinth.cut(window).cut(Shape_Cylinder(8.2,8,(0,0,110)))
    for x,y in Pattern_GetCircle(25,4,45)+[(-34,-10),(34,-10),(-18,p["J2_shoulder_width"]-8),(18,p["J2_shoulder_width"]-8)]:
        plinth_cut=plinth_cut.cut(Shape_Cylinder(p["m4_clearance"]/2,8,(x,y,110)))
    Component_Add("J1_RotatingPlatform","yaw",[("Platform",plinth),("ServiceAndBoltHoles",plinth_cut)],assembly="J1")

    # J2 stationary paired cheeks. Left mount is removable; right seat has a shoulder.
    left_blank=Shape_Ring(50,22,6,(0,-3,h),(0,1,0)).fuse(Shape_Box(90,6,h-118-18,-45,-3,118))
    left_blank=left_blank.cut(Shape_Cylinder(22,6,(0,-3,h),(0,1,0)))
    left_cut=left_blank
    for x,y in m["fixed_holes_xy"]:
        left_cut=left_cut.cut(Shape_Cylinder(p["m3_clearance"]/2,6,(x,-3,h-y),(0,1,0)))
    feet=Shape_Box(90,24,6,-45,-18,118)
    left_cut=left_cut.fuse(feet)
    for x in [-39,35]:
        wire=Part.makePolygon([App.Vector(x,-18,124),App.Vector(x,-3,124),App.Vector(x,-3,150),App.Vector(x,-18,124)])
        left_cut=left_cut.fuse(Part.Face(wire).extrude(App.Vector(rib,0,0)))
    for x in [-34,34]:
        left_cut=left_cut.cut(Shape_Cylinder(p["m4_clearance"]/2,6,(x,-10,118)))
    Component_Add("J2_LeftMotorCheek","yaw",[("Cheek",left_blank),("MountAndFoot",left_cut.removeSplitter())],assembly="J2")
    far=p["J2_shoulder_width"]
    right_blank=Shape_Cylinder(30,16,(0,far-16,h),(0,1,0)).fuse(Shape_Box(52,16,h-118,-26,far-16,118))
    through=Shape_Cylinder(10.2,16,(0,far-16,h),(0,1,0))
    recess=Shape_Cylinder((p["bearing_outer"]+p["bearing_allowance"])/2,p["bearing_width"],(0,far-p["bearing_width"],h),(0,1,0))
    right_cut=right_blank.cut(through.fuse(recess))
    # Upper corners retain M3 bearing cover screws; vertical feet accept M4 bolts.
    for dx,dz in [(-23,0),(23,0),(0,24)]:
        right_cut=right_cut.cut(Shape_Cylinder(p["insert_pilot_diameter"]/2,5,(dx,far-5,h+dz),(0,1,0)))
    for x in [-18,18]:
        right_cut=right_cut.cut(Shape_Cylinder(p["m4_insert_pilot"]/2,8,(x,far-8,118)))
    for x in [-24,20]:
        wire=Part.makePolygon([App.Vector(x,far-30,118),App.Vector(x,far-16,118),App.Vector(x,far-16,150),App.Vector(x,far-30,118)])
        right_cut=right_cut.fuse(Part.Face(wire).extrude(App.Vector(rib,0,0)))
    Component_Add("J2_RightBearingCheek","yaw",[("Cheek",right_blank),("SteppedBearingSeat",right_cut.removeSplitter())],assembly="J2")
    Component_Add("J2_BearingPlaceholder","yaw",Shape_Ring(21,10,12,(0,far-12,h),(0,1,0)),"bearing","J2")
    cap=Shape_Ring(29,11,3,(0,far,h),(0,1,0))
    for dx,dz in [(-23,0),(23,0),(0,24)]: cap=cap.cut(Shape_Cylinder(1.7,3,(dx,far,h+dz),(0,1,0)))
    Component_Add("J2_BearingRetainer","yaw",cap,assembly="J2")
    # Double-sided journal support; steel shaft is a provisional machining envelope.
    shaft=Shape_Cylinder(8,far-8,(0,8,0),(0,1,0)).fuse(Shape_Cylinder(9.9,16,(0,far-16,0),(0,1,0)))
    Component_Add("J2_ThroughShaft","upper",shaft,"metal","J2")
    Component_Add("J2_OutputAdapter","upper",Shape_Orient(Shape_OutputAdapter(p),(0,0,0),(0,1,0)),"metal","J2")

    # A closed box root crosses to the outer lane outside the shoulder ring.
    root_blank=Shape_Box(102,16,44,-20,8,-22)
    root_shell=root_blank.cut(Shape_Box(94,8,36,-16,12,-18))
    root_shell=root_shell.cut(Shape_Cylinder(8.3,16,(0,8,0),(0,1,0)))
    for x,y in m["output_holes_xy"]:
        root_shell=root_shell.cut(Shape_Cylinder(2.25,4,(x,8,-y),(0,1,0))).cut(Shape_Cylinder(3.8,4,(x,20,-y),(0,1,0)))
    dogleg=Shape_Box(24,8-(rail-18),44,58,rail-18,-22)
    dogleg=dogleg.cut(Shape_Box(16,8-(rail-18),36,62,rail-18,-18))
    Component_Add("Upper_RootBox","upper",[("BoxBlank",root_blank),("ScrewAccessAndCavity",root_shell.fuse(dogleg).removeSplitter())],assembly="J3")

    # Shallow 15 degree-ish bow changes the outer profile, never the 320 mm axes.
    width,height,bend=p["upper_box_width"],p["upper_box_height"],p["upper_bend_offset"]
    centers=[(62,0),(152,bend),(242,0),(u-26,0)]
    outer=[(x,z+height/2) for x,z in centers]+[(x,z-height/2) for x,z in reversed(centers)]
    inner=[(66,height/2-wall),(152,bend+height/2-wall),(242,height/2-wall),(u-30,height/2-wall),
           (u-30,-height/2+wall),(242,-height/2+wall),(152,bend-height/2+wall),(66,-height/2+wall)]
    blank=Shape_Profile(outer,rail-width/2,width-wall)
    upper_outer_solid=blank.copy()
    shell=blank.cut(Shape_Profile(inner,rail-width/2+wall,width))
    ribs=[]
    for x in [110,195,260]:
        ribs.append(blank.common(Shape_Box(rib,width-wall,100,x,rail-width/2,-30)))
    reinforced=shell.multiFuse(ribs)
    # Rib passages keep a continuous longitudinal cable route.
    for x in [110,195,260]:
        reinforced=reinforced.cut(Shape_Cylinder(p["cable_channel"]/2,rib,(x,rail,8),(1,0,0)))
    bosses=[]
    for x,z in [(90,21),(150,bend+21),(215,22),(270,21),(90,-17),(215,-15),(270,-17)]:
        boss=Shape_Cylinder(4.5,width-wall,(x,rail-width/2,z),(0,1,0))
        reinforced=reinforced.fuse(boss)
        reinforced=reinforced.cut(Shape_Cylinder(p["insert_pilot_diameter"]/2,p["insert_depth"],(x,rail+width/2-wall-p["insert_depth"],z),(0,1,0)))
        bosses.append((x,z))
    Component_Add("Upper_BoxShell","upper",[("BentProfile",blank),("OpenCavity",shell),("RibsInsertsAndCable",reinforced.removeSplitter())],assembly="J3")
    lid=Shape_Profile(outer,rail+width/2-wall,wall)
    for x,z in bosses:
        lid=lid.cut(Shape_Cylinder(p["m3_clearance"]/2,wall,(x,rail+width/2-wall,z),(0,1,0)))
    Component_Add("Upper_RemovableLid","upper",lid,assembly="J3")

    # J3 front-open housing, detachable nine-hole fixed plate, short counter-bearing yoke.
    back=rail-18
    housing_blank=Shape_Cylinder(52,-3-back,(u,back,0),(0,1,0))
    housing=housing_blank.cut(Shape_Cylinder(42,-3-(back+wall),(u,back+wall,0),(0,1,0)))
    housing=housing.cut(Shape_Cylinder(32,-3-back,(u,back,0),(0,1,0)))
    for x,y in Pattern_GetCircle(47):
        housing=housing.cut(Shape_Cylinder(p["insert_pilot_diameter"]/2,p["insert_depth"],(u+x,-3-p["insert_depth"],-y),(0,1,0)))
    housing=housing.cut(Shape_Box(20,p["cable_channel"],18,u+38,back+8,-9))
    Component_Add("J3_StatorHousing","upper",[("HousingBlank",housing_blank),("FrontLoadingCavity",housing.removeSplitter())],assembly="J3")
    Component_Add("J3_FixedMotorPlate","upper",[("Plate",Shape_Orient(plate0,(u,0,0),(0,1,0))),
                  ("BoltHoles",Shape_Orient(plate,(u,0,0),(0,1,0)))],assembly="J3")
    far=p["J3_yoke_width"]
    yoke=Shape_Box(18,far-6,20,u-28,-10,-72).fuse(Shape_Box(18,7,32,u-28,-10,-72))
    cheek=Shape_Box(48,16,72,u-24,far-16,-72).fuse(Shape_Cylinder(29,16,(u,far-16,0),(0,1,0)))
    cheek=cheek.cut(Shape_Cylinder(10.2,16,(u,far-16,0),(0,1,0)))
    cheek=cheek.cut(Shape_Cylinder(21+p["bearing_allowance"]/2,12,(u,far-12,0),(0,1,0)))
    for dx,dz in [(-23,0),(23,0),(0,24)]:
        cheek=cheek.cut(Shape_Cylinder(p["insert_pilot_diameter"]/2,5,(u+dx,far-5,dz),(0,1,0)))
    for zz in [-66,-58]:
        cheek=cheek.cut(Shape_Cylinder(p["m4_clearance"]/2,16,(u-19,far-16,zz),(0,1,0)))
        yoke=yoke.cut(Shape_Cylinder(p["m4_insert_pilot"]/2,8,(u-19,far-24,zz),(0,1,0)))
    Component_Add("J3_CounterBearingYoke","upper",yoke.removeSplitter(),assembly="J3")
    Component_Add("J3_RemovableBearingCheek","upper",cheek.removeSplitter(),assembly="J3")
    Component_Add("J3_BearingPlaceholder","upper",Shape_Ring(21,10,12,(u,far-12,0),(0,1,0)),"bearing","J3")
    cap=Shape_Ring(29,11,3,(u,far,0),(0,1,0))
    for dx,dz in [(-23,0),(23,0),(0,24)]: cap=cap.cut(Shape_Cylinder(1.7,3,(u+dx,far,dz),(0,1,0)))
    Component_Add("J3_BearingRetainer","upper",cap,assembly="J3")
    shaft=Shape_Cylinder(8,far-8,(0,8,0),(0,1,0)).fuse(Shape_Cylinder(9.9,16,(0,far-16,0),(0,1,0)))
    Component_Add("J3_ThroughShaft","fore",shaft,"metal","J3")
    # Flanged output tube bridges to the side lane; end lugs bolt to the split forearm shell.
    root=Shape_Ring(19,8.2,lane-22,(0,8,0),(0,1,0)).fuse(Shape_Box(34,28,32,-17,lane-14,-16))
    root=root.cut(Shape_Cylinder(8.2,28,(0,lane-14,0),(0,1,0)))
    root=root.fuse(Shape_Orient(Shape_OutputAdapter(p),(0,0,0),(0,1,0)))
    for x,y in m["output_holes_xy"]:
        root=root.cut(Shape_Cylinder(p["m4_clearance"]/2,lane+14,(x,0,-y),(0,1,0)))
    root=root.cut(Shape_Cylinder(1.65,8,(0,lane,8),(0,0,1)))
    Component_Add("J3_ForearmOutputHub","fore",root.removeSplitter(),"metal","J3")
    fore_blank=Shape_Box(l-52,36,40,0,lane-18,-20)
    fore_shell=fore_blank.cut(Shape_Box(l-56,28,36,0,lane-14,-16))
    fore_shell=fore_shell.cut(Shape_Cylinder(19.2,4,(0,lane-18,0),(0,1,0)))
    fore_shell=fore_shell.fuse(Shape_Ring(25,19.2,8,(0,lane-22,0),(0,1,0)))
    fore_shell=fore_shell.cut(Shape_Cylinder(8.2,40,(0,lane-22,0),(0,1,0)))
    for x,y in m["output_holes_xy"]:
        fore_shell=fore_shell.cut(Shape_Cylinder(4,4,(x,lane+14,-y),(0,1,0)))
    fore_shell=max(fore_shell.Solids,key=lambda shape:shape.Volume)
    Component_Add("Forearm_Box","fore",[("Blank",fore_blank),("OpenChannel",fore_shell)],assembly="J4")
    fore_lid=Shape_Box(l-52,36,4,0,lane-18,20).cut(fore_shell).removeSplitter()
    fore_lid=fore_lid.cut(Shape_Cylinder(4,4,(0,lane,20)))
    Component_Add("Forearm_Lid","fore",fore_lid,assembly="J4")

    # J4-J6 are credible stator/output blockouts, intentionally not manufacturing release.
    housing=Shape_Ring(46,42,40,(l-40,lane,0),(1,0,0))
    front=Shape_Orient(plate,(l,lane,0),(1,0,0))
    Component_Add("J4_MountHousing","fore",housing.fuse(front),"blockout","J4")
    j4_adapter=Shape_Orient(Shape_OutputAdapter(p),(0,0,0),(1,0,0)).fuse(Shape_Ring(25,8.2,2,(6,0,0),(1,0,0)))
    Component_Add("J4_OutputAdapter","roll",j4_adapter,"metal","J4")
    side=Shape_Box(6,82,16,5,-110,-8).fuse(Shape_Box(3,8,16,8,-28,-8))
    cross=Shape_Box(w+3,8,24,5,-110,-12)
    mount=Shape_Orient(plate,(w,-58,0),(0,1,0))
    # Rear-to-front side wall sits outside the motor radius.
    brace=Shape_Box(8,52,24,w+44,-110,-12)
    tail=Shape_Box(44,8,24,w+8,-110,-12)
    Component_Add("J5_RollCarrier","roll",side.multiFuse([cross,mount,brace,tail]).removeSplitter(),"blockout","J5")
    rear=fl-m["total_depth"]
    backplate=Shape_Ring(45,32,4,(rear-4,0,0),(1,0,0))
    sideplate=Shape_Box(fl-rear+4,4,24,rear-4,-47,-12)
    wrist_plate=Solid_CutHoles(Shape_Ring(45,22,6,(0,0,-3)),m["fixed_holes_xy"],p["m3_clearance"],-3,6)
    front=Shape_Orient(wrist_plate,(fl,0,0),(1,0,0))
    output=Shape_Cylinder(10,11,(0,-58,0),(0,1,0))
    Component_Add("J6_PitchCarrier","pitch",backplate.multiFuse([sideplate,front,output]).removeSplitter(),"blockout","J6")
    adapter=Shape_Orient(Shape_OutputAdapter(p),(0,0,0),(1,0,0))
    tool=Shape_Ring(10,5,t-8,(8,0,0),(1,0,0))
    Component_Add("Tool_Interface","tool",adapter.fuse(tool),"blockout","J6")
    # Integrate intersecting geometry, then split at a bolted service seam for printing.
    integrated_names=["Upper_RootBox","Upper_BoxShell","J3_StatorHousing","J3_CounterBearingYoke"]
    integrated=[v for v in components if v["name"] in integrated_names]
    merged=integrated[0]["shape"].multiFuse([v["shape"] for v in integrated[1:]]).removeSplitter()
    split=p["upper_split_x"]
    seam_z=bend*(242-split)/90
    flanges=upper_outer_solid.common(Shape_Box(12,width,120,split-6,rail-width/2,-40))
    merged=merged.fuse(flanges)
    seam_holes=[]
    for yy in [rail-9,rail+9]:
        for zz in [seam_z-14,seam_z+14]:
            seam_holes.append(Shape_Cylinder(p["m4_clearance"]/2,12,(split-6,yy,zz),(1,0,0)))
    seam_holes.append(Shape_Cylinder(p["cable_channel"]/2,12,(split-6,rail,seam_z),(1,0,0)))
    merged=merged.cut(Part.makeCompound(seam_holes)).removeSplitter()
    lid_component=next(v for v in components if v["name"]=="Upper_RemovableLid")
    lid_shape=lid_component["shape"].cut(merged).removeSplitter()
    # Trimmed tip slivers are not separate printable cover pieces.
    lid_shape=max(lid_shape.Solids,key=lambda shape:shape.Volume)
    lid_component["shape"]=lid_shape; lid_component["stages"]=[("FittedRemovableCover",lid_shape)]
    components[:]=[v for v in components if v["name"] not in integrated_names]
    proximal=merged.common(Shape_Box(split+100,400,300,-100,-150,-100)).removeSplitter()
    distal=merged.common(Shape_Box(500-split,400,300,split,-150,-100)).removeSplitter()
    Component_Add("Upper_MainShell_Proximal","upper",[("BoltedSplitShell",proximal)],assembly="J3")
    Component_Add("Upper_MainShell_Distal","upper",[("ElbowHousingAndYoke",distal)],assembly="J3")
    return components


def Robot_GetWorldParts(p,q,components):
    frames=arm_model.Frame_GetChain(p,q)
    result=[]
    for component in components:
        item=dict(component); shape=component["shape"].copy()
        shape.Placement=frames[component["owner"]].multiply(shape.Placement)
        item["shape"]=shape; result.append(item)
    return frames,result


def Robot_SetPose(doc,name,config=None):
    config=config or Robot_LoadConfig(); p=config["dimensions"]; q=config["poses"][name]
    frames=arm_model.Frame_GetChain(p,q)
    for obj in doc.Objects:
        if obj.TypeId=="PartDesign::Body" and hasattr(obj,"FrameKey"):
            obj.Placement=frames[obj.FrameKey]
    for data in arm_model.Arm_GetAxes(p,frames):
        axis=doc.getObject("Axis_"+data["name"]); origin=doc.getObject("Origin_"+data["name"])
        point=App.Vector(*data["origin_mm"]); vector=App.Vector(*data["axis_world"])
        axis.Shape=Part.makeLine(point-vector*65,point+vector*65)
        axis.AxisDirection=vector; axis.AxisOrigin=point
        origin.Shape=Part.Vertex(point)
    doc.PoseController.CurrentPose=list(config["poses"])
    doc.PoseController.CurrentPose=name
    doc.PoseController.AnglesDeg=q
    doc.recompute()
    return frames


def Robot_BuildMaster(config=None,save=True):
    config=config or Robot_LoadConfig(); p=config["dimensions"]
    if p["MotorCount"]!=6 or min(p[k] for k in ["link_wall","rib_thickness","print_clearance"])<=0:
        raise ValueError("Invalid master parameters")
    components=Robot_GetComponents(p)
    doc=App.newDocument("Robot_Master"); doc.Label="Robot Master v2 | J1-J3 engineering prototype | PROVISIONAL"
    sheet=doc.addObject("Spreadsheet::Sheet","MasterParameters")
    for row,(key,val) in enumerate(p.items(),2):
        sheet.set("A"+str(row),key); sheet.set("B"+str(row),str(val)); sheet.setAlias("B"+str(row),key)
        sheet.set("C"+str(row),"BASELINE" if key in config["confirmed_baseline"] else "PROVISIONAL")
    sheet.set("A1","Parameter"); sheet.set("B1","mm / deg / count"); sheet.set("C1","Evidence status")
    controller=doc.addObject("App::FeaturePython","PoseController")
    controller.addProperty("App::PropertyEnumeration","CurrentPose"); controller.CurrentPose=list(config["poses"])
    controller.addProperty("App::PropertyFloatList","AnglesDeg")
    controller.addProperty("App::PropertyString","Instructions"); controller.Instructions="Run SetRobotPose.FCMacro; editing this field alone does not move solids."
    skeleton=doc.addObject("App::DocumentObjectGroup","MasterSkeleton")
    for i in range(1,7):
        axis=doc.addObject("PartDesign::Feature","Axis_J"+str(i)); skeleton.addObject(axis)
        axis.addProperty("App::PropertyVector","AxisDirection"); axis.addProperty("App::PropertyVector","AxisOrigin")
        origin=doc.addObject("PartDesign::Feature","Origin_J"+str(i)); skeleton.addObject(origin)
    groups={}
    for key in ["base","yaw","upper","fore","roll","pitch","tool"]:
        groups[key]=doc.addObject("App::Part","Rigid_"+key)
        groups[key].Label=key+" | rigid link"
    for component in components:
        body=doc.addObject("PartDesign::Body",component["name"]); groups[component["owner"]].addObject(body)
        for prop,value in [("FrameKey",component["owner"]),("Role",component["role"]),("Subassembly",component["assembly"])]:
            body.addProperty("App::PropertyString",prop,"Engineering"); setattr(body,prop,value)
        body.addProperty("App::PropertyString","ReleaseStatus","Engineering")
        body.ReleaseStatus="REFERENCE-DERIVED ENVELOPE" if component["role"] in ["motor","rotor"] else "PROVISIONAL / NOT RELEASED FOR LOADED USE"
        for stage_name,shape in component["stages"]:
            feature=doc.addObject("PartDesign::Feature",component["name"]+"_"+stage_name)
            body.addObject(feature); feature.Shape=shape
        body.Tip=feature
    Robot_SetPose(doc,"HOME",config)
    target=Path(__file__).resolve().parents[1]/"freecad/Robot_Master.FCStd"
    if save: doc.saveAs(str(target))
    print("Built",len(components),"components",flush=True)
    return doc,components


def Robot_ExportWorldParts(parts,target):
    doc=App.newDocument("ExportTemporary")
    objects=[]
    for part in parts:
        if part["role"]=="reserve": continue
        obj=doc.addObject("PartDesign::Feature",part["name"]); obj.Shape=part["shape"]; objects.append(obj)
    Part.export(objects,str(target)); App.closeDocument(doc.Name)


def Robot_RunBuild():
    config=Robot_LoadConfig(); doc,components=Robot_BuildMaster(config)
    root=Path(__file__).resolve().parents[1]
    frames,world=Robot_GetWorldParts(config["dimensions"],config["poses"]["HOME"],components)
    Robot_ExportWorldParts(world,root/"exports/Robot_Master_coarse.step")
    for name,assemblies in [("J1_base",["J1"]),("J2_shoulder",["J2"]),("J3_upper_elbow",["J3"])]:
        Robot_ExportWorldParts([v for v in world if v["assembly"] in assemblies],root/"exports"/(name+".step"))
    return doc


if __name__=="__main__":
    Robot_RunBuild()
