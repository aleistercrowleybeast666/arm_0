"""Render actual CAD tessellation with matplotlib; no external reference artwork."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import arm_model as arm
from validate_layout import Task_SolveDownward


def Layout_RenderPreview():
    root = Path(__file__).resolve().parents[1]
    config = arm.Arm_LoadConfig(); p = config["dimensions"]
    poses = dict(config["poses"])
    poses.pop("EXTENDED")
    poses["CAKE_APPROACH"] = Task_SolveDownward(p,500,210)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})
    fig = plt.figure(figsize=(15,11),facecolor="#f4f6fa")
    colors = {"ground":"#485465","yaw":"#8d9cae","upper":"#2678aa","fore":"#2bb4a7",
              "roll":"#8296b0","pitch":"#b2bdce","tool":"#d95140"}
    for n,(name,q) in enumerate(poses.items(),1):
        ax = fig.add_subplot(2,2,n,projection="3d",computed_zorder=False)
        ax.set_facecolor("#f4f6fa")
        f, parts = arm.Arm_GetGeometry(p,q)
        for item in parts:
            verts,tri = item["shape"].tessellate(1.8)
            vertices = np.array([list(v) for v in verts])
            faces = vertices[np.array(tri)]
            color = "#edac35" if item["kind"] == "motor" else colors[item["owner"]]
            coll = Poly3DCollection(faces, facecolors=color, linewidths=0, alpha=1, shade=True,
                                    zsort="average")
            ax.add_collection3d(coll)
        for axis in arm.Arm_GetAxes(p,f):
            point = axis["origin_mm"]
            ax.scatter(*point,c="#cc3c40",s=12,zorder=5)
            ax.text(*point,axis["name"],fontsize=8,color="#8b2431",zorder=6)
        if name == "CAKE_APPROACH":
            t = np.linspace(0,2*np.pi,48)
            xx,yy=500+100*np.cos(t),70+100*np.sin(t)
            ax.plot_trisurf(np.r_[500,xx],np.r_[70,yy],np.full(49,200),color="#e4b4c5",alpha=.55)
            ax.plot(xx,yy,np.full(48,100),color="#bd7491",alpha=.7)
            ax.text2D(.52,.12,"Assumed cake / TCP +10 mm",transform=ax.transAxes,fontsize=8)
        ax.set_title(name+"\n"+" / ".join(f"{v:.0f}" for v in q)+" deg",loc="left",fontweight="bold",pad=0)
        ax.set_xlabel("X [mm]",labelpad=0); ax.set_ylabel("Y [mm]",labelpad=0); ax.set_zlabel("Z [mm]",labelpad=0)
        ax.view_init(elev=22,azim=-58)
        ax.set_xlim(-360,720); ax.set_ylim(-230,300); ax.set_zlim(0,850)
        ax.set_box_aspect((1080,530,850)); ax.tick_params(labelsize=7,pad=0)
        ax.grid(True,alpha=.2)
    fig.suptitle("ARM / PHASE 01    Motor-first folding layout",x=.055,ha="left",y=.975,fontsize=22,fontweight="bold",color="#25364a")
    fig.text(.055,.925,"180 / 320 / 290 / 60 / 35 / 90 mm     |     Yellow: six assumed motor envelopes, diameter 80 x 50 mm",fontsize=11,color="#4f637a")
    fig.text(.055,.035,"Original coarse geometry. Lane offset +70 mm. J3 stator stays on upper arm.\nSampled clearance only; bearings, motor dimensions, loads and cable travel remain unverified.",fontsize=10,color="#4f637a")
    fig.subplots_adjust(left=.02,right=.98,bottom=.085,top=.86,wspace=.02,hspace=.12)
    target = root/"exports"/"layout_preview.png"
    fig.savefig(target,dpi=140,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(target)


if __name__ == "__main__":
    Layout_RenderPreview()
