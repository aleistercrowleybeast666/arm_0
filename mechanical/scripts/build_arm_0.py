"""arm_0 V3: central clevis links and remotely driven J4. mm / degrees.
Independent primitives; reference-derived motor interfaces require hardware verification.
"""
from pathlib import Path
import math
import json
import FreeCAD as App
import Part
import arm_model
from cybergear_model import CyberGear_GetShapes, CyberGear_GetInterface, Solid_CutHoles
from geometry_arm_0 import Shape_Box, Shape_Cylinder, Shape_Ring, Shape_Orient, Shape_Profile, Pattern_GetCircle, J1_GetComponents


def Arm0_LoadConfig():
    return json.loads((Path(__file__).resolve().parents[1]/'arm_0_parameters.json').read_text(encoding='utf-8-sig'))


def Shape_Merge(shapes):
    return shapes[0].multiFuse(shapes[1:]).removeSplitter() if len(shapes)>1 else shapes[0]


def Shape_PolygonXY(points,z,height):
    pts=[App.Vector(x,y,z) for x,y in points]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,height))


def Shape_DrillY(shape,points,diam,y,length,ox=0,oz=0):
    return shape.cut(Part.makeCompound([Shape_Cylinder(diam/2,length,(ox+x,y,oz+z),(0,1,0)) for x,z in points])).removeSplitter()


def Shape_FixedPlate(m):
    plate=Shape_Ring(43,22,6,(0,17,0),(0,1,0))
    return Shape_DrillY(plate,[(x,-z) for x,z in m['fixed_holes_xy']],3.4,17,6)


def Joint_GetChild(p,m,proximal_roll=False):
    # Both cheeks are on the CHILD rigid body. Torque crosses through the clevis, not a shaft.
    positive=[(0,28),(40,28),(80,19),(80,27),(40,38),(0,38)]
    negative=[(0,-45),(40,-45),(80,-27),(80,-19),(40,-37),(0,-37)]
    if proximal_roll:
        positive=[(0,28),(35,28),(48,44),(84,44),(112,17),(112,25),(84,52),(48,52),(35,38),(0,38)]
        negative=[(0,-45),(35,-45),(48,-52),(84,-52),(112,-25),(112,-17),(84,-44),(48,-44),(35,-37),(0,-37)]
    left=Shape_Ring(28,10.2,10,(0,28,0),(0,1,0)).fuse(Shape_PolygonXY(positive,-24,48))
    right=Shape_Ring(28,10.2,8,(0,-45,0),(0,1,0)).fuse(Shape_PolygonXY(negative,-24,48))
    left=left.cut(Shape_Cylinder(10.2,10,(0,28,0),(0,1,0)))
    right=right.cut(Shape_Cylinder(10.2,8,(0,-45,0),(0,1,0)))
    left=Shape_DrillY(left,[(x,-z) for x,z in m['output_holes_xy']],4.5,28,10)
    right=Shape_DrillY(right,Pattern_GetCircle(16),3.4,-45,8)
    hub=Shape_Cylinder(19,4,(0,20,0),(0,1,0)).fuse(Shape_Cylinder(28,4,(0,24,0),(0,1,0)))
    hub=hub.fuse(Shape_Cylinder(10,10,(0,28,0),(0,1,0))).cut(Shape_Cylinder(5,18,(0,20,0),(0,1,0)))
    hub=Shape_DrillY(hub,[(x,-z) for x,z in m['output_holes_xy']],4.5,20,18)
    stub=Shape_Cylinder(9.9,25,(0,-45,0),(0,1,0)).fuse(Shape_Cylinder(20,3,(0,-48,0),(0,1,0)))
    stub=Shape_DrillY(stub,Pattern_GetCircle(16),3.4,-48,3)
    end=112 if proximal_roll else 80
    yy=21 if proximal_roll else 23
    for zz in [-15,15]:
        left=left.cut(Shape_Cylinder(2.25,12,(end-12,yy,zz),(1,0,0)))
        right=right.cut(Shape_Cylinder(2.25,12,(end-12,-yy,zz),(1,0,0)))
    return left.removeSplitter(),right.removeSplitter(),hub.removeSplitter(),stub.removeSplitter()


