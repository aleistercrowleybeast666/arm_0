"""Prototype 0 fastener interfaces. No plastic threads; all lengths remain hardware-verify.
Dimensions are mm. Installed nut blocks require school measurements; catalogue is separate.
"""
import math
import FreeCAD as App
import Part
from geometry_arm_0 import Shape_Cylinder,Shape_Ring,Shape_Box,Shape_Orient,Pattern_GetCircle
from cybergear_model import CyberGear_GetInterface


def Vector_Get(value): return App.Vector(*value)


def Shape_GetHex(af,height,point,axis):
    r=af/math.sqrt(3)
    pts=[App.Vector(r*math.cos(math.radians(30+60*i)),r*math.sin(math.radians(30+60*i)),0) for i in range(6)]
    face=Part.Face(Part.makePolygon(pts+[pts[0]]))
    return Shape_Orient(face.extrude(App.Vector(0,0,height)),point,axis)


def Hardware_GetDimensions(size):
    return {3:dict(head_d=5.5,head_h=3,af=5.5,nut_h=2.4,lock_h=4,washer_d=7,washer_h=.5,key=2.5,pitch=.5),
            4:dict(head_d=7,head_h=4,af=7,nut_h=3.2,lock_h=5,washer_d=9,washer_h=.8,key=3,pitch=.7),
            5:dict(head_d=8.5,head_h=5,af=8,nut_h=4,lock_h=5,washer_d=15,washer_h=1,key=4,pitch=.8)}[size]


