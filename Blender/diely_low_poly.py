# Stylizovane low poly stavebne diely (ako Scrap Mechanic) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vsetko je na mriezke 25 cm (1 policko = 0.25 m). Diely su v kolekcii "Diely" zoradene ako katalog,
# pri kazdom je napis s nazvom a rozmerom v polickach (dlzka x sirka x vyska).
#
# Pivot (bod, okolo ktoreho sa diel otaca a podla ktoreho sa prichytava):
#   - bloky, nosniky, piesty, loziska, naboje, capy, tocnica: v strede spodnej steny dielu
#   - korby: v cape sklapania (zadna spodna hrana v strede) - okolo neho sa korba vyklapa (os Y)
#   - kolesa: v strede kolesa, tocia sa okolo osi Y
# Piesty maju samostatnu piestnicu, ktora sa pri prehravani animacie (medzernik) vysuva a zasuva.
# Kolesa sa pri prehravani animacie tocia.
# Do priecinka Diely v domovskom priecinku ulozi FBX kazdeho dielu (pre Unreal) a subor Diely_zoznam.txt.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Diely"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Diely")
G = 0.25            # velkost policka mriezky (m)

# (nazov, farba, kovovost, drsnost)
MATERIALS = [
    ("Diel_Ocel", (0.45, 0.46, 0.48, 1.0), 0.7, 0.40),
    ("Diel_OcelPanel", (0.25, 0.26, 0.28, 1.0), 0.7, 0.45),
    ("Diel_Ram", (0.04, 0.04, 0.045, 1.0), 0.3, 0.50),
    ("Diel_Lak", (0.80, 0.30, 0.02, 1.0), 0.0, 0.45),
    ("Diel_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15),
    ("Diel_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55),
    ("Diel_Pneu", (0.015, 0.015, 0.015, 1.0), 0.0, 0.90),
    ("Diel_Disk", (0.75, 0.76, 0.78, 1.0), 0.8, 0.30),
    ("Diel_DiskKamion", (0.82, 0.82, 0.78, 1.0), 0.2, 0.40),
    ("Diel_Zlta", (0.85, 0.60, 0.02, 1.0), 0.0, 0.40),
    ("Diel_Cervena", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35),
    ("Diel_Mazivo", (0.22, 0.15, 0.04, 1.0), 0.3, 0.20),
    ("Diel_DiskCierny", (0.025, 0.025, 0.028, 1.0), 0.3, 0.35),
]
STEEL, PANEL, FRAME, PAINT, CHROME, DARK, TIRE, RIM, TRUCKRIM, YEL, RED, GREASE, BLACKRIM = range(13)
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


def add_cone(bm, r_back, r_front, depth, matrix, mat, segments=12, bev=0.0):
    # kuzel: r_back na zapornom konci lokalnej osi Z, r_front na kladnom
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=r_back, radius2=r_front, depth=depth, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    caps = [f for f in faces if len(f.verts) == segments]
    bevel(bm, {e for f in caps for e in f.edges}, min(bev, min(r_back, r_front) * 0.4, depth * 0.45), mat)


# ---------------------------------------------------------------------------
# Spolocne pomocky pre diely
# ---------------------------------------------------------------------------

def add_poly(bm, verts, faces, mat, bev=0.0):
    # vlastne teleso z vrcholov a ploch (indexy)
    v = [bm.verts.new(p) for p in verts]
    new_faces = [bm.faces.new([v[i] for i in f]) for f in faces]
    finish_shape(bm, new_faces, mat, bev)


def add_ball(bm, radius, location, mat):
    verts = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius, matrix=Matrix.Translation(location))["verts"]
    set_material(faces_of(verts), mat)


def add_panels(bm, size, mat, inset=0.04, t=0.008, faces="xyz"):
    # vystupujuce plechy na stenach kvadra (stred spodnej steny v 0) - vonkajsia plocha presne na hranici policka
    sx, sy, sz = size
    cz = sz * 0.5
    for s in SIDES_LR:
        if "x" in faces:
            add_box(bm, (t, sy - 2 * inset, sz - 2 * inset), (s * (sx * 0.5 - t * 0.5), 0.0, cz), mat, bev=0.003)
        if "y" in faces:
            add_box(bm, (sx - 2 * inset, t, sz - 2 * inset), (0.0, s * (sy * 0.5 - t * 0.5), cz), mat, bev=0.003)
        if "z" in faces:
            add_box(bm, (sx - 2 * inset, sy - 2 * inset, t), (0.0, 0.0, cz + s * (sz * 0.5 - t * 0.5)), mat, bev=0.003)


def add_bolts_square(bm, half, z, radius=0.009, mat=CHROME):
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, radius, 0.012, along_z((sx * half, sy * half, z)), mat, segments=6)


# ---------------------------------------------------------------------------
# Bloky (pivot v strede spodnej steny)
# ---------------------------------------------------------------------------

