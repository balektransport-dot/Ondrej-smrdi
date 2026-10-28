# Stylizovane low poly prevodovky k motorom R4, R6 a V8 pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori LEN prevodovky (motory nechá tak, nic na nich nemeni):
#   R4: 5-stupnova manualna, R6: 6-stupnova manualna, V8: automaticka - ciste diely bez paky.
# Ak su v scene motory (Motor_R4, Motor_R6, Motor_V8), prevodovka sa pripoji na prirubu svojho motora.
# Ak nie su, prevodovky sa postavia samotne na tie iste miesta.
# Vystupny hriadel je samostatny objekt a pri prehravani animacie (medzernik) sa toci.
# Do priecinka Prevodovky v domovskom priecinku ulozi FBX prevodoviek a vystupnych hriadelov (pre Unreal).
# Skript sa da spustit znova: stare prevodovky sa nahradia novymi.

import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

COLLECTION = "Prevodovky"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Prevodovky")
SPIN_SPEED = 0.25   # otacanie hriadela v radianoch za snimok animacie (rovnako ako kluka motora)

# Material sloty (kazdy motor ma vlastne farby)
BLOCK, HEAD, COVER, INTAKE, DARK, RUBBER, CHROME, EXHAUST, FILTER, PULLEY, TEXT, YEL, GEAR = range(13)
SLOT_NAMES = ["Blok", "Hlava", "Kryt", "Sanie", "Tmava", "Guma", "Chrom", "Vyfuk", "Filter", "Kladka", "Napis", "Zlta",
              "Prevodovka"]
ALU = ((0.50, 0.51, 0.53, 1.0), 0.6, 0.40)

# Spolocne materialy: (farba, kovovost, drsnost)
SHARED = {
    DARK: ((0.03, 0.03, 0.03, 1.0), 0.0, 0.55),
    RUBBER: ((0.015, 0.015, 0.015, 1.0), 0.0, 0.90),
    CHROME: ((0.85, 0.85, 0.85, 1.0), 1.0, 0.15),
    EXHAUST: ((0.18, 0.08, 0.04, 1.0), 0.5, 0.70),
    PULLEY: ((0.35, 0.36, 0.38, 1.0), 0.8, 0.35),
    YEL: ((0.85, 0.60, 0.02, 1.0), 0.0, 0.40),
    GEAR: ALU,
}

# Kladky: (y, z, polomer) na prednej strane motora
ENGINES = [
    dict(key="R4", label="R4", layout="inline", cylinders=4, pitch=0.09, place_y=1.5, crank_z=0.20,
         colors={BLOCK: ALU, HEAD: ALU, COVER: ((0.02, 0.10, 0.40, 1.0), 0.2, 0.35),
                 INTAKE: ((0.03, 0.03, 0.03, 1.0), 0.0, 0.50), FILTER: ((0.02, 0.10, 0.40, 1.0), 0.0, 0.40),
                 TEXT: ((0.90, 0.90, 0.90, 1.0), 0.0, 0.30)},
         pulleys=dict(Klukova=(0.0, 0.20, 0.070), Pumpa=(0.0, 0.40, 0.050),
                      Alternator=(-0.15, 0.48, 0.035), Napinac=(0.09, 0.30, 0.028)),
         fan=None,
         gearbox=dict(kind="manual", gears=5, bell=0.20, case=(0.28, 0.22, 0.22), tail=0.22)),
    dict(key="R6", label="R6", layout="inline", cylinders=6, pitch=0.10, place_y=0.0, crank_z=0.21,
         colors={BLOCK: ((0.10, 0.10, 0.11, 1.0), 0.3, 0.50), HEAD: ALU, COVER: ((0.40, 0.01, 0.01, 1.0), 0.2, 0.35),
                 INTAKE: ALU, FILTER: ((0.80, 0.25, 0.01, 1.0), 0.0, 0.40),
                 TEXT: ((0.90, 0.90, 0.90, 1.0), 0.0, 0.30)},
         pulleys=dict(Klukova=(0.0, 0.21, 0.080), Pumpa=(0.0, 0.42, 0.058), Alternator=(-0.16, 0.50, 0.038),
                      Posilnovac=(0.16, 0.50, 0.045), Napinac=(0.10, 0.31, 0.030)),
         fan=(6, 0.20),
         gearbox=dict(kind="manual", gears=6, bell=0.22, case=(0.36, 0.24, 0.25), tail=0.32)),
    dict(key="V8", label="V8", layout="v", cylinders=8, pitch=0.11, place_y=-1.7, crank_z=0.22,
         colors={BLOCK: ((0.75, 0.18, 0.01, 1.0), 0.0, 0.45), HEAD: ((0.75, 0.18, 0.01, 1.0), 0.0, 0.45),
                 COVER: ((0.85, 0.85, 0.85, 1.0), 1.0, 0.15), INTAKE: ALU,
                 FILTER: ((0.90, 0.90, 0.88, 1.0), 0.0, 0.40), TEXT: ((0.60, 0.01, 0.01, 1.0), 0.0, 0.30)},
         pulleys=dict(Klukova=(0.0, 0.22, 0.090), Pumpa=(0.0, 0.46, 0.065), Alternator=(-0.21, 0.55, 0.042),
                      Posilnovac=(0.21, 0.55, 0.050), Napinac=(0.11, 0.34, 0.033)),
         fan=(7, 0.22),
         gearbox=dict(kind="auto", bell=0.26, case=(0.34, 0.30, 0.28), tail=0.30)),
]
SIDES_LR = (-1.0, 1.0)


