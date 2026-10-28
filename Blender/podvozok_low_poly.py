# Stylizovany low poly podvozok kamiona pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Podvozok" so zlozenym podvozkom a dalsimi variantmi vedla neho:
#   Ram                     - rebrinovy ram (dva C-nosniky, priecniky, zadny naraznik, tazne oko)
#   Naprava_predna          - riadena naprava s pruzinami, tlmicmi, bubnami a riadenim
#   Naprava_zadna           - hnana naprava s diferencialom, pruzinami a tlmicmi
#   Koleso_predne           - kamionove koleso 105 cm
#   Koleso_dvojite          - dvojmontaz (dve kolesa naraz) na zadnu napravu
#   Blatnik_predny / _zadny - bez svetiel aj so svetlami (_svetla), L = lava strana (+Y), P = prava (-Y)
#   Vzduchojemy             - dva vzduchojemy na drziaku (ako na obrazku)
#   Kardan_1m / 1_5m / 2m   - kardan s krizovymi klbmi a posuvnou castou
# Pri prehravani animacie (medzernik) sa tocia kolesa aj kardan.
# Pivoty: ram v strede spodku, napravy v osi kolies, kolesa a blatniky v strede kolesa,
#         kardan v strede prednej priruby, vzduchojemy na doske, ktora dosadne na ram.
# Do priecinka Podvozok v domovskom priecinku ulozi FBX kazdeho dielu a subor Podvozok.txt s rozmermi.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Podvozok"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Podvozok")