def build_block():
    bm = bmesh.new()
    add_box(bm, (G - 0.016, G - 0.016, G - 0.016), (0.0, 0.0, G * 0.5), STEEL, bev=0.02)
    add_panels(bm, (G, G, G), PANEL)
    return finish_mesh(bm, "SM_Diel_Blok"), (1, 1, 1)


def build_wedge(n):
    # klin: sikma plocha z hornej zadnej hrany k spodnej prednej (n = dlzka v polickach)
    bm = bmesh.new()
    length = n * G
    tri = [(-length * 0.5, 0.0), (length * 0.5, 0.0), (-length * 0.5, G)]
    add_extruded(bm, tri, -G * 0.5, G * 0.5, "XZ", STEEL, bev=0.012)
    add_box(bm, (length - 0.08, G - 0.08, 0.008), (0.0, 0.0, 0.004), PANEL, bev=0.003)
    add_box(bm, (0.008, G - 0.08, G - 0.08), (-length * 0.5 + 0.004, 0.0, G * 0.5), PANEL, bev=0.003)
    angle = math.degrees(math.atan2(G, length))
    slope = math.hypot(length, G)
    nx, nz = math.sin(math.radians(angle)), math.cos(math.radians(angle))
    add_box(bm, (slope - 0.13, G - 0.08, 0.008), (-nx * 0.004, 0.0, G * 0.5 - nz * 0.004), PANEL,
            bev=0.003, rotation=(0.0, angle, 0.0))
    name = "SM_Diel_Klin" if n == 1 else "SM_Diel_Klin_%d" % n
    return finish_mesh(bm, name), (n, 1, 1)


def build_corner_wedge():
    # rohovy klin: stvorcova podstava, spicka hore v zadnom lavom rohu
    bm = bmesh.new()
    h = G * 0.5
    verts = [(-h, -h, 0.0), (h, -h, 0.0), (h, h, 0.0), (-h, h, 0.0), (-h, -h, G)]
    faces = [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    add_poly(bm, verts, faces, STEEL, bev=0.01)
    return finish_mesh(bm, "SM_Diel_Klin_roh"), (1, 1, 1)


def build_round_corner():
    # obly roh: stvrtina valca (zaoblenie z hornej zadnej hrany k spodnej prednej)
    bm = bmesh.new()
    h = G * 0.5
    pts = [(-h, 0.0)]
    steps = 6
    for k in range(steps + 1):
        a = math.radians(90.0 * k / steps)
        pts.append((-h + G * math.cos(a), G * math.sin(a)))
    add_extruded(bm, pts, -h, h, "XZ", STEEL, bev=0.01)
    add_box(bm, (G - 0.08, G - 0.08, 0.008), (0.0, 0.0, 0.004), PANEL, bev=0.003)
    return finish_mesh(bm, "SM_Diel_Obly_roh"), (1, 1, 1)


def build_round_block(n):
    # valec stojaci na podstave, n policok vysoky
    bm = bmesh.new()
    height = n * G
    add_cylinder(bm, G * 0.5 - 0.004, height, along_z((0.0, 0.0, height * 0.5)), STEEL, segments=16, bev=0.014)
    for z in (0.004, height - 0.004):
        add_cylinder(bm, 0.085, 0.008, along_z((0.0, 0.0, z)), PANEL, segments=12)
    for k in range(1, n):
        add_cylinder(bm, G * 0.5 - 0.002, 0.01, along_z((0.0, 0.0, k * G)), PANEL, segments=16)
    name = "SM_Diel_Valec" if n == 1 else "SM_Diel_Valec_%d" % n
    return finish_mesh(bm, name), (1, 1, n)


def build_beam(n):
    # nosnik ramu (hranol 1 x 1 policko) s pasnicami, odlahcovacimi otvormi a nitmi
    bm = bmesh.new()
    length = n * G
    add_box(bm, (length - 0.016, G - 0.03, G - 0.03), (0.0, 0.0, G * 0.5), FRAME, bev=0.01)
    for z in (0.012, G - 0.012):
        add_box(bm, (length, G, 0.024), (0.0, 0.0, z), FRAME, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.008, G - 0.03, G - 0.05), (s * (length * 0.5 - 0.004), 0.0, G * 0.5), FRAME)
    for i in range(n):
        x = -length * 0.5 + G * (i + 0.5)
        for s in SIDES_LR:
            add_cylinder(bm, 0.045, 0.006, along_y((x, s * (G * 0.5 - 0.016), G * 0.5)), DARK, segments=10)
    for i in range(2 * n):
        x = -length * 0.5 + G * 0.25 * (2 * i + 1)
        for s in SIDES_LR:
            add_cylinder(bm, 0.008, 0.008, along_z((x, s * 0.085, G - 0.004)), STEEL, segments=6)
            add_cylinder(bm, 0.008, 0.008, along_z((x, s * 0.085, 0.004)), STEEL, segments=6)
    return finish_mesh(bm, "SM_Diel_Nosnik_%d" % n), (n, 1, 1)


# ---------------------------------------------------------------------------
# Piest (teleskopicky): teleso + vnutorna trubka + piestnica s doskou.
# Zasunuty presne vyplni n policok, vysunie sa o n policok (zdvih).
# ---------------------------------------------------------------------------

