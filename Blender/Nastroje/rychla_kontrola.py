# Rychla kontrola modelu (Blender 3.0+ s Cycles): sest pohladov (3/4 spredu, 3/4 zozadu, bok, predok, zadok, zhora) do jedneho obrazka (cca 20 s)
# + volitelne AUTOMATICKE KONTROLY dielov: levitujuce diely (ziadny iny diel do 4 cm) a prieniky dielov (pocet trojuholnikov v prieniku, velkost prieniku).
#
# Pouzitie (premenne prostredia; python je Blender, napr. `blender -b -P rychla_kontrola.py` alebo bpy v python):
#   SCRIPT=zeriav_low_poly.py QV_ROOT=Zeriav_40t QV_OUT=/cesta/kontrola.png [QV_FRAME=650] [QV_CHECK=1] [QV_IGN=ignoruj.txt] [QV_TOP=40] [QV_W=560 QV_H=420] [QV_SAMPLES=10]
#     SCRIPT   skript s modelom (cesta alebo nazov vedla tohto suboru; EXPORT_FBX sa vypne)
#     QV_ROOT  predpona objektov stroja (hlavny objekt, napr. Zeriav_40t)
#     QV_FRAME snimka animacie (poloha: napr. 330 = podpery, 650 = praca s hakom)
#     QV_CHECK=1 vypise levitujuce diely a prieniky; QV_IGN = subor s riadkami "cast_nazvu_A|cast_nazvu_B" (zamerne prieniky, ktore sa nemaju vypisovat)
#     QV_CAMS  vlastne pohlady namiesto sesticky: "popis:x,y,z>cielx,ciely,cielz>ohnisko;..." (svetove suradnice, max 6)
#   Hak, lano, naklad na pase, vnorene teleskopy a piest podpery su v zozname vynimiek pre levitovanie.
import bpy, os, math, sys, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D = os.path.dirname(os.path.abspath(__file__)) + os.sep
name = os.environ["SCRIPT"]
root_name = os.environ["QV_ROOT"]
frame = int(os.environ.get("QV_FRAME", "1"))
t0 = time.time()
path = name if os.path.exists(name) else (D + name if os.path.exists(D + name) else os.path.join(D, "..", name))
src = open(path).read().replace("EXPORT_FBX = True", "EXPORT_FBX = False")
g = {"__name__": "__main__"}
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, name, "exec"), g)
sc = bpy.context.scene
sc.frame_set(frame)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
O = bpy.data.objects
for o in list(O):
    if o.name.startswith(("Diel_", "Menovka_", "Cube")):
        O.remove(o, do_unlink=True)
mine = [o for o in O if o.name == root_name or o.name.startswith(root_name + "_")]
meshes = [o for o in mine if o.type == "MESH"]


def world_tris(o):
    me = o.data
    me.calc_loop_triangles()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    return vs, [tuple(t.vertices) for t in me.loop_triangles]


def bbox_of(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))), Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))


