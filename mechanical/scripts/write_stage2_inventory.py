"""Write a reproducible file inventory after CAD, checks and GUI screenshots exist."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess


def Inventory_WriteStage2():
    root=Path(__file__).resolve().parents[2]
    sections={
        "FreeCAD 主文件":[root/"mechanical/freecad"/(name+".FCStd") for name in
            ["Robot_Master","CyberGear_Detail","CyberGear_Envelope","PAROL6_reference_assembly"]],
        "参数、脚本与宏":[root/"mechanical/master_parameters.json"]+[root/"mechanical/scripts"/name for name in
            ["import_parol6_urdf_to_freecad.py","measure_cybergear.py","cybergear_model.py","build_robot_master.py",
             "check_robot_master.py","export_robot_deliverables.py","write_stage2_inventory.py","build_stage2.ps1",
             "SetRobotPose.FCMacro","RebuildRobotMaster.FCMacro","ReviewStage2.FCMacro"]],
        "STEP":[root/"mechanical/exports"/name for name in
            ["Robot_Master_coarse.step","J1_base.step","J2_shoulder.step","J3_upper_elbow.step"]]
            +sorted((root/"mechanical/exports/envelope").glob("*.step")),
        "试装 STL":sorted((root/"mechanical/exports/print_fit").glob("*.stl")),
        "文档":[root/"mechanical/docs"/name for name in
            ["master_stage2_review.md","cybergear_interface.md","PAROL6_reference_review.md","Thor_reference_review.md",
             "reference_license_notes.md","assembly_concept.md","unresolved_issues.md"]],
        "原生 CAD 截图":[root/"mechanical/exports"/(name+".png") for name in
            ["Robot_HOME","Robot_STOW","Robot_SAFE_UNFOLD","Robot_CAKE_APPROACH","CyberGear_Detail",
             "CyberGear_Envelope","PAROL6_reference_assembly"]],
        "验证与来源读取记录":sorted(p for p in (root/"analysis/stage2").iterdir()
            if p.is_file() and p.name!="deliverable_manifest.json"),
        "更新的历史入口":[root/"mechanical/README.md",root/"reference/cybergear/README.md"]}
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),"files":[],"references":[]}
    text=["# 第二阶段文件清单","","本清单列出本轮新增交付文件和更新入口；不包含FreeCAD自动备份、Python缓存和第一阶段历史产物。",
          "依赖旧有自建运动学脚本 `mechanical/scripts/arm_model.py`，未修改该脚本。参考仓库内容保留在reference，不混入自己的Master。",
          "机器可读大小与SHA256记录见 [deliverable_manifest.json](../../analysis/stage2/deliverable_manifest.json)。",
          "本清单自身为 `mechanical/docs/stage2_files.md`；为避免循环哈希，清单和manifest本身不列入哈希表。",""]
    for section,paths in sections.items():
        text.extend(["## "+section,"","| 文件 | 字节 |","|---|---:|"])
        for path in paths:
            assert path.is_file(),str(path)
            relative=path.relative_to(root).as_posix()
            data=path.read_bytes()
            result["files"].append({"path":relative,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
            text.append(f"| [{relative}](../../{relative}) | {len(data)} |")
        text.append("")
    for name,relative in [("PAROL6","reference/PAROL6"),("Thor","reference/Thor"),("CyberGear","reference/cybergear/upstream")]:
        path=root/relative
        def Repository_Read(*args):
            return subprocess.check_output(["git","-c","safe.directory="+path.as_posix(),"-C",str(path),*args],text=True,encoding="utf-8").strip()
        result["references"].append({"name":name,"path":relative,"commit":Repository_Read("rev-parse","HEAD"),
            "remote":Repository_Read("remote","get-url","origin"),"status":Repository_Read("status","--porcelain")})
    original=root/"708小米电机SLDASM.SLDASM"
    result["user_original_sha256"]=hashlib.sha256(original.read_bytes()).hexdigest()
    assert result["user_original_sha256"]=="e1bf9c8fe0187b5db73f36c63d0125ffc5f59e8688d3b2b08b8d5f67b80ac2d5"
    (root/"mechanical/docs/stage2_files.md").write_text("\n".join(text),encoding="utf-8")
    (root/"analysis/stage2/deliverable_manifest.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"files":len(result["files"]),"references":result["references"],"original_unchanged":True},ensure_ascii=False,indent=2))


if __name__=="__main__": Inventory_WriteStage2()