# (nazov, farba, kovovost, drsnost, svietivost)
MATERIALS = [
    ("PV_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0),
    ("PV_Ocel", (0.45, 0.46, 0.48, 1.0), 0.7, 0.40, 0.0),
    ("PV_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0),
    ("PV_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0),
    ("PV_Disk", (0.80, 0.80, 0.77, 1.0), 0.3, 0.35, 0.0),
    ("PV_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0),
    ("PV_Plast", (0.025, 0.025, 0.028, 1.0), 0.0, 0.60, 0.0),
    ("PV_Vzduchojem", (0.30, 0.32, 0.36, 1.0), 0.5, 0.40, 0.0),
    ("PV_Kardan", (0.58, 0.59, 0.61, 1.0), 0.7, 0.35, 0.0),
    ("PV_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0),
    ("PV_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0),
    ("PV_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0),
    ("PV_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0),
]
FRAME, STEEL, CHROME, TIRE, RIM, DARK, PLASTIC, AIR, SHAFT, LAMP_OR, LAMP_RED, LAMP_WHITE, RED = range(13)
SIDES_LR = (-1.0, 1.0)

# rozmery zlozeneho podvozku (m)
WHEEL_R = 0.525          # polomer kolesa
FRAME_Z = 0.86           # spodok ramu nad zemou
FRAME_LEN = 5.6          # dlzka ramu
RAIL_Y = 0.43            # vonkajsia strana nosnika ramu od stredu
RAIL_H = 0.26            # vyska nosnika ramu
FRONT_X, REAR_X = 1.95, -1.55   # napravy (rozvor 3.5 m)
FRONT_TRACK = 1.00       # stred predneho kolesa od stredu
REAR_TRACK = 0.965       # stred dvojmontaze od stredu
HANG = FRAME_Z - WHEEL_R # spodok ramu nad osou kolies


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


def octagon(radius, cy, cz):
    # osemuholnik okolo osi X (vrcholy hore, dole a na bokoch)
    return [(cy + radius * math.sin(2.0 * math.pi * k / 8), cz - radius * math.cos(2.0 * math.pi * k / 8)) for k in range(8)]


def add_band_x(bm, outer, inner, x0, x1, mat):
    # uzavrety pas okolo osi X (obrys v rovine YZ), napr. pas okolo vzduchojemu
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


def add_ring_loop(bm, center, radius, mat, rod_r=0.012, steps=8):
    # oko z kratkych tyciek (lezi vodorovne)
    pts = [(center[0] + radius * math.cos(2.0 * math.pi * k / steps),
            center[1] + radius * math.sin(2.0 * math.pi * k / steps), center[2]) for k in range(steps)]
    for k in range(steps):
        add_rod(bm, pts[k], pts[(k + 1) % steps], rod_r, mat, segments=6)


def mirror_y(bm):
    # zrkadlova kopia na druhu stranu (L -> P)
    copy = bm.copy()
    bmesh.ops.scale(copy, vec=(1.0, -1.0, 1.0), verts=copy.verts[:])
    bmesh.ops.reverse_faces(copy, faces=copy.faces[:])
    return copy


# ---------------------------------------------------------------------------
# Kolesa: pivot v strede, os otacania Y, vonkajsia strana na +Y
# ---------------------------------------------------------------------------

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


def add_tread(bm, radius, depth, rows, count):
    # bloky dezenu po obvode: rows = [(posun_Y, sirka_bloku, posun_polovicu_kroku)]
    pitch = 2.0 * math.pi * radius / count
    for y, width, shift in rows:
        for k in range(count):
            a = math.degrees(2.0 * math.pi * (k + (0.5 if shift else 0.0)) / count)
            frame = Matrix.Rotation(math.radians(a), 4, "Y")
            add_box(bm, (pitch * 0.55, width, depth), (0.0, y, radius - depth * 0.5), TIRE, bev=depth * 0.3, frame=frame)


def ring_of(bm, count, radius, y, r, depth, mat, segments=6, offset=0.0):
    for k in range(count):
        a = 2.0 * math.pi * (k + offset) / count
        add_cylinder(bm, r, depth, along_y((radius * math.cos(a), y, radius * math.sin(a))), mat, segments=segments)


def add_truck_tire(bm, y):
    # pneumatika 105 cm s dezenom a rafikom (stred v y)
    width, tread = 0.30, 0.018
    body = WHEEL_R - tread
    add_ring(bm, body, 0.285, width, y, TIRE, 24, bev=width * 0.2)
    for s in SIDES_LR:
        add_ring(bm, body * 0.88, body * 0.82, 0.006, y + s * (width * 0.5 - 0.001), DARK, 24)
    # cestny dezen: stredne a krajne rebra po obvode, na krajnych rebrach zarezy
    for dy, bev in ((0.035, 0.0), (0.095, 0.01)):
        for s in SIDES_LR:
            add_ring(bm, WHEEL_R, body - 0.01, 0.05, y + s * dy, TIRE, 24, bev=bev)
    add_tread(bm, WHEEL_R - 0.004, tread - 0.004, [(y - 0.128, 0.03, False), (y + 0.128, 0.03, True)], 24)
    add_ring(bm, 0.285, 0.27, width - 0.03, y, RIM, 20)
    for s in SIDES_LR:
        add_ring(bm, 0.30, 0.275, 0.015, y + s * (width * 0.5 - 0.02), RIM, 20)


def build_wheel_front():
    # predne koleso: disk vonku (+Y), naboj s chromovymi maticami
    bm = bmesh.new()
    out = 0.15
    add_truck_tire(bm, 0.0)
    add_cylinder(bm, 0.27, 0.02, along_y((0.0, out - 0.06, 0.0)), RIM, segments=20)
    ring_of(bm, 10, 0.205, out - 0.048, 0.035, 0.006, DARK, segments=10, offset=0.5)
    add_cylinder(bm, 0.12, 0.06, along_y((0.0, out - 0.05, 0.0)), STEEL, segments=16, bev=0.008)
    ring_of(bm, 10, 0.095, out - 0.012, 0.011, 0.025, CHROME)
    add_cone(bm, 0.045, 0.07, 0.05, along_y((0.0, out - 0.03, 0.0)), CHROME, segments=12, bev=0.006)
    return finish_mesh(bm, "SM_Koleso_predne")


def build_wheel_dual():
    # dvojmontaz: dve kolesa s diskami chrbtom k sebe, pivot v strede medzi nimi
    bm = bmesh.new()
    for s in SIDES_LR:
        add_truck_tire(bm, s * 0.165)
        add_cylinder(bm, 0.27, 0.02, along_y((0.0, s * 0.012, 0.0)), RIM, segments=20)
        ring_of(bm, 10, 0.205, s * 0.024, 0.035, 0.006, DARK, segments=10, offset=0.5)
    add_cylinder(bm, 0.12, 0.06, along_y((0.0, 0.05, 0.0)), STEEL, segments=16, bev=0.008)
    ring_of(bm, 10, 0.095, 0.088, 0.011, 0.025, CHROME)
    add_cone(bm, 0.045, 0.07, 0.05, along_y((0.0, 0.105, 0.0)), CHROME, segments=12, bev=0.006)
    return finish_mesh(bm, "SM_Koleso_dvojite")


# ---------------------------------------------------------------------------
# Kardan: pivot v strede prednej priruby, hriadel ide dozadu (-X), toci sa okolo X
# ---------------------------------------------------------------------------

def add_cross_joint(bm, x0, sign):
    # priruba + vidlica + kriz klbu; x0 = plocha priruby, sign = smer k stredu hriadela
    def x(d):
        return x0 + sign * d

    add_cylinder(bm, 0.075, 0.02, along_x((x(0.01), 0.0, 0.0)), STEEL, segments=12, bev=0.004)
    for k in range(6):
        a = 2.0 * math.pi * (k + 0.5) / 6
        add_cylinder(bm, 0.01, 0.012, along_x((x(0.026), 0.055 * math.cos(a), 0.055 * math.sin(a))), CHROME, segments=6)
    add_cylinder(bm, 0.04, 0.03, along_x((x(0.035), 0.0, 0.0)), STEEL, segments=10)
    for s in SIDES_LR:
        add_box(bm, (0.07, 0.045, 0.025), (x(0.075), 0.0, s * 0.052), STEEL, bev=0.006)   # vidlica priruby
        add_box(bm, (0.07, 0.025, 0.045), (x(0.105), s * 0.052, 0.0), STEEL, bev=0.006)   # vidlica hriadela
    add_cylinder(bm, 0.016, 0.13, along_z((x(0.09), 0.0, 0.0)), STEEL, segments=6)
    add_cylinder(bm, 0.016, 0.13, along_y((x(0.09), 0.0, 0.0)), STEEL, segments=6)
    for s in SIDES_LR:
        add_cylinder(bm, 0.022, 0.02, along_z((x(0.09), 0.0, s * 0.068)), CHROME, segments=8)
        add_cylinder(bm, 0.022, 0.02, along_y((x(0.09), s * 0.068, 0.0)), CHROME, segments=8)
    add_cylinder(bm, 0.045, 0.03, along_x((x(0.135), 0.0, 0.0)), STEEL, segments=10)


def build_kardan(name, length):
    bm = bmesh.new()
    add_cross_joint(bm, 0.0, -1.0)
    add_cross_joint(bm, -length, 1.0)
    # posuvna cast s mazacou hlavickou a gumovou manzetou
    add_cylinder(bm, 0.05, 0.19, along_x((-0.245, 0.0, 0.0)), STEEL, segments=10, bev=0.006)
    add_cylinder(bm, 0.008, 0.02, along_z((-0.22, 0.0, 0.055)), CHROME, segments=6)
    for k in range(3):
        add_cylinder(bm, 0.047 if k % 2 == 0 else 0.04, 0.025, along_x((-0.352 - k * 0.025, 0.0, 0.0)), TIRE, segments=10)
    # rurka hriadela so zvarmi a vyvazovacim zavazim
    x0, x1 = -0.39, -(length - 0.15)
    add_cylinder(bm, 0.044, x0 - x1, along_x(((x0 + x1) * 0.5, 0.0, 0.0)), SHAFT, segments=10)
    for x in (x0, x1):
        add_cylinder(bm, 0.05, 0.016, along_x((x, 0.0, 0.0)), STEEL, segments=10)
    add_box(bm, (0.05, 0.03, 0.012), ((x0 + x1) * 0.5, 0.0, 0.046), STEEL, bev=0.003)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Ram: pivot v strede spodku, predok = +X
# ---------------------------------------------------------------------------

CROSS_X = (2.68, 1.30, 0.20, -0.80, -1.95)


def build_frame():
    bm = bmesh.new()
    length, h = FRAME_LEN, RAIL_H
    # dva C-nosniky: stojina vonku, pasnice smeruju dnu
    for s in SIDES_LR:
        add_box(bm, (length, 0.014, h), (0.0, s * (RAIL_Y - 0.007), h * 0.5), FRAME, bev=0.004)
        for z in (0.008, h - 0.008):
            add_box(bm, (length, 0.075, 0.016), (0.0, s * (RAIL_Y - 0.0375), z), FRAME, bev=0.004)

    # priecniky so stycnikmi a skrutkami
    for x in CROSS_X:
        add_box(bm, (0.10, 2.0 * (RAIL_Y - 0.014), 0.15), (x, 0.0, h * 0.55), FRAME, bev=0.012)
        add_box(bm, (0.13, 2.0 * (RAIL_Y - 0.09), 0.02), (x, 0.0, h * 0.55 + 0.08), FRAME, bev=0.004)
        for s in SIDES_LR:
            add_box(bm, (0.28, 0.008, h - 0.05), (x, s * (RAIL_Y - 0.018), h * 0.5), FRAME, bev=0.003)
            for dx in (-0.10, 0.0, 0.10):
                for dz in (-0.07, 0.07):
                    add_cylinder(bm, 0.011, 0.01, along_y((x + dx, s * (RAIL_Y + 0.004), h * 0.5 + dz)), STEEL, segments=6)

    # predok: cela doska s taznym okom
    front = length * 0.5
    add_box(bm, (0.02, 2.0 * RAIL_Y, h * 0.8), (front + 0.01, 0.0, h * 0.5), FRAME, bev=0.005)
    for s in SIDES_LR:
        for dz in (-0.07, 0.07):
            add_cylinder(bm, 0.012, 0.012, along_x((front + 0.024, s * 0.30, h * 0.5 + dz)), STEEL, segments=6)
    add_box(bm, (0.12, 0.08, 0.08), (front + 0.07, 0.0, h * 0.5), STEEL, bev=0.012)
    add_ring_loop(bm, (front + 0.175, 0.0, h * 0.5), 0.05, STEEL, rod_r=0.018)

    # zadok: siroky naraznik s odrazkami
    back = -length * 0.5
    add_box(bm, (0.14, 2.0 * RAIL_Y + 0.20, 0.20), (back + 0.05, 0.0, h * 0.5), FRAME, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.008, 0.12, 0.045), (back - 0.022, s * 0.40, h * 0.5), RED, bev=0.003)
        for dz in (-0.05, 0.05):
            add_cylinder(bm, 0.012, 0.012, along_x((back - 0.022, s * 0.20, h * 0.5 + dz)), STEEL, segments=6)
    return finish_mesh(bm, "SM_Ram")


# ---------------------------------------------------------------------------
# Napravy: pivot v osi kolies (v strede), spodok ramu je HANG nad pivotom
# ---------------------------------------------------------------------------

SPRING_Y = 0.40


def add_leaf_spring(bm, yc, half, z0, k, leaves=4):
    # listova pruzina: z0 = stred hlavneho listu, k = prehnutie, konce s okami
    w = 0.08
    for i in range(leaves):
        f = 1.0 - 0.2 * i
        path = []
        for j in range(7):
            x = half * f * (j / 3.0 - 1.0)
            path.append((x, z0 - i * 0.02 + k * x * x))
        add_extruded(bm, beam_outline(path, [0.009] * 7, cap=0.3), yc - w * 0.5, yc + w * 0.5, "XZ", FRAME, bev=0.003)
    ze = z0 + k * half * half
    for s in SIDES_LR:
        x = s * half
        add_cylinder(bm, 0.032, w + 0.01, along_y((x, yc, ze)), FRAME, segments=8)
        add_cylinder(bm, 0.013, w + 0.12, along_y((x, yc, ze)), CHROME, segments=6)
        # zaves pruziny na ram: dve bocnice a doska pod ramom
        for d in SIDES_LR:
            add_box(bm, (0.09, 0.012, HANG - ze + 0.03), (x, yc + d * 0.052, (HANG + ze - 0.03) * 0.5), FRAME, bev=0.004)
        add_box(bm, (0.16, 0.14, 0.02), (x, yc, HANG - 0.01), FRAME, bev=0.004)
    # stredna spona listov
    add_box(bm, (0.03, w + 0.01, 0.10), (0.0, yc, z0 - 0.03), STEEL, bev=0.005)
    return z0 + 0.009


def add_u_bolts(bm, yc, z_top, z_bottom, dx):
    # strmene: horna doska, 4 svorniky, spodna doska a matice
    add_box(bm, (2.0 * dx + 0.05, 0.14, 0.025), (0.0, yc, z_top + 0.0125), STEEL, bev=0.005)
    add_box(bm, (2.0 * dx + 0.05, 0.14, 0.02), (0.0, yc, z_bottom - 0.01), STEEL, bev=0.005)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            x, y = sx * dx, yc + sy * 0.058
            add_cylinder(bm, 0.011, z_top - z_bottom + 0.06, along_z((x, y, (z_top + z_bottom) * 0.5)), STEEL, segments=6)
            add_cylinder(bm, 0.018, 0.02, along_z((x, y, z_bottom - 0.03)), CHROME, segments=6)


def add_shock(bm, low, up):
    # tlmic: spodne oko na naprave, horne na drziaku na boku ramu
    a, b = Vector(low), Vector(up)
    mid = a.lerp(b, 0.55)
    add_rod(bm, a, mid, 0.035, DARK, segments=8)
    add_rod(bm, mid, b, 0.015, CHROME, segments=6)
    add_rod(bm, a.lerp(b, 0.62), a.lerp(b, 0.88), 0.042, DARK, segments=8)
    for p in (a, b):
        add_cylinder(bm, 0.028, 0.05, along_y(p), DARK, segments=8)
    add_box(bm, (0.10, 0.015, 0.12), (b.x, RAIL_Y + 0.0075, b.z), FRAME, bev=0.004)
    add_cylinder(bm, 0.013, b.y - RAIL_Y + 0.03, along_y((b.x, (b.y + RAIL_Y) * 0.5, b.z)), CHROME, segments=6)


def add_brake_drum(bm, y_in, y_out, hub_y, s):
    # brzdovy bubon s rebrami a naboj s prirubou pre koleso (s = strana)
    add_cylinder(bm, 0.225, 0.012, along_y((0.0, s * (y_in - 0.006), 0.0)), STEEL, segments=16)
    add_cylinder(bm, 0.21, y_out - y_in, along_y((0.0, s * (y_in + y_out) * 0.5, 0.0)), FRAME, segments=16, bev=0.012)
    for y in (y_in + 0.04, y_in + 0.08):
        add_cylinder(bm, 0.218, 0.014, along_y((0.0, s * y, 0.0)), FRAME, segments=16)
    add_cylinder(bm, 0.13, hub_y - y_out, along_y((0.0, s * (y_out + hub_y) * 0.5, 0.0)), STEEL, segments=16, bev=0.004)


def build_front_axle():
    bm = bmesh.new()
    kp = 0.86
    hub = FRONT_TRACK + 0.08          # dosadacia plocha disku kolesa
    # I-nosnik so znizenym stredom
    path = [(-kp, 0.0), (-0.62, -0.07), (0.62, -0.07), (kp, 0.0)]
    add_extruded_yz(bm, beam_outline(path, [0.05] * 4, cap=0.0), -0.045, 0.045, FRAME, bev=0.012)
    for s in SIDES_LR:
        # cap otocneho capu, tehlica s cepom, bubon
        add_cylinder(bm, 0.055, 0.22, along_z((0.0, s * kp, 0.0)), FRAME, segments=10, bev=0.012)
        for z in (-0.115, 0.115):
            add_cylinder(bm, 0.035, 0.012, along_z((0.0, s * kp, z)), STEEL, segments=8)
        add_cylinder(bm, 0.06, 0.06, along_y((0.0, s * (kp + 0.03), 0.0)), STEEL, segments=10)
        add_brake_drum(bm, 0.88, 1.06, hub, s)
        # riadiace rameno a brzdovy valec
        add_rod(bm, (0.0, s * 0.90, -0.06), (-0.20, s * 0.80, -0.03), 0.025, FRAME, segments=6)
        add_cylinder(bm, 0.032, 0.05, along_z((-0.20, s * 0.80, -0.03)), STEEL, segments=8)
        add_box(bm, (0.10, 0.04, 0.10), (-0.07, s * 0.68, 0.05), FRAME, bev=0.008)
        add_cylinder(bm, 0.07, 0.10, along_x((-0.13, s * 0.68, 0.10)), DARK, segments=12, bev=0.012)
        # pruzina, strmene, tlmic
        z_top = add_leaf_spring(bm, s * SPRING_Y, 0.70, 0.089, 0.20)
        add_box(bm, (0.16, 0.12, 0.04), (0.0, s * SPRING_Y, 0.0), FRAME, bev=0.006)
        add_u_bolts(bm, s * SPRING_Y, z_top, -0.12, 0.055)
        add_box(bm, (0.07, 0.05, 0.05), (0.0, s * 0.52, -0.01), FRAME, bev=0.006)
        add_shock(bm, (0.0, s * 0.52, 0.0), (-0.25, s * 0.475, HANG + 0.135))
    # spojovacia tyc riadenia
    add_rod(bm, (-0.20, -0.80, -0.03), (-0.20, 0.80, -0.03), 0.022, STEEL, segments=8)
    return finish_mesh(bm, "SM_Naprava_predna"), hub


def build_rear_axle():
    bm = bmesh.new()
    hub = REAR_TRACK - 0.022          # dosadacia plocha dvojmontaze
    # rurky napravy
    add_cylinder(bm, 0.075, 1.84, along_y((0.0, 0.0, 0.0)), FRAME, segments=10, bev=0.01)
    for s in SIDES_LR:
        add_cylinder(bm, 0.09, 0.03, along_y((0.0, s * 0.68, 0.0)), FRAME, segments=10)
    # diferencial: teleso, zadne veko so skrutkami, nos s prirubou pre kardan
    add_cylinder(bm, 0.22, 0.26, along_x((0.0, 0.0, 0.0)), FRAME, segments=12, bev=0.06)
    add_cylinder(bm, 0.18, 0.05, along_x((-0.15, 0.0, 0.0)), FRAME, segments=12, bev=0.02)
    for k in range(10):
        a = 2.0 * math.pi * k / 10
        add_cylinder(bm, 0.011, 0.012, along_x((-0.13, 0.195 * math.cos(a), 0.195 * math.sin(a))), STEEL, segments=6)
    add_cylinder(bm, 0.015, 0.012, along_x((-0.18, 0.0, -0.12)), STEEL, segments=6)
    add_cone(bm, 0.15, 0.09, 0.20, along_x((0.23, 0.0, 0.0)), FRAME, segments=10, bev=0.012)
    add_cylinder(bm, 0.06, 0.05, along_x((0.355, 0.0, 0.0)), STEEL, segments=10)
    add_cylinder(bm, 0.075, 0.02, along_x((0.39, 0.0, 0.0)), STEEL, segments=12, bev=0.004)
    for k in range(6):
        a = 2.0 * math.pi * (k + 0.5) / 6
        add_cylinder(bm, 0.01, 0.012, along_x((0.374, 0.055 * math.cos(a), 0.055 * math.sin(a))), CHROME, segments=6)
    for s in SIDES_LR:
        # brzdovy valec s pruzinovym zasobnikom
        add_box(bm, (0.12, 0.05, 0.06), (-0.12, s * 0.66, 0.06), FRAME, bev=0.006)
        add_cylinder(bm, 0.075, 0.10, along_x((-0.20, s * 0.66, 0.09)), DARK, segments=12, bev=0.012)
        add_cylinder(bm, 0.07, 0.08, along_x((-0.29, s * 0.66, 0.09)), DARK, segments=12, bev=0.012)
        # pruzina, strmene, tlmic
        z_top = add_leaf_spring(bm, s * SPRING_Y, 0.75, 0.179, 0.126)
        add_box(bm, (0.16, 0.12, 0.05), (0.0, s * SPRING_Y, 0.085), FRAME, bev=0.006)
        add_u_bolts(bm, s * SPRING_Y, z_top, -0.075, 0.09)
        add_box(bm, (0.07, 0.05, 0.05), (0.0, s * 0.52, 0.085), FRAME, bev=0.006)
        add_shock(bm, (0.0, s * 0.52, 0.10), (-0.25, s * 0.475, HANG + 0.135))
        add_brake_drum(bm, 0.70, 0.92, hub, s)
    return finish_mesh(bm, "SM_Naprava_zadna"), hub


# ---------------------------------------------------------------------------
# Blatniky: pivot v strede kolesa (daj ho na rovnake miesto ako koleso),
# L = vonkajsia strana +Y (lava strana auta), P = zrkadlovo (prava strana)
# ---------------------------------------------------------------------------

FENDER_R = 0.62           # vnutorny polomer blatnika


def add_marker(bm, angle, y, r=0.59):
    # oranzove obrysove svetlo na vonkajsom lemu
    frame = on_arc(angle)
    add_box(bm, (0.075, 0.012, 0.045), (0.0, y + 0.006, r), CHROME, bev=0.004, frame=frame)
    add_box(bm, (0.06, 0.01, 0.032), (0.0, y + 0.014, r), LAMP_OR, bev=0.003, frame=frame)


def add_fender_stays(bm, y_edge, plate_y, angles):
    # dve vzpery z blatnika na dosku, ktora dosadne na bok ramu
    zc = 0.40
    for a, sx in zip(angles, (1.0, -1.0)):
        rad = math.radians(a)
        p0 = ((FENDER_R + 0.01) * math.cos(rad), y_edge, (FENDER_R + 0.01) * math.sin(rad))
        add_rod(bm, p0, (sx * 0.09, plate_y + 0.012, zc), 0.018, STEEL, segments=6)
    add_box(bm, (0.26, 0.012, 0.16), (0.0, plate_y + 0.006, zc), FRAME, bev=0.004)
    for sx in SIDES_LR:
        for sz in SIDES_LR:
            add_cylinder(bm, 0.011, 0.01, along_y((sx * 0.10, plate_y + 0.016, zc + sz * 0.055)), CHROME, segments=6)


def fender_shell(bm, half_w, a0, a1, steps, ribs):
    r0, r1 = FENDER_R, FENDER_R + 0.028
    lip = half_w - 0.025
    sweep_profile(bm, [(r0, -half_w), (r1, -half_w), (r1, lip), (r0, lip)], a0, a1, steps, PLASTIC)
    sweep_profile(bm, [(0.555, lip), (r1, lip), (r1, lip + 0.005), (r1 - 0.022, half_w + 0.002), (0.555, half_w + 0.002)],
                  a0, a1, steps, PLASTIC)
    for y in ribs:
        sweep_profile(bm, [(r1 - 0.002, y - 0.03), (r1 + 0.012, y - 0.018), (r1 + 0.012, y + 0.018), (r1 - 0.002, y + 0.03)],
                      a0 + 3.0, a1 - 3.0, steps, PLASTIC)


def build_front_fender(lights):
    bm = bmesh.new()
    half_w = 0.215
    fender_shell(bm, half_w, 12.0, 168.0, 10, (0.0,))
    add_fender_stays(bm, -0.17, -(FRONT_TRACK - RAIL_Y), (55.0, 125.0))
    if lights:
        for a in (40.0, 90.0, 140.0):
            add_marker(bm, a, half_w + 0.002)
    return bm


def build_rear_fender(lights):
    bm = bmesh.new()
    half_w = 0.345
    fender_shell(bm, half_w, 15.0, 165.0, 8, (-0.14, 0.14))
    add_fender_stays(bm, -0.30, -(REAR_TRACK - RAIL_Y), (60.0, 120.0))
    # zasterka vzadu (-X) na drziaku
    end = math.radians(165.0)
    xb = (FENDER_R + 0.012) * math.cos(end)
    add_box(bm, (0.035, 0.68, 0.035), (xb, 0.0, 0.15), STEEL, bev=0.006)
    add_box(bm, (0.012, 0.64, 0.56), (xb, 0.0, -0.14), TIRE, bev=0.004)
    for y in (-0.2, 0.0, 0.2):
        add_box(bm, (0.016, 0.16, 0.012), (xb - 0.002, y, -0.36), TIRE, bev=0.003)
    if lights:
        # svetelna rampa: cervene, oranzove a biele (cuvacie) svetlo, obrysove svetla na boku
        add_box(bm, (0.05, 0.62, 0.08), (xb - 0.035, 0.0, 0.10), DARK, bev=0.008)
        for y, width, mat in ((0.19, 0.16, LAMP_RED), (0.025, 0.12, LAMP_OR), (-0.115, 0.10, LAMP_WHITE)):
            add_box(bm, (0.014, width, 0.055), (xb - 0.064, y, 0.10), mat, bev=0.004)
        for a in (45.0, 90.0, 135.0):
            add_marker(bm, a, half_w + 0.002)
    else:
        for s in SIDES_LR:
            add_box(bm, (0.008, 0.10, 0.04), (xb - 0.008, s * 0.20, -0.28), RED, bev=0.003)
    return bm


# ---------------------------------------------------------------------------
# Vzduchojemy: pivot v strede dosky, ktora dosadne na bok ramu, nadrze idu do +Y
# ---------------------------------------------------------------------------

def build_air_tanks():
    bm = bmesh.new()
    zc, r, length = -0.24, 0.15, 0.80
    tanks = (0.20, 0.53)
    # doska na ram a dve ramena
    add_box(bm, (0.62, 0.012, 0.22), (0.0, 0.006, -0.01), FRAME, bev=0.004)
    for sx in SIDES_LR:
        for sz in SIDES_LR:
            add_cylinder(bm, 0.011, 0.01, along_y((sx * 0.26, 0.016, -0.01 + sz * 0.07)), CHROME, segments=6)
        add_box(bm, (0.05, 0.70, 0.04), (sx * 0.24, 0.36, -0.07), FRAME, bev=0.008)
        add_rod(bm, (sx * 0.24, 0.012, -0.11), (sx * 0.24, 0.30, -0.08), 0.014, FRAME, segments=6)
    for yc in tanks:
        # osemhranna nadrz so zrazenymi celami, pasy, vypustny ventil, pripojka
        add_cylinder(bm, r, length, along_x((0.0, yc, zc)), AIR, segments=8, bev=0.06)
        for x in (-0.24, 0.24):
            add_band_x(bm, octagon(r + 0.012, yc, zc), octagon(r - 0.004, yc, zc), x - 0.02, x + 0.02, FRAME)
            add_cylinder(bm, 0.012, 0.03, along_z((x, yc, zc - r - 0.02)), CHROME, segments=6)
        add_cylinder(bm, 0.016, 0.05, along_z((0.0, yc, zc - r - 0.01)), STEEL, segments=6)
        add_box(bm, (0.012, 0.03, 0.012), (0.0, yc, zc - r - 0.035), RED, bev=0.003)
        add_cylinder(bm, 0.025, 0.04, along_x((length * 0.5 - 0.01, yc, zc)), STEEL, segments=8)
    # vzduchove hadicky medzi nadrzami a k ramu
    xe = length * 0.5 + 0.01
    add_rod(bm, (xe, tanks[0], zc), (xe, tanks[1], zc), 0.012, DARK, segments=6)
    add_rod(bm, (xe, tanks[0], zc), (xe, 0.04, -0.08), 0.012, DARK, segments=6)
    return finish_mesh(bm, "SM_Vzduchojemy")


# ---------------------------------------------------------------------------
# Scena a export
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


def add_spin(obj, index, expression):
    fcurve = obj.driver_add("rotation_euler", index)
    fcurve.driver.type = "SCRIPTED"
    fcurve.driver.expression = expression


def size_of(mesh):
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    return max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and (mesh.name.startswith("SM_Ram") or mesh.name.startswith("SM_Naprava_")
                                or mesh.name.startswith("SM_Koleso_predne") or mesh.name.startswith("SM_Koleso_dvojite")
                                or mesh.name.startswith("SM_Blatnik_") or mesh.name.startswith("SM_Vzduchojemy")
                                or mesh.name.startswith("SM_Kardan_")):
            bpy.data.meshes.remove(mesh)
    mats = [get_material(*m) for m in MATERIALS]

    # diely
    m = {}
    m["ram"] = build_frame()
    m["pred"], front_hub = build_front_axle()
    m["zad"], rear_hub = build_rear_axle()
    m["kol_p"] = build_wheel_front()
    m["kol_d"] = build_wheel_dual()
    for key, builder, name in (("bp", build_front_fender, "SM_Blatnik_predny"), ("bz", build_rear_fender, "SM_Blatnik_zadny")):
        for lights in (False, True):
            bm = builder(lights)
            bm_r = mirror_y(bm)
            suffix = "_svetla" if lights else ""
            m[key + suffix + "_L"] = finish_mesh(bm, name + suffix + "_L")
            m[key + suffix + "_P"] = finish_mesh(bm_r, name + suffix + "_P")
    m["vzduch"] = build_air_tanks()
    for length, tag in ((1.0, "1m"), (1.5, "1_5m"), (2.0, "2m")):
        m["kardan_" + tag] = build_kardan("SM_Kardan_" + tag, length)
    for mesh in m.values():
        for mat in mats:
            mesh.materials.append(mat)

    # kardan medzi prirubou diferencialu a predkom (mierne sklopeny)
    pinion = Vector((REAR_X + 0.40, 0.0, WHEEL_R))
    k_len, k_front_z = 2.0, 0.70
    tilt = math.asin((k_front_z - pinion.z) / k_len)
    k_front = (pinion.x + k_len * math.cos(tilt), 0.0, k_front_z)

    wheel_spin = "frame * 0.06"
    # (nazov objektu, diel, poloha, otocenie v stupnoch, tocenie: (os, vyraz))
    objects = [
        ("Ram", "ram", (0.0, 0.0, FRAME_Z), (0, 0, 0), None),
        ("Naprava_predna", "pred", (FRONT_X, 0.0, WHEEL_R), (0, 0, 0), None),
        ("Naprava_zadna", "zad", (REAR_X, 0.0, WHEEL_R), (0, 0, 0), None),
        ("Koleso_predne_L", "kol_p", (FRONT_X, FRONT_TRACK, WHEEL_R), (0, 0, 0), (1, wheel_spin)),
        ("Koleso_predne_P", "kol_p", (FRONT_X, -FRONT_TRACK, WHEEL_R), (0, 0, 180), (1, "-" + wheel_spin)),
        ("Koleso_zadne_L", "kol_d", (REAR_X, REAR_TRACK, WHEEL_R), (0, 0, 0), (1, wheel_spin)),
        ("Koleso_zadne_P", "kol_d", (REAR_X, -REAR_TRACK, WHEEL_R), (0, 0, 180), (1, "-" + wheel_spin)),
        ("Blatnik_predny_L", "bp_L", (FRONT_X, FRONT_TRACK, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_predny_P", "bp_P", (FRONT_X, -FRONT_TRACK, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_zadny_svetla_L", "bz_svetla_L", (REAR_X, REAR_TRACK, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_zadny_svetla_P", "bz_svetla_P", (REAR_X, -REAR_TRACK, WHEEL_R), (0, 0, 0), None),
        ("Vzduchojemy", "vzduch", (0.0, -RAIL_Y, FRAME_Z + 0.13), (0, 0, 180), None),
        ("Kardan_2m", "kardan_2m", k_front, (0, -math.degrees(tilt), 0), (0, "frame * 0.21")),
        # dalsie varianty vedla podvozku
        ("Blatnik_predny_svetla_L", "bp_svetla_L", (2.2, 3.0, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_predny_svetla_P", "bp_svetla_P", (0.7, 3.0, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_zadny_L", "bz_L", (-0.9, 3.0, WHEEL_R), (0, 0, 0), None),
        ("Blatnik_zadny_P", "bz_P", (-2.5, 3.0, WHEEL_R), (0, 0, 0), None),
        ("Kardan_1m", "kardan_1m", (1.0, 4.3, 0.3), (0, 0, 0), (0, "frame * 0.21")),
        ("Kardan_1_5m", "kardan_1_5m", (1.0, 4.7, 0.3), (0, 0, 0), (0, "frame * 0.21")),
    ]
    for name, key, location, rotation, spin in objects:
        obj = bpy.data.objects.new(name, m[key])
        coll.objects.link(obj)
        obj.location = location
        obj.rotation_euler = [math.radians(a) for a in rotation]
        if spin:
            add_spin(obj, *spin)

    lines = ["Podvozok - rozmery v metroch (dlzka X x sirka Y x vyska Z), predok auta = +X, lava strana = +Y.", ""]
    for key, mesh in m.items():
        lines.append("%-26s %.2f x %.2f x %.2f" % (mesh.name[3:], *size_of(mesh)))
    lines += [
        "",
        "Pivoty a skladanie (vsetko voci pivotu ramu = stred spodku ramu):",
        "  Ram: spodok ramu %.2f m nad zemou, vonkajsia strana nosnikov %.2f m od stredu, vyska nosnika %.2f m." % (FRAME_Z, RAIL_Y, RAIL_H),
        "  Naprava_predna: pivot v osi kolies, poloha (%.2f, 0, %.2f). Zavesy pruzin dosadnu na spodok ramu." % (FRONT_X, WHEEL_R - FRAME_Z),
        "  Naprava_zadna:  pivot v osi kolies, poloha (%.2f, 0, %.2f)." % (REAR_X, WHEEL_R - FRAME_Z),
        "  Koleso_predne: pivot v strede kolesa, od pivotu napravy (0, +-%.3f, 0), prave koleso otoc o 180 st. okolo Z." % FRONT_TRACK,
        "                 Dosadacia plocha naboja je %.3f m od stredu napravy." % front_hub,
        "  Koleso_dvojite: pivot v strede medzi pneumatikami, od pivotu napravy (0, +-%.3f, 0), prave otoc o 180 st." % REAR_TRACK,
        "                 Dosadacia plocha naboja je %.3f m od stredu napravy." % rear_hub,
        "  Blatniky: pivot v strede kolesa - poloz ich na rovnake miesto ako koleso. _L na lavu stranu, _P na pravu.",
        "            Doska vzpier dosadne na bok ramu.",
        "  Vzduchojemy: pivot v strede dosky, ktora dosadne na bok ramu (nadrze idu von, +Y). Na pravu stranu otoc o 180 st.",
        "  Kardan: pivot v strede prednej priruby, hriadel ide dozadu (-X). Zadna priruba dosadne na prirubu diferencialu,",
        "          ktora je od pivotu zadnej napravy (0.40, 0, 0). Kardan sa toci okolo svojej osi X.",
        "  Kolesa sa tocia okolo osi Y.",
    ]

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for mesh in m.values():
            export_mesh(coll, mesh)
        with open(os.path.join(EXPORT_DIR, "Podvozok.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    print("\n".join(lines))


main()
