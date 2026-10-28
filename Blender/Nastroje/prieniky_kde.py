# Kde presne sa dva diela prenikaju (Blender 3.0+; doplnok k rychla_kontrola.py): vypise zhluky prenikajucich trojuholnikov so svetovymi suradnicami
# (podla mensieho z dvoch trojuholnikov, takze sedi aj pri velkych plochach).
#
# Pouzitie (premenne prostredia; python je Blender, napr. `blender -b -P prieniky_kde.py`):
#   SCRIPT=pickup_vozik_low_poly.py ROOT=Pickup_dvojkabina PAIRS="kabina|pneu_koleso_predne_L,pneu_koleso_zadne_L|podlaha" [FR=1]
#     SCRIPT  skript s modelom (cesta alebo nazov vedla tohto suboru)
#     ROOT    predpona objektov stroja
#     PAIRS   dvojice casti nazvu (bez predpony ROOT_), oddelene ciarkou
#     FR      snimka animacie
import bpy, os, io, contextlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = os.path.dirname(os.path.abspath(__file__)) + os.sep
name = os.environ.get("SCRIPT", "pickup_vozik_low_poly.py")
path = name if os.path.exists(name) else (D + name if os.path.exists(D + name) else os.path.join(D, "..", name))
src = open(path).read().replace("EXPORT_FBX = True", "EXPORT_FBX = False")
g = {"__name__": "__main__"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, name, "exec"), g)
bpy.context.scene.frame_set(int(os.environ.get("FR", "1")))
bpy.context.view_layer.update()
root = os.environ["ROOT"]
O = bpy.data.objects


def tri(o):
    me = o.data
    me.calc_loop_triangles()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    return vs, [tuple(t.vertices) for t in me.loop_triangles]


for pair in os.environ["PAIRS"].split(","):
    a, b = pair.split("|")
    oa, ob = O[root + "_" + a], O[root + "_" + b]
    va, ta = tri(oa)
    vb, tb = tri(ob)
    A = BVHTree.FromPolygons(va, ta, all_triangles=True)
    B = BVHTree.FromPolygons(vb, tb, all_triangles=True)
    pairs = A.overlap(B)
    print("== %s x %s : %d dvojic trojuholnikov" % (a, b, len(pairs)))
    pts = []
    for i, j in pairs:
        pa = sum((va[k] for k in ta[i]), Vector()) / 3.0
        pb = sum((vb[k] for k in tb[j]), Vector()) / 3.0
        aa = (va[ta[i][1]] - va[ta[i][0]]).cross(va[ta[i][2]] - va[ta[i][0]]).length
        ab = (vb[tb[j][1]] - vb[tb[j][0]]).cross(vb[tb[j][2]] - vb[tb[j][0]]).length
        pts.append(pa if aa < ab else pb)
    clusters = {}
    for p in pts:
        clusters.setdefault((round(p.x / 0.25), round(p.y / 0.25), round(p.z / 0.25)), []).append(p)
    for k, ps in sorted(clusters.items(), key=lambda kv: -len(kv[1]))[:6]:
        lo = [min(p[i] for p in ps) for i in range(3)]
        hi = [max(p[i] for p in ps) for i in range(3)]
        print("   %3d tri  x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % (len(ps), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