PAD = 0.04  # hrubka hornej dosky piestnice


def piston_dims(n):
    stroke = n * G
    house = n * G - PAD               # vyska telesa (doska piestnice sedi navrchu)
    stage = stroke * 0.5 + 0.03       # dlzka trubky aj piestnice (polovica zdvihu + prekrytie)
    return stroke, house, stage


def build_piston_base(n):
    bm = bmesh.new()
    stroke, house, stage = piston_dims(n)
    add_box(bm, (G - 0.01, G - 0.01, 0.03), (0.0, 0.0, 0.015), STEEL, bev=0.006)
    add_bolts_square(bm, G * 0.5 - 0.03, 0.033)
    add_cylinder(bm, 0.08, house - 0.05, along_z((0.0, 0.0, 0.03 + (house - 0.05) * 0.5)), YEL, segments=12, bev=0.01)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, 0.012, house - 0.03, along_z((sx * 0.09, sy * 0.09, 0.03 + (house - 0.03) * 0.5)), STEEL, segments=6)
    add_box(bm, (G - 0.03, G - 0.03, 0.02), (0.0, 0.0, house - 0.01), STEEL, bev=0.005)
    add_cylinder(bm, 0.065, 0.006, along_z((0.0, 0.0, house + 0.001)), DARK, segments=12)
    return finish_mesh(bm, "SM_Diel_Piest_%d" % int(n * 25)), (1, 1, n)


def build_piston_tube(n):
    # vnutorna trubka: pivot na jej hornom konci
    bm = bmesh.new()
    _, _, stage = piston_dims(n)
    add_cylinder(bm, 0.055, stage, along_z((0.0, 0.0, -stage * 0.5)), CHROME, segments=12)
    add_cylinder(bm, 0.06, 0.015, along_z((0.0, 0.0, -0.0075)), DARK, segments=12)
    return finish_mesh(bm, "SM_Diel_Piest_%d_Trubka" % int(n * 25))


def build_piston_rod(n):
    # piestnica s hornou doskou: pivot na spodku dosky
    bm = bmesh.new()
    _, _, stage = piston_dims(n)
    add_cylinder(bm, 0.035, stage, along_z((0.0, 0.0, -stage * 0.5)), CHROME, segments=10)
    add_box(bm, (G - 0.01, G - 0.01, PAD), (0.0, 0.0, PAD * 0.5), STEEL, bev=0.008)
    add_bolts_square(bm, G * 0.5 - 0.03, PAD - 0.003)
    add_panels(bm, (G - 0.01, G - 0.01, PAD), PANEL, inset=0.03, t=0.006, faces="z")
    return finish_mesh(bm, "SM_Diel_Piest_%d_Piestnica" % int(n * 25))


# ---------------------------------------------------------------------------
# Lozisko, naboje kolies, gulovy cap
# ---------------------------------------------------------------------------

