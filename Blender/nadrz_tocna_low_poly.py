# Stylizovane low poly nadrze a posuvna tocna pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Nadrz_Tocna":
#   Nadrz_velka, Nadrz_mala - hlinikove nadrze s pasmi, drziakmi na ram (strana +Y), vieckom a plavakom
#   Tocna - posuvna tocna na kolajniciach so zubami, s mazacimi drazkami, zamkom a uvolnovacou tycou
# Pivot: v strede spodku dielu (nadrz: spodok nadrze, tocna: spodok kolajnic).
# Do priecinka Nadrz_Tocna v domovskom priecinku ulozi FBX a subor Nadrz_Tocna.txt s rozmermi.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Nadrz_Tocna"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Nadrz_Tocna")

# (nazov, farba, kovovost, drsnost)
MATERIALS = [
    ("NT_Hlinik", (0.58, 0.59, 0.61, 1.0), 0.85, 0.30),
    ("NT_Tmava", (0.035, 0.035, 0.04, 1.0), 0.2, 0.55),
    ("NT_Tocna", (0.05, 0.05, 0.055, 1.0), 0.3, 0.50),
    ("NT_Ocel", (0.45, 0.46, 0.48, 1.0), 0.7, 0.40),
    ("NT_Cervena", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35),
    ("NT_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15),
    ("NT_Guma", (0.015, 0.015, 0.015, 1.0), 0.0, 0.90),
]
ALU, DARK, PLATE, STEEL, RED, CHROME, RUBBER = range(7)
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
# Nadrz (pivot v strede spodku, strana k ramu = +Y)
# ---------------------------------------------------------------------------

def add_band_x(bm, outer, inner, x0, x1, mat):
    # uzavrety pas okolo osi X (obrys v rovine YZ), napr. pas okolo nadrze
    o0 = [bm.verts.new((x0, p[0], p[1])) for p in outer]
    o1 = [bm.verts.new((x1, p[0], p[1])) for p in outer]
    i0 = [bm.verts.new((x0, p[0], p[1])) for p in inner]
    i1 = [bm.verts.new((x1, p[0], p[1])) for p in inner]
    faces = []
    n = len(outer)
    for a in range(n):
        b = (a + 1) % n
        faces.append(bm.faces.new((o0[a], o0[b], o1[b], o1[a])))
        faces.append(bm.faces.new((i0[b], i0[a], i1[a], i1[b])))
        faces.append(bm.faces.new((o0[b], o0[a], i0[a], i0[b])))
        faces.append(bm.faces.new((o1[a], o1[b], i1[b], i1[a])))
    finish_shape(bm, faces, mat, 0.0)


def chamfer_outline(half_w, half_h, chamfer, zc):
    # osemuholnik = obdlznik so zrazenymi rohmi (rez nadrzou)
    w, h, c = half_w, half_h, chamfer
    pts = [(w, h - c), (w - c, h), (-(w - c), h), (-w, h - c), (-w, -(h - c)), (-(w - c), -h), (w - c, -h), (w, -(h - c))]
    return [(y, z + zc) for y, z in pts]


def build_tank(name, length, width, height):
    bm = bmesh.new()
    c = min(width, height) * 0.13      # zrazenie hran
    add_box(bm, (length, width, height), (0.0, 0.0, height * 0.5), ALU, bev=c)

    # dva pasy okolo nadrze, drziaky s doskou na ram (strana +Y)
    for x in (-length * 0.28, length * 0.28):
        outer = chamfer_outline(width * 0.5 + 0.01, height * 0.5 + 0.01, c, height * 0.5)
        inner = chamfer_outline(width * 0.5 - 0.002, height * 0.5 - 0.002, c, height * 0.5)
        add_band_x(bm, outer, inner, x - 0.03, x + 0.03, DARK)
        add_box(bm, (0.07, 0.10, height * 0.8), (x, width * 0.5 + 0.05, height * 0.5), DARK, bev=0.008)
        add_box(bm, (0.13, 0.012, height * 0.6), (x, width * 0.5 + 0.106, height * 0.5), DARK, bev=0.003)
        for dz in (-height * 0.2, height * 0.2):
            for dx in (-0.04, 0.04):
                add_cylinder(bm, 0.009, 0.012, along_y((x + dx, width * 0.5 + 0.114, height * 0.5 + dz)), CHROME, segments=6)
        add_cylinder(bm, 0.012, 0.03, along_z((x, -width * 0.5 + c * 0.5, -0.004)), CHROME, segments=6)

    # plniace hrdlo s cervenym vieckom (vonkajsia strana, vpredu)
    fx, fy = length * 0.32, -width * 0.25
    add_cylinder(bm, 0.045, 0.04, along_z((fx, fy, height + 0.015)), STEEL, segments=10, bev=0.004)
    add_cylinder(bm, 0.058, 0.03, along_z((fx, fy, height + 0.045)), RED, segments=8, bev=0.006)
    add_box(bm, (0.012, 0.075, 0.012), (fx, fy, height + 0.064), RED, bev=0.003)

    # plavak (merac paliva) s hadickami k ramu a vypustna zatka
    px = -length * 0.18
    add_cylinder(bm, 0.07, 0.012, along_z((px, 0.0, height + 0.004)), STEEL, segments=10)
    add_box(bm, (0.05, 0.04, 0.03), (px, 0.0, height + 0.024), DARK, bev=0.005)
    for dx in (-0.02, 0.02):
        add_rod(bm, (px + dx, 0.02, height + 0.025), (px + dx, width * 0.5 + 0.03, height + 0.03), 0.009, RUBBER)
        add_rod(bm, (px + dx, width * 0.5 + 0.03, height + 0.03), (px + dx, width * 0.5 + 0.12, height - 0.08), 0.009, RUBBER)
    add_cylinder(bm, 0.018, 0.02, along_z((0.0, 0.0, 0.0)), STEEL, segments=6)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Posuvna tocna (pivot v strede spodku kolajnic, zarez sa otvara dozadu = -X)
# ---------------------------------------------------------------------------

def plate_outline(r=0.46):
    # platna zhora: predok polkruh, vzadu rohy a V-zarez k zamku v strede
    pts = [(0.04, -0.04), (0.04, 0.04), (-0.10, 0.04), (-0.48, 0.16), (-0.48, 0.30), (-0.30, r), (0.0, r)]
    for k in range(1, 9):
        a = math.radians(90.0 - 180.0 * k / 9)
        pts.append((r * math.cos(a), r * math.sin(a)))
    pts += [(0.0, -r), (-0.30, -r), (-0.48, -0.30), (-0.48, -0.16), (-0.10, -0.04)]
    return pts


def arc_band(r_out, r_in, a0, a1, steps=14):
    outer = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
              r_out * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]
    inner = [(r_in * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
              r_in * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]
    return outer + inner[::-1]


def add_ring_loop(bm, center, radius, mat, rod_r=0.01, steps=10):
    # oko z kratkych tyciek (lezi vodorovne)
    pts = [(center[0] + radius * math.cos(2.0 * math.pi * k / steps),
            center[1] + radius * math.sin(2.0 * math.pi * k / steps), center[2]) for k in range(steps)]
    for k in range(steps):
        add_rod(bm, pts[k], pts[(k + 1) % steps], rod_r, mat, segments=6)


def build_fifth_wheel():
    bm = bmesh.new()
    rail_y, rail_len = 0.40, 1.20

    # kolajnice so zubami a dorazmi
    for s in SIDES_LR:
        add_box(bm, (rail_len, 0.10, 0.06), (0.0, s * rail_y, 0.03), DARK, bev=0.008)
        for k in range(17):
            x = -0.48 + k * 0.06
            add_box(bm, (0.03, 0.035, 0.012), (x, s * (rail_y - 0.025), 0.064), PLATE)
        for x in (-rail_len * 0.5 + 0.02, rail_len * 0.5 - 0.02):
            add_box(bm, (0.04, 0.12, 0.09), (x, s * rail_y, 0.045), DARK, bev=0.006)
        for x in (-0.45, 0.0, 0.45):
            add_cylinder(bm, 0.012, 0.012, along_z((x, s * (rail_y + 0.03), 0.062)), CHROME, segments=6)

    # vozik na kolajniciach a stojany s capmi
    add_box(bm, (0.55, 0.92, 0.035), (0.0, 0.0, 0.0775), PLATE, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.45, 0.14, 0.05), (0.0, s * rail_y, 0.085), PLATE, bev=0.008)
        add_box(bm, (0.30, 0.10, 0.08), (0.0, s * 0.33, 0.135), PLATE, bev=0.01)
        add_cylinder(bm, 0.03, 0.14, along_y((0.0, s * 0.33, 0.17)), STEEL, segments=10)
        for x in (-0.18, 0.18):
            add_cylinder(bm, 0.01, 0.012, along_z((x, s * 0.44, 0.1)), CHROME, segments=6)

    # platna so zrazenymi hranami a mazacimi drazkami v tvare U
    add_extruded(bm, plate_outline(), 0.17, 0.23, "XY", PLATE, bev=0.022)
    for r in (0.17, 0.25, 0.33):
        add_extruded(bm, arc_band(r + 0.018, r, -145.0, 145.0), 0.226, 0.236, "XY", DARK)

    # zamok na konci zarezu a uvolnovacia tyc s okom a cervenou rukovatou (lava strana)
    add_box(bm, (0.04, 0.08, 0.05), (0.02, 0.0, 0.195), STEEL, bev=0.006)
    add_box(bm, (0.10, 0.06, 0.05), (0.0, -0.36, 0.15), PLATE, bev=0.008)
    handle_end = (0.30, -0.66, 0.12)
    add_rod(bm, (0.0, -0.36, 0.15), handle_end, 0.012, STEEL, segments=8)
    loop_c = (handle_end[0] + 0.03, handle_end[1] - 0.05, handle_end[2])
    add_ring_loop(bm, loop_c, 0.055, STEEL)
    add_box(bm, (0.05, 0.03, 0.03), (loop_c[0] + 0.02, loop_c[1] - 0.05, loop_c[2]), RED, bev=0.006)
    return finish_mesh(bm, "SM_Tocna")