def Joint_GetBearing():
    seat=Shape_Ring(23,16.15,12,(0,-33,0),(0,1,0)).fuse(Shape_Ring(23,10.3,2,(0,-21,0),(0,1,0)))
    seat=Shape_DrillY(seat,Pattern_GetCircle(20,3,90),2.3,-33,5)
    cap=Shape_DrillY(Shape_Ring(23,10.5,2,(0,-35,0),(0,1,0)),Pattern_GetCircle(20,3,90),3.4,-35,2)
    bearing=Shape_Ring(16,10,10,(0,-31,0),(0,1,0))
    return seat,cap,bearing


def Arm0_GetComponents(p):
    parts=J1_GetComponents(p); m=CyberGear_GetInterface(); motors=CyberGear_GetShapes()
    u,l,h=p['UpperArm'],p['Forearm'],p['BaseHeight']; w,fl=p['Wrist'],p['Flange']
    wall,rib=p['link_wall'],p['rib_thickness']; mx=p['j4_output_x']
    def Component_Add(name,owner,shape,role='printed',assembly='',note='PROVISIONAL'):
        shape=shape.removeSplitter()
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError(f'{name}: valid={shape.isValid()} solids={[(s.Volume,str(s.BoundBox)) for s in shape.Solids]}')
        parts.append(dict(name=name,owner=owner,shape=shape,role=role,assembly=assembly,note=note))
    def Component_Translate(shape,x=0,y=0,z=0):
        result=shape.copy(); result.translate(App.Vector(x,y,z)); return result
    specs=[(1,'base','yaw',(0,0,90),(0,0,90),(0,0,1)),
           (2,'yaw','upper',(0,20,h),(0,20,0),(0,1,0)),
           (3,'upper','fore',(u,20,0),(0,20,0),(0,1,0)),
           (4,'fore','roll',(mx,0,0),(mx-l,0,0),(1,0,0)),
           (5,'roll','pitch',(w,0,0),(0,0,0),(0,1,0)),
           (6,'pitch','tool',(fl,0,0),(0,0,0),(1,0,0))]
    for j,fixed,moving,fs,rs,axis in specs:
        for key,owner,origin,role in [('stator',fixed,fs,'motor'),('rotor',moving,rs,'rotor')]:
            Component_Add(f'J{j}_CyberGear_{key.title()}',owner,Shape_Orient(motors[key],origin,axis),role,f'J{j}','REFERENCE-DERIVED / HARDWARE VERIFY')
        reserve=Shape_Orient(motors['cable_reserve'],fs,axis)
        Component_Add(f'J{j}_ConnectorReserve',fixed,reserve,'reserve',f'J{j}','PROVISIONAL DIRECTION')
    # J2 fixed stator and opposite bearing structure, tied through the compact yaw platform.
    plate=Shape_FixedPlate(m)
    foot=Shape_Box(90,20,6,-45,7,118-h)
    pedestal=Shape_Box(76,6,44,-38,17,124-h)
    mount=plate.fuse(foot).fuse(pedestal).cut(Shape_Cylinder(22,6,(0,17,0),(0,1,0)))
    for x in [-34,34]: mount=mount.cut(Shape_Cylinder(2.25,6,(x,20,118-h)))
    Component_Add('J2_StatorPedestal','yaw',Component_Translate(mount,z=h),assembly='J2')
    seat,cap,bearing=Joint_GetBearing()
    opposite=seat.fuse(Shape_Box(40,8,52,-20,-29,118-h)).fuse(Shape_Box(48,20,6,-24,-37,118-h))
    opposite=opposite.cut(Shape_Cylinder(16.15,12,(0,-33,0),(0,1,0))).cut(Shape_Cylinder(10.3,14,(0,-33,0),(0,1,0)))
    for x in [-18,18]: opposite=opposite.cut(Shape_Cylinder(3.1,8,(x,-26,118-h)))
    Component_Add('J2_OppositeBearingPedestal','yaw',Component_Translate(opposite,z=h),assembly='J2')
    Component_Add('J2_BearingRetainer','yaw',Component_Translate(cap,z=h),assembly='J2')
    Component_Add('J2_BearingPlaceholder','yaw',Component_Translate(bearing,z=h),'bearing','J2','GEOMETRIC PLACEHOLDER 20x32x10')
    left,right,hub,stub=Joint_GetChild(p,m)
    Component_Add('J2_OutputCheek','upper',left,assembly='J2')
    Component_Add('J2_OppositeForkCheek','upper',right,assembly='J2')
    Component_Add('J2_ShortOutputHub','upper',hub,'metal','J2')
    Component_Add('J2_ShortBearingStub','upper',stub,'metal','J2')
    # Central upper box: broad hollow section with shallow bow to the outside of forward folding.
    width,height,bend=p['upper_box_width'],p['upper_box_height'],p['upper_bend_offset']
    profile=[(80,0),(160,bend*80/190),(230,bend*150/190),(270,bend)]
    outline=[(x,z+height/2) for x,z in profile]+[(x,z-height/2) for x,z in reversed(profile)]
    inner=[(x,z+height/2-wall) for x,z in profile]+[(x,z-height/2+wall) for x,z in reversed(profile)]
    blank=Shape_Profile(outline,-width/2,width-wall)
    shell=blank.cut(Shape_Profile(inner,-width/2+wall,width))
    for xx in [84,145,210,262]:
        rr=blank.common(Shape_Box(rib,width,150,xx,-width/2,-40))
        rr=rr.cut(Shape_Cylinder(7,rib,(xx,0,bend*(xx-80)/190),(1,0,0)))
        shell=shell.fuse(rr)
    endframe=Shape_Box(10,width,height,80,-width/2,-height/2).cut(Shape_Box(10,width-16,height-16,80,-width/2+8,-height/2+8))
    shell=shell.fuse(endframe)
    lids=Shape_Profile(outline,width/2-wall,wall).cut(endframe)
    for xx,zz in [(xx,factor*bend+sign*(height/2-10)) for xx,factor in [(92,12/190),(145,65/190),(210,130/190),(260,180/190)] for sign in [-1,1]]:
        shell=shell.fuse(Shape_Cylinder(4.5,width-wall,(xx,-width/2,zz),(0,1,0)))
        shell=shell.cut(Shape_Cylinder(2.3,5,(xx,width/2-wall-5,zz),(0,1,0)))
        lids=lids.cut(Shape_Cylinder(1.7,wall,(xx,width/2-wall,zz),(0,1,0)))
    # End flanges bolt cheeks to central box, without a long cross-joint shaft.
    for xx in [80,264]:
        for yy in [-23,23]:
            for zz in [-15,15]: shell=shell.cut(Shape_Cylinder(2.25,10 if xx==80 else 6,(xx,yy,zz+(bend if xx==264 else 0)),(1,0,0)))
    # Internal diaphragm carries the removable J3 mounts; cover is not the sole load path.
    diaphragm=Shape_Box(10,width,22,258,-width/2,24)
    shell=shell.fuse(diaphragm)
    lids=lids.cut(diaphragm)
    # J3 stator front support attaches along +Y, rear support along -Y; both remain upper.
    front=Component_Translate(plate,x=u)
    tie=Shape_Profile([(260,15),(285,12),(295,20),(295,36),(260,40)],17,6)
    front=front.fuse(tie)
    rear=Component_Translate(seat,x=u).fuse(Shape_Profile([(260,16),(308,5),(316,17),(280,40),(260,48)],-33,8))
    rear=rear.cut(Shape_Cylinder(16.15,12,(u,-33,0),(0,1,0))).cut(Shape_Cylinder(10.3,14,(u,-33,0),(0,1,0)))
    for zz in [28,40]:
        front=front.cut(Shape_Cylinder(2.25,6,(265,17,zz),(0,1,0)))
        rear=rear.cut(Shape_Cylinder(2.25,14,(265,-33,zz),(0,1,0)))
        shell=shell.cut(Shape_Cylinder(2.25,width,(265,-width/2,zz),(0,1,0)))
        lids=lids.cut(Shape_Cylinder(2.25,wall,(265,width/2-wall,zz),(0,1,0)))
    # Keep detachable interfaces: subtract mating boxes, retain actual bolts/shoulders in the concept.
    shell=shell.cut(front).cut(rear).removeSplitter()
    lids=lids.cut(front).cut(rear).removeSplitter()
    Component_Add('Upper_CentralBox','upper',shell,assembly='J3')
    Component_Add('Upper_RemovableCover','upper',lids,assembly='J3')
    Component_Add('J3_StatorMount','upper',front,assembly='J3')
    Component_Add('J3_FixedBearingSupport','upper',rear,assembly='J3')
    Component_Add('J3_BearingRetainer','upper',Component_Translate(cap,x=u),assembly='J3')
    Component_Add('J3_BearingPlaceholder','upper',Component_Translate(bearing,x=u),'bearing','J3','GEOMETRIC PLACEHOLDER 20x32x10')
    left,right,hub,stub=Joint_GetChild(p,m,True)
    Component_Add('J3_OutputForkCheek','fore',left,assembly='J3')
    Component_Add('J3_OppositeForkCheek','fore',right,assembly='J3')
    Component_Add('J3_ShortOutputHub','fore',hub,'metal','J3')
    Component_Add('J3_ShortBearingStub','fore',stub,'metal','J3')
    # Proximal J4 at x=82 output; center of the 36.5 mm envelope is 63.75 from J3.
    j4plate=Solid_CutHoles(Shape_Ring(43,22,6,(0,0,-3)),m['fixed_holes_xy'],3.4,-3,6)
    housing=Shape_Ring(41.5+wall,41.5,33.5,(mx-36.5,0,0),(1,0,0)).fuse(Shape_Orient(j4plate,(mx,0,0),(1,0,0)))
    # Flat bolted tabs join the two local fork branches without penetrating the motor.
    tabs=[Shape_Box(6,10,32,mx-3,42,-16),Shape_Box(6,10,32,mx-3,-52,-16)]
    housing=Shape_Merge([housing]+tabs)
    for yy in [-48,48]:
        for zz in [-10,10]: housing=housing.cut(Shape_Cylinder(1.7,6,(mx-3,yy,zz),(1,0,0)))
    Component_Add('J4_ProximalStatorHousing','fore',housing,assembly='J4')
    for branch in parts:
        if branch['name'] in ['J3_OutputForkCheek','J3_OppositeForkCheek']: branch['shape']=branch['shape'].cut(housing).removeSplitter()
    width,height=p['forearm_box_width'],p['forearm_box_height']
    start,end=112,l-4
    outer=Shape_Box(end-start,width,height-wall,start,-width/2,-height/2)
    cavity=Shape_Box(end-start,width-2*wall,height,start,-width/2+wall,-height/2+wall)
    fore=outer.cut(cavity)
    entryframe=Shape_Box(10,width,height-wall,start,-width/2,-height/2).cut(Shape_Box(10,width-16,height,start,-width/2+8,-height/2+8))
    fore=fore.fuse(entryframe)
    # Corner cable duct stays below the divider and radially outside both tube bearings and the distal clamp.
    fore=fore.fuse(Shape_Box(end-start-4,width-2*wall,2,start+4,-width/2+wall,-15))
    for xx in [116,190,270]:
        rr=Shape_Box(rib,width-2*wall,height-wall,xx,-width/2+wall,-height/2)
        rr=rr.cut(Shape_Cylinder(13,rib,(xx,0,0),(1,0,0))).cut(Shape_Box(rib,14,7,xx,-7,-22))
        fore=fore.fuse(rr)
    for xx in [124,200,274]:
        for yy in [-19,19]:
            fore=fore.fuse(Shape_Cylinder(4.5,10,(xx,yy,height/2-wall-10)))
            fore=fore.cut(Shape_Cylinder(2.3,5,(xx,yy,height/2-wall-5)))
    cover=Shape_Box(end-start,width,wall,start,-width/2,height/2-wall)
    for xx in [124,200,274]:
        for yy in [-19,19]: cover=cover.cut(Shape_Cylinder(1.7,wall,(xx,yy,height/2-wall)))
    # Bearing housings span the shell walls; bore shoulders allow removal from the end.
    for label,xx in [('Proximal',104),('Distal',262)]:
        carrier=Shape_Ring(23,16.15,10,(xx,0,0),(1,0,0)).fuse(Shape_Ring(23,11.4,2,(xx+10,0,0),(1,0,0)))
        carrier=carrier.fuse(Shape_Box(12,width,8,xx,-width/2,-27)).cut(Shape_Cylinder(16.15,10,(xx,0,0),(1,0,0)))
        fore=fore.cut(carrier).cut(Shape_Cylinder(23,12,(xx,0,0),(1,0,0)))
        cover=cover.cut(carrier)
        for branch in parts:
            if branch["name"] in ["J3_OutputForkCheek","J3_OppositeForkCheek"]: branch["shape"]=branch["shape"].cut(carrier).removeSplitter()
        cap4=Shape_Ring(23,11.4,2,(xx-2,0,0),(1,0,0))
        for yy,zz in Pattern_GetCircle(20,3,90):
            cap4=cap4.cut(Shape_Cylinder(1.7,2,(xx-2,yy,zz),(1,0,0)))
            carrier=carrier.cut(Shape_Cylinder(1.15,5,(xx,yy,zz),(1,0,0)))
        fore=fore.cut(cap4)
        cover=cover.cut(cap4)
        Component_Add('J4_'+label+'BearingRetainer','fore',cap4,assembly='J4')
        Component_Add('J4_'+label+'BearingHousing','fore',carrier,assembly='J4')
        Component_Add('J4_'+label+'Bearing','fore',Shape_Ring(16,11.1,10,(xx,0,0),(1,0,0)),'bearing','J4','GEOMETRIC PLACEHOLDER 22.2x32x10')
    fore=fore.cut(Shape_Cylinder(20,12,(274,0,0),(1,0,0)))
    for yy in [-21,21]:
        for zz in [-15,15]:fore=fore.cut(Shape_Cylinder(2.25,10,(112,yy,zz),(1,0,0)))
    Component_Add('Forearm_CentralBox','fore',fore,assembly='J4')
    Component_Add('Forearm_RemovableCover','fore',cover,assembly='J4')
    duct=Shape_Box(end-start,p['forearm_cable_width'],p['forearm_cable_height'],start,12,-22)
    Component_Add('Forearm_CableDuctReserve','fore',duct,'reserve','J4','PROVISIONAL 8x5 corner duct; harness gauge and bends must be verified')
    adapter=Shape_Ring(19,5,6,(mx-l,0,0),(1,0,0)).fuse(Shape_Ring(18,11.15,12,(mx+6-l,0,0),(1,0,0)))
    # Axial M4 output access plus two split-clamp concept holes outside the rotating tube.
    canonical=Solid_CutHoles(Shape_Ring(19,5,6),m['output_holes_xy'],4.5,0,6)
    adapter=Shape_Orient(canonical,(mx-l,0,0),(1,0,0)).fuse(Shape_Ring(18,11.15,12,(mx+6-l,0,0),(1,0,0)))
    adapter=adapter.cut(Shape_Box(12,10,1,mx+6-l,10.5,-.5)).cut(Shape_Cylinder(1.7,22,(mx+12-l,15,-11)))
    Component_Add('J4_MotorOutputAdapter','roll',adapter,'metal','J4')
    tube_start=mx+8; tube_end=tube_start+p['j4_torque_tube_length']
    tube=Shape_Ring(p['j4_torque_tube_od']/2,p['j4_torque_tube_od']/2-p['j4_torque_tube_wall'],p['j4_torque_tube_length'],(tube_start-l,0,0),(1,0,0))
    Component_Add('J4_TorqueTube','roll',tube,'metal','J4')
    distal=Shape_Ring(18,11.15,14,(-14,0,0),(1,0,0)).fuse(Shape_Ring(25,8,4,(0,0,0),(1,0,0)))
    distal=distal.cut(Shape_Box(14,10,1,-14,10.5,-.5)).cut(Shape_Cylinder(1.7,22,(-11,15,-11)))
    for yy,zz in Pattern_GetCircle(20,3,90): distal=distal.cut(Shape_Cylinder(2.25,4,(0,yy,zz),(1,0,0)))
    Component_Add('J4_DistalOutputHub','roll',distal,'metal','J4')
    from wrist_arm_0 import Wrist_GetComponents
    parts.extend(Wrist_GetComponents(p))
    # Cut the same static route through shell, end frames, bearing housings and retainers.
    for part in parts:
        if part['owner']=='fore' and part['role']=='printed': part['shape']=part['shape'].cut(duct).removeSplitter()
        if not part['shape'].isValid() or len(part['shape'].Solids)!=1: raise ValueError('Final component topology: '+part['name'])
    return parts