# ---------------------------------------------------------------------------
# Skladanie z tvarov so zrazenymi hranami
# ---------------------------------------------------------------------------

def set_material(faces, index):
    for f in faces:
        f.material_index = index


def faces_of(verts):
    return {f for v in verts for f in v.link_faces}


def bevel(bm, edges, offset, mat):
    # zrazene hrany; nove plochy dostanu farbu dielu
    if offset > 0.0 and edges:
        res = bmesh.ops.bevel(bm, geom=list(edges), offset=offset, segments=1, profile=0.5,
                              affect="EDGES", clamp_overlap=True)
        set_material(res["faces"], mat)


def finish_shape(bm, faces, mat, bev):
    faces = list(faces)
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    set_material(faces, mat)
    bevel(bm, {e for f in faces for e in f.edges}, bev, mat)


def place(location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
    # posun + otocenie (stupne, poradie XYZ)
    rot = Euler([math.radians(a) for a in rotation], "XYZ").to_matrix().to_4x4()
    return Matrix.Translation(Vector(location)) @ rot


def add_box(bm, size, location, mat, bev=0.0, rotation=(0.0, 0.0, 0.0), frame=None):
    matrix = (frame or Matrix()) @ place(location, rotation) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    verts = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)["verts"]
    finish_shape(bm, faces_of(verts), mat, min(bev, min(size) * 0.45))


def add_cylinder(bm, radius, depth, matrix, mat, segments=8, bev=0.0):
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=radius, radius2=radius, depth=depth, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    caps = [f for f in faces if len(f.verts) == segments]
    bevel(bm, {e for f in caps for e in f.edges}, min(bev, radius * 0.4, depth * 0.45), mat)


def along_x(location):
    return place(location, (0.0, 90.0, 0.0))


def along_y(location):
    return place(location, (90.0, 0.0, 0.0))


def along_z(location):
    return place(location)


def add_extruded(bm, points, a0, a1, plane, mat, bev=0.0):
    # mnohouholnik (2D body) vytiahnuty do hrubky: plane "XZ" -> hrubka v Y, "XY" -> hrubka v Z
    def vert(p, a):
        return bm.verts.new((p[0], a, p[1]) if plane == "XZ" else (p[0], p[1], a))

    v0 = [vert(p, a0) for p in points]
    v1 = [vert(p, a1) for p in points]
    faces = [bm.faces.new(v0), bm.faces.new(v1[::-1])]
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((v0[i], v0[j], v1[j], v1[i])))
    finish_shape(bm, faces, mat, bev)


def add_band(bm, outer, inner, y0, y1, mat):
    # uzavrety pas (napr. gumovy pas): vonkajsi a vnutorny obrys v rovine XZ
    o0 = [bm.verts.new((p[0], y0, p[1])) for p in outer]
    o1 = [bm.verts.new((p[0], y1, p[1])) for p in outer]
    i0 = [bm.verts.new((p[0], y0, p[1])) for p in inner]
    i1 = [bm.verts.new((p[0], y1, p[1])) for p in inner]
    faces = []
    n = len(outer)
    for a in range(n):
        b = (a + 1) % n
        faces.append(bm.faces.new((o0[a], o0[b], o1[b], o1[a])))
        faces.append(bm.faces.new((i0[b], i0[a], i1[a], i1[b])))
        faces.append(bm.faces.new((o0[b], o0[a], i0[a], i0[b])))
        faces.append(bm.faces.new((o1[a], o1[b], i1[b], i1[a])))
    finish_shape(bm, faces, mat, 0.0)


