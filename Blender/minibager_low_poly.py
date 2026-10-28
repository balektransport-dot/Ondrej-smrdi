# Stylizovany low poly mini bager pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "MiniBager" s pohyblivymi dielmi (kazdy ma pivot v cape, okolo ktoreho sa toci):
#   Podvozok  - pasy a ram (pivot na zemi)
#   Radlica   - predna radlica (otaca sa okolo osi Y)
#   Vrsok     - kabina a karoseria (otaca sa okolo osi Z)
#   Vyloznik  -> Rameno -> Lopata (otacaju sa okolo osi Y)
#   Valce: kazdy ma valec a piest, ktore sa samy natacaju k sebe (Damped Track),
#          takze ked v Blenderi otocis vyloznik, rameno alebo lopatu, piesty sa vysuvaju same.
# Do priecinka MiniBager v domovskom priecinku ulozi FBX kazdeho dielu (pre Unreal)
# a subor MiniBager_pivoty.txt s polohami cap (kde ktory diel pripojit).
# Skript sa da spustit znova: stary bager sa nahradi novym.

import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

COLLECTION = "MiniBager"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "MiniBager")

# ---------------------------------------------------------------------------
# Rozmery a capy (metre). Zem z = 0, predok +X, lavy bok +Y.
# ---------------------------------------------------------------------------

SWING_Z = 0.66                      # vyska otocneho venca (pivot Vrsku)
BLADE_PIN = (0.52, 0.0, 0.36)       # cap radlice na podvozku
BOOM_PIN = (0.80, -0.32, 0.36)      # cap vyloznika na vrsku
BOOM_TIP = (2.33, 0.0, 1.08)        # cap ramena na vyloznku
BUCKET_PIN = (0.10, 0.0, -1.26)     # cap lopaty na ramene

# Hydraulicke valce: (nazov, diel so zakladnou, bod, diel s piestom, bod, polomer valca)
CYLINDERS = [
    ("Radlica", "Podvozok", (0.40, 0.0, 0.52), "Radlica", (0.56, 0.0, 0.05), 0.045),
    ("Vyloznik", "Vrsok", (0.98, -0.32, 0.0), "Vyloznik", (0.72, 0.0, 0.84), 0.065),
    ("Rameno", "Vyloznik", (0.63, 0.0, 1.62), "Rameno", (-0.08, 0.0, 0.44), 0.060),
    ("Lopata", "Rameno", (-0.20, 0.0, 0.20), "Lopata", (-0.24, 0.0, 0.20), 0.050),
]

# Farby (linearne RGB) - zmen podla chuti
YELLOW = (0.80, 0.47, 0.01, 1.0)
ORANGE = (0.80, 0.26, 0.01, 1.0)

GLASS_COLOR = (0.12, 0.18, 0.18, 1.0)
GLASS_ALPHA = 0.25                  # 0 = uplne priehladne, 1 = nepriehladne

