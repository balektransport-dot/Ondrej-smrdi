# Stylizovana low poly sklopka (maly nakladiak so sklapacou korbou a bocnicami) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Sklopka". Pohyblive diely su samostatne objekty:
#   Sklopka_korba             - sklapa sa dozadu (cap vzadu na rame), pod nou je schovany piest
#   Sklopka_bocnica_L / _P / _zadna - bocnice sa sklapaju dole (panty dole)
#   kolesa (predne, zadne dvojmontaze)
#   Sklopka_volant, Sklopka_rucicka_* - volant a rucicky budikov sa tocia okolo vlastnej osi
# Ked pustis animaciu (medzernik): otvori sa zadna bocnica, korba sa vyklopi, vrati sa a potom sa
# sklopia bocne bocnice; volant sa kruti a rucicky budikov sa hybu.
# Kabina je duta s interierom (palubna doska s budikmi, volant, sedadla, panely dveri, tunel motora).
# Predok = +X, lava strana = +Y. Pociatok (0,0,0) = zem pod zadnou napravou.
# Do priecinka Sklopka v domovskom priecinku ulozi FBX kazdeho dielu a subor Sklopka.txt.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Sklopka"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Sklopka")

# (nazov, farba, kovovost, drsnost, svietivost, priehladnost)
MATERIALS = [
    ("SKL_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0, 1.0),
    ("SKL_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0, 1.0),
    ("SKL_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0, 1.0),
    ("SKL_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("SKL_Disk", (0.30, 0.31, 0.32, 1.0), 0.5, 0.40, 0.0, 1.0),
    ("SKL_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("SKL_Kabina", (0.82, 0.82, 0.80, 1.0), 0.1, 0.35, 0.0, 1.0),
    ("SKL_Hlinik", (0.60, 0.61, 0.62, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("SKL_Naraznik", (0.10, 0.10, 0.11, 1.0), 0.2, 0.50, 0.0, 1.0),
    ("SKL_Sklo", (0.12, 0.18, 0.18, 1.0), 0.0, 0.05, 0.0, 0.25),
    ("SKL_Interier", (0.09, 0.09, 0.10, 1.0), 0.0, 0.70, 0.0, 1.0),
    ("SKL_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("SKL_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("SKL_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0, 1.0),
    ("SKL_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("SKL_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0, 1.0),
    ("SKL_Cervena", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("SKL_Interier_tmavy", (0.045, 0.055, 0.075, 1.0), 0.0, 0.65, 0.0, 1.0),
    ("SKL_Budik", (0.008, 0.008, 0.010, 1.0), 0.0, 0.30, 0.0, 1.0),
    ("SKL_Bezova", (0.45, 0.38, 0.28, 1.0), 0.0, 0.50, 0.0, 1.0),
    ("SKL_Zelena", (0.05, 0.55, 0.10, 1.0), 0.0, 0.40, 1.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, PAINT, ALU, BUMPER, GLASS, SEAT, LAMP_OR, LAMP_RED, LAMP_WHITE, RED,
 WHITE, REDPAINT, INT, GAUGE, BEIGE, GREEN) = range(21)
SIDES_LR = (-1.0, 1.0)

# rozmery (m)
WHEEL_R = 0.40
FRONT_X = 3.30                 # predna naprava (rozvor 3.3 m)
FRONT_HUB = 0.93               # disk predneho kolesa od stredu
REAR_HUB = 0.785               # disk zadnej dvojmontaze od stredu
FRONT_SPINDLE = 0.80           # koniec prednej napravy (tu sa nasadi koleso s nabojom)
REAR_SPINDLE = 0.62            # koniec zadnej napravy
RAIL_Y = 0.40                  # os nosnika ramu
FRAME_BOT, FRAME_TOP = 0.65, 0.85
FRAME_X0, FRAME_X1 = -1.35, 4.05
CAB_X0, CAB_X1 = 2.65, 4.25    # kabina (zadok, predok)
CAB_HALF = 1.0
BELT = 1.55                    # spodok okien
ROOF = 2.52
CAB_FLOOR = 1.00               # podlaha v kabine
TIP = Vector((-1.30, 0.0, FRAME_TOP))   # cap sklapania korby
BED_X0, BED_X1 = -0.10, 3.65             # korba v suradniciach korby (od capu)
BED_HALF = 1.05
FLOOR_Z = 0.18                           # vrch podlahy korby nad capom
SIDE_H = 0.45                            # vyska bocnic
RAM_BASE = Vector((0.65, 0.0, 0.62))     # spodne oko piestu (na rame)
RAM_TOP = Vector((1.05, 0.0, 0.08))      # horne oko piestu (pod korbou, suradnice korby)
TIP_DEG = 45.0
SIDE_OPEN_DEG = 160.0
REAR_OPEN_DEG = 160.0


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


def add_transformed(bm, matrix, fn, *args, **kwargs):
    # vytvor tvar v pociatku a preloz/otoc ho maticou
    before = set(bm.verts)
    fn(bm, *args, **kwargs)
    bmesh.ops.transform(bm, matrix=matrix, verts=[v for v in bm.verts if v not in before])


def add_leaf_spring(bm, yc, half, z_seat, z_eye, hang_z, leaves=3, w=0.07):
    # listova pruzina od sedla na naprave po zavesy pod ramom
    z0 = z_seat + (leaves - 1) * 0.018 + 0.008
    k = (z_eye - z0) / (half * half)
    for i in range(leaves):
        f = 1.0 - 0.7 * i / leaves
        path = [(half * f * (j / 3.0 - 1.0), z0 - i * 0.018 + k * (half * f * (j / 3.0 - 1.0)) ** 2) for j in range(7)]
        add_extruded(bm, beam_outline(path, [0.008] * 7, cap=0.3), yc - w * 0.5, yc + w * 0.5, "XZ", FRAME, bev=0.003)
    for s in SIDES_LR:
        x = s * half
        add_cylinder(bm, 0.026, w + 0.01, along_y((x, yc, z_eye)), FRAME, segments=8)
        for d in SIDES_LR:
            add_box(bm, (0.07, 0.01, hang_z - z_eye + 0.03), (x, yc + d * 0.045, (hang_z + z_eye - 0.03) * 0.5), FRAME, bev=0.003)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, 0.009, 0.16, along_z((sx * 0.06, yc + sy * 0.05, z_seat)), STEEL, segments=6)
    add_box(bm, (0.16, 0.12, 0.02), (0.0, yc, z0 + 0.018), STEEL, bev=0.004)


# ---------------------------------------------------------------------------
# Kolesa aj s nabojom a bubnom: pivot na konci napravy (vnutorna strana bubna), os Y, vonkajsia strana +Y
# ---------------------------------------------------------------------------

def add_drum(bm, y_in, y_out, s):
    add_cylinder(bm, 0.18, 0.012, along_y((0.0, s * (y_in + 0.006), 0.0)), STEEL, segments=14)
    add_cylinder(bm, 0.17, y_out - y_in - 0.027, along_y((0.0, s * (y_in + y_out - 0.015) * 0.5, 0.0)), FRAME, segments=14, bev=0.01)
    add_cylinder(bm, 0.11, 0.015, along_y((0.0, s * (y_out - 0.0075), 0.0)), STEEL, segments=12)


def add_tire(bm, y, width=0.22):
    add_ring(bm, WHEEL_R - 0.012, 0.215, width, y, TIRE, 24, bev=width * 0.18)
    for s in SIDES_LR:
        add_ring(bm, WHEEL_R, WHEEL_R - 0.03, 0.05, y + s * 0.05, TIRE, 24)
        add_ring(bm, 0.335, 0.325, 0.006, y + s * (width * 0.5 - 0.001), DARK, 24)
        add_ring(bm, 0.235, 0.212, 0.014, y + s * (width * 0.5 - 0.02), RIM, 18)
    add_ring(bm, 0.215, 0.205, width - 0.03, y, RIM, 18)


def add_disc(bm, y0, y1, s):
    add_cylinder(bm, 0.206, y1 - y0, along_y((0.0, (y0 + y1) * 0.5, 0.0)), RIM, segments=18)
    ring_of(bm, 8, 0.15, y1 if s > 0 else y0, 0.03, 0.006, DARK, segments=8, offset=0.5)


def add_hub_cap(bm, y):
    add_cylinder(bm, 0.10, 0.05, along_y((0.0, y + 0.025, 0.0)), STEEL, segments=14, bev=0.006)
    ring_of(bm, 8, 0.075, y + 0.058, 0.01, 0.02, CHROME)
    add_cone(bm, 0.035, 0.055, 0.04, along_y((0.0, y + 0.07, 0.0)), CHROME, segments=10, bev=0.005)


def build_wheel_front():
    bm = bmesh.new()
    add_tire(bm, -0.07)
    add_disc(bm, 0.0, 0.015, 1.0)
    add_hub_cap(bm, 0.015)
    hub = FRONT_HUB - FRONT_SPINDLE
    shift(bm, (0.0, hub, 0.0))
    add_drum(bm, 0.0, hub, 1.0)
    return finish_mesh(bm, "SM_Sklopka_koleso_predne")


def build_wheel_dual():
    bm = bmesh.new()
    for s in SIDES_LR:
        add_tire(bm, 0.015 + s * 0.13)
    add_disc(bm, 0.0, 0.015, -1.0)
    add_disc(bm, 0.015, 0.03, 1.0)
    add_hub_cap(bm, 0.03)
    hub = REAR_HUB - REAR_SPINDLE
    shift(bm, (0.0, hub, 0.0))
    add_drum(bm, 0.0, hub, 1.0)
    return finish_mesh(bm, "SM_Sklopka_koleso_zadne")


# ---------------------------------------------------------------------------
# Podvozok: ram, napravy, kardan, nadrz, baterie, vyfuk, zasterky, zadna svetelna lista
# ---------------------------------------------------------------------------

def build_chassis():
    bm = bmesh.new()
    length, xc = FRAME_X1 - FRAME_X0, (FRAME_X0 + FRAME_X1) * 0.5
    zc, h = (FRAME_BOT + FRAME_TOP) * 0.5, FRAME_TOP - FRAME_BOT
    for s in SIDES_LR:
        add_box(bm, (length, 0.012, h), (xc, s * (RAIL_Y + 0.024), zc), FRAME, bev=0.003)
        for z in (FRAME_BOT + 0.006, FRAME_TOP - 0.006):
            add_box(bm, (length, 0.06, 0.012), (xc, s * RAIL_Y, z), FRAME, bev=0.003)
        for i in range(12):
            add_cylinder(bm, 0.009, 0.006, along_y((FRAME_X0 + 0.3 + i * 0.45, s * (RAIL_Y + 0.031), zc)), DARK, segments=8)
    for x in (-1.30, -0.40, RAM_BASE.x, 1.60, 2.60, 3.95):
        add_box(bm, (0.06, 2.0 * RAIL_Y + 0.036, 0.14), (x, 0.0, zc), FRAME, bev=0.008)

    # cap korby vzadu, drziak piestu
    for s in SIDES_LR:
        add_box(bm, (0.08, 0.012, 0.08), (TIP.x, s * 0.30, TIP.z - 0.03), FRAME, bev=0.003)
        add_cylinder(bm, 0.035, 0.07, along_y((TIP.x, s * 0.30, TIP.z)), STEEL, segments=10)
        add_box(bm, (0.12, 0.01, 0.14), (RAM_BASE.x, s * 0.06, RAM_BASE.z + 0.02), FRAME, bev=0.003)
    add_cylinder(bm, 0.014, 0.90, along_y(TIP), CHROME, segments=6)
    add_cylinder(bm, 0.016, 0.14, along_y(RAM_BASE), CHROME, segments=6)

    # predna naprava (I-nosnik) s pruzinami a bubnami
    fz = WHEEL_R
    add_transformed(bm, Matrix.Translation((FRONT_X, 0.0, 0.0)), add_extruded_yz,
                    beam_outline([(-0.78, fz), (-0.55, fz - 0.03), (0.55, fz - 0.03), (0.78, fz)], [0.045] * 4, cap=0.0),
                    -0.04, 0.04, FRAME, bev=0.01)
    for s in SIDES_LR:
        add_cylinder(bm, 0.05, 0.18, along_z((FRONT_X, s * 0.78, fz)), FRAME, segments=10, bev=0.01)
        add_cylinder(bm, 0.05, FRONT_SPINDLE - 0.77, along_y((FRONT_X, s * (FRONT_SPINDLE + 0.77) * 0.5, fz)), STEEL, segments=10)
        add_transformed(bm, Matrix.Translation((FRONT_X, 0.0, 0.0)), add_leaf_spring,
                        s * RAIL_Y, 0.55, fz + 0.015, 0.58, FRAME_BOT)
        add_rod(bm, (FRONT_X - 0.04, s * 0.78, fz - 0.07), (FRONT_X - 0.20, s * 0.70, fz - 0.05), 0.02, FRAME)
    add_rod(bm, (FRONT_X - 0.20, -0.70, fz - 0.05), (FRONT_X - 0.20, 0.70, fz - 0.05), 0.018, STEEL, segments=8)

    # zadna naprava s diferencialom, pruzinami a bubnami
    add_cylinder(bm, 0.06, 2.0 * REAR_SPINDLE, along_y((0.0, 0.0, fz)), FRAME, segments=10)
    add_cylinder(bm, 0.17, 0.22, along_x((0.0, 0.0, fz)), FRAME, segments=12, bev=0.05)
    add_cylinder(bm, 0.13, 0.04, along_x((-0.12, 0.0, fz)), FRAME, segments=12, bev=0.015)
    add_cone(bm, 0.11, 0.07, 0.16, along_x((0.19, 0.0, fz)), FRAME, segments=10, bev=0.01)
    add_cylinder(bm, 0.06, 0.02, along_x((0.28, 0.0, fz)), STEEL, segments=10)
    for s in SIDES_LR:
        add_cylinder(bm, 0.085, 0.02, along_y((0.0, s * (REAR_SPINDLE - 0.01), fz)), STEEL, segments=10)
        add_transformed(bm, Matrix.Translation((0.0, 0.0, 0.0)), add_leaf_spring,
                        s * RAIL_Y, 0.65, fz + 0.06, 0.58, FRAME_BOT, 4)
        add_box(bm, (0.14, 0.10, 0.04), (0.0, s * RAIL_Y, fz + 0.04), FRAME, bev=0.005)

    # motor a prevodovka pod kabinou, kardan
    add_box(bm, (0.50, 0.40, 0.30), (2.55, 0.0, 0.70), DARK, bev=0.04)
    add_box(bm, (0.70, 0.55, 0.45), (3.15, 0.0, 0.82), DARK, bev=0.05)
    add_rod(bm, (2.30, 0.0, 0.62), (0.29, 0.0, fz), 0.04, STEEL, segments=8)
    for p in ((2.30, 0.0, 0.62), (0.29, 0.0, fz)):
        add_cylinder(bm, 0.06, 0.03, along_x(p), STEEL, segments=10)

    # nadrz (lava strana), baterie a vzduchojem (prava), vyfuk
    tx, ty, tz = 1.95, 0.70, 0.62
    add_box(bm, (0.70, 0.45, 0.42), (tx, ty, tz), ALU, bev=0.06)
    for x in (tx - 0.22, tx + 0.22):
        add_box(bm, (0.04, 0.47, 0.44), (x, ty, tz), DARK, bev=0.01)
        add_box(bm, (0.05, ty - 0.43 - 0.2, 0.06), (x, (ty + 0.43) * 0.5 - 0.1, tz + 0.10), DARK, bev=0.005)
    add_cylinder(bm, 0.045, 0.04, along_z((tx + 0.18, ty + 0.10, tz + 0.23)), STEEL, segments=8)
    add_cylinder(bm, 0.055, 0.03, along_z((tx + 0.18, ty + 0.10, tz + 0.26)), REDPAINT, segments=8, bev=0.006)
    add_box(bm, (0.60, 0.45, 0.32), (1.95, -0.70, 0.64), DARK, bev=0.03)
    add_box(bm, (0.56, 0.02, 0.26), (1.95, -0.93, 0.64), FRAME, bev=0.005)
    add_cylinder(bm, 0.13, 0.55, along_x((1.15, -0.62, 0.62)), STEEL, segments=10, bev=0.04)
    add_rod(bm, (0.86, -0.62, 0.62), (0.62, -0.88, 0.50), 0.03, STEEL, segments=8)
    add_rod(bm, (2.40, -0.15, 0.60), (1.44, -0.55, 0.62), 0.035, STEEL, segments=8)

    # zasterky za zadnymi kolesami
    for s in SIDES_LR:
        add_box(bm, (0.04, 0.42, 0.04), (-0.48, s * (RAIL_Y + 0.24), 0.74), FRAME, bev=0.006)
        add_box(bm, (0.012, 0.40, 0.42), (-0.48, s * 0.82, 0.52), TIRE, bev=0.004)
        add_box(bm, (0.05, 0.03, 0.04), (-0.48, s * (RAIL_Y + 0.045), 0.74), FRAME, bev=0.004)

    # zadna svetelna lista na drziakoch (ako na fotke)
    bx, bz = FRAME_X0 - 0.04, 0.48
    add_box(bm, (0.08, 2.00, 0.10), (bx, 0.0, bz), ALU, bev=0.012)
    for s in SIDES_LR:
        add_box(bm, (0.05, 0.05, FRAME_BOT - bz + 0.02), (FRAME_X0 + 0.02, s * RAIL_Y, (FRAME_BOT + bz) * 0.5), ALU, bev=0.006)
        add_box(bm, (0.04, 0.24, 0.07), (bx - 0.045, s * 0.86, bz), DARK, bev=0.006)
        for y, width, mat in ((0.95, 0.05, LAMP_OR), (0.86, 0.10, LAMP_RED), (0.775, 0.045, LAMP_WHITE)):
            add_box(bm, (0.008, width, 0.05), (bx - 0.068, s * y, bz), mat, bev=0.002)
        add_box(bm, (0.04, 0.03, 0.025), (bx, s * 1.02, bz + 0.03), LAMP_OR, bev=0.004)
    add_box(bm, (0.006, 0.40, 0.10), (bx - 0.045, 0.0, bz - 0.01), WHITE, bev=0.002)
    return finish_mesh(bm, "SM_Sklopka_podvozok")


# ---------------------------------------------------------------------------
# Kabina (pivot v pociatku): spodok plny po podlahu, nad nim tenke steny, aby bola duta
# ---------------------------------------------------------------------------

def quad(x0, x1, y0, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def face_frame(center, tilt_deg):
    # suradnice plochy, ktora sa diva na vodica (-X) a je naklonena dozadu o tilt_deg:
    # lokalna X = vpravo z pohladu vodica (-Y), Y = hore po ploche, Z = smerom k vodicovi
    t = math.radians(tilt_deg)
    x_axis = Vector((0.0, -1.0, 0.0))
    y_axis = Vector((math.sin(t), 0.0, math.cos(t)))
    z_axis = Vector((-math.cos(t), 0.0, math.sin(t)))
    rot = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    return Matrix.Translation(Vector(center)) @ rot


def add_text(bm, text, size, matrix, mat):
    # cislo/napis ako tenky mesh (na budiky)
    curve = bpy.data.curves.new("SKL_tmp_text", "FONT")
    curve.body = text
    curve.size = size
    curve.extrude = 0.0004
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    obj = bpy.data.objects.new("SKL_tmp_text", curve)
    bpy.context.scene.collection.objects.link(obj)
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    before_v, before_f = set(bm.verts), set(bm.faces)
    bm.from_mesh(mesh)
    bmesh.ops.transform(bm, matrix=matrix, verts=[v for v in bm.verts if v not in before_v])
    for f in bm.faces:
        if f not in before_f:
            f.material_index = mat
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.curves.remove(curve)
    bpy.data.meshes.remove(mesh)


def plan(x0, x1, half, c_front, c_rear, z):
    # pohlad zhora na kabinu: obdlznik so zrezanymi rohmi (vpredu viac, vzadu menej)
    pts = [(x0 + c_rear, -half), (x1 - c_front, -half), (x1, -half + c_front), (x1, half - c_front),
           (x1 - c_front, half), (x0 + c_rear, half), (x0, half - c_rear), (x0, -half + c_rear)]
    return [Vector((x, y, z)) for x, y in pts]


def add_loft(bm, bottom, top, mat, bev=0.0):
    # teleso medzi dvoma mnohouholnikmi s rovnakym poctom bodov
    b = [bm.verts.new(p) for p in bottom]
    t = [bm.verts.new(p) for p in top]
    n = len(b)
    faces = [bm.faces.new(b[::-1]), bm.faces.new(t)]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((b[i], b[j], t[j], t[i])))
    finish_shape(bm, faces, mat, bev)


def inward_of(a, b, center):
    # vodorovny smer od steny a-b dnu do kabiny
    d = Vector((b.x - a.x, b.y - a.y, 0.0))
    n = Vector((-d.y, d.x, 0.0)).normalized()
    mid = (a + b) * 0.5
    if n.dot(Vector((center.x - mid.x, center.y - mid.y, 0.0))) < 0.0:
        n = -n
    return n


def add_quad_panel(bm, corners, thickness, mat, inward, bev=0.0):
    # tenka stena zo 4 rohov, hrubka smerom dnu
    outer = [bm.verts.new(c) for c in corners]
    inner = [bm.verts.new(c + inward * thickness) for c in corners]
    faces = [bm.faces.new(outer), bm.faces.new(inner[::-1])]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(bm.faces.new((outer[i], inner[i], inner[j], outer[j])))
    finish_shape(bm, faces, mat, bev)


def add_window(bm, a0, a1, b1, b0, inward, frame_mat=DARK):
    # okno: sklo vsadene dnu a gumovy ramik po obvode (a = dole, b = hore)
    corners = [a0, a1, b1, b0]
    for p, q in zip(corners, corners[1:] + corners[:1]):
        add_box_between(bm, p + inward * 0.012, q + inward * 0.012, 0.05, 0.035, frame_mat, bev=0.006)
    c = (a0 + a1 + b1 + b0) * 0.25
    inset = [c + (p - c) * 0.94 + inward * 0.018 for p in corners]
    add_quad_panel(bm, inset, 0.008, GLASS, inward)


def y_side(z):
    # bok hornej casti kabiny sa smerom hore zuzuje
    return CAB_HALF - 0.08 * (z - BELT) / (ROOF - BELT)


def build_cab():
    bm = bmesh.new()
    h = CAB_HALF
    c_front, c_rear = 0.14, 0.05
    center = Vector(((CAB_X0 + CAB_X1) * 0.5, 0.0, 0.0))

    # spodok po podlahu: bocny obrys s podbehom, predne zvisle hrany zrezane
    arch_r, bottom = 0.52, 0.62
    da = math.degrees(math.asin((bottom - WHEEL_R) / arch_r))
    outline = [(CAB_X0, 0.76), (CAB_X0 + 0.10, bottom)]
    for k in range(9):
        a = math.radians(180.0 - da - (180.0 - 2.0 * da) * k / 8)
        outline.append((FRONT_X + arch_r * math.cos(a), WHEEL_R + arch_r * math.sin(a)))
    outline += [(CAB_X1 - 0.08, bottom), (CAB_X1, bottom + 0.08), (CAB_X1, CAB_FLOOR), (CAB_X0, CAB_FLOOR)]
    before = set(bm.faces)
    add_extruded(bm, outline, -h, h, "XZ", PAINT)
    lower = [f for f in bm.faces if f not in before]
    corner_edges = {e for f in lower for e in f.edges
                    if all(v.co.x > CAB_X1 - 0.001 and abs(v.co.y) > h - 0.001 for v in e.verts)}
    bevel(bm, corner_edges, c_front, PAINT)
    before_rear = {e for f in bm.faces if f not in before for e in f.edges
                   if all(v.co.x < CAB_X0 + 0.001 and abs(v.co.y) > h - 0.001 for v in e.verts)}
    bevel(bm, before_rear, c_rear, PAINT)

    # steny od podlahy po okna (duta kabina), po obryse so zrezanymi rohmi
    belt = plan(CAB_X0, CAB_X1, h, c_front, c_rear, BELT)
    low = plan(CAB_X0, CAB_X1, h, c_front, c_rear, CAB_FLOOR - 0.03)
    for i in range(8):
        j = (i + 1) % 8
        n = inward_of(low[i], low[j], center)
        add_quad_panel(bm, [low[i], low[j], belt[j], belt[i]], 0.03, PAINT, n)

    # horna cast: sklo vpredu, zalomene rohy (cierne), dvere s oknom, zadne bocne panely, zadna stena
    roof = plan(CAB_X0 + 0.10, CAB_X1 - 0.20, h - 0.08, 0.12, c_rear, ROOF)
    win_top = ROOF - 0.15                            # vrch okna dveri, nad nim pas karoserie
    for i in range(8):
        j = (i + 1) % 8
        a0, a1, b1, b0 = belt[i], belt[j], roof[j], roof[i]
        n = inward_of(a0, a1, center)
        if i == 2:                                     # predne sklo
            add_window(bm, a0, a1, b1, b0, n)
        elif i in (1, 3):                              # zalomene predne rohy
            add_quad_panel(bm, [a0, a1, b1, b0], 0.03, PAINT, n, bev=0.004)
        elif i in (0, 4):                              # boky: okno dveri + panel za dverami
            front_first = i == 0
            ax = Vector((2.97, a0.y, BELT))
            bx = Vector((2.99, b0.y, ROOF))
            if front_first:   # pravy bok: od zadu dopredu
                quarter, door = (a0, ax, bx, b0), (ax, a1, b1, bx)
            else:             # lavy bok: od predu dozadu
                door, quarter = (a0, ax, bx, b0), (ax, a1, b1, bx)
            add_quad_panel(bm, list(quarter), 0.03, PAINT, n, bev=0.004)
            d0, d1, d2, d3 = door
            t = (win_top - BELT) / (ROOF - BELT)
            e1, e0 = d1.lerp(d2, t), d0.lerp(d3, t)
            add_window(bm, d0, d1, e1, e0, n)
            add_quad_panel(bm, [e0, e1, d2, d3], 0.03, PAINT, n, bev=0.004)
            top_line = [e0.lerp(d3, 0.45), e1.lerp(d2, 0.45)]
            add_box_between(bm, top_line[0] - n * 0.003, top_line[1] - n * 0.003, 0.006, 0.006, DARK)
            add_box_between(bm, ax + n * 0.02, bx + n * 0.02, 0.07, 0.07, PAINT, bev=0.01)
        elif i == 6:                                   # zadna stena s malym oknom
            add_quad_panel(bm, [a0, a1, b1, b0], 0.03, PAINT, n, bev=0.004)
            mid = (BELT + ROOF) * 0.5 + 0.03
            xw = CAB_X0 + 0.10 * (mid - BELT) / (ROOF - BELT) - 0.003
            add_box(bm, (0.01, 1.0, 0.40), (xw, 0.0, mid), GLASS, rotation=(0.0, math.degrees(math.atan2(0.10, ROOF - BELT)), 0.0))
            add_box(bm, (0.008, 1.06, 0.46), (xw + 0.004, 0.0, mid), DARK, rotation=(0.0, math.degrees(math.atan2(0.10, ROOF - BELT)), 0.0))
        else:
            add_quad_panel(bm, [a0, a1, b1, b0], 0.03, PAINT, n, bev=0.004)

    # strecha so zrezanymi hranami a previsom nad sklom, zvyseny strecny diel so svetlami
    add_loft(bm, plan(CAB_X0 + 0.08, CAB_X1 - 0.16, h - 0.06, 0.13, 0.06, ROOF - 0.03),
             plan(CAB_X0 + 0.10, CAB_X1 - 0.17, h - 0.07, 0.13, 0.06, ROOF + 0.02), PAINT, bev=0.006)
    add_loft(bm, plan(CAB_X0 + 0.10, CAB_X1 - 0.17, h - 0.07, 0.13, 0.06, ROOF + 0.02),
             plan(CAB_X0 + 0.26, CAB_X1 - 0.45, h - 0.30, 0.10, 0.06, ROOF + 0.22), PAINT, bev=0.006)
    for y in (-0.30, 0.0, 0.30):
        add_box(bm, (0.03, 0.07, 0.03), (CAB_X1 - 0.31, y, ROOF + 0.12), LAMP_OR, bev=0.005, rotation=(0.0, -36.0, 0.0))

    # boky: prelis, pas, linie dveri, kluka, smerovka, lem podbehu, madla, schodiky, zrkadla
    side_len = CAB_X1 - c_front - CAB_X0 - c_rear
    side_x = CAB_X0 + c_rear + side_len * 0.5
    for s in SIDES_LR:
        yo = s * (h + 0.003)
        add_box(bm, (side_len - 0.04, 0.014, 0.022), (side_x, s * (h + 0.005), 1.22), PAINT, bev=0.006)
        door_x1 = CAB_X1 - c_front - 0.03
        for x in (2.97, door_x1):
            add_box(bm, (0.006, 0.006, BELT - 0.96), (x, yo, (BELT + 0.96) * 0.5), DARK)
        add_box(bm, (door_x1 - 2.97, 0.006, 0.006), ((door_x1 + 2.97) * 0.5, yo, 0.96), DARK)
        add_box(bm, (0.11, 0.025, 0.03), (3.06, s * (h + 0.012), 1.42), DARK, bev=0.006)
        add_box(bm, (0.05, 0.012, 0.05), (2.90, s * (h + 0.006), 1.10), LAMP_OR, bev=0.003, rotation=(0.0, 45.0, 0.0))
        add_box(bm, (0.065, 0.008, 0.065), (2.90, s * (h + 0.002), 1.10), DARK, rotation=(0.0, 45.0, 0.0))
        flare = [(arch_r - 0.005, s * (h - 0.01)), (arch_r + 0.08, s * (h - 0.01)),
                 (arch_r + 0.08, s * (h + 0.025)), (arch_r + 0.02, s * (h + 0.045))]
        add_transformed(bm, Matrix.Translation((FRONT_X, 0.0, WHEEL_R)), sweep_profile, flare, da, 180.0 - da, 5, PAINT)
        add_rod(bm, (CAB_X0 + 0.07, s * (h + 0.03), 1.05), (CAB_X0 + 0.07, s * (h + 0.03), 1.95), 0.012, CHROME)
        for z in (1.05, 1.95):
            add_rod(bm, (CAB_X0 + 0.07, s * (h - 0.01), z), (CAB_X0 + 0.07, s * (h + 0.03), z), 0.01, CHROME)
        for z in (0.48, 0.30):
            add_box(bm, (0.22, 0.17, 0.035), (CAB_X0 + 0.12, s * (h - 0.09), z), DARK, bev=0.006)
        for x in (CAB_X0 + 0.04, CAB_X0 + 0.20):
            add_box(bm, (0.02, 0.02, 0.46), (x, s * (h - 0.09), 0.50), DARK)
        for z0, z1 in ((2.15, 2.10), (1.72, 1.78)):
            add_rod(bm, (CAB_X1 - c_front - 0.04, s * (y_side(z0) - 0.01), z0), (4.02, s * (h + 0.22), z1), 0.012, DARK, segments=6)
        add_box(bm, (0.05, 0.14, 0.36), (4.00, s * (h + 0.25), 1.94), DARK, bev=0.012)
        add_box(bm, (0.006, 0.12, 0.32), (3.973, s * (h + 0.25), 1.94), CHROME)
        add_box(bm, (0.04, 0.10, 0.14), (4.00, s * (h + 0.24), 1.66), DARK, bev=0.01)
        # predne svetla v ramikoch, smerovky na zrezanych rohoch, stierace
        add_box(bm, (0.02, 0.26, 0.16), (CAB_X1 + 0.006, s * 0.66, 0.95), DARK, bev=0.008)
        add_cylinder(bm, 0.07, 0.02, along_x((CAB_X1 + 0.012, s * 0.70, 0.95)), CHROME, segments=8)
        add_cylinder(bm, 0.055, 0.02, along_x((CAB_X1 + 0.02, s * 0.70, 0.95)), LAMP_WHITE, segments=8)
        add_box(bm, (0.012, 0.06, 0.06), (CAB_X1 + 0.012, s * 0.58, 0.95), LAMP_WHITE, bev=0.004)
        add_box(bm, (0.014, 0.09, 0.08), (CAB_X1 - c_front * 0.5 + 0.004, s * (h - c_front * 0.5 + 0.004), 0.95),
                LAMP_OR, bev=0.004, rotation=(0.0, 0.0, s * 45.0))
        add_rod(bm, (CAB_X1 - 0.012, s * 0.06, BELT + 0.06), (CAB_X1 - 0.02, s * 0.62, BELT + 0.12), 0.008, DARK)

    # predok: linia pod sklom, maska s rebrami a znakom, zahnuty naraznik, SPZ, hmlovky
    add_box(bm, (0.016, 2.0 * (h - c_front) - 0.04, 0.025), (CAB_X1 + 0.008, 0.0, 1.42), PAINT, bev=0.006)
    add_box(bm, (0.012, 0.92, 0.26), (CAB_X1 + 0.004, 0.0, 0.98), DARK, bev=0.004)
    for z in (0.90, 0.96, 1.02, 1.08):
        add_box(bm, (0.016, 0.88, 0.022), (CAB_X1 + 0.008, 0.0, z), STEEL, bev=0.003)
    add_cylinder(bm, 0.035, 0.012, along_x((CAB_X1 + 0.01, 0.0, 1.16)), CHROME, segments=6)
    bumper = [(CAB_X1 - 0.25, -h - 0.01), (CAB_X1 - 0.10, -h - 0.01), (CAB_X1 + 0.06, -h + 0.17),
              (CAB_X1 + 0.06, h - 0.17), (CAB_X1 - 0.10, h + 0.01), (CAB_X1 - 0.25, h + 0.01)]
    add_extruded(bm, bumper, 0.48, 0.76, "XY", BUMPER, bev=0.03)
    add_box(bm, (0.04, 2.0 * h - 0.30, 0.04), (CAB_X1 + 0.05, 0.0, 0.50), BUMPER, bev=0.012)
    add_box(bm, (0.006, 0.42, 0.10), (CAB_X1 + 0.063, 0.0, 0.62), WHITE, bev=0.002)
    for s in SIDES_LR:
        add_box(bm, (0.012, 0.14, 0.06), (CAB_X1 + 0.064, s * 0.62, 0.62), LAMP_WHITE, bev=0.004)
    return finish_mesh(bm, "SM_Sklopka_kabina")


# ---------------------------------------------------------------------------
# Interier: palubna doska s budikmi, stlpik riadenia, sedadla, panely dveri, tunel motora
# ---------------------------------------------------------------------------

DRIVER_Y = 0.45
CLUSTER = face_frame((3.915, DRIVER_Y, 1.71), 20.0)        # pristrojovy panel pred vodicom
# budiky: (nazov, posun na paneli (vpravo, hore), polomer, cisla, hodnota pri volnobehu)
GAUGES = [
    ("rychlost", (-0.12, 0.0), 0.075, ["0", "20", "40", "60", "80", "100", "120", "140"], 0.0),
    ("otacky", (0.12, 0.0), 0.075, ["0", "5", "10", "15", "20", "25", "30", "35"], 0.17),
    ("palivo", (0.0, 0.035), 0.028, [], 0.75),
    ("teplota", (0.0, -0.035), 0.028, [], 0.5),
]
WHEEL_TILT = 35.0
WHEEL_CENTER = Vector((3.72, DRIVER_Y, 1.80))
STEERING = face_frame(WHEEL_CENTER, WHEEL_TILT)


def gauge_frame(offset):
    return CLUSTER @ Matrix.Translation((offset[0], offset[1], 0.0))


def gauge_angle(value):
    # hodnota 0..1 -> uhol rucicky (0 = vlavo dole, 1 = vpravo dole), proti smeru hodin z pohladu vodica
    return math.radians(135.0 - 270.0 * value)


def build_interior():
    bm = bmesh.new()
    h = CAB_HALF
    # podlaha, tunel motora, obklad zadnej steny a stropu
    add_box(bm, (4.08 - CAB_X0 - 0.06, 2.0 * h - 0.10, 0.01), ((CAB_X0 + 0.06 + 4.08) * 0.5, 0.0, CAB_FLOOR + 0.005), SEAT)
    add_prism(bm, quad(2.75, 3.80, -0.24, 0.24, CAB_FLOOR), quad(2.85, 3.70, -0.19, 0.19, 1.30), INT, bev=0.02)
    add_box(bm, (0.01, 2.0 * h - 0.08, BELT - CAB_FLOOR), (CAB_X0 + 0.035, 0.0, (BELT + CAB_FLOOR) * 0.5), INT)
    add_box(bm, (1.18, 2.0 * h - 0.30, 0.01), (3.39, 0.0, ROOF - 0.045), INT)

    # palubna doska (bocny profil vytiahnuty na sirku kabiny)
    dash = [(4.19, CAB_FLOOR), (4.19, 1.60), (3.97, 1.645), (3.90, 1.56), (3.93, 1.30), (4.05, 1.15), (4.10, CAB_FLOOR)]
    add_extruded(bm, dash, -0.86, 0.86, "XZ", INT, bev=0.02)
    add_box(bm, (0.20, 0.50, 0.03), (4.06, -0.35, 1.655), INT, bev=0.01)
    for y in (-0.72, -0.05, 0.75):
        add_box(bm, (0.012, 0.12, 0.05), (3.905, y, 1.52), GAUGE, bev=0.004, rotation=(0.0, -20.0, 0.0))
    add_box(bm, (0.012, 0.18, 0.05), (3.915, -0.35, 1.40), GAUGE, bev=0.004, rotation=(0.0, -12.0, 0.0))

    # pristrojovy panel: stitok, tienidlo, budiky s cislami a ryskami, kontrolky
    add_box(bm, (0.46, 0.21, 0.012), (0.0, 0.0, -0.008), GAUGE, bev=0.004, frame=CLUSTER)
    add_box(bm, (0.48, 0.16, 0.16), (0.0, -0.07, -0.09), INT, bev=0.02, frame=CLUSTER)
    add_box(bm, (0.50, 0.05, 0.10), (0.0, 0.115, 0.045), INT, bev=0.015, frame=CLUSTER)
    for s in SIDES_LR:
        add_box(bm, (0.03, 0.22, 0.09), (s * 0.245, 0.0, 0.04), INT, bev=0.01, frame=CLUSTER)
    for i, mat in enumerate((LAMP_OR, GREEN, LAMP_RED, WHITE, LAMP_OR, GREEN)):
        add_box(bm, (0.018, 0.012, 0.004), (-0.075 + i * 0.03, 0.085, 0.002), mat, frame=CLUSTER)
    for name, offset, radius, numbers, _ in GAUGES:
        g = gauge_frame(offset)
        add_cylinder(bm, radius, 0.006, g @ Matrix.Translation((0.0, 0.0, 0.003)), GAUGE, segments=16)
        add_transformed(bm, g @ Matrix.Rotation(math.radians(90.0), 4, "X"), add_ring,
                        radius + 0.008, radius, 0.012, 0.004, STEEL, 16)
        ticks = 28 if numbers else 4
        for k in range(ticks + 1):
            value = k / ticks
            major = (not numbers) or k % 4 == 0
            length = radius * (0.22 if major else 0.12)
            mat = WHITE
            if name == "otacky" and 0.43 <= value <= 0.58:
                mat = GREEN
            if name == "otacky" and value >= 0.86:
                mat = LAMP_RED
            add_box(bm, (radius * 0.04, length, 0.002), (0.0, radius * 0.92 - length * 0.5, 0.007), mat,
                    frame=g @ Matrix.Rotation(gauge_angle(value), 4, "Z"))
        for k, text in enumerate(numbers):
            a = gauge_angle(k / (len(numbers) - 1))
            r = radius * 0.62
            pos = Matrix.Translation((-r * math.sin(a), r * math.cos(a), 0.007))
            add_text(bm, text, radius * 0.17, g @ pos, WHITE)
        add_cylinder(bm, radius * 0.12, 0.008, g @ Matrix.Translation((0.0, 0.0, 0.01)), STEEL, segments=8)

    # stlpik riadenia s krytom, pedale
    n = Vector((STEERING[0][2], STEERING[1][2], STEERING[2][2]))
    add_rod(bm, WHEEL_CENTER - n * 0.08, WHEEL_CENTER - n * 0.42, 0.028, INT, segments=8)
    add_box_between(bm, WHEEL_CENTER - n * 0.22, WHEEL_CENTER - n * 0.40, 0.10, 0.11, INT, bev=0.015)
    for y in (0.33, 0.47, 0.58):
        add_box(bm, (0.04, 0.07, 0.10), (4.02, y, CAB_FLOOR + 0.12), DARK, bev=0.006, rotation=(0.0, -30.0, 0.0))

    # panely dveri (lakat, vrecko, kluka), sedadla, radiaca paka
    for s in SIDES_LR:
        y = s * (h - 0.045)
        add_box(bm, (1.09, 0.025, BELT - CAB_FLOOR - 0.04), (3.535, y, (BELT + CAB_FLOOR) * 0.5), INT, bev=0.008)
        add_box(bm, (0.60, 0.03, 0.10), (3.62, y - s * 0.01, 1.16), SEAT, bev=0.01)
        add_box(bm, (0.42, 0.07, 0.05), (3.45, y - s * 0.03, 1.40), SEAT, bev=0.015)
        add_box(bm, (0.10, 0.03, 0.03), (3.92, y - s * 0.015, 1.42), STEEL, bev=0.006)
        add_box(bm, (0.12, 0.012, 0.09), (2.96, y, 1.85), INT, bev=0.004)
    for y, width in ((DRIVER_Y, 0.50), (-0.42, 0.80)):
        add_box(bm, (0.36, width - 0.10, 0.30), (3.28, y, CAB_FLOOR + 0.16), DARK, bev=0.02)
        add_box(bm, (0.48, width, 0.12), (3.30, y, CAB_FLOOR + 0.37), SEAT, bev=0.035)
        add_box(bm, (0.13, width, 0.66), (3.03, y, CAB_FLOOR + 0.76), SEAT, bev=0.035, rotation=(0.0, -12.0, 0.0))
    for y in (DRIVER_Y, -0.22, -0.62):
        add_box(bm, (0.09, 0.26, 0.16), (2.95, y, CAB_FLOOR + 1.20), SEAT, bev=0.03, rotation=(0.0, -12.0, 0.0))
    add_rod(bm, (3.68, 0.12, 1.28), (3.62, 0.12, 1.52), 0.012, STEEL)
    add_cylinder(bm, 0.03, 0.05, along_z((3.62, 0.12, 1.54)), DARK, segments=8, bev=0.01)
    return finish_mesh(bm, "SM_Sklopka_interier")


def build_steering_wheel():
    # volant: pivot v strede, toci sa okolo svojej osi Z (os stlpika riadenia)
    bm = bmesh.new()
    rx = Matrix.Rotation(math.radians(90.0), 4, "X")
    add_transformed(bm, rx, add_ring, 0.225, 0.19, 0.035, 0.0, INT, 12, bev=0.008)
    add_transformed(bm, rx, add_ring, 0.212, 0.203, 0.006, 0.019, BEIGE, 12)
    for s in SIDES_LR:
        add_box(bm, (0.16, 0.045, 0.022), (s * 0.12, -0.025, -0.008), INT, bev=0.008,
                rotation=(0.0, 0.0, s * 12.0))
    add_box(bm, (0.04, 0.12, 0.02), (0.0, -0.12, -0.01), INT, bev=0.008)
    add_cylinder(bm, 0.075, 0.06, along_z((0.0, 0.0, 0.0)), DARK, segments=10, bev=0.015)
    add_cylinder(bm, 0.05, 0.02, along_z((0.0, 0.0, 0.035)), INT, segments=10, bev=0.006)
    add_cylinder(bm, 0.03, 0.08, along_z((0.0, 0.0, -0.07)), DARK, segments=8)
    return finish_mesh(bm, "SM_Sklopka_volant")


def build_needle(name, length):
    # rucicka budika: pivot v strede budika, toci sa okolo svojej osi Z, pri hodnote 0 smeruje hore
    bm = bmesh.new()
    add_box(bm, (length * 0.07, length, 0.003), (0.0, length * 0.38, 0.0), REDPAINT, bev=0.0)
    add_cylinder(bm, length * 0.12, 0.004, along_z((0.0, 0.0, 0.0)), DARK, segments=8)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Korba (pivot = cap sklapania TIP) a bocnice (pivot v pantoch dole)
# ---------------------------------------------------------------------------

def build_bed():
    bm = bmesh.new()
    h = BED_HALF
    length, xc = BED_X1 - BED_X0, (BED_X0 + BED_X1) * 0.5
    # pomocny ram korby na nosnikoch, priecniky, podlaha, okrajove nosniky
    for s in SIDES_LR:
        add_box(bm, (length - 0.05, 0.08, 0.10), (xc, s * RAIL_Y, 0.05), FRAME, bev=0.008)
        add_box(bm, (length, 0.05, 0.08), (xc, s * (h - 0.025), FLOOR_Z - 0.04), ALU, bev=0.008)
    for i in range(9):
        add_box(bm, (0.06, 2.0 * h - 0.04, 0.07), (i * 0.45, 0.0, 0.135), FRAME, bev=0.006)
    add_box(bm, (length, 2.0 * h, 0.012), (xc, 0.0, FLOOR_Z - 0.006), ALU, bev=0.003)
    # cap sklapania, drziak piestu
    for s in SIDES_LR:
        add_cylinder(bm, 0.035, 0.08, along_y((0.0, s * RAIL_Y, 0.0)), STEEL, segments=10)
        add_box(bm, (0.10, 0.01, 0.08), (RAM_TOP.x, s * 0.06, RAM_TOP.z + 0.01), FRAME, bev=0.003)
    add_box(bm, (0.08, 2.0 * RAIL_Y - 0.08, 0.06), (RAM_TOP.x, 0.0, 0.07), FRAME, bev=0.006)
    add_cylinder(bm, 0.016, 0.14, along_y(RAM_TOP), CHROME, segments=6)
    # celo s ochranou kabiny
    fx = BED_X1 - 0.025
    add_box(bm, (0.05, 2.0 * h, 0.75), (fx, 0.0, FLOOR_Z + 0.375), ALU, bev=0.01)
    for z in (0.20, 0.40, 0.60):
        add_box(bm, (0.056, 2.0 * h - 0.08, 0.01), (fx, 0.0, FLOOR_Z + z), DARK)
    add_box(bm, (0.07, 2.0 * h, 0.05), (fx, 0.0, FLOOR_Z + 0.75), ALU, bev=0.012)
    add_prism(bm, quad(fx - 0.025, fx + 0.025, -0.85, 0.85, FLOOR_Z + 0.775),
              quad(fx - 0.025, fx + 0.025, -0.70, 0.70, FLOOR_Z + 1.02), ALU, bev=0.01)
    for y in (-0.35, 0.0, 0.35):
        add_box(bm, (0.056, 0.03, 0.22), (fx, y, FLOOR_Z + 0.89), DARK)
    # zadne stlpiky so zamkami, panty bocnic na okrajoch
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.06, SIDE_H), (BED_X0 + 0.03, s * (h - 0.03), FLOOR_Z + SIDE_H * 0.5), ALU, bev=0.008)
        add_box(bm, (0.065, 0.065, 0.02), (BED_X0 + 0.03, s * (h - 0.03), FLOOR_Z + SIDE_H + 0.01), DARK, bev=0.005)
        for x in (0.4, 1.78, 3.2):
            add_box(bm, (0.08, 0.02, 0.05), (x, s * (h + 0.005), FLOOR_Z - 0.02), STEEL, bev=0.004)
        for y in (0.5, -0.5):
            add_box(bm, (0.02, 0.08, 0.05), (BED_X0 - 0.005, y, FLOOR_Z - 0.02), STEEL, bev=0.004)
    return finish_mesh(bm, "SM_Sklopka_korba")


def build_dropside(length):
    # bocnica (lava): pivot v pante dole na vonkajsej hrane, doska ide hore (+Z), hrubka dnu (-Y)
    bm = bmesh.new()
    t = 0.035
    add_box(bm, (length, t, SIDE_H - 0.02), (0.0, -t * 0.5, SIDE_H * 0.5), ALU, bev=0.006)
    for z in (0.15, 0.30):
        add_box(bm, (length - 0.06, 0.006, 0.012), (0.0, 0.002, z), DARK)
    for z in (0.08, 0.225, 0.37):
        add_box(bm, (length - 0.04, 0.01, 0.035), (0.0, 0.003, z), ALU, bev=0.004)
    add_box(bm, (length, 0.05, 0.035), (0.0, -0.02, SIDE_H - 0.0175), ALU, bev=0.01)
    add_box(bm, (length, 0.045, 0.03), (0.0, -0.02, 0.015), ALU, bev=0.008)
    n = max(2, int(length / 0.9))
    for i in range(n):
        x = -length * 0.5 + length * (i + 0.5) / n
        add_cylinder(bm, 0.016, 0.08, along_x((x, 0.004, 0.0)), STEEL, segments=8)
    for s in SIDES_LR:
        x = s * (length * 0.5 - 0.07)
        add_box(bm, (0.06, 0.02, 0.04), (x, 0.012, SIDE_H - 0.08), DARK, bev=0.005)
        add_rod(bm, (x, 0.024, SIDE_H - 0.08), (x - s * 0.06, 0.024, SIDE_H - 0.11), 0.007, CHROME)
    return bm


def build_ram_body():
    # valec piestu: pivot v spodnom oku na rame, telo smeruje do -X (ku korbe)
    bm = bmesh.new()
    add_cylinder(bm, 0.04, 0.08, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_cylinder(bm, 0.06, 0.85, along_x((-0.455, 0.0, 0.0)), FRAME, segments=12, bev=0.008)
    for x in (-0.06, -0.86):
        add_cylinder(bm, 0.066, 0.025, along_x((x, 0.0, 0.0)), STEEL, segments=12)
    add_cylinder(bm, 0.012, 0.04, along_z((-0.12, 0.0, 0.07)), STEEL, segments=6)
    return finish_mesh(bm, "SM_Sklopka_piest_valec")


def build_ram_rod():
    bm = bmesh.new()
    add_cylinder(bm, 0.03, 0.07, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_cylinder(bm, 0.035, 0.85, along_x((0.455, 0.0, 0.0)), CHROME, segments=10)
    return finish_mesh(bm, "SM_Sklopka_piestnica")


# ---------------------------------------------------------------------------
# Scena a export
# ---------------------------------------------------------------------------

def get_material(name, color, metallic, roughness, emission, alpha):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (color[0], color[1], color[2], alpha)
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
        if alpha < 1.0:
            bsdf.inputs["Alpha"].default_value = alpha
            for attr, value in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                try:
                    setattr(mat, attr, value)
                except Exception:
                    pass
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


def new_object(coll, name, data, location=(0.0, 0.0, 0.0), parent=None, rotation=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, data)
    coll.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.rotation_euler = [math.radians(a) for a in rotation]
    return obj


def place_spinning(coll, name, mesh, frame, parent):
    # objekt s pivotom v osi: lokalna os Z je os otacania (uhol = rotation_euler[2] v rezime ZYX)
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    obj.parent = parent
    obj.rotation_mode = "ZYX"
    obj.location = frame.to_translation()
    obj.rotation_euler = frame.to_3x3().to_euler("ZYX")
    return obj


def key(obj, path, index, frames):
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
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.get("sklopka"):
            bpy.data.meshes.remove(mesh)
    mats = [get_material(*m) for m in MATERIALS]

    parts = {}

    def put(mesh):
        parts[mesh.name[3:]] = mesh

    put(build_chassis())
    put(build_cab())
    put(build_interior())
    put(build_steering_wheel())
    put(build_needle("SM_Sklopka_rucicka_velka", 0.065))
    put(build_needle("SM_Sklopka_rucicka_mala", 0.024))
    put(build_wheel_front())
    put(build_wheel_dual())
    put(build_bed())
    side = build_dropside(BED_X1 - BED_X0 - 0.11)
    side_p = mirror_y(side)
    put(finish_mesh(side, "SM_Sklopka_bocnica_L"))
    put(finish_mesh(side_p, "SM_Sklopka_bocnica_P"))
    rear = build_dropside(2.0 * (BED_HALF - 0.06))
    bmesh.ops.rotate(rear, cent=(0.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, "Z"), verts=rear.verts[:])
    put(finish_mesh(rear, "SM_Sklopka_bocnica_zadna"))
    put(build_ram_body())
    put(build_ram_rod())
    for key_name, mesh in parts.items():
        base = "SM_" + key_name
        if mesh.name != base:
            old = bpy.data.meshes.get(base)
            if old is not None and old.users == 0:
                bpy.data.meshes.remove(old)
                mesh.name = base
        mesh["sklopka"] = 1
        for mat in mats:
            mesh.materials.append(mat)

    # zostava s pohyblivymi dielmi
    root = new_object(coll, "Sklopka", parts["Sklopka_podvozok"])
    new_object(coll, "Sklopka_kabina", parts["Sklopka_kabina"], parent=root)
    new_object(coll, "Sklopka_interier", parts["Sklopka_interier"], parent=root)
    wheel = place_spinning(coll, "Sklopka_volant", parts["Sklopka_volant"], STEERING, root)
    needles = []
    for name, offset, radius, _, idle in GAUGES:
        mesh = parts["Sklopka_rucicka_velka" if radius > 0.05 else "Sklopka_rucicka_mala"]
        needle = place_spinning(coll, "Sklopka_rucicka_" + name,
                                mesh, gauge_frame(offset) @ Matrix.Translation((0.0, 0.0, 0.012)), root)
        needles.append((name, needle, idle))
    for s, side_name in ((1.0, "L"), (-1.0, "P")):
        rot = (0.0, 0.0, 0.0 if s > 0 else 180.0)
        new_object(coll, "Sklopka_koleso_predne_" + side_name, parts["Sklopka_koleso_predne"],
                   (FRONT_X, s * FRONT_SPINDLE, WHEEL_R), root, rot)
        new_object(coll, "Sklopka_koleso_zadne_" + side_name, parts["Sklopka_koleso_zadne"],
                   (0.0, s * REAR_SPINDLE, WHEEL_R), root, rot)
    bed = new_object(coll, "Sklopka_korba", parts["Sklopka_korba"], TIP, root)
    side_x = (BED_X0 + 0.06 + BED_X1 - 0.05) * 0.5
    left = new_object(coll, "Sklopka_bocnica_L", parts["Sklopka_bocnica_L"], (side_x, BED_HALF, FLOOR_Z), bed)
    right = new_object(coll, "Sklopka_bocnica_P", parts["Sklopka_bocnica_P"], (side_x, -BED_HALF, FLOOR_Z), bed)
    back = new_object(coll, "Sklopka_bocnica_zadna", parts["Sklopka_bocnica_zadna"], (BED_X0, 0.0, FLOOR_Z), bed)
    cyl = new_object(coll, "Sklopka_piest_valec", parts["Sklopka_piest_valec"], RAM_BASE, root)
    rod = new_object(coll, "Sklopka_piestnica", parts["Sklopka_piestnica"], RAM_TOP, bed)
    aim_top = new_object(coll, "Sklopka_piest_ciel_hore", None, RAM_TOP, bed)
    aim_low = new_object(coll, "Sklopka_piest_ciel_dole", None, RAM_BASE, root)
    for empty in (aim_top, aim_low):
        empty.empty_display_size = 0.05
        empty.hide_render = True
    track(cyl, aim_top, "TRACK_NEGATIVE_X")
    track(rod, aim_low, "TRACK_X")

    # animacia
    tip, rear_open, side_open = -math.radians(TIP_DEG), -math.radians(REAR_OPEN_DEG), math.radians(SIDE_OPEN_DEG)
    key(back, "rotation_euler", 1, [(1, 0.0), (10, 0.0), (40, rear_open), (175, rear_open), (205, 0.0)])
    key(bed, "rotation_euler", 0 + 1, [(1, 0.0), (45, 0.0), (95, tip), (135, tip), (175, 0.0)])
    key(left, "rotation_euler", 0, [(1, 0.0), (205, 0.0), (235, -side_open), (265, -side_open), (295, 0.0)])
    key(right, "rotation_euler", 0, [(1, 0.0), (205, 0.0), (235, side_open), (265, side_open), (295, 0.0)])
    base_z = wheel.rotation_euler[2]
    key(wheel, "rotation_euler", 2, [(1, base_z), (60, base_z + math.radians(120.0)), (140, base_z - math.radians(120.0)),
                                     (200, base_z)])
    for name, needle, idle in needles:
        z0 = needle.rotation_euler[2]
        if name in ("rychlost", "otacky"):
            peak = 0.6 if name == "rychlost" else 0.75
            key(needle, "rotation_euler", 2, [(1, z0 + gauge_angle(0.0)), (40, z0 + gauge_angle(idle)),
                                              (120, z0 + gauge_angle(peak)), (200, z0 + gauge_angle(idle)),
                                              (260, z0 + gauge_angle(idle))])
        else:
            needle.rotation_euler[2] = z0 + gauge_angle(idle)
    scene.frame_start, scene.frame_end = 1, 300

    # zoznam dielov a pravidla
    lines = ["Sklopka - diely (rozmery X x Y x Z v metroch). Pociatok = zem pod zadnou napravou, predok = +X, lava = +Y.", ""]
    for key_name, mesh in parts.items():
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        lines.append("%-28s %.2f x %.2f x %.2f" % (key_name, max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))

    def vec(v):
        return "(%.3f, %.3f, %.3f)" % tuple(v)

    n_wheel = STEERING.to_3x3() @ Vector((0.0, 0.0, 1.0))
    n_gauge = CLUSTER.to_3x3() @ Vector((0.0, 0.0, 1.0))
    lines += [
        "",
        "Podvozok, kabina, interier: pivot v pociatku (daj ich na 0,0,0).",
        "Kolesa su aj s nabojom a bubnom: pivot na konci napravy, vonkajsia strana +Y, pravu stranu otoc o 180 st. okolo Z.",
        "  predne: (%.2f, +-%.2f, %.2f)   zadne: (0, +-%.2f, %.2f). Tocia sa okolo Y." % (FRONT_X, FRONT_SPINDLE, WHEEL_R, REAR_SPINDLE, WHEEL_R),
        "Korba: pivot v cape sklapania %s, sklopenie = otocenie okolo Y o 0 az -%g st." % (vec(TIP), TIP_DEG),
        "Bocnice (pivot v pantoch, v suradniciach korby):",
        "  L %s, P %s - otvorenie okolo X: L o -%g st., P o +%g st." % (vec((side_x, BED_HALF, FLOOR_Z)), vec((side_x, -BED_HALF, FLOOR_Z)),
                                                                        SIDE_OPEN_DEG, SIDE_OPEN_DEG),
        "  zadna %s - otvorenie okolo Y o -%g st." % (vec((BED_X0, 0.0, FLOOR_Z)), REAR_OPEN_DEG),
        "Piest: valec %s na rame mieri osou -X na piestnicu, piestnica %s (od korby) mieri osou +X na valec." % (vec(RAM_BASE), vec(RAM_TOP)),
        "Volant: pivot v strede %s, os otacania %s (lokalna os Z dielu)." % (vec(WHEEL_CENTER), vec(n_wheel)),
        "Rucicky budikov: pivot v strede budika, os otacania %s (lokalna os Z). Pri otoceni 0 smeruju hore;" % vec(n_gauge),
        "  hodnota 0 = otocenie +135 st. (vlavo dole), maximum = -135 st. (vpravo dole). Stredy budikov:",
    ]
    for name, offset, radius, _, _ in GAUGES:
        lines.append("    %-9s %s" % (name, vec((gauge_frame(offset) @ Matrix.Translation((0.0, 0.0, 0.012))).to_translation())))

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for key_name, mesh in parts.items():
            export_mesh(coll, mesh, "SM_" + key_name)
        with open(os.path.join(EXPORT_DIR, "Sklopka.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    print("\n".join(lines))


main()