def Fastener_GetPlan(p):
    plan=[]; counters={};m=CyberGear_GetInterface();h,u,l,w,fl,mx=[p[k] for k in ['BaseHeight','UpperArm','Forearm','Wrist','Flange','j4_output_x']]
    def Add(j,a,b,size,points,axis,grip,receiver='LOCK_NUT',washer=True,remove=(),nut_entry=None,note='',head_recess=0):
        counters[j]=counters.get(j,0)+1;fid=f'F-J{j}-{counters[j]:03d}'
        plan.append(dict(id=fid,joint=f'J{j}',a=a,b=b,size=size,points=points,axis=axis,grip=grip,receiver=receiver,washer=washer,remove=list(remove),nut_entry=nut_entry,note=note,head_recess=head_recess))
    Add(1,'J1_BaseTray','LAB_BENCH',5,[(x,y,p['link_wall']) for x,y in Pattern_GetCircle(92,4,0)],(0,0,-1),p['link_wall']+20,note='Bench thickness UNKNOWN; 20 mm fixture budget only, not a measured table or bolt length.')
    Add(1,'J1_MotorMount','J1_BaseTray',3,[(x,y,92.5) for x,y in Pattern_GetCircle(47)],(0,0,-1),14,receiver='LOCK_NUT',washer=False,nut_entry=(1,0,0),remove=['J1_BearingSeat','J1_BearingPlaceholder','J1_OutputHub','J1_RotatingPlatform'],note='Nut pockets in rib sides, accessible with base opened.',head_recess=.5)
    Add(1,'J1_BearingSeat','J1_BaseTray',3,[(x,y,105.4) for x,y in Pattern_GetCircle(57)],(0,0,-1),26.9,receiver='LOCK_NUT',nut_entry=(1,0,0),remove=['J1_RotatingPlatform'])
    Add(1,'J1_RotatingPlatform','J1_OutputHub',4,[(x,y,118) for x,y in [(25,0),(-25,0),(0,45),(0,-45)]],(0,0,-1),8,receiver='METAL_TAPPED_THREAD',washer=False)
    # Stator: +canonical Z is outwards, plate outer face is output datum +3.
    specs=[(1,'J1_MotorMount','base',(0,0,90),(0,0,1)),(2,'J2_StatorPedestal','yaw',(0,20,h),(0,1,0)),(3,'J3_StatorMount','upper',(u,20,0),(0,1,0)),(4,'J4_ProximalStatorHousing','fore',(mx,0,0),(1,0,0)),(5,'J5_CompactStatorSupport','roll',(w,0,0),(0,1,0)),(6,'J6_OnePieceConnector','pitch',(fl,0,0),(1,0,0))]
    for j,a,owner,origin,axis in specs:
        placement=App.Placement(Vector_Get(origin),App.Rotation(App.Vector(0,0,1),Vector_Get(axis)))
        points=[tuple(placement.multVec(App.Vector(x,y,2 if j==1 else 3))) for x,y in m['fixed_holes_xy']]
        Add(j,a,f'J{j}_CyberGear_Stator',3,points,tuple(-Vector_Get(axis)),5 if j==1 else 6,'CYBERGEAR_THREAD',False,remove=['CHILD_LINKS','J5_RemovableBearingSeat','J6_OutputBearing','J6_BearingRetainer'],note='9-M3 reference pattern; final length/thread engagement TBD, verify motor hardware.')
    # Output holes: retain the current short hubs; add local head/driver pockets where required.
    outs=[(1,'J1_OutputHub','yaw',(0,0,110),(0,0,1),20),
          (2,'J2_OutputCheek','upper',(0,38,0),(0,1,0),18),
          (3,'J3_OutputForkCheek','fore',(0,38,0),(0,1,0),18),
          (4,'J4_MotorOutputAdapter','roll',(mx-l+2,0,0),(1,0,0),2),
          (5,'J5_ShortOutputHub','pitch',(0,2,0),(0,1,0),2),
          (6,'J6_ShortOutputHub','tool',(6,0,0),(1,0,0),6)]
    for j,a,owner,origin,axis,grip in outs:
        placement=App.Placement(Vector_Get(origin),App.Rotation(App.Vector(0,0,1),Vector_Get(axis)))
        points=[tuple(placement.multVec(App.Vector(x,y,0))) for x,y in m['output_holes_xy']]
        Add(j,a,f'J{j}_CyberGear_Rotor',4,points,tuple(-Vector_Get(axis)),grip,'CYBERGEAR_THREAD',False,remove=['J1_RotatingPlatform','J5_RemovableBearingSeat','J5_OutputSupportBearing','J5_BearingRetainer','J6_OnePieceConnector','J6_OutputBearing','J6_BearingRetainer'],note='6-M4; grip envelope is not procurement length; 1 mm thread occupancy only.')
    Add(2,'J1_RotatingPlatform','J2_StatorPedestal',4,[(x,20,114.8) for x in [-34,34]],(0,0,1),9.2,nut_entry='RADIAL_Z')
    Add(2,'J1_RotatingPlatform','J2_OppositeBearingPedestal',4,[(x,-26,114.8) for x in [-18,18]],(0,0,1),9.2,nut_entry='RADIAL_Z')
    for j,box,out,opp in [(2,'Upper_CentralBox','J2_OutputCheek','J2_OppositeForkCheek'),(3,'Forearm_CentralBox','J3_OutputForkCheek','J3_OppositeForkCheek')]:
        end=80 if j==2 else 112; yy=23 if j==2 else 28
        for side,cheek in [(1,out),(-1,opp)]:
            if j==2:
                Add(j,cheek,box,4,[(end-4,side*yy,z) for z in [-15,15]],(1,0,0),14,nut_entry=(0,side,0),remove=['Upper_RemovableCover'],note='Parallel flange stack uses M4 bolts/lock nuts; local straight driver channel in cheek.')
            else:
                Add(j,box,cheek,4,[(126,side*yy,z) for z in [-21,21]],(-1,0,0),20,nut_entry=(0,side,0),remove=['Forearm_RemovableCover'],note='Parallel stack; reversed insertion outside box sides avoids J4 motor and cable duct. Image M4 block is for perpendicular independent plates only.')

        Add(j,opp,f'J{j}_ShortBearingStub',3,[(x,-42.6,z) for x,z in Pattern_GetCircle(16)],(0,-1,0),5.4,nut_entry=(0,-1,0),note='Reverse bolt direction and recessed heads preserve the fixed retainer clearance.')
        cap=f'J{j}_BearingRetainer';seat='J2_OppositeBearingPedestal' if j==2 else 'J3_FixedBearingSupport';ox=0 if j==2 else u;oz=h if j==2 else 0
        Add(j,cap,seat,3,[(ox+x,-35,oz+z) for x,z in Pattern_GetCircle(20,3,90)],(0,1,0),10,'LOCK_NUT',False,nut_entry='RADIAL_Y',remove=['CHILD_LINKS'],note='Side-entry replaceable hex nuts; no plastic thread. Moving opposite cheek has a local annular head relief.')
    Add(3,'J3_StatorMount','J3_FixedBearingSupport',4,[(265,23,z) for z in [28,40]],(0,-1,0),56,nut_entry=(0,-1,0),remove=['Upper_RemovableCover'],note='Through upper diaphragm; 2 bolts retain both fixed supports, independent of the cover.')
    Add(4,'J4_ProximalStatorHousing','J3_OutputForkCheek',4,[(85,52.5,z) for z in [-10,10]],(-1,0,0),12,nut_entry=(0,1,0))
    Add(4,'J4_ProximalStatorHousing','J3_OppositeForkCheek',4,[(85,-52.5,z) for z in [-10,10]],(-1,0,0),12,nut_entry=(0,-1,0))
    for label,xx,attach in [('Proximal',104,136),('Distal',262,256)]:
        Add(4,f'J4_{label}BearingRetainer',f'J4_{label}BearingHousing',3,[(xx-2,y,z) for y,z in Pattern_GetCircle(21.8,3,90)],(1,0,0),9,'LOCK_NUT',False,nut_entry='RADIAL_X',remove=['Forearm_RemovableCover','J4_TorqueTube','J4_MotorOutputAdapter','J4_DistalOutputHub'],note='Small cap/seat bosses move M3 heads clear of rotating clamp.')
        Add(4,f'J4_{label}BearingHousing','Forearm_CentralBox',4,[(attach,y,-18.5) for y in [-7,7]],(0,0,-1),8.5,washer=label!='Distal',nut_entry=(0,0,-1),remove=['Forearm_RemovableCover'],note='Local mounting ears overlap bottom wall; lock nuts underneath. Distal screws/nuts seat directly on local pads without washers to clear retainer; bearing stress requires first-article review.')
    for a,x in [('J4_MotorOutputAdapter',mx-l+12),('J4_DistalOutputHub',-11)]:
        Add(4,a,a,3,[(x,15,math.sqrt(18**2-15**2))],(0,0,-1),math.sqrt(18**2-15**2)+.5 if a=='J4_DistalOutputHub' else 2*math.sqrt(18**2-15**2),receiver='METAL_TAPPED_THREAD' if a=='J4_DistalOutputHub' else 'LOCK_NUT',washer=a!='J4_DistalOutputHub',nut_entry=(0,0,-1),remove=['Forearm_RemovableCover'],note='Existing split clamp; distal M3 metal thread avoids cable divider; torque capacity provisional.')
    Add(5,'J5_CompactStatorSupport','J4_DistalOutputHub',4,[(10,y,z) for y,z in Pattern_GetCircle(20,3,90)],(-1,0,0),6,'METAL_TAPPED_THREAD',False)
    Add(5,'J5_RemovableBearingSeat','J5_CompactStatorSupport',3,[(w+x,7,z) for x,z in Pattern_GetCircle(27,3,90)],(0,-1,0),4,'METAL_TAPPED_THREAD',False,remove=['J6_OnePieceConnector'])
    Add(5,'J5_BearingRetainer','J5_RemovableBearingSeat',3,[(w+x,18,z) for x,z in Pattern_GetCircle(20,3,90)],(0,-1,0),4,'LOCK_NUT',False,nut_entry='RADIAL_Y',remove=['CHILD_LINKS'],note='One mm cap lip and recessed standard heads; replaceable side-entry metal nuts.')
    Add(5,'J6_OnePieceConnector','J6_OnePieceConnector',3,[(15,28,math.sqrt(23**2-15**2))],(0,0,-1),2*math.sqrt(23**2-15**2),nut_entry=(0,0,-1),note='Existing clamp remains provisional.')
    Add(6,'J6_BearingRetainer','J6_OnePieceConnector',3,[(fl+25,y,z) for y,z in Pattern_GetCircle(20,3,90)],(-1,0,0),5,'LOCK_NUT',False,nut_entry='RADIAL_X',remove=['J6_RemovableToolAdapter'])
    Add(6,'J6_RemovableToolAdapter','J6_RemovableToolAdapter',3,[(35,13,math.sqrt(20**2-13**2))],(0,0,-1),2*math.sqrt(20**2-13**2),nut_entry=(0,0,-1),note='13 mm overlap remains provisional; no new transmission concept.')
    Add(3,'Upper_RemovableCover','Upper_CentralBox',3,[(x,27,54*(x-80)/190+sgn*22) for x in [108,145,210,246] for sgn in [-1,1]],(0,-1,0),4.8,'LOCK_NUT',True,nut_entry=(0,1,0),note='Nut is removable through the open cover side; 8 M3 only.')
    Add(4,'Forearm_RemovableCover','Forearm_CentralBox',3,[(x,y,27) for x in [136,200,274] for y in [-19,19]],(0,0,-1),4.8,'LOCK_NUT',True,nut_entry=(0,0,1),note='Nut is removable after lifting the cover; 6 M3 only.')
    prerequisites={
        'F-J1-002':['J1_CyberGear_Stator'], 'F-J1-004':['J2_CyberGear_Stator'],
        'F-J1-006':['J2_CyberGear_Stator','J2_StatorPedestal'],
        'F-J4-001':['J3_OutputForkCheek','J3_OppositeForkCheek','Forearm_CentralBox'],
        'F-J4-002':['J4_TorqueTube'], 'F-J6-002':['J6_RemovableToolAdapter'],
        'F-J2-003':['J1_OutputHub'], 'F-J2-004':['J1_OutputHub'],
        'F-J4-005':['J4_ProximalStatorHousing','J4_CyberGear_Stator','J3_OutputForkCheek','J3_OppositeForkCheek'],
        'F-J4-008':['J4_DistalBearingRetainer'],
        'F-J5-003':['J5_OutputSupportBearing','J5_BearingRetainer','J5_RemovableBearingSeat','J5_CyberGear_Stator']}
    for r in plan:r['remove']=list(dict.fromkeys(r['remove']+prerequisites.get(r['id'],[])))
    return plan