def build_bearing():
    # otocne lozisko (staticke): spodny blok, ulozenie s gulickami, horna otocna doska
    bm = bmesh.new()
    add_box(bm, (G - 0.01, G - 0.01, 0.12), (0.0, 0.0, 0.06), STEEL, bev=0.012)
    add_panels(bm, (G, G, 0.12), PANEL, inset=0.03, faces="xy")
    add_cylinder(bm, 0.10, 0.06, along_z((0.0, 0.0, 0.15)), DARK, segments=16, bev=0.006)
    for k in range(12):
        a = 2.0 * math.pi * k / 12
        add_cylinder(bm, 0.012, 0.03, along_z((0.105 * math.cos(a), 0.105 * math.sin(a), 0.16)), CHROME, segments=6)
    add_cylinder(bm, 0.11, 0.04, along_z((0.0, 0.0, 0.23)), STEEL, segments=16, bev=0.008)
    for k in range(6):
        a = 2.0 * math.pi * (k + 0.5) / 6
        add_cylinder(bm, 0.009, 0.01, along_z((0.075 * math.cos(a), 0.075 * math.sin(a), G - 0.005)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Diel_Lozisko"), (1, 1, 1)


def build_hub(truck):
    # naboj kolesa: montazna doska na -Y (k ramu), na +Y priruba so skrutkami pre koleso
    bm = bmesh.new()
    zc = G * 0.5
    face = G * 0.5
    add_box(bm, (G - 0.01, 0.03, G - 0.01), (0.0, -face + 0.015, zc), STEEL, bev=0.006)
    for sx in SIDES_LR:
        for sz in SIDES_LR:
            add_cylinder(bm, 0.009, 0.012, along_y((sx * 0.09, -face + 0.033, zc + sz * 0.09)), CHROME, segments=6)
    add_cone(bm, 0.07, 0.10, 0.17, along_y((0.0, -face + 0.115, zc)), PANEL, segments=12, bev=0.008)
    if truck:
        add_cylinder(bm, 0.115, 0.07, along_y((0.0, face - 0.075, zc)), DARK, segments=16, bev=0.008)
    flange_r, studs, stud_r = (0.11, 10, 0.085) if truck else (0.08, 5, 0.055)
    add_cylinder(bm, flange_r, 0.03, along_y((0.0, face - 0.025, zc)), STEEL, segments=16, bev=0.006)
    for k in range(studs):
        a = 2.0 * math.pi * k / studs
        add_cylinder(bm, 0.008, 0.03, along_y((stud_r * math.cos(a), face, zc + stud_r * math.sin(a))), CHROME, segments=6)
    add_cylinder(bm, 0.03, 0.02, along_y((0.0, face - 0.005, zc)), DARK, segments=10)
    name = "SM_Diel_Naboj_nakladny" if truck else "SM_Diel_Naboj_osobny"
    return finish_mesh(bm, name), (1, 1, 1)


def build_ball_hitch():
    bm = bmesh.new()
    add_box(bm, (G - 0.01, G - 0.01, 0.03), (0.0, 0.0, 0.015), STEEL, bev=0.006)
    add_bolts_square(bm, G * 0.5 - 0.03, 0.033)
    add_box(bm, (0.07, 0.07, 0.12), (0.0, 0.0, 0.09), DARK, bev=0.01)
    add_cylinder(bm, 0.045, 0.015, along_z((0.0, 0.0, 0.155)), DARK, segments=10)
    add_cylinder(bm, 0.018, 0.05, along_z((0.0, 0.0, 0.185)), CHROME, segments=8)
    add_ball(bm, 0.025, (0.0, 0.0, G - 0.026), CHROME)
    return finish_mesh(bm, "SM_Diel_Gulovy_cap"), (1, 1, 1)


# ---------------------------------------------------------------------------
# Tocnica a kralovsky cap (navesova suprava), 4 x 4 policka
# ---------------------------------------------------------------------------

def fifth_wheel_outline(r=0.46, throat=0.03, lock_x=0.03, steps=20, scale=1.0):
    # pohlad zhora: kruh s V-zarezom dozadu (-X), na konci zarezu je zamok pre kralovsky cap
    pts = [(-0.06, -throat), (lock_x, -throat), (lock_x, throat), (-0.06, throat)]
    a0, a1 = 158.0, -158.0
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return [(x * scale, y * scale) for x, y in pts]


def build_fifth_wheel():
    bm = bmesh.new()
    add_box(bm, (0.9, 0.9, 0.02), (0.0, 0.0, 0.01), FRAME, bev=0.006)
    for x in (-0.38, 0.38):
        for y in (-0.38, 0.38):
            add_cylinder(bm, 0.012, 0.012, along_z((x, y, 0.025)), CHROME, segments=6)
    for s in SIDES_LR:
        add_box(bm, (0.6, 0.12, 0.15), (0.0, s * 0.30, 0.095), FRAME, bev=0.012)
        add_cylinder(bm, 0.035, 0.14, along_y((0.0, s * 0.30, 0.165)), STEEL, segments=10)
    add_box(bm, (0.5, 0.7, 0.04), (0.0, 0.0, 0.175), FRAME, bev=0.008)
    add_extruded(bm, fifth_wheel_outline(), 0.195, 0.245, "XY", FRAME, bev=0.01)
    add_extruded(bm, fifth_wheel_outline(scale=0.9), 0.244, 0.25, "XY", GREASE)
    add_box(bm, (0.05, 0.10, 0.03), (0.06, 0.0, 0.23), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Diel_Tocnica"), (4, 4, 1)


def build_king_pin():
    # doska pod navesom (navrchu policka) s kralovskym capom smerom dole
    bm = bmesh.new()
    add_box(bm, (1.0, 1.0, 0.03), (0.0, 0.0, G - 0.015), FRAME, bev=0.008)
    add_box(bm, (0.9, 0.05, 0.04), (0.0, 0.0, G - 0.05), FRAME)
    add_box(bm, (0.05, 0.9, 0.04), (0.0, 0.0, G - 0.05), FRAME)
    add_cylinder(bm, 0.40, 0.004, along_z((0.0, 0.0, G - 0.032)), GREASE, segments=20)
    add_cylinder(bm, 0.05, 0.02, along_z((0.0, 0.0, G - 0.04)), STEEL, segments=12)
    add_cylinder(bm, 0.026, 0.085, along_z((0.0, 0.0, G - 0.0925)), CHROME, segments=10)
    add_cylinder(bm, 0.033, 0.018, along_z((0.0, 0.0, G - 0.125)), CHROME, segments=10)
    for x in (-0.44, 0.44):
        for y in (-0.44, 0.44):
            add_cylinder(bm, 0.012, 0.01, along_z((x, y, G - 0.033)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Diel_Kralovsky_cap"), (4, 4, 1)


# ---------------------------------------------------------------------------
# Korby na hlinu: pivot v cape sklapania (zadna spodna hrana v strede), korba ide dopredu (+X)
# ---------------------------------------------------------------------------

def build_dump_body(name, w_cells, l_cells, h_cells, canopy=0.0):
    bm = bmesh.new()
    w, length, h = w_cells * G, l_cells * G, h_cells * G
    hw = w * 0.5
    floor_top = 0.10
    front = length - canopy            # predna stena (pred nou je strieska nad kabinou)

    # pomocny ram pod podlahou: dva pozdlzne nosniky a priecniky
    rail_y = w * 0.3
    for s in SIDES_LR:
        add_box(bm, (front - 0.06, 0.08, 0.08), (front * 0.5, s * rail_y, 0.04), FRAME, bev=0.008)
    for i in range(int(front / 0.5)):
        add_box(bm, (0.05, rail_y * 2 + 0.08, 0.05), (0.25 + i * 0.5, 0.0, 0.045), FRAME)

    # podlaha
    add_box(bm, (front, w - 0.06, 0.02), (front * 0.5, 0.0, floor_top - 0.01), PAINT, bev=0.004)

    # bocnice s hornym a spodnym lemom a zvislymi rebrami
    wall_y = hw - 0.03 - 0.0125
    wall_h = h - 0.06 - floor_top
    for s in SIDES_LR:
        add_box(bm, (front, 0.025, wall_h), (front * 0.5, s * wall_y, floor_top + wall_h * 0.5), PAINT)
        add_box(bm, (front, 0.06, 0.06), (front * 0.5, s * (hw - 0.03), h - 0.03), PAINT, bev=0.01)
        add_box(bm, (front, 0.05, 0.06), (front * 0.5, s * (hw - 0.025), floor_top + 0.03), PAINT, bev=0.008)
        for i in range(1, int(front / 0.5) + 1):
            x = min(i * 0.5, front - 0.05)
            add_box(bm, (0.05, 0.03, wall_h - 0.06), (x, s * (hw - 0.015), floor_top + wall_h * 0.5), PAINT, bev=0.006)

    # predna stena s vodorovnymi rebrami
    add_box(bm, (0.03, w - 0.06, h - floor_top), (front - 0.06, 0.0, floor_top + (h - floor_top) * 0.5), PAINT)
    for z in (h * 0.4, h * 0.75):
        add_box(bm, (0.03, w - 0.10, 0.05), (front - 0.03, 0.0, z), PAINT, bev=0.006)

    # strieska nad kabinou (len vacsie korby)
    if canopy > 0.0:
        add_box(bm, (canopy + 0.04, w - 0.06, 0.02), (front + canopy * 0.5 - 0.02, 0.0, h - 0.01), PAINT, bev=0.004)
        for s in SIDES_LR:
            gusset = [(front - 0.04, h * 0.55), (length - 0.01, h - 0.02), (front - 0.04, h - 0.02)]
            add_extruded(bm, gusset, s * (hw - 0.05), s * (hw - 0.03), "XZ", PAINT, bev=0.004)

    # zadne celo s rebrami, pantami hore a zamkami dole, odrazky
    add_box(bm, (0.025, w - 0.08, h - floor_top - 0.04), (0.035, 0.0, floor_top + (h - floor_top - 0.04) * 0.5), PAINT)
    for z in (h * 0.35, h * 0.7):
        add_box(bm, (0.02, w - 0.12, 0.04), (0.012, 0.0, z), PAINT, bev=0.005)
    for s in SIDES_LR:
        add_cylinder(bm, 0.025, 0.08, along_y((0.035, s * (hw - 0.10), h - 0.04)), DARK, segments=8)
        add_box(bm, (0.04, 0.06, 0.05), (0.02, s * (hw - 0.10), floor_top + 0.04), DARK, bev=0.005)
        add_box(bm, (0.005, 0.08, 0.03), (0.0025, s * (hw - 0.20), floor_top + 0.09), RED)

    # cap sklapania vzadu (presne v pivote) a uchyt piestu vpredu
    for s in SIDES_LR:
        for d in (-0.035, 0.035):
            add_box(bm, (0.10, 0.03, 0.10), (0.05, s * rail_y + d, 0.05), FRAME, bev=0.006)
        add_cylinder(bm, 0.025, 0.11, along_y((0.0, s * rail_y, 0.0)), STEEL, segments=8)
    add_box(bm, (0.10, 0.12, 0.08), (front * 0.7, 0.0, 0.04), FRAME, bev=0.008)
    add_cylinder(bm, 0.025, 0.16, along_y((front * 0.7, 0.0, 0.02)), STEEL, segments=8)
    return finish_mesh(bm, name), (l_cells, w_cells, h_cells)


# ---------------------------------------------------------------------------
# Kolesa: pivot v strede, os otacania Y, vonkajsia strana disku na +Y
# ---------------------------------------------------------------------------

def add_tread(bm, radius, depth, rows, count, sides=False):
    # bloky dezenu po obvode: rows = [(posun_Y, sirka_bloku, posun_polovicu_kroku)]
    pitch = 2.0 * math.pi * radius / count
    for y, width, shift in rows:
        for k in range(count):
            a = math.degrees(2.0 * math.pi * (k + (0.5 if shift else 0.0)) / count)
            frame = Matrix.Rotation(math.radians(a), 4, "Y")
            add_box(bm, (pitch * 0.55, width, depth), (0.0, y, radius - depth * 0.5), TIRE, bev=depth * 0.3, frame=frame)
            if sides:
                # bloky prechadzajuce na bocnicu (offroad)
                s = 1.0 if y > 0 else -1.0
                add_box(bm, (pitch * 0.5, 0.025, 0.07), (0.0, y + s * width * 0.5, radius - depth - 0.03), TIRE,
                        bev=0.006, frame=frame)


def add_ring(bm, r_out, r_in, width, y, mat, segments, bev=0.0):
    # duty prstenec okolo osi Y (pneumatika, obvod disku) - stred zostane otvoreny
    y0, y1 = y - width * 0.5, y + width * 0.5
    angles = [2.0 * math.pi * k / segments for k in range(segments)]
    o0 = [bm.verts.new((r_out * math.cos(a), y0, r_out * math.sin(a))) for a in angles]
    o1 = [bm.verts.new((r_out * math.cos(a), y1, r_out * math.sin(a))) for a in angles]
    i0 = [bm.verts.new((r_in * math.cos(a), y0, r_in * math.sin(a))) for a in angles]
    i1 = [bm.verts.new((r_in * math.cos(a), y1, r_in * math.sin(a))) for a in angles]
    faces = []
    for a in range(segments):
        b = (a + 1) % segments
        faces.append(bm.faces.new((o0[a], o0[b], o1[b], o1[a])))
        faces.append(bm.faces.new((i0[b], i0[a], i1[a], i1[b])))
        faces.append(bm.faces.new((o0[b], o0[a], i0[a], i0[b])))
        faces.append(bm.faces.new((o1[a], o1[b], i1[b], i1[a])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    set_material(faces, mat)
    if bev > 0.0:
        # zaoblene ramena pneumatiky = len vonkajsie hrany
        edges = set()
        for ring in (o0, o1):
            for a in range(segments):
                e = bm.edges.get((ring[a], ring[(a + 1) % segments]))
                if e:
                    edges.add(e)
        bevel(bm, edges, bev, mat)


def add_tire(bm, radius, width, tread_depth, segments, rim_r):
    body = radius - tread_depth
    add_ring(bm, body, rim_r, width, 0.0, TIRE, segments, bev=width * 0.2)
    for s in SIDES_LR:
        add_ring(bm, body * 0.88, body * 0.82, 0.006, s * (width * 0.5 - 0.001), DARK, segments)


def ring_of(bm, count, radius, y, r, depth, mat, segments=6, offset=0.0):
    for k in range(count):
        a = 2.0 * math.pi * (k + offset) / count
        add_cylinder(bm, r, depth, along_y((radius * math.cos(a), y, radius * math.sin(a))), mat, segments=segments)


def build_wheel_car():
    # osobne koleso 66 cm, hlinikovy disk s 5 ramenami
    bm = bmesh.new()
    radius, width = 0.33, 0.22
    out = width * 0.5
    add_tire(bm, radius, width, 0.012, 28, 0.205)
    add_tread(bm, radius, 0.012, [(-0.07, 0.05, False), (0.0, 0.06, True), (0.07, 0.05, False)], 28)
    add_ring(bm, 0.205, 0.19, width - 0.02, 0.0, RIM, 24)
    add_ring(bm, 0.215, 0.195, 0.015, out - 0.02, RIM, 24)
    add_cylinder(bm, 0.19, 0.01, along_y((0.0, out - 0.065, 0.0)), DARK, segments=20)
    for k in range(5):
        frame = Matrix.Rotation(math.radians(72.0 * k), 4, "Y")
        add_box(bm, (0.045, 0.03, 0.15), (0.0, out - 0.04, 0.12), RIM, bev=0.008, frame=frame)
    add_cylinder(bm, 0.06, 0.04, along_y((0.0, out - 0.04, 0.0)), RIM, segments=12, bev=0.006)
    ring_of(bm, 5, 0.042, out - 0.015, 0.008, 0.02, CHROME, offset=0.5)
    add_cylinder(bm, 0.028, 0.012, along_y((0.0, out - 0.014, 0.0)), DARK, segments=12)
    mount = out - 0.06
    return finish_mesh(bm, "SM_Diel_Koleso_osobne"), radius, width, mount


def build_wheel_offroad():
    # offroad koleso 86 cm, velke hroty, cierny beadlock disk
    bm = bmesh.new()
    radius, width = 0.43, 0.32
    out = width * 0.5
    add_tire(bm, radius, width, 0.035, 24, 0.235)
    add_tread(bm, radius, 0.035, [(-0.075, 0.13, False), (0.075, 0.13, True)], 14, sides=True)
    add_ring(bm, 0.235, 0.22, width - 0.03, 0.0, BLACKRIM, 20)
    add_ring(bm, 0.255, 0.215, 0.02, out - 0.02, BLACKRIM, 20)
    ring_of(bm, 16, 0.245, out - 0.008, 0.007, 0.012, CHROME)
    add_ring(bm, 0.213, 0.203, 0.006, out - 0.031, RED, 20)
    add_cylinder(bm, 0.22, 0.02, along_y((0.0, out - 0.045, 0.0)), BLACKRIM, segments=20)
    ring_of(bm, 8, 0.15, out - 0.033, 0.03, 0.006, DARK, segments=10, offset=0.5)
    add_cylinder(bm, 0.07, 0.05, along_y((0.0, out - 0.04, 0.0)), BLACKRIM, segments=12, bev=0.006)
    ring_of(bm, 6, 0.052, out - 0.012, 0.009, 0.02, CHROME)
    add_cylinder(bm, 0.035, 0.015, along_y((0.0, out - 0.012, 0.0)), DARK, segments=10)
    mount = out - 0.065
    return finish_mesh(bm, "SM_Diel_Koleso_offroad"), radius, width, mount


def build_wheel_truck():
    # kamionove koleso 105 cm, ocelovy disk s 10 otvormi
    bm = bmesh.new()
    radius, width = 0.525, 0.30
    out = width * 0.5
    add_tire(bm, radius, width, 0.018, 32, 0.285)
    add_tread(bm, radius, 0.018, [(-0.075, 0.11, False), (0.075, 0.11, True)], 22)
    add_ring(bm, 0.285, 0.27, width - 0.03, 0.0, TRUCKRIM, 24)
    add_ring(bm, 0.30, 0.275, 0.015, out - 0.02, TRUCKRIM, 24)
    add_cylinder(bm, 0.27, 0.02, along_y((0.0, out - 0.06, 0.0)), TRUCKRIM, segments=24)
    ring_of(bm, 10, 0.205, out - 0.048, 0.035, 0.006, DARK, segments=10, offset=0.5)
    add_cylinder(bm, 0.12, 0.06, along_y((0.0, out - 0.05, 0.0)), PANEL, segments=16, bev=0.008)
    ring_of(bm, 10, 0.095, out - 0.012, 0.011, 0.025, CHROME)
    add_cone(bm, 0.045, 0.07, 0.05, along_y((0.0, out - 0.03, 0.0)), PANEL, segments=12, bev=0.006)
    mount = out - 0.08
    return finish_mesh(bm, "SM_Diel_Koleso_kamion"), radius, width, mount


# ---------------------------------------------------------------------------
# Katalog v scene, menovky, pohyb piestov a kolies, export
# ---------------------------------------------------------------------------

def get_material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color  # farba v pohlade Solid
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


MATS = []


def new_object(coll, name, mesh, location, parent=None):
    if not mesh.materials:
        for mat in MATS:
            mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.parent = parent
    obj.location = location
    return obj


def add_label(coll, text, location):
    curve = bpy.data.curves.new("Napis_" + text.split("\n")[0], "FONT")
    curve.body = text
    curve.size = 0.07
    curve.align_x = "CENTER"
    curve.materials.append(MATS[DARK])
    obj = bpy.data.objects.new(curve.name, curve)
    coll.objects.link(obj)
    obj.location = location


def add_driver(obj, prop, index, expression):
    fcurve = obj.driver_add(prop, index)
    fcurve.driver.type = "SCRIPTED"
    fcurve.driver.expression = expression


def clear_collection(coll):
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("SM_Diel_") and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.name.startswith("Napis_") and curve.users == 0:
            bpy.data.curves.remove(curve)


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


def cells_text(cells):
    return "%dx%dx%d" % cells


def main():
    global MATS
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)
    MATS = [get_material(*m) for m in MATERIALS]

    meshes, lines = [], ["Diely - mriezka 25 cm. Rozmer = dlzka (X) x sirka (Y) x vyska (Z) v polickach.", ""]
    gap, y_cursor = 0.35, 0.0

    def place_row(title, items):
        # items: (nazov, funkcia) -> funkcia vracia (mesh, policka); rad ide pozdlz X
        nonlocal y_cursor
        built = [(name, *fn()) for name, fn in items]
        depth = max(cells[1] for _, _, cells in built) * G
        row_y = y_cursor + depth * 0.5
        x = 0.0
        lines.append("== %s ==" % title)
        for name, mesh, cells in built:
            length = cells[0] * G
            pivot_x = x if name.startswith("Korba") else x + length * 0.5
            new_object(coll, name, mesh, (pivot_x, row_y, 0.0))
            meshes.append(mesh)
            add_label(coll, "%s\n%s" % (name, cells_text(cells)), (x + length * 0.5, row_y - depth * 0.5 - 0.12, 0.001))
            lines.append("%-15s %-9s = %.2f x %.2f x %.2f m" % (name, cells_text(cells), cells[0] * G, cells[1] * G, cells[2] * G))
            x += length + gap
        lines.append("")
        y_cursor += depth + 0.6

    place_row("Bloky", [("Blok", build_block), ("Klin", lambda: build_wedge(1)), ("Klin_2", lambda: build_wedge(2)),
                        ("Klin_roh", build_corner_wedge), ("Obly_roh", build_round_corner),
                        ("Valec", lambda: build_round_block(1)), ("Valec_2", lambda: build_round_block(2))])
    place_row("Nosniky ramu", [("Nosnik_%d" % n, (lambda n=n: build_beam(n))) for n in (2, 3, 4, 6, 8)])

    # mechanika: piesty maju pohyblive casti
    row_y = y_cursor + 0.5            # najsirsi diel (tocnica) ma 4 policka = 1 m
    label_y = row_y - 0.5 - 0.12
    x = 0.0
    lines.append("== Mechanika ==")
    for n in (1, 2):
        stroke, house, _ = piston_dims(n)
        base_mesh, cells = build_piston_base(n)
        name = "Piest_%d" % int(n * 25)
        base = new_object(coll, name, base_mesh, (x + G * 0.5, row_y, 0.0))
        tube = new_object(coll, name + "_Trubka", build_piston_tube(n), (0.0, 0.0, house), parent=base)
        rod = new_object(coll, name + "_Piestnica", build_piston_rod(n), (0.0, 0.0, house), parent=base)
        add_driver(tube, "location", 2, "%.4f + %.4f * (1 - cos(frame * 0.05))" % (house, stroke * 0.25))
        add_driver(rod, "location", 2, "%.4f + %.4f * (1 - cos(frame * 0.05))" % (house, stroke * 0.5))
        meshes += [base_mesh, tube.data, rod.data]
        add_label(coll, "%s\n%s, zdvih %d cm" % (name, cells_text(cells), int(stroke * 100)), (x + G * 0.5, label_y, 0.001))
        lines.append("%-15s %-9s zdvih %d cm. Trubka a piestnica maju pivot v (0, 0, %.3f) a idu hore o polovicu / cely zdvih."
                     % (name, cells_text(cells), int(stroke * 100), house))
        x += G + gap
    for name, fn in (("Lozisko", build_bearing), ("Naboj_osobny", lambda: build_hub(False)),
                     ("Naboj_nakladny", lambda: build_hub(True)), ("Gulovy_cap", build_ball_hitch),
                     ("Tocnica", build_fifth_wheel), ("Kralovsky_cap", build_king_pin)):
        mesh, cells = fn()
        length = cells[0] * G
        new_object(coll, name, mesh, (x + length * 0.5, row_y, 0.0))
        meshes.append(mesh)
        add_label(coll, "%s\n%s" % (name, cells_text(cells)), (x + length * 0.5, label_y, 0.001))
        note = ""
        if name.startswith("Naboj"):
            note = " Koleso sa montuje na prirubu na strane +Y."
        elif name == "Tocnica":
            note = " Vrch (spojenie s kralovskym capom) je vo vyske 0.25 m."
        elif name == "Kralovsky_cap":
            note = " Doska je navrchu policka (prisrubuje sa pod naves), cap smeruje dole."
        lines.append("%-15s %-9s%s" % (name, cells_text(cells), note))
        x += length + gap
    lines.append("")
    y_cursor = row_y + 0.5 + 0.6

    place_row("Korby (pivot = cap sklapania vzadu dole, korba ide dopredu po +X)", [
        ("Korba_S", lambda: build_dump_body("SM_Diel_Korba_S", 6, 8, 2)),
        ("Korba_M", lambda: build_dump_body("SM_Diel_Korba_M", 8, 12, 3, canopy=0.5)),
        ("Korba_L", lambda: build_dump_body("SM_Diel_Korba_L", 10, 16, 4, canopy=0.75))])

    # kolesa stoja na zemi, tocia sa
    row_y = y_cursor + 0.3
    x = 0.0
    lines.append("== Kolesa (pivot v strede, os Y, vonkajsia strana +Y) ==")
    for name, fn in (("Koleso_osobne", build_wheel_car), ("Koleso_offroad", build_wheel_offroad),
                     ("Koleso_kamion", build_wheel_truck)):
        mesh, radius, width, mount = fn()
        wheel = new_object(coll, name, mesh, (x + radius, row_y, radius))
        add_driver(wheel, "rotation_euler", 1, "frame * 0.06")
        meshes.append(mesh)
        add_label(coll, "%s\npriemer %d cm" % (name, round(radius * 200)), (x + radius, row_y - 0.45, 0.001))
        lines.append("%-15s priemer %.2f m, sirka %.2f m. Montazna plocha disku je %.3f m od stredu na strane +Y."
                     % (name, radius * 2, width, mount))
        x += radius * 2 + gap

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for mesh in meshes:
            export_mesh(coll, mesh)
        with open(os.path.join(EXPORT_DIR, "Diely_zoznam.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)

    if scene.frame_end < 250:
        scene.frame_end = 250
    print("\n".join(lines))
    print("Hotovo: %d dielov, %d vrcholov spolu. Medzernik = piesty sa vysuvaju, kolesa sa tocia."
          % (len(meshes), sum(len(m.vertices) for m in meshes)))


main()