def add_prism(bm, bottom, top, mat, bev=0.0):
    b = [bm.verts.new(p) for p in bottom]
    t = [bm.verts.new(p) for p in top]
    faces = [bm.faces.new(b[::-1]), bm.faces.new(t)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(bm.faces.new((b[i], b[j], t[j], t[i])))
    finish_shape(bm, faces, mat, bev)


def stadium(x_front, x_back, radius, z_center, steps=5):
    # obrys "stadionu" (dve polkruznice + rovne useky) v rovine XZ
    pts = []
    for k in range(steps + 1):
        a = math.radians(-90.0 + 180.0 * k / steps)
        pts.append((x_front + radius * math.cos(a), z_center + radius * math.sin(a)))
    for k in range(steps + 1):
        a = math.radians(90.0 + 180.0 * k / steps)
        pts.append((x_back + radius * math.cos(a), z_center + radius * math.sin(a)))
    return pts


def beam_outline(path, halfs, cap=0.6):
    # obrys nosnika okolo lomenej ciary (2D body XZ): kazdy bod ma vlastnu polovicnu hrubku
    def norm(v):
        length = math.hypot(v[0], v[1]) or 1.0
        return (v[0] / length, v[1] / length)

    dirs = [norm((b[0] - a[0], b[1] - a[1])) for a, b in zip(path, path[1:])]
    upper, lower = [], []
    for i, p in enumerate(path):
        d_prev = dirs[max(i - 1, 0)]
        d_next = dirs[min(i, len(dirs) - 1)]
        n = norm((-(d_prev[1] + d_next[1]), d_prev[0] + d_next[0]))
        cos_half = max(0.5, n[0] * -d_next[1] + n[1] * d_next[0])
        h = halfs[i] / cos_half
        upper.append((p[0] + n[0] * h, p[1] + n[1] * h))
        lower.append((p[0] - n[0] * h, p[1] - n[1] * h))
    start, end = path[0], path[-1]
    tip = (end[0] + dirs[-1][0] * halfs[-1] * cap, end[1] + dirs[-1][1] * halfs[-1] * cap)
    tail = (start[0] - dirs[0][0] * halfs[0] * cap, start[1] - dirs[0][1] * halfs[0] * cap)
    return lower + [tip] + upper[::-1] + [tail]


def finish_mesh(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        axis = max(range(3), key=lambda i: abs(f.normal[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = ((co.y, co.z), (co.x, co.z), (co.x, co.y))[axis]
            loop[uv].uv = (u, v)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False  # ostre plochy = low poly vzhlad
    return mesh


def add_rod(bm, p0, p1, radius, mat, segments=6):
    # tenky valec medzi dvoma bodmi (hadice)
    a, b = Vector(p0), Vector(p1)
    direction = b - a
    rot = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    add_cylinder(bm, radius, direction.length, Matrix.Translation((a + b) * 0.5) @ rot, mat, segments=segments)


# ---------------------------------------------------------------------------
# Napis, remen, kladky
# ---------------------------------------------------------------------------

# natocenie napisu: na boku citatelne z +Y, navrchu citatelne spredu (+X)
TEXT_SIDE_Y = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))).to_4x4()
TEXT_TOP = Matrix(((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))).to_4x4()


def add_text(bm, text, size, matrix, mat, depth=0.002):
    # napis z pisma Blendera premeneny na plochy (lezi v rovine XY, cita sa po +X)
    curve = bpy.data.curves.new("tmp_napis", "FONT")
    curve.body = text
    curve.size = size
    curve.extrude = depth
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new("tmp_napis", curve)
    bpy.context.scene.collection.objects.link(obj)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
    verts = [bm.verts.new(matrix @ v.co) for v in mesh.vertices]
    faces = []
    for poly in mesh.polygons:
        try:
            faces.append(bm.faces.new([verts[i] for i in poly.vertices]))
        except ValueError:
            pass
    set_material(faces, mat)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.curves.remove(curve)
    bpy.data.meshes.remove(mesh)




# ---------------------------------------------------------------------------
# Prevodovka: pivot na prirube motora, ide dozadu (-X), os hriadela je Z = 0
# ---------------------------------------------------------------------------

def add_cone(bm, r_back, r_front, depth, matrix, mat, segments=12, bev=0.0):
    # kuzel: r_back na zapornom konci lokalnej osi Z, r_front na kladnom
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=r_back, radius2=r_front, depth=depth, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    caps = [f for f in faces if len(f.verts) == segments]
    bevel(bm, {e for f in caps for e in f.edges}, min(bev, min(r_back, r_front) * 0.4, depth * 0.45), mat)


def build_gearbox(spec, info):
    g = spec["gearbox"]
    bm = bmesh.new()
    r = info["flange_r"]
    bell = g["bell"]
    case_l, case_w, case_h = g["case"]
    case_z = -0.03
    x0, x1 = -bell, -bell - case_l          # predok a zadok skrine
    x_tail = x1 - g["tail"]
    cx = (x0 + x1) * 0.5
    auto = g["kind"] == "auto"

    # priruba so skrutkami a zvon spojky / menica
    add_cylinder(bm, r + 0.005, 0.02, along_x((-0.01, 0.0, 0.0)), GEAR, segments=12, bev=0.004)
    for k in range(8):
        a = 2.0 * math.pi * (k + 0.5) / 8
        add_cylinder(bm, 0.012, 0.03, along_x((-0.01, (r - 0.015) * math.cos(a), (r - 0.015) * math.sin(a))),
                     CHROME, segments=6)
    add_cone(bm, r * 0.62, r, bell - 0.02, along_x((-0.02 - (bell - 0.02) * 0.5, 0.0, 0.0)), GEAR, bev=0.01)

    # skrina s rebrami pri koncoch, zatky
    add_box(bm, (case_l, case_w, case_h), (cx, 0.0, case_z), GEAR, bev=0.05 if auto else 0.03)
    for s in SIDES_LR:
        for x in (x0 - 0.03, x0 - 0.06, x1 + 0.06, x1 + 0.03):
            add_box(bm, (0.014, 0.012, case_h * 0.75), (x, s * (case_w * 0.5 + 0.004), case_z), GEAR)
    add_cylinder(bm, 0.015, 0.02, along_y((cx + 0.05, -(case_w * 0.5 + 0.005), case_z - case_h * 0.3)), CHROME, segments=6)
    add_cylinder(bm, 0.015, 0.02, along_y((cx - 0.05, -(case_w * 0.5 + 0.005), case_z + case_h * 0.1)), CHROME, segments=6)

    # predlzenie k vystupu a gumovy uchyt
    add_cone(bm, 0.05, 0.085, g["tail"], along_x(((x1 + x_tail) * 0.5, 0.0, 0.0)), GEAR, segments=10, bev=0.008)
    add_box(bm, (0.08, 0.16, 0.05), ((x1 + x_tail) * 0.5, 0.0, -0.095), RUBBER, bev=0.01)
    add_box(bm, (0.10, 0.22, 0.015), ((x1 + x_tail) * 0.5, 0.0, -0.125), DARK)

    if not auto:
        # manual: rovne veko navrchu so skrutkami (bez paky - diel do skladacky auta)
        top = case_z + case_h * 0.5
        lid_l, lid_w = case_l * 0.6, case_w * 0.6
        add_box(bm, (lid_l, lid_w, 0.02), (cx, 0.0, top + 0.01), GEAR, bev=0.004)
        for sx in SIDES_LR:
            for sy in SIDES_LR:
                add_cylinder(bm, 0.008, 0.012, along_z((cx + sx * (lid_l * 0.5 - 0.02), sy * (lid_w * 0.5 - 0.02), top + 0.022)),
                             CHROME, segments=6)
        label = "%d ST" % g["gears"]
    else:
        # automat: olejova vana so skrutkami, rurky chladica oleja, modulator
        bottom = case_z - case_h * 0.5
        pan_l = case_l * 0.85
        add_box(bm, (pan_l, case_w * 0.9, 0.06), (cx, 0.0, bottom - 0.025), DARK, bev=0.012)
        for k in range(5):
            x = cx - pan_l * 0.5 + 0.03 + k * (pan_l - 0.06) / 4
            for s in SIDES_LR:
                add_cylinder(bm, 0.007, 0.012, along_z((x, s * (case_w * 0.45 + 0.004), bottom - 0.002)), CHROME, segments=6)
        for dz in (0.0, 0.04):
            add_rod(bm, (x0 - 0.04, case_w * 0.5 + 0.01, case_z - 0.04 + dz), (-0.03, r * 0.8, -0.06 + dz), 0.008, CHROME)
        add_cylinder(bm, 0.025, 0.06, along_y((x1 + 0.04, case_w * 0.5 + 0.03, case_z - 0.05)), CHROME, segments=8)
        label = "AUT"

    add_text(bm, label, 0.055, Matrix.Translation((cx, case_w * 0.5 + 0.0015, case_z)) @ TEXT_SIDE_Y, DARK)
    return finish_mesh(bm, "SM_Motor_%s_Prevodovka" % spec["key"]), x_tail - 0.012


def build_output(name):
    # vystupna priruba s krizovym klbom, os X, pivot v strede
    bm = bmesh.new()
    add_cylinder(bm, 0.05, 0.02, along_x((0.0, 0.0, 0.0)), PULLEY, segments=10, bev=0.004)
    for k in range(4):
        a = 2.0 * math.pi * (k + 0.5) / 4
        add_cylinder(bm, 0.008, 0.03, along_x((-0.005, 0.032 * math.cos(a), 0.032 * math.sin(a))), CHROME, segments=6)
    for s in SIDES_LR:
        add_box(bm, (0.07, 0.016, 0.045), (-0.045, s * 0.032, 0.0), PULLEY, bev=0.004)
    add_cylinder(bm, 0.012, 0.09, along_y((-0.065, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.012, 0.06, along_z((-0.065, 0.0, 0.0)), DARK, segments=8)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Scena: len prevodovky, napojene na motory (ak su v scene)
# ---------------------------------------------------------------------------

def engine_info(spec):
    # rozmery zadnej priruby motora (rovnake ako v skripte motorov)
    if spec["layout"] == "inline":
        length = spec["cylinders"] * spec["pitch"] + 0.10
        return dict(back=-length * 0.5, flange_r=0.17 + 0.01 * spec["cylinders"] / 2, flange_z=spec["crank_z"] + 0.03)
    length = 4 * spec["pitch"] + 0.12
    return dict(back=-length * 0.5, flange_r=0.24, flange_z=spec["crank_z"] + 0.04)


def get_material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat  # material uz existuje (napr. z motorov) - pouzi ho
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    if mat.node_tree is None:
        try:
            mat.use_nodes = True  # starsie verzie Blendera
        except Exception:
            pass
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def engine_materials(spec):
    mats = []
    for slot, slot_name in enumerate(SLOT_NAMES):
        color, metallic, roughness = spec["colors"].get(slot) or SHARED.get(slot) or ALU
        mats.append(get_material("%s_%s" % (spec["key"], slot_name), color, metallic, roughness))
    return mats


def add_spin(obj, ratio):
    fcurve = obj.driver_add("rotation_euler", 0)
    fcurve.driver.type = "SCRIPTED"
    fcurve.driver.expression = "frame * %.4f" % (-SPIN_SPEED * ratio)


def clear_collection(coll):
    # zmaz prevodovky z minula - aj tie, co vytvoril skript motorov (napr. s pakou)
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for spec in ENGINES:
        for name in ("%s_Vystup" % spec["key"], "%s_Prevodovka" % spec["key"]):
            obj = bpy.data.objects.get(name)
            if obj:
                bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if ("_Prevodovka" in mesh.name or "_Vystup" in mesh.name) and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def export_mesh(coll, mesh):
    temp = bpy.data.objects.new(mesh.name, mesh)
    coll.objects.link(temp)
    select_only(temp)
    path = os.path.join(EXPORT_DIR, mesh.name + ".fbx")
    try:
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                                 apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE")
    except Exception as error:
        print("FBX sa nepodarilo ulozit:", path, error)
    bpy.data.objects.remove(temp, do_unlink=True)


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)

    meshes = []
    for spec in ENGINES:
        info = engine_info(spec)
        mats = engine_materials(spec)
        gb_mesh, out_x = build_gearbox(spec, info)
        out_mesh = build_output("SM_Motor_%s_Vystup" % spec["key"])
        for mesh in (gb_mesh, out_mesh):
            for mat in mats:
                mesh.materials.append(mat)
            meshes.append(mesh)

        gearbox = bpy.data.objects.new("%s_Prevodovka" % spec["key"], gb_mesh)
        coll.objects.link(gearbox)
        flange = (info["back"] - 0.02, 0.0, info["flange_z"])
        engine = bpy.data.objects.get("Motor_" + spec["key"])
        if engine:
            gearbox.parent = engine
            gearbox.location = flange
            where = "na motore Motor_%s" % spec["key"]
        else:
            gearbox.location = (flange[0], spec["place_y"], flange[2])
            where = "samostatne (motor v scene nie je)"
        output = bpy.data.objects.new("%s_Vystup" % spec["key"], out_mesh)
        coll.objects.link(output)
        output.parent = gearbox
        output.location = (out_x, 0.0, 0.0)
        add_spin(output, 1.0)
        print("%s: prevodovka %s" % (gearbox.name, where))

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for mesh in meshes:
            export_mesh(coll, mesh)
        print("Ulozene do:", EXPORT_DIR)

    if scene.frame_end < 250:
        scene.frame_end = 250
    print("Hotovo: %d dielov. Medzernik = vystupne hriadele sa tocia." % len(meshes))


main()