def Arm0_GetWorldParts(p,q,parts):
    frames=arm_model.Frame_GetChain(p,q); world=[]
    for part in parts:
        item=dict(part); shape=part['shape'].copy(); shape.Placement=frames[part['owner']].multiply(shape.Placement)
        item['shape']=shape; world.append(item)
    return frames,world


def Arm0_SetPose(doc,name,cfg=None):
    cfg=cfg or Arm0_LoadConfig(); q=cfg['poses'][name]; frames=arm_model.Frame_GetChain(cfg['dimensions'],q)
    for obj in doc.Objects:
        if obj.TypeId=='PartDesign::Body' and hasattr(obj,'FrameKey'): obj.Placement=frames[obj.FrameKey]
    for data in arm_model.Arm_GetAxes(cfg['dimensions'],frames):
        axis=doc.getObject('Axis_'+data['name']); point=App.Vector(*data['origin_mm']); direction=App.Vector(*data['axis_world'])
        axis.Shape=Part.makeLine(point-direction*55,point+direction*55); axis.AxisOrigin=point; axis.AxisDirection=direction
        doc.getObject('Origin_'+data['name']).Shape=Part.Vertex(point)
    doc.PoseController.CurrentPose=list(cfg['poses']); doc.PoseController.CurrentPose=name; doc.PoseController.AnglesDeg=q
    doc.recompute(); return frames


