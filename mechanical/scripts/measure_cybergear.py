"""Find boundary loops on STL mounting planes; dimensional evidence, not thread metrology."""
from pathlib import Path
from collections import Counter,defaultdict
import json
import numpy as np
import FreeCAD
import Mesh


def Mesh_GetPlaneLoops(mesh, axial_y):
    points,triangles=mesh.Topology
    pts=np.array([list(x) for x in points])
    edges=Counter()
    for tri in triangles:
        if all(abs(pts[i,1]-axial_y)<0.002 for i in tri):
            for a,b in zip(tri,tri[1:]+tri[:1]):
                edges[tuple(sorted((a,b)))]+=1
    adjacency=defaultdict(list)
    for (a,b),n in edges.items():
        if n==1: adjacency[a].append(b); adjacency[b].append(a)
    seen=set(); loops=[]
    for start in adjacency:
        if start in seen: continue
        stack=[start]; group=[]
        while stack:
            a=stack.pop()
            if a in seen: continue
            seen.add(a); group.append(a); stack.extend(adjacency[a])
        v=pts[group][:,[0,2]]
        mat=np.column_stack((2*v[:,0],2*v[:,1],np.ones(len(v))))
        fit=np.linalg.lstsq(mat,(v*v).sum(1),rcond=None)[0]
        center=fit[:2]; radius=np.sqrt(max(0,fit[2]+center@center))
        error=float(np.max(np.abs(np.linalg.norm(v-center,axis=1)-radius)))
        loops.append({"center_xz":center.tolist(),"radius":float(radius),"fit_error_mm":error,"vertices":len(v)})
    return loops


if __name__=="__main__":
    root=Path(__file__).resolve().parents[2]
    directory=root/"reference/cybergear/upstream/Cybergear model(SOLIDWORKS 2022 & STL)"
    result={}
    for file,planes in [("Cybergear - motor-1.STL",[3.14544094,28.14544094]),("Cybergear - rotor-1.STL",[0.14544068])]:
        mesh=Mesh.Mesh(str(directory/file))
        result[file]={str(y):Mesh_GetPlaneLoops(mesh,y) for y in planes}
    (root/"analysis/stage2/cybergear_plane_loops.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    for file,planes in result.items():
        print(file)
        for plane,loops in planes.items():
            print(plane,[v for v in loops if v['fit_error_mm']<.01])
