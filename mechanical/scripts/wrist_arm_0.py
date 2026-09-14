"""Compact serial wrist. Reference-derived interfaces; bearing/load capacity provisional."""
import FreeCAD as App
from geometry_arm_0 import Shape_Box, Shape_Cylinder, Shape_Ring, Shape_Orient, Pattern_GetCircle
from cybergear_model import CyberGear_GetInterface, Solid_CutHoles


def Wrist_GetComponents(p):
    # Imported lazily to share primitives without changing the established FK.
    from build_arm_0 import Shape_DrillY, Shape_PolygonXY
    m=CyberGear_GetInterface(); w=p['Wrist']; fl=p['Flange']; wr=p['wrist_shaft_diameter']/2
    parts=[]
    def Component_Add(name,owner,shape,role,assembly,note='PROVISIONAL compact wrist; hardware and loads unverified'):
        shape=shape.removeSplitter()
        if not shape.isValid() or len(shape.Solids)!=1: raise ValueError(name+' invalid topology')
        parts.append(dict(name=name,owner=owner,shape=shape,role=role,assembly=assembly,note=note))
    plate=Shape_Orient(Solid_CutHoles(Shape_Ring(44,22,6,(0,0,-3)),m['fixed_holes_xy'],3.4,-3,6),(w,0,0),(0,1,0))
    # Short single-sided stator pedestal from J4 flange; no enclosing rectangular frame.
    root=Shape_Ring(25,8.2,6,(4,0,0),(1,0,0))
    bridge=Shape_Box(w-24,6,28,10,-3,-14)
    support=plate.fuse(root).fuse(bridge).cut(Shape_Cylinder(22,6,(w,-3,0),(0,1,0)))
    for yy,zz in Pattern_GetCircle(20,3,90): support=support.cut(Shape_Cylinder(2.25,6,(4,yy,zz),(1,0,0)))
    support=Shape_DrillY(support,Pattern_GetCircle(27,3,90),2.8,-1,4,ox=w)
    seat=Shape_Ring(31,20.3,4,(w,3,0),(0,1,0)).fuse(Shape_Ring(23,8.5,2,(w,7,0),(0,1,0)))
    seat=seat.fuse(Shape_Ring(23,16.15,9,(w,9,0),(0,1,0)))
    seat=Shape_DrillY(seat,Pattern_GetCircle(27,3,90),3.4,3,4,ox=w)
    cap=Shape_Ring(23,8.5,3,(w,18,0),(0,1,0))
    seat=Shape_DrillY(seat,Pattern_GetCircle(20,3,90),2.3,13,5,ox=w)
    cap=Shape_DrillY(cap,Pattern_GetCircle(20,3,90),3.4,18,3,ox=w)
    Component_Add('J5_CompactStatorSupport','roll',support,'metal','J5')
    Component_Add('J5_RemovableBearingSeat','roll',seat,'metal','J5')
    Component_Add('J5_OutputSupportBearing','roll',Shape_Ring(16,7.5,9,(w,9,0),(0,1,0)),'bearing','J5','GEOMETRIC PLACEHOLDER 15x32x9; single outboard support plus motor internal bearings')
    Component_Add('J5_BearingRetainer','roll',cap,'printed','J5')
    # Adapter is installed first; the removable seat and bearing slide over the neck.
    # The one-piece J6 connector clamps the final 12 mm and is axially retained at its face.
    hub=Shape_Ring(19,5,4,(0,0,0),(0,1,0)).fuse(Shape_Ring(wr-.1,5,30,(0,4,0),(0,1,0)))
    hub=Shape_DrillY(hub,[(x,-z) for x,z in m['output_holes_xy']],4.5,0,4)
    Component_Add('J5_ShortOutputHub','pitch',hub,'metal','J5')
    # One metal connector: J5 face flange -> tapered side web -> J6 mounting ring.
    connector=Shape_Ring(28,5,6,(0,34,0),(0,1,0)).fuse(Shape_Ring(23,7.55,12,(0,22,0),(0,1,0)))
    web=Shape_PolygonXY([(0,34),(27,34),(53,43),(fl,43),(fl,49),(51,49),(25,40),(0,40)],-19,38)
    front=Shape_Orient(Solid_CutHoles(Shape_Ring(44,22,6,(0,0,-3)),m['fixed_holes_xy'],3.4,-3,6),(fl,0,0),(1,0,0))
    # A short tab overlaps the ring volumetrically; web stays outside the motor ears.
    tab=Shape_Box(6,11,30,fl-3,38,-15)
    connector=connector.fuse(web).fuse(front).fuse(tab)
    connector=connector.cut(Shape_Box(24,12,1,0,22,-.5)).cut(Shape_Cylinder(1.7,38,(15,28,-19)))
    nose=Shape_Ring(23,8.5,2,(fl+11,0,0),(1,0,0)).fuse(Shape_Ring(23,16.15,12,(fl+13,0,0),(1,0,0)))
    import Part
    cone=Part.makeCone(43,23,8,App.Vector(fl+3,0,0),App.Vector(1,0,0)).cut(Part.makeCone(37,17,8,App.Vector(fl+3,0,0),App.Vector(1,0,0)))
    connector=connector.fuse(cone).fuse(nose)
    cap6=Shape_Ring(23,8.5,3,(fl+25,0,0),(1,0,0))
    for yy,zz in Pattern_GetCircle(20,3,90):
        connector=connector.cut(Shape_Cylinder(1.15,5,(fl+20,yy,zz),(1,0,0)))
        cap6=cap6.cut(Shape_Cylinder(1.7,3,(fl+25,yy,zz),(1,0,0)))
    # Counterbores open the nine front motor screw access channels through the nose.
    for yy,zz in m['fixed_holes_xy']:
        # Shape_Orient maps canonical XY to (world -Z, world Y) for +X.
        connector=connector.cut(Shape_Cylinder(3.2,10,(fl+3,zz,-yy),(1,0,0)))
    Component_Add('J6_OnePieceConnector','pitch',connector,'metal','J6','ONE-PIECE metal flange/web/ring connector; process, stiffness and preload unverified')
    Component_Add('J6_OutputBearing','pitch',Shape_Ring(16,7.5,9,(fl+14,0,0),(1,0,0)),'bearing','J6','GEOMETRIC PLACEHOLDER 15x32x9')
    Component_Add('J6_BearingRetainer','pitch',cap6,'printed','J6')
    hub6=Solid_CutHoles(Shape_Ring(19,5,8).fuse(Shape_Ring(wr-.1,5,34,(0,0,8))),m['output_holes_xy'],4.5,0,8)
    hub6=Shape_Orient(hub6,(0,0,0),(1,0,0))
    Component_Add('J6_ShortOutputHub','tool',hub6,'metal','J6','Metal output neck installed with motor from rear; support seat remains on connector')
    adapter=Shape_Ring(20,7.55,13,(29,0,0),(1,0,0)).fuse(Shape_Ring(20,5,5,(42,0,0),(1,0,0)))
    adapter=adapter.fuse(Shape_Ring(12,6,p['Tool']-47,(47,0,0),(1,0,0)))
    adapter=adapter.cut(Shape_Box(13,21,1,29,0,-.5)).cut(Shape_Cylinder(1.7,36,(35,13,-18)))
    Component_Add('J6_RemovableToolAdapter','tool',adapter,'metal','J6','Removable split-clamp tool adapter, 13 mm engagement; axial retention and torque capacity provisional')
    return parts