def Arm0_BuildDocument(cfg=None,save=True):
    cfg=cfg or Arm0_LoadConfig(); p=cfg['dimensions']
    for k,v in dict(BaseHeight=180,UpperArm=320,Forearm=290,Wrist=60,Tool=90,MotorCount=6).items():
        if p[k]!=v: raise ValueError('Locked baseline '+k)
    if p['Flange']<86: raise ValueError('Compact serial wrist requires Flange >=86 mm; revalidate any change')
    if p['FoldLane']!=0 or p['UpperLane']!=0: raise ValueError('V3 requires central link lanes')
    parts=Arm0_GetComponents(p); doc=App.newDocument('arm_0'); doc.Label='arm_0 | Prototype 0'
    sheet=doc.addObject('Spreadsheet::Sheet','MasterParameters')
    for row,(k,v) in enumerate(p.items(),2):
        sheet.set('A'+str(row),k); sheet.set('B'+str(row),str(v)); sheet.setAlias('B'+str(row),k)
        sheet.set('C'+str(row),'BASELINE LOCKED' if k in cfg['confirmed_baseline'] else 'LEGACY OFFSET / LOCKED ZERO' if k in cfg['deprecated_parameters'] else 'RESERVED / NOT DRIVING GEOMETRY' if k in cfg.get('reserved_parameters',[]) else 'PROVISIONAL')
    controller=doc.addObject('App::FeaturePython','PoseController'); controller.addProperty('App::PropertyEnumeration','CurrentPose'); controller.CurrentPose=list(cfg['poses'])
    controller.addProperty('App::PropertyFloatList','AnglesDeg'); controller.addProperty('App::PropertyString','Instructions'); controller.Instructions='Select CurrentPose, then run SetArm0Pose.FCMacro.'
    skel=doc.addObject('App::DocumentObjectGroup','MasterSkeleton')
    for i in range(1,7):
        axis=doc.addObject('PartDesign::Feature',f'Axis_J{i}'); skel.addObject(axis)
        axis.addProperty('App::PropertyVector','AxisOrigin'); axis.addProperty('App::PropertyVector','AxisDirection')
        skel.addObject(doc.addObject('PartDesign::Feature',f'Origin_J{i}'))
    groups={k:doc.addObject('App::Part','Rigid_'+k) for k in ['base','yaw','upper','fore','roll','pitch','tool']}
    for part in parts:
        body=doc.addObject('PartDesign::Body',part['name']); groups[part['owner']].addObject(body)
        for key,value in [('FrameKey',part['owner']),('Role',part['role']),('Subassembly',part['assembly']),('ReleaseStatus',part.get('note','PROVISIONAL'))]:
            body.addProperty('App::PropertyString',key,'Engineering'); setattr(body,key,value)
        feature=doc.addObject('PartDesign::Feature',part['name']+'_Geometry'); body.addObject(feature); feature.Shape=part['shape']; body.Tip=feature
    Arm0_SetPose(doc,'HOME',cfg)
    if save: doc.saveAs(str(Path(__file__).resolve().parents[1]/'freecad/arm_0.FCStd'))
    print('Built arm_0:',len(parts),'components',flush=True); return doc,parts


def Arm0_ExportParts(parts,path):
    doc=App.newDocument('ExportTemporary'); objects=[]
    for part in parts:
        if part['role']=='reserve': continue
        obj=doc.addObject('PartDesign::Feature',part['name']); obj.Shape=part['shape']; objects.append(obj)
    Part.export(objects,str(path)); App.closeDocument(doc.Name)


def Arm0_RunBuild():
    cfg=Arm0_LoadConfig(); doc,parts=Arm0_BuildDocument(cfg); _,world=Arm0_GetWorldParts(cfg['dimensions'],cfg['poses']['HOME'],parts)
    directory=Path(__file__).resolve().parents[1]/'exports'
    Arm0_ExportParts(world,directory/'arm_0.step')
    for j in ['J1','J2','J3']: Arm0_ExportParts([v for v in world if v['assembly']==j],directory/f'arm_0_{j}.step')


if __name__=='__main__': Arm0_RunBuild()