# (nazov, farba, kovovost, drsnost)
MATERIALS = [
    ("MB_Zlta", YELLOW, 0.0, 0.45),
    ("MB_Oranzova", ORANGE, 0.0, 0.45),
    ("MB_Siva", (0.09, 0.09, 0.09, 1.0), 0.0, 0.55),
    ("MB_Tmava", (0.02, 0.02, 0.02, 1.0), 0.0, 0.60),
    ("MB_Guma", (0.06, 0.05, 0.04, 1.0), 0.0, 0.90),
    ("MB_Ocel", (0.13, 0.11, 0.09, 1.0), 0.6, 0.60),
    ("MB_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15),
    ("MB_Sklo", GLASS_COLOR, 0.0, 0.05),
    ("MB_Majak", (1.00, 0.30, 0.00, 1.0), 0.0, 0.30),
    ("MB_Cervena", (0.70, 0.01, 0.01, 1.0), 0.0, 0.30),
    ("MB_Svetlo", (0.95, 0.95, 0.90, 1.0), 0.0, 0.20),
]
YEL, ORA, GREY, DARK, RUBBER, STEEL, CHROME, GLASS, BEACON, RED, LIGHT_M = range(11)
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


def add_pin(bm, location, radius, width, mat=GREY):
    add_cylinder(bm, radius, width, along_y(location), mat, segments=8, bev=0.01)


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


# ---------------------------------------------------------------------------
# Podvozok (pivot na zemi pod stredom)
# ---------------------------------------------------------------------------

TRACK_Y = 0.70      # stred pasu od stredu stroja
TRACK_W = 0.32      # sirka pasu
TRACK_R = 0.26      # polomer koncov pasu
TRACK_X = 0.74      # stred predneho/zadneho kolesa pasu
TRACK_T = 0.07      # hrubka gumy


def build_undercarriage():
    bm = bmesh.new()
    for s in SIDES_LR:
        y = s * TRACK_Y
        y0, y1 = y - TRACK_W * 0.5, y + TRACK_W * 0.5
        add_band(bm, stadium(TRACK_X, -TRACK_X, TRACK_R, TRACK_R),
                 stadium(TRACK_X, -TRACK_X, TRACK_R - TRACK_T, TRACK_R), y0, y1, RUBBER)
        # vystupky na gume hore
        for k in range(12):
            x = -0.66 + k * 0.12
            add_box(bm, (0.06, TRACK_W, 0.025), (x, y, TRACK_R * 2 + 0.012), RUBBER)
        # ram pasu, napinacie koleso vpredu, hnacie koleso s motorom vzadu, kladky
        add_extruded(bm, [(-0.66, 0.15), (0.66, 0.15), (0.74, 0.40), (-0.74, 0.40)],
                     y - 0.10, y + 0.10, "XZ", GREY, bev=0.02)
        add_cylinder(bm, 0.18, 0.22, along_y((TRACK_X, y, TRACK_R)), GREY, segments=10, bev=0.02)
        add_cylinder(bm, 0.18, 0.22, along_y((-TRACK_X, y, TRACK_R)), GREY, segments=8, bev=0.02)
        add_cylinder(bm, 0.12, 0.30, along_y((-TRACK_X, y - s * 0.05, TRACK_R)), DARK, segments=8, bev=0.02)
        for x in (-0.45, -0.15, 0.15, 0.45):
            add_cylinder(bm, 0.07, 0.20, along_y((x, y, 0.14)), GREY, segments=8, bev=0.01)
            add_pin(bm, (x, y + s * 0.10, 0.14), 0.03, 0.04, DARK)
        add_cylinder(bm, 0.06, 0.16, along_y((0.0, y, 0.39)), GREY, segments=8, bev=0.01)
        # spojky k strednemu ramu
        for x in (-0.35, 0.35):
            add_box(bm, (0.30, 0.20, 0.14), (x, s * 0.55, 0.30), DARK, bev=0.02)

    # stredny ram a otocny veniec
    add_box(bm, (1.05, 0.96, 0.26), (0.0, 0.0, 0.43), DARK, bev=0.05)
    add_cylinder(bm, 0.48, 0.10, along_z((0.0, 0.0, SWING_Z - 0.05)), DARK, segments=16, bev=0.02)
    return finish_mesh(bm, "SM_MiniBager_Podvozok")


def build_blade():
    # radlica: pivot v cape BLADE_PIN, list stoji na zemi (z = -BLADE_PIN.z)
    bm = bmesh.new()
    ground = -BLADE_PIN[2]
    profile = [(0.74, ground), (0.66, ground + 0.13), (0.63, ground + 0.26), (0.645, ground + 0.38),
               (0.69, ground + 0.43), (0.63, ground + 0.43), (0.585, ground + 0.38), (0.575, ground + 0.26),
               (0.60, ground + 0.13), (0.67, ground)]
    add_extruded(bm, profile, -0.925, 0.925, "XZ", STEEL, bev=0.015)
    for s in SIDES_LR:
        add_box(bm, (0.17, 0.03, 0.40), (0.655, s * 0.93, ground + 0.21), STEEL, bev=0.01)
        add_box(bm, (0.62, 0.10, 0.12), (0.30, s * 0.40, -0.06), STEEL, bev=0.02, rotation=(0.0, 8.0, 0.0))
        add_pin(bm, (0.0, s * 0.40, 0.0), 0.05, 0.14)
    add_box(bm, (0.12, 0.16, 0.12), (0.56, 0.0, 0.03), STEEL, bev=0.02)
    for y in (-0.55, 0.0, 0.55):
        add_box(bm, (0.06, 0.04, 0.30), (0.56, y, ground + 0.20), STEEL)
    return finish_mesh(bm, "SM_MiniBager_Radlica")


# ---------------------------------------------------------------------------
# Vrsok: karoseria, kabina (pivot v strede otocneho venca)
# ---------------------------------------------------------------------------

BODY_W = 0.82       # polovicna sirka karoserie = polomer zadku
BODY_FRONT = 0.60   # predna hrana
BODY_RC = -0.05     # stred zaobleneho zadku


def body_outline(x_cut=None, steps=8, grow=0.0):
    # pohlad zhora: rovny predok, polkruhovy zadok; x_cut = odrez vsetko pred touto hranicou
    r = BODY_W + grow
    front = BODY_FRONT + grow if x_cut is None else x_cut
    if front > BODY_RC:
        pts, tail = [(front, -r), (front, r), (BODY_RC, r)], [(BODY_RC, -r)]
    else:
        y = math.sqrt(max(r * r - (front - BODY_RC) ** 2, 0.0))
        pts, tail = [(front, -y), (front, y)], []
    for k in range(1, steps):
        a = math.radians(90.0 + 180.0 * k / steps)
        pts.append((BODY_RC + r * math.cos(a), r * math.sin(a)))
    return pts + tail


def hood_outline(cab_back=-0.30, right_front=0.40, right_inner=-0.50, steps=8):
    # zlta kapota: za kabinou cez cely zadok a dopredu po pravom boku (tvar L)
    r = BODY_W
    y = math.sqrt(r * r - (cab_back - BODY_RC) ** 2)
    pts = [(right_front, -r), (right_front, right_inner), (cab_back, right_inner), (cab_back, y)]
    for k in range(1, steps):
        a = math.radians(90.0 + 180.0 * k / steps)
        pts.append((BODY_RC + r * math.cos(a), r * math.sin(a)))
    pts.append((BODY_RC, -r))
    return pts


def rear_frame(angle_deg, z):
    # ramec na zaoblenom zadku: X = dotycnica, Y = von, Z = hore
    a = math.radians(angle_deg)
    p = (BODY_RC + (BODY_W + 0.005) * math.cos(a), (BODY_W + 0.005) * math.sin(a), z)
    return place(p, (0.0, 0.0, angle_deg - 90.0))


def build_upper():
    bm = bmesh.new()
    # spodny sivy pas a zlta zadna kapota
    add_extruded(bm, body_outline(), 0.0, 0.34, "XY", GREY, bev=0.04)
    add_extruded(bm, hood_outline(), 0.34, 0.95, "XY", YEL, bev=0.12)
    # uchyt vyloznika (dopredu az po zakladnu valca)
    add_box(bm, (0.52, 0.30, 0.50), (0.77, -0.32, 0.20), YEL, bev=0.04)
    add_pin(bm, BOOM_PIN, 0.07, 0.34)
    add_pin(bm, CYLINDERS[1][2], 0.06, 0.34)

    # vystrazne pruhy a svetla na zadku
    for angle in (125.0, 235.0):
        frame = rear_frame(angle, 0.18)
        add_box(bm, (0.32, 0.012, 0.13), (0.0, 0.0, 0.0), DARK, frame=frame)
        for k in range(4):
            add_box(bm, (0.035, 0.016, 0.16), (-0.105 + k * 0.07, 0.0, 0.0), YEL, rotation=(0.0, 40.0, 0.0), frame=frame)
    for angle in (160.0, 200.0):
        add_box(bm, (0.08, 0.015, 0.05), (0.0, 0.0, 0.0), RED, frame=rear_frame(angle, 0.08))
    # tmave drazky po obvode spodneho pasu
    for z in (0.22, 0.27):
        add_extruded(bm, body_outline(grow=0.006), z, z + 0.012, "XY", DARK)
    # vecko nadrze na lavom boku kapoty
    add_cylinder(bm, 0.05, 0.03, along_y((-0.45, 0.70, 0.66)), GREY, segments=8, bev=0.01)
    # madlo na kapote
    add_box(bm, (0.03, 0.12, 0.06), (-0.55, -0.40, 0.98), DARK)

    build_cab(bm)
    return finish_mesh(bm, "SM_MiniBager_Vrsok")


def build_cab(bm):
    x0, x1, y0, y1 = -0.30, 0.62, -0.15, 0.80
    cx, cy, w, d = (x0 + x1) * 0.5, (y0 + y1) * 0.5, y1 - y0, x1 - x0
    z0, z1 = 0.50, 1.86
    # spodok kabiny (podlaha), stlpiky, strecha
    add_box(bm, (d, w, 0.16), (cx, cy, 0.42), GREY, bev=0.03)
    for x in (x0 + 0.035, x1 - 0.035):
        for y in (y0 + 0.035, y1 - 0.035):
            add_box(bm, (0.07, 0.07, z1 - z0), (x, y, (z0 + z1) * 0.5), ORA, bev=0.015)
    add_box(bm, (d + 0.07, w + 0.07, 0.12), (cx, cy, z1 + 0.04), ORA, bev=0.07)
    add_box(bm, (d - 0.12, w - 0.12, 0.07), (cx, cy, z1 + 0.12), ORA, bev=0.04)
    # predny spodny oranzovy panel a pracovne svetla na streche
    add_box(bm, (0.05, w - 0.10, 0.10), (x1 - 0.01, cy, z0 + 0.05), ORA, bev=0.02)
    for y in (y0 + 0.10, y1 - 0.10):
        add_box(bm, (0.06, 0.10, 0.06), (x1 + 0.02, y, z1 + 0.04), LIGHT_M, bev=0.01)

    # skla (prehladne) s ciernymi ramikmi
    hz = z1 - z0 - 0.02
    zc = (z0 + z1) * 0.5
    add_box(bm, (0.02, w - 0.10, hz), (x1 - 0.02, cy, zc), GLASS)
    add_box(bm, (0.02, w - 0.10, hz), (x0 + 0.02, cy, zc), GLASS)
    for y in (y0 + 0.02, y1 - 0.02):
        add_box(bm, (d - 0.10, 0.02, hz), (cx, y, zc), GLASS)
    add_box(bm, (0.03, w - 0.08, 0.04), (x1 - 0.015, cy, 1.02), DARK)          # predne sklo delene
    add_box(bm, (0.04, 0.035, hz), (0.12, y1 - 0.015, zc), DARK)               # dvere
    add_box(bm, (d - 0.10, 0.035, 0.04), (cx, y1 - 0.015, 1.10), DARK)
    add_box(bm, (0.04, 0.05, 0.10), (0.18, y1 + 0.01, 1.15), DARK)             # klucka

    # sedadlo a ovladace
    add_box(bm, (0.40, 0.42, 0.12), (-0.02, cy, 0.72), DARK, bev=0.03)
    add_box(bm, (0.10, 0.42, 0.55), (-0.18, cy, 1.00), DARK, bev=0.03)
    for y in (cy - 0.26, cy + 0.26):
        add_box(bm, (0.30, 0.09, 0.16), (0.02, y, 0.74), DARK, bev=0.02)
        add_cylinder(bm, 0.02, 0.18, along_z((0.12, y, 0.90)), DARK, segments=6)

    for y in (cy - 0.09, cy + 0.09):
        add_box(bm, (0.10, 0.07, 0.03), (x1 - 0.14, y, z0 + 0.05), DARK)
        add_rod(bm, (x1 - 0.22, y, z0 + 0.05), (x1 - 0.30, y, z0 + 0.42), 0.012, DARK)

    # majak na streche a zrkadla
    add_cylinder(bm, 0.015, 0.10, along_z((x0 + 0.12, y1 - 0.15, z1 + 0.20)), DARK, segments=6)
    add_cylinder(bm, 0.05, 0.10, along_z((x0 + 0.12, y1 - 0.15, z1 + 0.28)), BEACON, segments=8, bev=0.015)
    for y, s in ((y1, 1.0), (y0, -1.0)):
        add_box(bm, (0.02, 0.02, 0.30), (x1 + 0.03, y + s * 0.04, 1.45), DARK)
        add_box(bm, (0.02, 0.10, 0.17), (x1 + 0.03, y + s * 0.07, 1.65), DARK, bev=0.005)


# ---------------------------------------------------------------------------
# Vyloznik, rameno, lopata (kazdy ma pivot vo svojom cape, os otacania Y)
# ---------------------------------------------------------------------------

def build_boom():
    # ohnuty vyloznik: strmo hore takmer do vysky strechy, potom dopredu a mierne dole
    bm = bmesh.new()
    elbow = (0.75, 1.36)
    tip = (BOOM_TIP[0], BOOM_TIP[2])
    add_extruded(bm, beam_outline([(0.0, 0.0), elbow, tip], [0.11, 0.15, 0.09]),
                 -0.11, 0.11, "XZ", YEL, bev=0.035)
    add_cylinder(bm, 0.12, 0.26, along_y((0.0, 0.0, 0.0)), YEL, segments=10, bev=0.02)
    add_cylinder(bm, 0.10, 0.28, along_y(BOOM_TIP), YEL, segments=10, bev=0.02)
    add_pin(bm, (0.0, 0.0, 0.0), 0.05, 0.32)
    add_pin(bm, BOOM_TIP, 0.045, 0.34)

    # uchyty valcov: vpredu na dolnej casti (valec vyloznika), hore na ohybe (valec ramena)
    rod_end = CYLINDERS[1][4]
    add_box(bm, (0.16, 0.16, 0.16), (rod_end[0] - 0.04, 0.0, rod_end[2] + 0.02), YEL, bev=0.02)
    add_pin(bm, rod_end, 0.05, 0.22)
    base = CYLINDERS[2][2]
    add_box(bm, (0.16, 0.14, 0.16), (base[0] + 0.02, 0.0, base[2] - 0.05), YEL, bev=0.02)
    add_pin(bm, base, 0.05, 0.22)

    # hadice po vrchu vyloznika
    for y in (-0.05, 0.05):
        add_rod(bm, (0.08, y, 0.22), (0.64, y, 1.56), 0.015, DARK)
        add_rod(bm, (0.64, y, 1.56), (2.20, y, 1.22), 0.015, DARK)
    return finish_mesh(bm, "SM_MiniBager_Vyloznik")


def build_stick():
    bm = bmesh.new()
    top = CYLINDERS[2][4]
    bucket = (BUCKET_PIN[0], BUCKET_PIN[2])
    add_extruded(bm, beam_outline([(top[0], top[2] - 0.03), (0.0, 0.0), bucket], [0.09, 0.12, 0.075]),
                 -0.085, 0.085, "XZ", YEL, bev=0.025)
    add_cylinder(bm, 0.10, 0.20, along_y((0.0, 0.0, 0.0)), YEL, segments=10, bev=0.02)
    add_cylinder(bm, 0.075, 0.19, along_y(top), YEL, segments=8, bev=0.02)
    add_cylinder(bm, 0.075, 0.21, along_y(BUCKET_PIN), YEL, segments=8, bev=0.02)
    add_pin(bm, top, 0.035, 0.23)
    add_pin(bm, BUCKET_PIN, 0.04, 0.25)

    # uchyt valca lopaty na zadnej strane ramena
    base = CYLINDERS[3][2]
    add_box(bm, (0.16, 0.10, 0.10), (base[0] + 0.06, 0.0, base[2]), YEL, bev=0.02)
    add_pin(bm, base, 0.04, 0.16)

    # hadica dolu po ramene
    add_rod(bm, (-0.02, 0.095, 0.30), (0.08, 0.095, -1.08), 0.012, DARK)
    return finish_mesh(bm, "SM_MiniBager_Rameno")


def build_bucket():
    bm = bmesh.new()
    # obrys plechu lopaty z boku (od hornej hrany dopredu, dole a dozadu k brite)
    curve = [(0.115, 0.023), (0.276, -0.115), (0.345, -0.345), (0.276, -0.575),
             (0.092, -0.713), (-0.161, -0.736), (-0.391, -0.644)]
    half_w = 0.30
    add_extruded(bm, beam_outline(curve, [0.022] * len(curve), cap=0.0), -half_w, half_w, "XZ", STEEL, bev=0.008)
    side = [(-0.07, 0.08)] + curve
    for s in SIDES_LR:
        add_extruded(bm, side, s * half_w, s * (half_w + 0.02), "XZ", STEEL, bev=0.006)
    # vystuha hornej hrany
    add_box(bm, (0.08, half_w * 2.0, 0.05), (0.09, 0.0, 0.03), STEEL, bev=0.01)

    # zuby na brite
    lip, prev = curve[-1], curve[-2]
    d = (lip[0] - prev[0], lip[1] - prev[1])
    length = math.hypot(*d)
    d = (d[0] / length, d[1] / length)
    n = (-d[1], d[0])
    for y in (-0.22, -0.075, 0.075, 0.22):
        tip = (lip[0] + d[0] * 0.11, lip[1] + d[1] * 0.11)

        def square(c, a, b):
            return [(c[0] + n[0] * a * sx, y + b * sy, c[1] + n[1] * a * sx) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        add_prism(bm, square(lip, 0.024, 0.032), square(tip, 0.006, 0.01), STEEL)

    # usi s capom k ramenu a spojka hore k piestu
    lever = CYLINDERS[3][4]
    for y in (-0.09, 0.09):
        add_box(bm, (0.46, 0.03, 0.18), (-0.10, y, 0.04), STEEL, bev=0.01)
        add_box(bm, (0.20, 0.03, 0.07), ((lever[0] - 0.16) * 0.5, y * 0.7, (lever[2] + 0.04) * 0.5), STEEL,
                bev=0.01, rotation=(0.0, -116.6, 0.0))
    add_pin(bm, (0.0, 0.0, 0.0), 0.06, 0.24)
    add_pin(bm, lever, 0.05, 0.20)
    return finish_mesh(bm, "SM_MiniBager_Lopata")


def add_rod(bm, p0, p1, radius, mat, segments=6):
    # tenky valec medzi dvoma bodmi (hadice)
    a, b = Vector(p0), Vector(p1)
    direction = b - a
    rot = direction.to_track_quat("Z", "Y").to_matrix().to_4x4()
    add_cylinder(bm, radius, direction.length, Matrix.Translation((a + b) * 0.5) @ rot, mat, segments=segments)


# ---------------------------------------------------------------------------
# Hydraulicky valec: valec (pivot v zakladni) a piest (pivot v oku piestu), oba smeruju po +X
# ---------------------------------------------------------------------------

def build_cylinder_barrel(name, length, radius):
    bm = bmesh.new()
    add_cylinder(bm, radius, length - 0.06, along_x(((length + 0.06) * 0.5, 0.0, 0.0)), DARK, segments=8, bev=0.01)
    add_cylinder(bm, radius * 1.15, 0.06, along_x((length - 0.03, 0.0, 0.0)), GREY, segments=8, bev=0.01)
    add_box(bm, (0.08, radius * 1.4, radius * 1.4), (0.04, 0.0, 0.0), DARK)
    add_cylinder(bm, radius * 1.15, radius * 2.4, along_y((0.0, 0.0, 0.0)), DARK, segments=8, bev=0.01)
    return finish_mesh(bm, name)


def build_cylinder_rod(name, length, radius):
    bm = bmesh.new()
    rod_r = radius * 0.55
    add_cylinder(bm, rod_r, length - 0.05, along_x(((length + 0.05) * 0.5, 0.0, 0.0)), CHROME, segments=8)
    add_cylinder(bm, rod_r * 1.8, radius * 2.2, along_y((0.0, 0.0, 0.0)), GREY, segments=8, bev=0.01)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Materialy, scena, export
# ---------------------------------------------------------------------------

# (nazov objektu, funkcia, rodic, poloha capu v rodicovi)
PARTS = [
    ("Podvozok", build_undercarriage, None, (0.0, 0.0, 0.0)),
    ("Radlica", build_blade, "Podvozok", BLADE_PIN),
    ("Vrsok", build_upper, "Podvozok", (0.0, 0.0, SWING_Z)),
    ("Vyloznik", build_boom, "Vrsok", BOOM_PIN),
    ("Rameno", build_stick, "Vyloznik", BOOM_TIP),
    ("Lopata", build_bucket, "Rameno", BUCKET_PIN),
]
ROTATION_AXIS = {"Radlica": "Y", "Vrsok": "Z", "Vyloznik": "Y", "Rameno": "Y", "Lopata": "Y"}


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
    if name == "MB_Sklo":
        make_glass(mat, bsdf)
    return mat


def make_glass(mat, bsdf):
    # priehladne sklo cez Alpha - funguje v pohlade Material Preview (Eevee) aj v Cycles
    mat.diffuse_color = (GLASS_COLOR[0], GLASS_COLOR[1], GLASS_COLOR[2], GLASS_ALPHA)
    if bsdf and "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = GLASS_ALPHA
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"   # Blender 4.2 a novsi
    if hasattr(mat, "blend_method"):
        try:
            mat.blend_method = "BLEND"          # starsie verzie
        except Exception:
            pass


def add_materials(mesh):
    for name, color, metallic, roughness in MATERIALS:
        mesh.materials.append(get_material(name, color, metallic, roughness))


def clear_collection(coll):
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.name.startswith("SM_MiniBager_") and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def add_empty(coll, name, parent, location):
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.05
    empty.hide_render = True
    coll.objects.link(empty)
    empty.parent = parent
    empty.location = location
    empty.hide_set(True)  # pomocny bod pre piest, v scene nezavadzia (stale funguje)
    return empty


def add_tracked(coll, name, mesh, parent, location, target):
    # diel otoceny po osi +X vzdy na ciel (valec na piest, piest na valec)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.parent = parent
    obj.location = location
    constraint = obj.constraints.new("DAMPED_TRACK")
    constraint.target = target
    constraint.track_axis = "TRACK_X"
    return obj


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def export_mesh(coll, mesh):
    # kazdy diel sa exportuje samostatne v strede sveta, aby mal pivot v cape
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


def fmt(p):
    return "(%.2f, %.2f, %.2f)" % tuple(p)


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)

    objects, meshes = {}, []
    lines = ["MiniBager - polohy cap v metroch (Blender: X dopredu, Y dolava, Z hore; v Unreale x100 = cm).", ""]
    for name, builder, parent, location in PARTS:
        mesh = builder()
        add_materials(mesh)
        meshes.append(mesh)
        obj = bpy.data.objects.new(name, mesh)
        coll.objects.link(obj)
        if parent:
            obj.parent = objects[parent]
            lines.append("%-9s pripoj na %-9s v %s, otaca sa okolo osi %s" % (name, parent, fmt(location), ROTATION_AXIS[name]))
        obj.location = location
        objects[name] = obj
    bpy.context.view_layer.update()

    lines.append("")
    for cname, base_part, base_pt, rod_part, rod_pt, radius in CYLINDERS:
        a = objects[base_part].matrix_world @ Vector(base_pt)
        b = objects[rod_part].matrix_world @ Vector(rod_pt)
        length = (b - a).length * 0.68  # vydrzi cely rozsah pohybu bez medzery
        barrel = build_cylinder_barrel("SM_MiniBager_Valec_" + cname, length, radius)
        rod = build_cylinder_rod("SM_MiniBager_Piest_" + cname, length, radius)
        for mesh in (barrel, rod):
            add_materials(mesh)
            meshes.append(mesh)
        base_target = add_empty(coll, "Ciel_Zaklad_" + cname, objects[base_part], base_pt)
        rod_target = add_empty(coll, "Ciel_Piest_" + cname, objects[rod_part], rod_pt)
        add_tracked(coll, "Valec_" + cname, barrel, objects[base_part], base_pt, rod_target)
        add_tracked(coll, "Piest_" + cname, rod, objects[rod_part], rod_pt, base_target)
        lines.append("Valec %-8s: valec na %-8s v %s, piest na %-8s v %s, oba miera po +X na druhy cap"
                     % (cname, base_part, fmt(base_pt), rod_part, fmt(rod_pt)))

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for mesh in meshes:
            export_mesh(coll, mesh)
        with open(os.path.join(EXPORT_DIR, "MiniBager_pivoty.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)

    print("\n".join(lines))
    select_only(objects["Vyloznik"])
    print("Hotovo: %d dielov, %d vrcholov spolu" % (len(meshes), sum(len(m.vertices) for m in meshes)))
    print("Skus: vyber Vyloznik, Rameno alebo Lopata a otoc okolo Y (R, Y) - piesty sa pohnu same.")


main()
