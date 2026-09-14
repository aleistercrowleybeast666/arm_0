"""Export arm_0 local print candidates and lightweight collision boxes; verify STEP round trips."""
from pathlib import Path
import json
import FreeCAD as App
import Part
import Mesh
import MeshPart
import build_arm_0 as arm


def Arm0_ExportDeliverables():
    root=Path(__file__).resolve().parents[2]; cfg=arm.Arm0_LoadConfig();p=cfg['dimensions'];parts=arm.Arm0_GetComponents(p)
    output=root/'mechanical/exports';report=dict(print_fit=[],step_round_trip={},envelopes=[],bridge={})
    for part in parts:
        if part['role']!='printed':continue
        mesh=MeshPart.meshFromShape(Shape=part['shape'],LinearDeflection=.12,AngularDeflection=.2,Relative=False)
        path=output/'print_fit'/(part['name']+'.stl');mesh.write(str(path));loaded=Mesh.Mesh(str(path));assert loaded.isSolid(),part['name']
        b=part['shape'].BoundBox
        report['print_fit'].append(dict(name=part['name'],closed_mesh=True,triangles=loaded.CountFacets,bounds_mm=[b.XLength,b.YLength,b.ZLength],release='Static fit/assembly candidate only; material and orientation require engineering review'))
    _,world=arm.Arm0_GetWorldParts(p,cfg['poses']['HOME'],parts)
    extra=[('arm_0_wrist.step',[v for v in world if v['assembly'] in ['J5','J6']]),('arm_0_J6_OnePieceConnector.step',[v for v in parts if v['name']=='J6_OnePieceConnector'])]
    for filename,selected in extra: arm.Arm0_ExportParts(selected,output/filename)
    for filename,selected in [('arm_0.step',world)]+[(f'arm_0_{j}.step',[v for v in world if v['assembly']==j]) for j in ['J1','J2','J3']]+extra:
        physical=[v for v in selected if v['role']!='reserve'];shape=Part.read(str(output/filename))
        reference_volume=sum(v['shape'].Volume for v in physical)
        error=abs(shape.Volume-reference_volume)
        remaining=list(shape.Solids);round_trip_parts=[]
        assert shape.isValid() and len(remaining)==len(physical),(filename,'solid topology')
        for part in physical:
            original=part['shape'].Solids[0]
            restored=min(remaining,key=lambda x:(x.CenterOfMass-original.CenterOfMass).Length)
            remaining.remove(restored)
            shift=(restored.CenterOfMass-original.CenterOfMass).Length
            relative_error=abs(restored.Volume-original.Volume)/original.Volume
            bound_error=max(abs(getattr(restored.BoundBox,key)-getattr(original.BoundBox,key)) for key in ['XMin','YMin','ZMin','XMax','YMax','ZMax'])
            assert restored.isValid() and relative_error<1e-5 and shift<.001 and bound_error<.001,(filename,part['name'],relative_error,shift,bound_error)
            round_trip_parts.append(dict(name=part['name'],relative_volume_error=relative_error,center_shift_mm=shift,bounds_error_mm=bound_error))
        # Boolean/conical surfaces have integration noise at STEP round-trip. Require
        # micron-level location agreement as well as bounded absolute/relative volume.
        assert error<1.0 and error/reference_volume<1e-5,(filename,error)
        report['step_round_trip'][filename]=dict(valid=True,solids=len(shape.Solids),volume_error_mm3=error,relative_volume_error=error/reference_volume,
            parts=round_trip_parts,tolerance='All solids valid; whole volume <1 mm3 AND relative <1e-5; each solid relative <1e-5, centroid and bounds each <0.001 mm')
    for owner in ['base','yaw','upper','fore','roll','pitch','tool']:
        chosen=[v for v in parts if v['owner']==owner and v['role']!='reserve'];boxes=[]
        for v in chosen:
            b=v['shape'].BoundBox;boxes.append(arm.Shape_Box(b.XLength,b.YLength,b.ZLength,b.XMin,b.YMin,b.ZMin))
        path=output/'envelope'/('arm_0_'+owner+'_envelope.step')
        arm.Arm0_ExportParts([dict(name='arm_0_'+owner,shape=Part.makeCompound(boxes),role='envelope')],path)
        report['envelopes'].append(dict(file=path.name,rigid_frame=owner,faces=6*len(boxes),semantics='Conservative component AABBs in local rigid frame, may produce false positives'))
    for name,q in cfg['poses'].items():
        frames,_=arm.Arm0_GetWorldParts(p,q,parts)
        report['bridge'][name]={k:dict(translation_mm=list(frames[k].Base),quaternion_xyzw=list(frames[k].Rotation.Q)) for k in ['base','yaw','upper','fore','roll','pitch','tool']}
    (root/'analysis/v3/export_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(print_candidates=len(report['print_fit']),step={k:{n:v[n] for n in ['valid','solids','volume_error_mm3']} for k,v in report['step_round_trip'].items()}),indent=2),flush=True)


if __name__=='__main__': Arm0_ExportDeliverables()
