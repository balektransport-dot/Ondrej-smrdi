# Stylizovany low poly vyklopny privesny vozik (na motorku a pod.) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Vozik" s dvoma podkolekciami:
#   Vozik_celok - hotovy vozik: korba sa vyklapa (pod nou je schovany piest), zadne celo sa otvara
#                 a sluzi ako najazd, oporne koliesko vpredu sa da zdvihnut. Pohyb uvidis, ked pustis
#                 animaciu (medzernik): celo sa otvori, korba sa vyklopi, vrati sa spat a koliesko sa zdvihne.
#   Vozik_diely - ten isty vozik rozlozeny na samostatne diely s menovkami (na skladanie po svojom).
# Pivoty: pevne diely maju spolocny pivot na zemi pod osou kolies (daj ich vsetky na 0,0,0 a sedia),
#         pohyblive diely maju pivot v klbe (pant cela, cap korby, piest, koliesko) - polohy su vo Vozik.txt.
# Predok (oje) = +X, lava strana = +Y. Do priecinka Vozik v domovskom priecinku ulozi FBX kazdeho dielu.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Vozik"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Vozik")

# (nazov, farba, kovovost, drsnost, svietivost)
MATERIALS = [
    ("VZ_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0),
    ("VZ_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0),
    ("VZ_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0),
    ("VZ_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0),
    ("VZ_Disk", (0.72, 0.73, 0.75, 1.0), 0.6, 0.35, 0.0),
    ("VZ_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0),
    ("VZ_Lak_svetly", (0.42, 0.42, 0.43, 1.0), 0.2, 0.45, 0.0),
    ("VZ_Lak_tmavy", (0.13, 0.13, 0.14, 1.0), 0.2, 0.45, 0.0),
    ("VZ_Blatnik", (0.58, 0.57, 0.55, 1.0), 0.0, 0.50, 0.0),
    ("VZ_Podlaha", (0.26, 0.26, 0.27, 1.0), 0.4, 0.55, 0.0),
    ("VZ_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0),
    ("VZ_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0),
    ("VZ_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0),
    ("VZ_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0),
    ("VZ_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, PAINT, PAINT2, FENDER, FLOOR, LAMP_OR, LAMP_RED, LAMP_WHITE, RED,
 WHITE) = range(15)
SIDES_LR = (-1.0, 1.0)

# rozmery (m), pociatok = zem pod osou kolies
WHEEL_R = 0.29            # polomer kolesa (13")
AXLE_Z = WHEEL_R
HUB_Y = 0.78              # dosadacia plocha kolesa od stredu
RAIL_Y = 0.45             # os nosnika ramu
FRAME_TOP = 0.50          # vrch ramu = spodok korby
TILT = Vector((-0.20, 0.0, FRAME_TOP))      # cap vyklapania korby
BOX_BACK, BOX_FRONT = -0.95, 1.15           # korba (x)
BOX_HALF = 0.66                             # polovica sirky korby
FLOOR_TOP = 0.10                            # vrch podlahy nad spodkom korby
WALL_TOP = 0.50                             # vrch bocnic nad spodkom korby
GATE_HINGE = Vector((BOX_BACK - TILT.x, 0.0, 0.06))   # pant zadneho cela (v suradniciach korby)
PISTON_BASE = Vector((0.95, 0.0, 0.44))               # spodne oko piestu (na rame)
PISTON_TOP = Vector((0.60, 0.0, -0.015))              # horne oko piestu (pod korbou, suradnice korby)
JOCKEY = Vector((1.60, 0.33, 0.55))                   # vrch nohy oporneho kolieska (dole)
JOCKEY_LIFT = 0.20                                    # o kolko sa koliesko zdvihne
TILT_DEG = 25.0                                       # vyklopenie korby
GATE_DEG = 90.0                                       # otvorenie cela


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
# Dalsie pomocky
# ---------------------------------------------------------------------------

def add_cone(bm, r_back, r_front, depth, matrix, mat, segments=12, bev=0.0):
    # kuzel: r_back na zapornom konci lokalnej osi Z, r_front na kladnom
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=r_back, radius2=r_front, depth=depth, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    caps = [f for f in faces if len(f.verts) == segments]
    bevel(bm, {e for f in caps for e in f.edges}, min(bev, min(r_back, r_front) * 0.4, depth * 0.45), mat)


def add_extruded_yz(bm, points, x0, x1, mat, bev=0.0):
    # mnohouholnik v rovine YZ (body (y, z)) vytiahnuty do hrubky v X
    v0 = [bm.verts.new((x0, p[0], p[1])) for p in points]
    v1 = [bm.verts.new((x1, p[0], p[1])) for p in points]
    faces = [bm.faces.new(v0), bm.faces.new(v1[::-1])]
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((v0[i], v0[j], v1[j], v1[i])))
    finish_shape(bm, faces, mat, bev)


def sweep_profile(bm, profile, a0, a1, steps, mat):
    # konvexny profil (r, y) otoceny okolo osi Y od uhla a0 po a1 (0 = vpredu +X, 90 = hore, 180 = vzadu)
    rings = []
    for k in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * k / steps)
        rings.append([bm.verts.new((r * math.cos(a), y, r * math.sin(a))) for r, y in profile])
    faces = [bm.faces.new(rings[0]), bm.faces.new(rings[-1][::-1])]
    n = len(profile)
    for k in range(steps):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i])))
    finish_shape(bm, faces, mat, 0.0)


def on_arc(angle):
    # natocenie dielu na obluku: lokalna os Z smeruje od stredu kolesa pod uhlom angle
    return Matrix.Rotation(math.radians(90.0 - angle), 4, "Y")


def mirror_y(bm):
    # zrkadlova kopia na druhu stranu (L -> P)
    copy = bm.copy()
    bmesh.ops.scale(copy, vec=(1.0, -1.0, 1.0), verts=copy.verts[:])
    bmesh.ops.reverse_faces(copy, faces=copy.faces[:])
    return copy


def shift(bm, offset):
    # posun celeho dielu (presun pivotu na dosadaciu plochu)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts[:])


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


def ring_of(bm, count, radius, y, r, depth, mat, segments=6, offset=0.0):
    for k in range(count):
        a = 2.0 * math.pi * (k + offset) / count
        add_cylinder(bm, r, depth, along_y((radius * math.cos(a), y, radius * math.sin(a))), mat, segments=segments)


def add_at(bm, offset, fn, *args, **kwargs):
    # vytvor tvar okolo pociatku (napr. prstenec okolo osi Y) a posun ho na miesto
    before = set(bm.verts)
    fn(bm, *args, **kwargs)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=[v for v in bm.verts if v not in before])


def add_box_between(bm, p0, p1, width, height, mat, bev=0.0):
    # hranol (napr. stvorhranna rurka) medzi dvoma bodmi, otoceny len okolo Z a Y
    a, b = Vector(p0), Vector(p1)
    d = b - a
    yaw = math.degrees(math.atan2(d.y, d.x))
    pitch = -math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
    frame = Matrix.Translation((a + b) * 0.5) @ Euler((0.0, math.radians(pitch), math.radians(yaw)), "XYZ").to_matrix().to_4x4()
    add_box(bm, (d.length, width, height), (0.0, 0.0, 0.0), mat, bev=bev, frame=frame)


def add_ring_loop(bm, center, radius, mat, rod_r=0.012, steps=8):
    # oko z kratkych tyciek (lezi vodorovne)
    pts = [(center[0] + radius * math.cos(2.0 * math.pi * k / steps),
            center[1] + radius * math.sin(2.0 * math.pi * k / steps), center[2]) for k in range(steps)]
    for k in range(steps):
        add_rod(bm, pts[k], pts[(k + 1) % steps], rod_r, mat, segments=6)


# ---------------------------------------------------------------------------
# Pevne diely (spolocny pivot = zem pod osou kolies)
# ---------------------------------------------------------------------------

def build_frame():
    bm = bmesh.new()
    x0, x1 = -0.22, 1.10
    length, xc = x1 - x0, (x0 + x1) * 0.5
    for s in SIDES_LR:
        # C-profil: stojina vonku, pasnice dnu
        add_box(bm, (length, 0.012, 0.10), (xc, s * 0.480, 0.45), FRAME, bev=0.003)
        for z in (0.406, 0.494):
            add_box(bm, (length, 0.06, 0.012), (xc, s * 0.452, z), FRAME, bev=0.003)
        for i in range(6):
            add_cylinder(bm, 0.009, 0.006, along_y((x0 + 0.12 + i * 0.22, s * 0.487, 0.45)), DARK, segments=8)
    for x in (-0.18, 0.20, 1.05):
        add_box(bm, (0.05, 0.948, 0.07), (x, 0.0, 0.45), FRAME, bev=0.006)
    # cap vyklapania korby (vzadu) a drziak piestu (vpredu)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.012, 0.05), (TILT.x, s * 0.36, FRAME_TOP - 0.02), FRAME, bev=0.003)
        add_cylinder(bm, 0.025, 0.06, along_y((TILT.x, s * 0.36, TILT.z)), STEEL, segments=10)
        add_box(bm, (0.10, 0.008, 0.08), (PISTON_BASE.x + 0.04, s * 0.04, PISTON_BASE.z), FRAME, bev=0.003)
    add_cylinder(bm, 0.01, 0.94, along_y(TILT), CHROME, segments=6)
    add_cylinder(bm, 0.012, 0.10, along_y(PISTON_BASE), CHROME, segments=6)
    return finish_mesh(bm, "SM_Vozik_ram")


DRAW_REAR, DRAW_FRONT = (1.06, 0.45, 0.45), (1.94, 0.05, 0.43)


def drawbar_y(x):
    # y lavej rurky oja v mieste x
    t = (x - DRAW_REAR[0]) / (DRAW_FRONT[0] - DRAW_REAR[0])
    return DRAW_REAR[1] + (DRAW_FRONT[1] - DRAW_REAR[1]) * t, DRAW_REAR[2] + (DRAW_FRONT[2] - DRAW_REAR[2]) * t


def build_drawbar():
    bm = bmesh.new()
    for s in SIDES_LR:
        add_box_between(bm, (DRAW_REAR[0], s * DRAW_REAR[1], DRAW_REAR[2]),
                        (DRAW_FRONT[0], s * DRAW_FRONT[1], DRAW_FRONT[2]), 0.07, 0.07, FRAME, bev=0.008)
    add_box(bm, (0.12, 0.16, 0.08), (1.95, 0.0, 0.43), FRAME, bev=0.01)
    y, z = drawbar_y(1.35)
    add_box(bm, (0.05, 2.0 * y, 0.04), (1.35, 0.0, z), FRAME, bev=0.005)
    # zasuvka svetiel s kablom a poistne lanko
    add_box(bm, (0.05, 0.04, 0.05), (1.38, -0.16, z + 0.045), DARK, bev=0.006)
    add_rod(bm, (1.40, -0.16, z + 0.05), (1.92, -0.06, 0.47), 0.008, DARK)
    add_ring_loop(bm, (2.00, 0.07, 0.40), 0.02, STEEL, rod_r=0.004, steps=8)
    return finish_mesh(bm, "SM_Vozik_oje")


def build_coupling():
    # gulova spojka s rukovatou (gula tahaca je v bode (2.20, 0, 0.43))
    bm = bmesh.new()
    add_box(bm, (0.24, 0.085, 0.075), (2.08, 0.0, 0.455), STEEL, bev=0.015)
    add_cylinder(bm, 0.045, 0.085, along_y((2.20, 0.0, 0.44)), STEEL, segments=10)
    add_cylinder(bm, 0.046, 0.04, along_z((2.20, 0.0, 0.425)), DARK, segments=10)
    add_cylinder(bm, 0.016, 0.06, along_y((2.02, 0.0, 0.497)), STEEL, segments=8)
    add_rod(bm, (2.02, 0.0, 0.497), (2.19, 0.0, 0.53), 0.011, STEEL, segments=6)
    add_box(bm, (0.07, 0.032, 0.026), (2.20, 0.0, 0.534), DARK, bev=0.008)
    for x in (1.99, 2.07):
        add_cylinder(bm, 0.009, 0.10, along_y((x, 0.0, 0.45)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Vozik_spojka")


def build_axle():
    # gumova torzna naprava s vlecenymi ramenami a nabojmi
    bm = bmesh.new()
    xt, zt = 0.18, 0.36
    add_box(bm, (0.08, 1.30, 0.08), (xt, 0.0, zt), STEEL, bev=0.012)
    for s in SIDES_LR:
        for d in SIDES_LR:
            add_box(bm, (0.12, 0.01, 0.10), (xt, s * RAIL_Y + d * 0.045, 0.39), FRAME, bev=0.003)
        add_box(bm, (0.11, 0.06, 0.11), (xt, s * 0.66, zt), STEEL, bev=0.012)
        add_box_between(bm, (xt, s * 0.66, zt), (0.0, s * 0.70, AXLE_Z), 0.05, 0.05, STEEL, bev=0.008)
        add_cylinder(bm, 0.09, 0.07, along_y((0.0, s * 0.735, AXLE_Z)), STEEL, segments=12, bev=0.01)
        add_cylinder(bm, 0.07, 0.01, along_y((0.0, s * (HUB_Y - 0.005), AXLE_Z)), STEEL, segments=12)
    return finish_mesh(bm, "SM_Vozik_naprava")


def build_fender():
    # blatnik lavy (+Y), vzpery na bok ramu
    bm = bmesh.new()
    r0, r1, yi, yo = 0.36, 0.375, 0.69, 0.91
    sweep_profile(bm, [(r0, yi), (r1, yi), (r1, yo - 0.02), (r0, yo - 0.02)], 10.0, 170.0, 9, FENDER)
    sweep_profile(bm, [(0.31, yo - 0.02), (r1, yo - 0.02), (r1, yo - 0.015), (r1 - 0.015, yo), (0.31, yo)],
                  10.0, 170.0, 9, FENDER)
    sweep_profile(bm, [(r1 - 0.002, 0.775), (r1 + 0.008, 0.785), (r1 + 0.008, 0.815), (r1 - 0.002, 0.825)],
                  14.0, 166.0, 9, FENDER)
    shift(bm, (0.0, 0.0, AXLE_Z))
    for a, sx in ((25.0, 1.0), (155.0, -1.0)):
        p = ((r0 + 0.01) * math.cos(math.radians(a)), yi + 0.03, AXLE_Z + (r0 + 0.01) * math.sin(math.radians(a)))
        add_rod(bm, p, (sx * 0.20, 0.494, 0.43), 0.014, STEEL, segments=6)
    add_box(bm, (0.50, 0.008, 0.07), (0.0, 0.490, 0.43), FRAME, bev=0.002)
    for x in (-0.20, 0.20):
        add_cylinder(bm, 0.009, 0.008, along_y((x, 0.497, 0.43)), CHROME, segments=6)
    return bm


def build_jockey_holder():
    # objimka na oji, vonkajsia rurka a klucka hore
    bm = bmesh.new()
    x, y = JOCKEY.x, JOCKEY.y
    dy, dz = drawbar_y(x)
    add_cylinder(bm, 0.032, 0.42, along_z((x, y, 0.57)), STEEL, segments=10)
    add_box(bm, (0.09, y - dy + 0.05, 0.08), (x, (y + dy) * 0.5, dz), STEEL, bev=0.01)
    add_rod(bm, (x, y + 0.03, dz), (x, y + 0.09, dz), 0.008, STEEL)
    add_rod(bm, (x - 0.035, y + 0.09, dz), (x + 0.035, y + 0.09, dz), 0.01, DARK)
    add_cylinder(bm, 0.042, 0.03, along_z((x, y, 0.795)), DARK, segments=10)
    add_rod(bm, (x, y, 0.815), (x + 0.13, y, 0.815), 0.01, STEEL)
    add_cylinder(bm, 0.018, 0.06, along_z((x + 0.13, y, 0.85)), DARK, segments=8)
    return finish_mesh(bm, "SM_Vozik_drziak_kolieska")


# ---------------------------------------------------------------------------
# Pohyblive diely (pivot v klbe)
# ---------------------------------------------------------------------------

def build_wheel():
    # koleso 13": pivot na dosadacej ploche disku, vonkajsia strana +Y
    bm = bmesh.new()
    yc, width = 0.01, 0.165
    add_ring(bm, 0.278, 0.185, width, yc, TIRE, 20, bev=0.035)
    for s in SIDES_LR:
        add_ring(bm, WHEEL_R, 0.27, 0.045, yc + s * 0.035, TIRE, 20)
        add_ring(bm, 0.255, 0.245, 0.006, yc + s * (width * 0.5 - 0.001), DARK, 20)
        add_ring(bm, 0.197, 0.18, 0.012, yc + s * 0.066, RIM, 16)
    add_ring(bm, 0.185, 0.175, 0.14, yc, RIM, 16)
    add_cylinder(bm, 0.176, 0.012, along_y((0.0, 0.006, 0.0)), RIM, segments=16)
    ring_of(bm, 8, 0.125, 0.013, 0.024, 0.004, DARK, segments=8, offset=0.5)
    ring_of(bm, 4, 0.072, 0.018, 0.01, 0.012, CHROME)
    add_cylinder(bm, 0.055, 0.035, along_y((0.0, 0.028, 0.0)), CHROME, segments=10, bev=0.01)
    return finish_mesh(bm, "SM_Vozik_koleso")


def build_jockey_wheel():
    # noha oporneho kolieska s vidlicou a koleckom: pivot hore na osi nohy, posuva sa hore/dole (Z)
    bm = bmesh.new()
    leg = JOCKEY.z - 0.20
    add_cylinder(bm, 0.024, leg, along_z((0.0, 0.0, -leg * 0.5)), STEEL, segments=8)
    add_box(bm, (0.12, 0.10, 0.015), (0.02, 0.0, -leg - 0.005), STEEL, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.10, 0.008, 0.16), (0.045, s * 0.036, -leg - 0.08), STEEL, bev=0.003)
    wc = (0.06, 0.0, -JOCKEY.z + 0.09)
    add_at(bm, wc, add_ring, 0.09, 0.05, 0.05, 0.0, TIRE, 12, bev=0.012)
    add_at(bm, wc, add_ring, 0.05, 0.015, 0.055, 0.0, RIM, 10)
    add_cylinder(bm, 0.01, 0.09, along_y(wc), CHROME, segments=6)
    return finish_mesh(bm, "SM_Vozik_oporne_koliesko")


def build_piston_body():
    # valec piestu: pivot v spodnom oku na rame, telo smeruje do -X (ku korbe)
    bm = bmesh.new()
    add_cylinder(bm, 0.028, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_cylinder(bm, 0.038, 0.375, along_x((-0.2125, 0.0, 0.0)), FRAME, segments=10, bev=0.006)
    add_cylinder(bm, 0.042, 0.02, along_x((-0.39, 0.0, 0.0)), STEEL, segments=10)
    add_cylinder(bm, 0.042, 0.02, along_x((-0.04, 0.0, 0.0)), STEEL, segments=10)
    add_cylinder(bm, 0.01, 0.03, along_z((-0.07, 0.0, 0.045)), STEEL, segments=6)
    return finish_mesh(bm, "SM_Vozik_piest_valec")


def build_piston_rod():
    # piestnica: pivot v hornom oku pod korbou, smeruje do +X (do valca)
    bm = bmesh.new()
    add_cylinder(bm, 0.022, 0.045, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_cylinder(bm, 0.016, 0.38, along_x((0.21, 0.0, 0.0)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Vozik_piestnica")


# ---------------------------------------------------------------------------
# Korba a co je na nej (pivot = cap vyklapania TILT)
# ---------------------------------------------------------------------------

XB, XF = BOX_BACK - TILT.x, BOX_FRONT - TILT.x


def add_wall(bm, size, center, along):
    # stena: plech, tmavy pruh, horny lem a rebro (along = "x" pre bocnicu, "y" pre celo)
    length, height = size
    cx, cy, cz = center
    t = 0.024
    if along == "x":
        dims = lambda l, th, h: (l, th, h)
    else:
        dims = lambda l, th, h: (th, l, h)
    add_box(bm, dims(length, t, height), (cx, cy, cz), PAINT, bev=0.004)
    add_box(bm, dims(length - 0.01, t + 0.006, 0.06), (cx, cy, cz + 0.01), PAINT2, bev=0.003)
    add_box(bm, dims(length, t + 0.012, 0.035), (cx, cy, cz + height * 0.5 - 0.0175), PAINT, bev=0.006)
    add_box(bm, dims(length - 0.02, t + 0.008, 0.012), (cx, cy, cz - height * 0.30), PAINT, bev=0.003)


def build_box():
    bm = bmesh.new()
    h = BOX_HALF
    length, xc = XF - XB, (XB + XF) * 0.5
    # ram korby pod podlahou (pozdlzne nosniky lezia na rame vozika)
    for s in SIDES_LR:
        add_box(bm, (length, 0.06, 0.08), (xc, s * (h - 0.03), 0.04), FRAME, bev=0.006)
        add_box(bm, (length - 0.06, 0.06, 0.08), (xc, s * RAIL_Y, 0.04), FRAME, bev=0.006)
    for x in (XB + 0.03, -0.35, PISTON_TOP.x, 1.00, XF - 0.03):
        add_box(bm, (0.05, 2.0 * h - 0.10, 0.07), (x, 0.0, 0.036), FRAME, bev=0.005)
    # podlaha z dosiek
    floor_x0 = XB + 0.035
    add_box(bm, (XF - 0.01 - floor_x0, 2.0 * h - 0.02, 0.01), ((floor_x0 + XF - 0.01) * 0.5, 0.0, 0.085), DARK)
    for i in range(7):
        y = -h + 0.04 + 0.085 + i * 0.18
        add_box(bm, (XF - 0.02 - floor_x0, 0.17, 0.012), ((floor_x0 + XF - 0.02) * 0.5, y, 0.094), FLOOR, bev=0.003)
    # rohove stlpiky, bocnice, predne celo
    for x in (XB + 0.03, XF - 0.03):
        for s in SIDES_LR:
            add_box(bm, (0.06, 0.06, WALL_TOP + 0.03), (x, s * (h - 0.03), (WALL_TOP + 0.03) * 0.5), DARK, bev=0.006)
            add_box(bm, (0.07, 0.07, 0.015), (x, s * (h - 0.03), WALL_TOP + 0.035), DARK, bev=0.004)
    wall_h = WALL_TOP - 0.08
    for s in SIDES_LR:
        add_wall(bm, (length - 0.12, wall_h), (xc, s * (h - 0.012), 0.08 + wall_h * 0.5), "x")
        add_box(bm, (0.05, 0.034, wall_h), (xc, s * (h - 0.012), 0.08 + wall_h * 0.5), PAINT, bev=0.006)
        add_box(bm, (0.04, 0.02, wall_h - 0.04), (xc, s * (h - 0.034), 0.08 + wall_h * 0.5), PAINT2, bev=0.004)
        # obrysove svetla na boku, zamky zadneho cela
        for x in (XB + 0.12, XF - 0.12):
            add_box(bm, (0.06, 0.008, 0.032), (x, s * (h + 0.004), 0.04), DARK, bev=0.002)
            add_box(bm, (0.045, 0.006, 0.022), (x, s * (h + 0.009), 0.04), LAMP_OR, bev=0.002)
        add_box(bm, (0.02, 0.05, 0.05), (XB - 0.005, s * (h - 0.03), 0.44), DARK, bev=0.004)
        add_cylinder(bm, 0.008, 0.07, along_y((XB - 0.012, s * (h - 0.06), 0.44)), CHROME, segments=6)
        # panty cela, cap vyklapania, drziak piestu
        add_cylinder(bm, 0.015, 0.06, along_y((GATE_HINGE.x, s * 0.50, GATE_HINGE.z)), STEEL, segments=8)
        add_cylinder(bm, 0.025, 0.05, along_y((0.0, s * RAIL_Y, 0.0)), STEEL, segments=10)
        add_box(bm, (0.08, 0.008, 0.05), (PISTON_TOP.x, s * 0.035, -0.005), FRAME, bev=0.002)
    add_wall(bm, (2.0 * h - 0.12, wall_h), (XF - 0.012, 0.0, 0.08 + wall_h * 0.5), "y")
    add_cylinder(bm, 0.01, 0.08, along_y(PISTON_TOP), CHROME, segments=6)
    return finish_mesh(bm, "SM_Vozik_korba")


def build_rear_light():
    # zadne svetlo lave (pod korbou vzadu): oranzove von, cervene, biele dnu
    bm = bmesh.new()
    add_box(bm, (0.05, 0.22, 0.07), (XB - 0.025, 0.50, 0.02), DARK, bev=0.008)
    for y, width, mat in ((0.585, 0.045, LAMP_OR), (0.50, 0.10, LAMP_RED), (0.415, 0.045, LAMP_WHITE)):
        add_box(bm, (0.008, width, 0.05), (XB - 0.052, y, 0.02), mat, bev=0.002)
    return bm


def build_plate_holder():
    bm = bmesh.new()
    add_box(bm, (0.008, 0.42, 0.11), (XB - 0.006, 0.0, -0.03), DARK, bev=0.003)
    add_box(bm, (0.006, 0.40, 0.09), (XB - 0.012, 0.0, -0.03), WHITE, bev=0.002)
    add_box(bm, (0.03, 0.10, 0.025), (XB - 0.02, 0.0, 0.04), DARK, bev=0.004)
    add_box(bm, (0.004, 0.07, 0.01), (XB - 0.036, 0.0, 0.034), LAMP_WHITE)
    return finish_mesh(bm, "SM_Vozik_drziak_SPZ")


def build_tailgate():
    # zadne celo: pivot v pante dole vzadu, otvara sa okolo Y (o -90 st. = lezi ako najazd)
    bm = bmesh.new()
    half = BOX_HALF - 0.065
    gate_h = WALL_TOP - GATE_HINGE.z
    add_wall(bm, (2.0 * half, gate_h), (0.015, 0.0, gate_h * 0.5), "y")
    for s in SIDES_LR:
        add_box(bm, (0.02, 0.06, 0.03), (-0.005, s * (half - 0.08), gate_h - 0.06), DARK, bev=0.004)
        for y in (0.40, 0.10):
            add_cylinder(bm, 0.015, 0.06, along_y((0.0, s * y, 0.0)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Vozik_zadne_celo")


# ---------------------------------------------------------------------------
# Scena: hotovy vozik (pohyblive diely, animacia) + rozlozene diely, export
# ---------------------------------------------------------------------------

def get_material(name, color, metallic, roughness, emission):
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
        if emission > 0.0:
            for key in ("Emission Color", "Emission"):
                if key in bsdf.inputs:
                    bsdf.inputs[key].default_value = color
                    break
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def export_mesh(coll, mesh, file_name):
    temp = bpy.data.objects.new(file_name, mesh)
    coll.objects.link(temp)
    select_only(temp)
    path = os.path.join(EXPORT_DIR, file_name + ".fbx")
    try:
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                                 apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE")
    except Exception as error:
        print("FBX sa nepodarilo ulozit:", path, error)
    bpy.data.objects.remove(temp, do_unlink=True)


def join_meshes(name, meshes):
    # spoji viac dielov do jedneho (vsetky su v rovnakych suradniciach)
    bm = bmesh.new()
    for mesh in meshes:
        bm.from_mesh(mesh)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def bounds(mesh):
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def child_collection(parent, name):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if parent.children.get(coll.name) is None:
        parent.children.link(coll)
    return coll


def clear_collection(coll):
    for sub in [coll] + list(coll.children):
        for obj in list(sub.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.get("vozik"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_Vozik"):
            bpy.data.curves.remove(curve)


def add_label(coll, text, location, mat):
    curve = bpy.data.curves.new("Menovka_" + text.split("\n")[0], "FONT")
    curve.body = text
    curve.size = 0.07
    curve.align_x = "CENTER"
    curve.materials.append(mat)
    obj = bpy.data.objects.new(curve.name, curve)
    coll.objects.link(obj)
    obj.location = location


def new_object(coll, name, data, location=(0.0, 0.0, 0.0), parent=None, rotation=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = [math.radians(a) for a in rotation]
    return obj


def key(obj, path, index, frames):
    # kluce animacie: frames = [(snimka, hodnota), ...]
    for frame, value in frames:
        getattr(obj, path)[index] = value
        obj.keyframe_insert(data_path=path, index=index, frame=frame)


def track(obj, target, axis):
    con = obj.constraints.new("DAMPED_TRACK")
    con.target = target
    con.track_axis = axis


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    whole = child_collection(coll, "Vozik_celok")
    kit = child_collection(coll, "Vozik_diely")
    clear_collection(coll)
    mats = [get_material(*m) for m in MATERIALS]

    # samostatne diely
    parts = {}

    def put(mesh):
        parts[mesh.name[3:]] = mesh

    put(build_frame())
    put(build_drawbar())
    put(build_coupling())
    put(build_axle())
    fender = build_fender()
    fender_p = mirror_y(fender)
    put(finish_mesh(fender, "SM_Vozik_blatnik_L"))
    put(finish_mesh(fender_p, "SM_Vozik_blatnik_P"))
    put(build_jockey_holder())
    put(build_wheel())
    put(build_jockey_wheel())
    put(build_piston_body())
    put(build_piston_rod())
    put(build_box())
    light = build_rear_light()
    light_p = mirror_y(light)
    put(finish_mesh(light, "SM_Vozik_svetlo_L"))
    put(finish_mesh(light_p, "SM_Vozik_svetlo_P"))
    put(build_plate_holder())
    put(build_tailgate())
    # hotovy vozik: pevne diely spojene do podvozku, svetla a SPZ do korby
    put(join_meshes("SM_Vozik_podvozok_komplet", [parts[k] for k in (
        "Vozik_ram", "Vozik_oje", "Vozik_spojka", "Vozik_naprava", "Vozik_blatnik_L", "Vozik_blatnik_P",
        "Vozik_drziak_kolieska")]))
    put(join_meshes("SM_Vozik_korba_komplet", [parts[k] for k in (
        "Vozik_korba", "Vozik_svetlo_L", "Vozik_svetlo_P", "Vozik_drziak_SPZ")]))
    for key_name, mesh in parts.items():
        base = "SM_" + key_name
        if mesh.name != base:
            old = bpy.data.meshes.get(base)
            if old is not None and old.users == 0:
                bpy.data.meshes.remove(old)
                mesh.name = base
        mesh["vozik"] = 1
        if not mesh.materials:
            for mat in mats:
                mesh.materials.append(mat)

    # --- hotovy vozik s pohyblivymi dielmi ---
    chassis = new_object(whole, "Vozik", parts["Vozik_podvozok_komplet"])
    box = new_object(whole, "Vozik_korba", parts["Vozik_korba_komplet"], TILT, chassis)
    gate = new_object(whole, "Vozik_zadne_celo", parts["Vozik_zadne_celo"], GATE_HINGE, box)
    for s, name in ((1.0, "Vozik_koleso_L"), (-1.0, "Vozik_koleso_P")):
        new_object(whole, name, parts["Vozik_koleso"], (0.0, s * HUB_Y, AXLE_Z), chassis, (0.0, 0.0, 0.0 if s > 0 else 180.0))
    jockey = new_object(whole, "Vozik_oporne_koliesko", parts["Vozik_oporne_koliesko"], JOCKEY, chassis)
    cyl = new_object(whole, "Vozik_piest_valec", parts["Vozik_piest_valec"], PISTON_BASE, chassis)
    rod = new_object(whole, "Vozik_piestnica", parts["Vozik_piestnica"], PISTON_TOP, box)
    aim_top = new_object(whole, "Vozik_piest_ciel_hore", None, PISTON_TOP, box)
    aim_low = new_object(whole, "Vozik_piest_ciel_dole", None, PISTON_BASE, chassis)
    for empty in (aim_top, aim_low):
        empty.empty_display_size = 0.05
        empty.hide_render = True
    track(cyl, aim_top, "TRACK_NEGATIVE_X")
    track(rod, aim_low, "TRACK_X")

    # animacia: otvor celo, vyklop korbu, vrat spat, zdvihni koliesko
    gate_open, tilt = -math.radians(GATE_DEG), -math.radians(TILT_DEG)
    key(gate, "rotation_euler", 1, [(1, 0.0), (15, 0.0), (45, gate_open), (175, gate_open), (205, 0.0)])
    key(box, "rotation_euler", 1, [(1, 0.0), (55, 0.0), (95, tilt), (135, tilt), (170, 0.0)])
    key(jockey, "location", 2, [(1, JOCKEY.z), (210, JOCKEY.z), (240, JOCKEY.z + JOCKEY_LIFT), (260, JOCKEY.z + JOCKEY_LIFT)])
    scene.frame_start, scene.frame_end = 1, 260

    # --- rozlozene diely (katalog vedla) ---
    rows = [
        ["Vozik_ram", "Vozik_oje", "Vozik_spojka", "Vozik_naprava", "Vozik_blatnik_L", "Vozik_blatnik_P",
         "Vozik_drziak_kolieska", "Vozik_oporne_koliesko", "Vozik_koleso"],
        ["Vozik_korba", "Vozik_zadne_celo", "Vozik_svetlo_L", "Vozik_svetlo_P", "Vozik_drziak_SPZ",
         "Vozik_piest_valec", "Vozik_piestnica"],
    ]
    lines = ["Vozik - rozmery dielov (dlzka X x sirka Y x vyska Z) v metroch:", ""]
    y_cursor = 2.4
    for keys in rows:
        depth = max(bounds(parts[k])[1][1] - bounds(parts[k])[1][0] for k in keys)
        row_y = y_cursor + depth * 0.5
        x = -1.0
        for k in keys:
            mesh = parts[k]
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            slot = max(x1 - x0, 0.9)
            new_object(kit, k.replace("Vozik_", "Diel_"), mesh,
                       (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0))
            add_label(kit, "%s\n%.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0),
                      (x + slot * 0.5, row_y - depth * 0.5 - 0.18, 0.001), mats[DARK])
            lines.append("%-26s %.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0))
            x += slot + 0.35
        y_cursor += depth + 0.8
    for k in ("Vozik_podvozok_komplet", "Vozik_korba_komplet"):
        (x0, x1), (y0, y1), (z0, z1) = bounds(parts[k])
        lines.append("%-26s %.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0))

    lines += [
        "",
        "SKLADANIE (pociatok 0,0,0 = zem pod osou kolies, predok = +X, lava strana = +Y)",
        "  Pevne diely (ram, oje, spojka, naprava, blatniky, drziak kolieska) maju pivot v pociatku - daj ich na 0,0,0.",
        "  Korba: pivot v cape vyklapania (%.2f, 0, %.2f). Svetla a drziak SPZ maju ten isty pivot ako korba." % (TILT.x, TILT.z),
        "         Vyklopenie = otocenie okolo Y o 0 az -%g st. (zadok ide dole)." % TILT_DEG,
        "  Zadne celo: pivot v pante (%.2f, 0, %.2f) od pivotu korby. Otvorenie = otocenie okolo Y o 0 az -%g st." % (
            GATE_HINGE.x, GATE_HINGE.z, GATE_DEG),
        "         Pri vyklopenej korbe lezi otvorene celo ako najazd az po zem.",
        "  Koleso: pivot na dosadacej ploche disku, (0, +-%.2f, %.2f), prave otoc o 180 st. okolo Z, toci sa okolo Y." % (HUB_Y, AXLE_Z),
        "  Oporne koliesko: pivot hore na nohe (%.2f, %.2f, %.2f), zdvihne sa posunom o +%.2f v Z." % (
            JOCKEY.x, JOCKEY.y, JOCKEY.z, JOCKEY_LIFT),
        "  Piest: valec ma pivot v spodnom oku na rame (%.2f, 0, %.2f) a mieri osou -X na horne oko." % (PISTON_BASE.x, PISTON_BASE.z),
        "         Piestnica ma pivot v hornom oku pod korbou (%.2f, 0, %.3f od pivotu korby) a mieri osou +X na spodne oko." % (
            PISTON_TOP.x, PISTON_TOP.z),
        "         (V Blenderi to robia obmedzenia Damped Track, v Unreali staci oba diely natocit k sebe - Find Look at Rotation.)",
        "  Gula tahaca patri do bodu (2.20, 0, 0.43).",
    ]

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for k, mesh in parts.items():
            export_mesh(coll, mesh, "SM_" + k)
        with open(os.path.join(EXPORT_DIR, "Vozik.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    print("\n".join(lines))


main()