if os.environ.get("QV_CHECK"):
    tol = float(os.environ.get("QV_TOL", "0.04"))
    info = {}
    for o in meshes:
        vs, tr = world_tris(o)
        if not tr:
            continue
        info[o.name] = (o, BVHTree.FromPolygons(vs, tr, all_triangles=True), vs, bbox_of(o))
    names = list(info)
    skip_float = ("_hak", "_lano", "_naklad", "_lista", "_valec_zdvihu", "_podpera_tyc", "_rameno_")
    print("== LEVITUJUCE DIELY (vzdialenost k najblizsiemu inemu dielu > %.2f m) ==" % tol)
    for n in names:
        if n.endswith(skip_float) or any(k in n for k in skip_float):
            continue
        o, tree, vs, (b0, b1) = info[n]
        best = 1e9
        for m in names:
            if m == n:
                continue
            o2, tree2, vs2, (c0, c1) = info[m]
            if any(b0[i] - tol > c1[i] or b1[i] + tol < c0[i] for i in range(3)):
                continue
            step = max(1, len(vs) // 150)
            for p in vs[::step]:
                loc = tree2.find_nearest(p)
                if loc[0] is not None and loc[3] < best:
                    best = loc[3]
            if best < 0.002:
                break
        if best > tol:
            print("  %-48s %.3f m" % (n, best if best < 1e8 else -1))
    print("== PRENIKY DIELOV (pocet trojuholnikov v prieniku, velkost prieniku) ==")
    rows = []
    for i, n in enumerate(names):
        o, tree, vs, (b0, b1) = info[n]
        for m in names[i + 1:]:
            o2, tree2, vs2, (c0, c1) = info[m]
            ov = [min(b1[k], c1[k]) - max(b0[k], c0[k]) for k in range(3)]
            if min(ov) <= 0.0:
                continue
            pairs = tree.overlap(tree2)
            if len(pairs) > 0:
                rows.append((ov[0] * ov[1] * ov[2], len(pairs), n, m, ov))
    rows.sort(reverse=True)
    ign = []
    if os.environ.get("QV_IGN") and os.path.exists(os.environ["QV_IGN"]):
        ign = [tuple(l.strip().split("|")) for l in open(os.environ["QV_IGN"]) if "|" in l]
    rows = [r for r in rows if not any((a_ in r[2] and b_ in r[3]) or (a_ in r[3] and b_ in r[2]) for a_, b_ in ign)]
    for vol, cnt, n, m, ov in rows[:int(os.environ.get("QV_TOP", "40"))]:
        print("  %-40s x %-40s tri %4d  %.2f x %.2f x %.2f" % (n[len(root_name) + 1:], m[len(root_name) + 1:], cnt, ov[0], ov[1], ov[2]))
    print("  (celkom dvojic s prienikom: %d)" % len(rows))

# pohlady
allp = [bbox_of(o) for o in meshes]
lo = Vector((min(b[0][i] for b in allp) for i in range(3)))
hi = Vector((max(b[1][i] for b in allp) for i in range(3)))
c = (lo + hi) * 0.5
ext = hi - lo
R = ext.length * 0.5
for o in O:
    if o not in mine and o.type in ("MESH", "EMPTY", "FONT", "CURVE"):
        o.hide_render = True
bpy.ops.mesh.primitive_plane_add(size=300, location=(c.x, c.y, 0.0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
b = fm.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (0.30, 0.30, 0.29, 1); b.inputs["Roughness"].default_value = 0.9
floor.data.materials.append(fm)
light = O["Light"]; light.data.type = "SUN"; light.data.energy = 3.0; light.data.angle = math.radians(3)
light.rotation_euler = (math.radians(50), math.radians(10), math.radians(-60))
bg = sc.world.node_tree.nodes.get("Background")
sky = sc.world.node_tree.nodes.new("ShaderNodeTexSky")
sc.world.node_tree.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.25
cam = O["Camera"]
sc.camera = cam
W, H = int(os.environ.get("QV_W", "480")), int(os.environ.get("QV_H", "360"))
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = int(os.environ.get("QV_SAMPLES", "10"))
try:
    sc.cycles.use_denoising = True
except Exception:
    pass
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
cam.data.clip_end = 1000.0
views = [("3/4 predok", (0.8, 0.8, 0.45), False), ("3/4 zadok", (-0.8, -0.8, 0.45), False), ("bok L", (0.0, 1.0, 0.0), True),
         ("predok", (1.0, 0.0, 0.0), True), ("zadok", (-1.0, 0.0, 0.0), True), ("zhora", (0.0, 0.0, 1.0), True)]
imgs = []
custom = os.environ.get("QV_CAMS")
if custom:
    views = []
    for item in custom.split(";"):
        lab, cams = item.split(":")
        cp, tp, lens = cams.split(">")
        views.append((lab, tuple(float(v) for v in cp.split(",")), tuple(float(v) for v in tp.split(",")), float(lens)))
for view in views:
    if custom:
        label, cp, tp, lens = view
        cam.data.type = "PERSP"; cam.data.lens = lens
        cam.location = Vector(cp)
        cam.rotation_euler = (Vector(tp) - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "/tmp/claude-0/qv_tmp.png"
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load("/tmp/claude-0/qv_tmp.png")
        imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4))
        bpy.data.images.remove(im)
        continue
    label, d, ortho = view
    d = Vector(d).normalized()
    if ortho:
        cam.data.type = "ORTHO"
        horiz = ext.x if abs(d.y) > 0.5 else ext.y
        vert = ext.z if abs(d.z) < 0.5 else (ext.x if True else ext.y)
        cam.data.ortho_scale = max(horiz * H / W if False else horiz, vert * W / H, 1.0) * 1.08
        cam.location = c + d * (R * 3.0)
    else:
        cam.data.type = "PERSP"; cam.data.lens = 35.0
        cam.location = c + d * (R * 2.15)
    up = "Y"
    rot = (c - cam.location).to_track_quat("-Z", "Y")
    cam.rotation_euler = rot.to_euler()
    sc.render.filepath = "/tmp/claude-0/qv_tmp.png"
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load("/tmp/claude-0/qv_tmp.png")
    arr = np.array(im.pixels[:], dtype=np.float32).reshape(H, W, 4)
    bpy.data.images.remove(im)
    imgs.append(arr)
while len(imgs) < 6:
    imgs.append(np.zeros_like(imgs[0]))
rows = [np.concatenate(imgs[0:3], axis=1), np.concatenate(imgs[3:6], axis=1)]
sheet = np.concatenate(rows[::-1], axis=0)       # pixely Blendera ide odspodu
out = bpy.data.images.new("sheet", 3 * W, 2 * H)
out.pixels = sheet.flatten().tolist()
out.filepath_raw = os.environ["QV_OUT"]
out.file_format = "PNG"
out.save()
print("QV hotovo: %s (%.1f s); poradie: %s" % (os.environ["QV_OUT"], time.time() - t0, ", ".join(v[0] for v in views)))
