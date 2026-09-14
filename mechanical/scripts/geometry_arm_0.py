"""Independent arm_0 primitive helpers and retained V2 J1 base geometry."""
import math
import FreeCAD as App
import Part
from cybergear_model import CyberGear_GetInterface, Solid_CutHoles

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


def J1_GetComponents(p):
    components=[]
    wall,rib=p["link_wall"],p["rib_thickness"]
    def Component_Add(name,owner,shape_or_stages,role="printed",assembly="J1"):
        stages=shape_or_stages if isinstance(shape_or_stages,list) else [("Form",shape_or_stages)]
        components.append(dict(name=name,owner=owner,shape=stages[-1][1],stages=stages,role=role,assembly=assembly))
    radius=p["J1_base_radius"]
    blank=Shape_Cylinder(radius,87)
    hollow=blank.cut(Shape_Cylinder(radius-wall,83,(0,0,wall)))
    webs=[]
    for angle in [45,135,225,315]:
        web=Shape_Box(radius-45, rib,87-wall,45,-rib/2,wall)
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
    platform=Shape_Cylinder(65,8,(0,0,110)).cut(Shape_Cylinder(8.2,8,(0,0,110)))
    for x,y in Pattern_GetCircle(25)+[(-34,20),(34,20),(-18,-26),(18,-26)]:
        platform=platform.cut(Shape_Cylinder(2.25,8,(x,y,110)))
    Component_Add("J1_RotatingPlatform","yaw",platform)
    return components