# ---------------------------------------------------------------------------
# Scena a export
# ---------------------------------------------------------------------------

def get_material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
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
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.name in ("SM_Nadrz_velka", "SM_Nadrz_mala", "SM_Tocna") and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    mats = [get_material(*m) for m in MATERIALS]

    parts = [
        ("Nadrz_velka", build_tank("SM_Nadrz_velka", 1.20, 0.62, 0.62), (0.0, 0.0, 0.0)),
        ("Nadrz_mala", build_tank("SM_Nadrz_mala", 0.80, 0.50, 0.50), (0.0, 1.2, 0.0)),
        ("Tocna", build_fifth_wheel(), (2.0, 0.5, 0.0)),
    ]
    lines = ["Nadrz a tocna - rozmery v metroch, pivot v strede spodku dielu.", ""]
    for name, mesh, location in parts:
        for mat in mats:
            mesh.materials.append(mat)
        obj = bpy.data.objects.new(name, mesh)
        coll.objects.link(obj)
        obj.location = location
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        lines.append("%-12s %.2f x %.2f x %.2f m" % (name, max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    lines += ["", "Nadrze: drziaky na ram su na strane +Y (dosky 0.11 m od boku nadrze).",
              "Tocna: platna (spojenie s kralovskym capom) je navrchu vo vyske 0.23 m nad spodkom kolajnic,",
              "       zarez sa otvara dozadu (-X), kolajnice su od seba 0.80 m (na nosniky ramu)."]

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for _, mesh, _ in parts:
            export_mesh(coll, mesh)
        with open(os.path.join(EXPORT_DIR, "Nadrz_Tocna.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    print("\n".join(lines))


main()