def Fastener_Apply(parts,p):
    by={v['name']:v for v in parts}; plan=Fastener_GetPlan(p); hardware=[]
    def Cut(name,shape):
        if name in by:
            raw=by[name]['shape'].cut(shape,1e-6)
            clean=raw.removeSplitter()
            by[name]['shape']=clean if clean.isValid() else raw
            solids=sorted(by[name]['shape'].Solids,key=lambda x:x.Volume,reverse=True)
            # A through access cut can leave a sub-mm3 unsupported machining chip.
            # Discard only these detached chips; never repair a disconnected load-bearing member.
            if len(solids)>1 and sum(x.Volume for x in solids[1:])<1 and solids[0].Volume>10000:
                by[name].setdefault('removed_access_chips_mm3',[]).append(sum(x.Volume for x in solids[1:]))
                by[name]['shape']=solids[0]
            if not by[name]['shape'].isValid() or len(by[name]['shape'].Solids)!=1:
                raise ValueError('Invalid CUT '+name+' '+str(shape.BoundBox)+' solids='+str([(x.Volume,str(x.BoundBox)) for x in solids]))

    def Fuse(name,shape):
        by[name]['shape']=by[name]['shape'].fuse(shape).removeSplitter()
        if not by[name]['shape'].isValid(): raise ValueError('Invalid FUSE '+name+' '+str(shape.BoundBox))
    # Local bosses and access reliefs. Preserve all joint origins and main link sections.
    for j in [2,3]:
        opp='J2_OppositeForkCheek' if j==2 else 'J3_OppositeForkCheek'
        Cut(opp,Shape_Ring(24,16,2.1,(0,-39.1,0),(0,1,0)))
        seat='J2_OppositeBearingPedestal' if j==2 else 'J3_FixedBearingSupport';ox=0 if j==2 else p['UpperArm'];oz=p['BaseHeight'] if j==2 else 0
        for x,z in Pattern_GetCircle(20,3,90): Fuse(seat,Shape_Cylinder(4.1,6,(ox+x,-27,oz+z),(0,1,0)))
        Cut(seat,Shape_Cylinder(16.15,12,(ox,-33,oz),(0,1,0)))
        for side,cheek in [(1,'J2_OutputCheek' if j==2 else 'J3_OutputForkCheek'),(-1,opp)]:
            end=80 if j==2 else 112; yy=23 if j==2 else 28
            for z in ([-15,15] if j==2 else [-21,21]): Fuse(cheek,Shape_Cylinder(5.2,6,(end-6,side*yy,z),(1,0,0)))
    # J4 housing tab bolts clear the motor skirt at their revised local Y positions.
    for side,cheek in [(1,'J3_OutputForkCheek'),(-1,'J3_OppositeForkCheek')]:
        for z in [-10,10]:
            Fuse('J4_ProximalStatorHousing',Shape_Cylinder(5,6,(79,side*52.5,z),(1,0,0)))
            Fuse(cheek,Shape_Cylinder(5,6,(73,side*52.5,z),(1,0,0)))
            Cut(cheek,by['J4_ProximalStatorHousing']['shape'])
    for label,xx,attach in [('Proximal',104,136),('Distal',262,256)]:
        housing=f'J4_{label}BearingHousing';cap=f'J4_{label}BearingRetainer'
        for y,z in Pattern_GetCircle(21.8,3,90):
            Fuse(housing,Shape_Cylinder(4.1,12,(xx,y,z),(1,0,0)))
            Fuse(cap,Shape_Cylinder(4.1,2,(xx-2,y,z),(1,0,0)))
            for name in ['Forearm_CentralBox','Forearm_RemovableCover']+(['J3_OutputForkCheek','J3_OppositeForkCheek'] if label=='Proximal' else []):
                Cut(name,Shape_Cylinder(4.2,12.1,(xx-.05,y,z),(1,0,0)))
                Cut(name,Shape_Cylinder(4.2,2.1,(xx-2.05,y,z),(1,0,0)))
        for y in [-7,7]:
            Fuse(housing,Shape_Box(attach+6-min(xx+10,attach-5),10,4, min(xx+10,attach-5),y-5,-22.5))
            # Restore the existing floor under the small ear; the ear sits on it.
            fx=max(xx+12,attach-5) if label=='Proximal' else attach-5
            Fuse('Forearm_CentralBox',Shape_Box(attach+5-fx,10,4.5,fx,y-5,-27).cut(by[cap]['shape']))
            Cut('Forearm_CentralBox',Shape_Box(attach+6-min(xx+10,attach-5)+.1,10.2,4.1,min(xx+10,attach-5)-.05,y-5.1,-22.5))
        Cut(housing,by[cap]['shape'])
        if label=='Proximal':
            for side in [-1,1]:
                for z in [-21,21]:Cut(housing,Shape_Cylinder(6.1,22,(100,side*28,z),(1,0,0)))
        # Only new boss/ear clearance is cut; avoid coincident recuts of the old seat.
    for side in [-1,1]:
        for z in [-21,21]:
            boss=Shape_Cylinder(6,14,(112,side*28,z),(1,0,0));Fuse('Forearm_CentralBox',boss);Cut('Forearm_RemovableCover',boss)
    Cut('Forearm_CentralBox',Shape_Cylinder(23,8,(275,0,0),(1,0,0)))
    # Recessed retainer heads with a supporting outer lip, without changing bearing centers.
    for cap,seat,origin,axis in [('J5_BearingRetainer','J5_RemovableBearingSeat',(p['Wrist'],17,0),(0,1,0)),('J6_BearingRetainer','J6_OnePieceConnector',(p['Flange']+24,0,0),(1,0,0))]:
        lip=Shape_Ring(23,16.2,1,origin,axis);Fuse(cap,lip);Cut(seat,lip)
    for rec in plan:
        a,b=rec['a'],rec['b'];owner=by[a]['owner'];size=rec['size'];d=Vector_Get(rec['axis']);hd=Hardware_GetDimensions(size);t=hd['washer_h'] if rec['washer'] else 0
        rec['owner']=owner;rec['instances']=[]
        for index,coords in enumerate(rec['points'],1):
            P=Vector_Get(coords);head=P-d*t;exit=P+d*rec['grip'];prefix=rec['id'].replace('-','_')+f'_{index:02d}'
            is_nut=rec['receiver'] in ['HEX_NUT','LOCK_NUT'];height=hd['nut_h'] if rec['receiver']=='HEX_NUT' else hd['lock_h'];nutstart=exit+d*t
            shaftlength=rec['grip']+t+(t+height+hd['pitch'] if is_nut else 0)
            shaft=Shape_Cylinder(size/2-.1,shaftlength,tuple(head),tuple(d))
            if not is_nut:shaft=shaft.fuse(Shape_Cylinder(size*.36,1,tuple(exit),tuple(d)))
            bolt=shaft.fuse(Shape_Cylinder(hd['head_d']/2,hd['head_h'],tuple(head-d*hd['head_h']),tuple(d))).removeSplitter()
            # Drill exact mating members; the original motor thread envelope is preserved.
            bore=Shape_Cylinder((size+.4 if size==3 else size+.5)/2,rec['grip']+(t+height+1 if is_nut else 0 if rec['receiver']=='METAL_TAPPED_THREAD' else 1),tuple(P),tuple(d))
            Cut(a,bore)
            if b!='LAB_BENCH' and not b.endswith(('Stator','Rotor')):
                if rec['receiver']=='METAL_TAPPED_THREAD':
                    Cut(b,Shape_Cylinder({3:1.25,4:1.65,5:2.1}[size],1,tuple(exit),tuple(d)))
                else:Cut(b,bore)
            # Opening for recessed heads (and washers), including local interference inside A.
            clearance=Shape_Cylinder(max(hd['head_d']/2+.2,hd['washer_d']/2+.2 if t else 0),hd['head_h']+t,tuple(head-d*hd['head_h']),tuple(d))
            Cut(a,clearance)
            extra=[]
            if a=='J3_StatorMount' and b=='J3_FixedBearingSupport':extra=['Upper_CentralBox','Upper_RemovableCover']
            if a=='J4_ProximalStatorHousing' and b.startswith('J3_'):extra=[b]
            if b.startswith('J4_') and b.endswith('BearingHousing'):extra=['Forearm_CentralBox','Forearm_RemovableCover']+(['J3_OutputForkCheek','J3_OppositeForkCheek'] if 'Proximal' in b else [])
            if b=='Forearm_CentralBox' and a.startswith('J4_'):extra=[b]
            if b=='Upper_CentralBox' and a.startswith('J2_'):extra=['Upper_RemovableCover']
            if a=='Forearm_CentralBox' and b.startswith('J3_'):extra=['Forearm_RemovableCover','J4_ProximalBearingHousing']
            for name in extra:Cut(name,bore);Cut(name,clearance)
            items=[('Bolt',bolt)]
            if t:items.append(('HeadWasher',Shape_Ring(hd['washer_d']/2,(size+.4)/2,t,tuple(head),tuple(d))))
            nutentry=None;nutshape=None
            if is_nut:
                nutblank=Shape_GetHex(hd['af'],height,tuple(nutstart),tuple(d));nutshape=nutblank.cut(Shape_Cylinder((size+.1)/2,height,tuple(nutstart),tuple(d)))
                items.append(('LockNut' if rec['receiver']=='LOCK_NUT' else 'HexNut',nutshape))
                if t:items.append(('NutWasher',Shape_Ring(hd['washer_d']/2,(size+.4)/2,t,tuple(exit),tuple(d))))
                entry=rec['nut_entry']
                if isinstance(entry,str):
                    center=App.Vector(0,0,0)
                    if entry=='RADIAL_Y':
                        center=App.Vector(p['UpperArm'] if a.startswith('J3_') else p['Wrist'] if a.startswith('J5_') else 0,nutstart.y,p['BaseHeight'] if a.startswith('J2_') else 0)
                    elif entry=='RADIAL_X':center=App.Vector(nutstart.x,0,0)
                    else:center=App.Vector(0,0,nutstart.z)
                    nutentry=nutstart-center;nutentry.normalize()
                else:nutentry=Vector_Get(entry or tuple(d))
                # Open pocket/removal slot, not a sealed insert cavity. Head/receiver are same-link.
                pocket=Shape_GetHex(hd['af']+.45,height+.4,tuple(nutstart-d*.2),tuple(d))
                bb=pocket.BoundBox;travel=nutentry*12
                low=[min(getattr(bb,k+'Min'),getattr(bb,k+'Min')+travel[i]) for i,k in enumerate('XYZ')]
                high=[max(getattr(bb,k+'Max'),getattr(bb,k+'Max')+travel[i]) for i,k in enumerate('XYZ')]
                slot=Shape_Box(*[high[i]-low[i] for i in range(3)],*low)
                Cut(b,pocket);Cut(b,slot)
                for name in extra:Cut(name,pocket);Cut(name,slot)
                # Fasteners whose pocket opens through a detachable cover have that access cut too.
                for cover in ['Upper_RemovableCover','Forearm_RemovableCover']:
                    if b in ['Upper_CentralBox','Forearm_CentralBox'] and by[cover]['owner']==owner:Cut(cover,pocket)
                if t:
                    Cut(b,items[-1][1])
                    for name in extra:Cut(name,items[-1][1])
            names=[]
            for kind,shape in items:
                name=prefix+'_'+kind;names.append(name)
                hardware.append(dict(name=name,owner=owner,shape=shape.removeSplitter(),role='hardware_placeholder',assembly=rec['joint'],note='FASTENER ENVELOPE / LENGTH TBD / '+rec['id'],fastener_id=rec['id'],mates=[a,b],hardware_kind=kind,size=size))
            tool=Shape_Cylinder(hd['key']/math.sqrt(3)+.25,35,tuple(head-d*(hd['head_h']+.05)),tuple(-d))
            if b=='Forearm_CentralBox' and a.startswith('J4_'):Cut(b,tool)
            if a=='J4_MotorOutputAdapter' and rec['receiver']=='CYBERGEAR_THREAD':Cut(a,tool)
            if rec['id'] in ['F-J2-005','F-J2-006','F-J5-003']:Cut(a,tool)
            if a in ['J4_ProximalBearingRetainer','J4_DistalBearingRetainer']:Cut('Forearm_CentralBox',tool)
            if a=='J1_OutputHub' and rec['receiver']=='CYBERGEAR_THREAD':Cut('J1_RotatingPlatform',Shape_Cylinder(3.75,12,tuple(P),tuple(-d)))
            if a=='J1_MotorMount':Cut('J1_BearingSeat',clearance)
            rec['instances'].append(dict(names=names,point=list(P),tool=tool,nut=nutshape,nut_entry=list(nutentry) if nutentry else None))
    for v in parts+hardware:
        s=v['shape'];
        if not s.isValid() or len(s.Solids)!=1:raise ValueError('Fastener modification invalid: '+v['name']+' '+str(len(s.Solids)))
    return parts+hardware,plan
