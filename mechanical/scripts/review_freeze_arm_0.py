"""Compare frozen dimensions, poses, FK and non-hardware rigid ownership with the accepted baseline."""
from pathlib import Path
import json,csv,subprocess,hashlib


def Freeze_RunAudit():
    root=Path(__file__).resolve().parents[2];cfg=json.loads((root/'mechanical/arm_0_parameters.json').read_text(encoding='utf-8'));base=cfg['freeze_review_baseline_commit']
    def Git_GetFile(name):return subprocess.check_output(['git','show',base+':'+name],cwd=root)
    old=json.loads(Git_GetFile('mechanical/arm_0_parameters.json').decode('utf-8-sig'));previous=json.loads(Git_GetFile('analysis/v3/validation.json').decode('utf-8-sig'))
    old_parts={(v['name'],v['owner'],v['role']) for v in previous['valid_solids'] if v['role']!='reserve'}
    rows=list(csv.DictReader((root/'mechanical/docs/assembly_manifest.csv').read_text(encoding='utf-8-sig').splitlines()))
    current_parts={(v['part_name'],v['rigid_link'],v['role']) for v in rows if v['role']!='hardware_placeholder'}
    keys=['BaseHeight','UpperArm','Forearm','Wrist','Flange','Tool','FoldLane','UpperLane']
    result=dict(baseline_commit=base,dimensions_unchanged=all(cfg['dimensions'][k]==old['dimensions'][k] for k in keys),poses_unchanged=cfg['poses']==old['poses'],core_part_ownership_unchanged=old_parts==current_parts,core_part_count=len(current_parts),fk_source_unchanged=(root/'mechanical/scripts/arm_model.py').read_bytes().replace(b'\r\n',b'\n')==Git_GetFile('mechanical/scripts/arm_model.py').replace(b'\r\n',b'\n'),scope='Local holes, bosses, access channels and fasteners modified; no main topology or pose redesign')
    assert all(result[k] for k in ['dimensions_unchanged','poses_unchanged','core_part_ownership_unchanged','fk_source_unchanged']),result
    (root/'analysis/v4/freeze_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':Freeze_RunAudit()
