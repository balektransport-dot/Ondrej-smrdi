# Stylizovane low poly odtahovky na pevnom podvozku (4x2, 6x2, 8x2) pre Blender 3.0 a novsi: kabina 3, kolesa s dezenom, nadrze, blatniky a
# svetla ako pri tahacoch (bez tocne). Dva druhy odtahoviek, kazdy v europskom (eu) a americkom (us) style:
#   Plosinova (4x2, 6x2): podram sa sklopi zadkom dole, plosina po nom zjazdi sikmo dole az na zem, navijak s lanom vytiahne odtahovane auto
#     (auto je v scene a po snimkach sa vytiahne a odveze; kolesa sa otacaju).
#   Tazka (6x2, 8x2): vyprostovacia odtahovka na kamiony.
# Ovladanie vlastnostami na objekte auta (panel N -> Item) a animacia (snimky 450 az 900).
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Odtahovky": podkolekcie <Druh>_<styl>_<podvozok> (napr. Plosinova_EU_4x2) a Odtahovky_diely (kazdy diel samostatne s menovkou).
# Ovladanie podvozku (vlastnosti na objekte auta): Vyska_podvozku, Zdvih_napravy (6x2, 8x2), Vyklopenie_kabiny, Kabina_klopenie,
#   Kabina_naklon, Riadenie, Motor (1 = R4, 2 = R6, 3 = V8).
# Predok = +X, lava strana = +Y. Pociatok auta = zem pod prvou prednou napravou.
# Do priecinka Odtahovky v domovskom priecinku ulozi FBX kazdeho dielu a subor Odtahovky.txt.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Odtahovky"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Odtahovky")

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
    ("TH3_Sklo_tmave", (0.02, 0.035, 0.045, 1.0), 0.0, 0.05, 0.0, 0.35),
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
    ("TH_Lak_modry", (0.07, 0.16, 0.28, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("TH_Lak_tyrkysovy", (0.22, 0.60, 0.60, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("TH_Lak_cerveny", (0.50, 0.05, 0.035, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("TH_Zlta", (0.85, 0.60, 0.03, 1.0), 0.0, 0.45, 0.0, 1.0),
    ("TH3_Lak_biely", (0.88, 0.89, 0.90, 1.0), 0.2, 0.35, 0.0, 1.0),
    ("TH3_Akcent_modry", (0.20, 0.30, 0.40, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("TH3_Akcent_oranzovy", (0.85, 0.36, 0.04, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("TH3_Akcent_zeleny", (0.08, 0.40, 0.20, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("NOS_Akcent_cerveny", (0.62, 0.07, 0.05, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("NOS_Akcent_zlty", (0.92, 0.70, 0.05, 1.0), 0.2, 0.40, 0.0, 1.0),
    ("NOS_Kora", (0.20, 0.13, 0.08, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("NOS_Drevo", (0.62, 0.45, 0.25, 1.0), 0.0, 0.80, 0.0, 1.0),
    ("NOS_Pozink", (0.55, 0.57, 0.58, 1.0), 0.6, 0.45, 0.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, PAINT, ALU, BUMPER, GLASS, SEAT, LAMP_OR, LAMP_RED, LAMP_WHITE, RED,
 WHITE, REDPAINT, INT, GAUGE, BEIGE, GREEN, PAINT_BLUE, PAINT_TEAL, PAINT_RED, YELLOW,
 PAINT_WHITE, ACC_BLUE, ACC_ORANGE, ACC_GREEN, ACC_RED, ACC_YELLOW, BARK, WOODCUT, GALV) = range(34)
SIDES_LR = (-1.0, 1.0)
ACCENT = ACC_BLUE          # akcentova farba na kabine (na kazdom tahaci ina)

# kabina sa stavia v svojich suradniciach (ako pri sklopke) a potom sa zvacsi a posunie na tahac
CAB_X0, CAB_X1 = 2.65, 4.25
CAB_HALF = 1.0
BELT = 1.55
ROOF = 2.52
CAB_FLOOR = 1.00
CAB_WHEEL_R = 0.40
CAB_ARCH_X = 3.30

# tahac (m)
WHEEL_R = 0.525            # koleso 22.5"
CAB_SCALE = 1.18
CAB_FLOOR_Z = 1.40         # podlaha kabiny nad zemou (motor sa zmesti pod nu)
CAB_OFFSET = Vector((-CAB_ARCH_X * CAB_SCALE, 0.0, CAB_FLOOR_Z - CAB_FLOOR * CAB_SCALE))
CAB_HINGE = Vector((1.03, 0.0, 0.91))      # cap vyklapania kabiny (vpredu na rame, tesne pod kabinou)
CAB_MATRIX = Matrix.Translation(-CAB_HINGE) @ Matrix.Translation(CAB_OFFSET) @ Matrix.Scale(CAB_SCALE, 4)
CAB_TILT = 0.96                            # vyklopenie kabiny (rad, 55 st.)
CAB_REAR_X = CAB_X0 * CAB_SCALE + CAB_OFFSET.x
CAB_FRONT_X = CAB_X1 * CAB_SCALE + CAB_OFFSET.x
CAB_MOUNT = Vector((CAB_REAR_X - 0.065, 0.55, 1.24))  # zadne uchytenie kabiny (oko na kabine)
CAB_MOUNT_LOW = 0.96                                  # oko na rame pod nim
RAIL_Y = 0.40
FRAME_BOT, FRAME_TOP = 0.80, 1.08
FRAME_FRONT = 0.80
FRONT_SPINDLE = 0.88       # koniec prednej napravy (koleso s nabojom sa nasadi sem)
KINGPIN_Y = 0.86           # cap riadenia (okolo neho sa koleso natoci)
REAR_SPINDLE = 0.743       # koniec hnacej a vlecenej napravy (dvojmontaz)
HUB_LEN = 0.20
SPRING_HALF = 0.70
SPRING_EYE_Z = FRAME_BOT - 0.07
SPRING_SEAT = 0.06
FRONT_SHOCK_LOW = Vector((0.06, 0.56, 0.03))      # od napravy
FRONT_SHOCK_UP = Vector((-0.30, 0.50, FRAME_BOT + 0.10))   # x od napravy, z od zeme
REAR_SHOCK_LOW = Vector((0.12, 0.55, 0.0))
REAR_SHOCK_UP = Vector((0.35, 0.50, FRAME_BOT + 0.15))
SHOCK_PART = 0.34                                 # dlzka valca aj piestnice tlmica
ARM_PIVOT = Vector((0.65, RAIL_Y, 0.66))          # x od napravy, z od zeme
ARM_CLAMP_Z = -0.12                               # rameno pod osou napravy
BAG_BEHIND = 0.32
BAG_BOTTOM_Z = 0.50
GEARBOX_OUT = Vector((-1.30, 0.0, 0.90))          # koniec vystupneho hriadela kazdej nasej prevodovky
PINION_X = 0.40
LIFT_HEIGHT = 0.15
BODY_FOLLOW = 0.6
DEG = 0.017453
STEER_RATIO = 12.0         # volant sa toci 12x viac ako kolesa

# Odtahovky na pevnych podvozkoch (rovnaka kabina, kolesa, nadrze, blatniky a svetla ako tahace, bez tocne)
CONFIGS = [
    {"cfg": "4x2", "axles": [("front", 0.0), ("drive", -4.50)], "rear_end": -6.20, "fifth": -5.30, "tank_x": -1.60, "motor": 1},
    {"cfg": "6x2", "axles": [("front", 0.0), ("drive", -4.60), ("tag", -5.95)], "rear_end": -7.30, "fifth": -6.30, "tank_x": -1.50, "motor": 2},
    {"cfg": "8x2", "axles": [("front", 0.0), ("front", -1.95), ("drive", -5.70), ("tag", -7.05)], "rear_end": -8.40, "fifth": -7.40,
     "tank_x": -3.13, "motor": 3},
]
# (kluc, nazov v scene, akcentova farba, podvozky)
VARIANTS = [("ploso_eu", "Plosinova_EU", ACC_YELLOW, ("4x2", "6x2")), ("ploso_us", "Plosinova_US", ACC_RED, ("4x2", "6x2")),
            ("tazka_eu", "Tazka_EU", ACC_ORANGE, ("6x2", "8x2")), ("tazka_us", "Tazka_US", ACC_BLUE, ("6x2", "8x2"))]
TRUCKS = []
for _i, (_variant, _vname, _accent, _cfgs) in enumerate(VARIANTS):
    for _cfg in CONFIGS:
        if _cfg["cfg"] in _cfgs:
            TRUCKS.append(dict(_cfg, name="%s_%s" % (_vname, _cfg["cfg"]), variant=_variant, paint=PAINT_WHITE, accent=_accent, style=_variant[-2:],
                               x=-22.0 * _i, y=-4.5 * len([t for t in TRUCKS if t["variant"] == _variant])))


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
# Nase motory R4 / R6 / V8 s prevodovkami (ten isty kod ako v skripte Motory),
# zabalene do funkcie, aby sa ich mena nebili s menami tahaca
# ---------------------------------------------------------------------------

def motory():
    COLLECTION = "Motory"
    EXPORT_FBX = True
    EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Motory")
    SPIN_SPEED = 0.25   # otacanie klukovej kladky v radianoch za snimok animacie

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


    def to_world(frame, p):
        return frame @ Vector(p)


    def convex_hull(points):
        pts = sorted(points, key=lambda p: (p[0], p[1]))

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower, upper = [], []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        return lower[:-1] + upper[:-1]


    def add_belt(bm, pulleys, x, width, mat, thickness=0.008, samples=32):
        # remen = obal okolo vsetkych kladiek (y, z, polomer) v rovine YZ
        pts = []
        for cy, cz, r in pulleys:
            for k in range(samples):
                a = 2.0 * math.pi * k / samples
                pts.append((cy + (r + thickness) * math.cos(a), cz + (r + thickness) * math.sin(a), cy, cz, r))
        hull = convex_hull(pts)
        outer = [(p[0], p[1]) for p in hull]
        inner = [(p[2] + (p[0] - p[2]) * p[4] / (p[4] + thickness), p[3] + (p[1] - p[3]) * p[4] / (p[4] + thickness)) for p in hull]
        x0, x1 = x - width * 0.5, x + width * 0.5
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


    def build_pulley(name, r, fan=None, fan_mat=DARK, damper=False, alt_fan=False):
        # kladka s osou po X, pivot v strede (toci sa okolo X)
        bm = bmesh.new()
        w = 0.03
        add_cylinder(bm, r, w, along_x((0.0, 0.0, 0.0)), PULLEY, segments=16, bev=0.004)
        for x in (-w * 0.5 + 0.003, w * 0.5 - 0.003):
            add_cylinder(bm, r * 1.06, 0.006, along_x((x, 0.0, 0.0)), PULLEY, segments=16)
        add_cylinder(bm, r * 0.45, w + 0.016, along_x((0.004, 0.0, 0.0)), DARK, segments=12, bev=0.003)
        add_cylinder(bm, max(0.012, r * 0.16), w + 0.03, along_x((0.008, 0.0, 0.0)), CHROME, segments=6)
        if r > 0.05:
            for k in range(4):
                a = 2.0 * math.pi * (k + 0.5) / 4
                add_cylinder(bm, r * 0.12, 0.004, along_x((w * 0.5 + 0.001, r * 0.70 * math.cos(a), r * 0.70 * math.sin(a))),
                             DARK, segments=8)
        if damper:
            # tlmic kmitov za klukovou kladkou
            add_cylinder(bm, r * 0.92, 0.028, along_x((-w * 0.5 - 0.016, 0.0, 0.0)), DARK, segments=16, bev=0.004)
        if alt_fan:
            # chladiace lopatky alternatora za kladkou
            for k in range(8):
                frame = Matrix.Rotation(math.radians(45.0 * k), 4, "X")
                add_box(bm, (0.012, 0.006, r * 0.9), (-w * 0.5 - 0.008, 0.0, r * 0.95), DARK, rotation=(0.0, 0.0, 20.0), frame=frame)
        if fan:
            blades, fan_r = fan
            add_cylinder(bm, 0.03, 0.06, along_x((w * 0.5 + 0.03, 0.0, 0.0)), DARK, segments=8)
            add_cylinder(bm, 0.06, 0.02, along_x((w * 0.5 + 0.065, 0.0, 0.0)), fan_mat, segments=12, bev=0.004)
            for k in range(blades):
                frame = Matrix.Translation((w * 0.5 + 0.065, 0.0, 0.0)) @ Matrix.Rotation(math.radians(360.0 * k / blades), 4, "X")
                length = fan_r - 0.05
                add_box(bm, (0.008, 0.07, length), (0.0, 0.0, 0.05 + length * 0.5), fan_mat, bev=0.003,
                        rotation=(0.0, 0.0, 28.0), frame=frame)
        return finish_mesh(bm, name)


    def build_front(bm, spec, front, cover_size, cover_center):
        # kryt rozvodov, vodna pumpa, alternator, posilnovac, napinac a remen
        p = spec["pulleys"]
        add_box(bm, (0.04, cover_size[0], cover_size[1]), (front + 0.02, 0.0, cover_center), BLOCK, bev=0.015)
        wy, wz, wr = p["Pumpa"]
        add_cylinder(bm, wr * 0.85, 0.035, along_x((front + 0.035, wy, wz)), BLOCK, segments=10, bev=0.005)

        ay, az, _ = p["Alternator"]
        add_cylinder(bm, 0.065, 0.07, along_x((front + 0.005, ay, az)), HEAD, segments=12, bev=0.008)
        for dx in (-0.015, 0.012):
            add_cylinder(bm, 0.068, 0.006, along_x((front + dx, ay, az)), DARK, segments=12)
        add_box(bm, (0.05, 0.05, 0.05), (front - 0.01, ay * 0.6, az - 0.05), BLOCK)

        if "Posilnovac" in p:
            py, pz, _ = p["Posilnovac"]
            add_cylinder(bm, 0.05, 0.07, along_x((front + 0.005, py, pz)), PULLEY, segments=10, bev=0.006)
            add_cylinder(bm, 0.03, 0.06, along_z((front - 0.02, py, pz + 0.075)), DARK, segments=8, bev=0.004)
            add_cylinder(bm, 0.02, 0.012, along_z((front - 0.02, py, pz + 0.11)), YEL, segments=8)

        ty, tz, _ = p["Napinac"]
        add_box(bm, (0.02, 0.03, 0.10), (front + 0.04, ty - 0.02, tz - 0.045), DARK, rotation=(25.0, 0.0, 0.0))
        add_belt(bm, list(p.values()), front + 0.06, 0.022, RUBBER)


    # ---------------------------------------------------------------------------
    # Radovy motor (R4, R6): predok je +X, sanie na -Y, vyfuk na +Y, zem z = 0
    # ---------------------------------------------------------------------------

    def add_coils(bm, xs, top, frame=None, loom_side=1.0):
        # zapalovacie cievky na kryte ventilov - kolko cievok, tolko valcov
        frame = frame or Matrix()
        for x in xs:
            add_cylinder(bm, 0.02, 0.06, frame @ along_z((x, 0.0, top + 0.02)), DARK, segments=8, bev=0.004)
            add_box(bm, (0.035, 0.03, 0.02), (x, 0.0, top + 0.055), DARK, bev=0.004, frame=frame)
            add_box(bm, (0.012, 0.03, 0.012), (x, loom_side * 0.025, top + 0.05), RUBBER, frame=frame)
        add_rod(bm, to_world(frame, (xs[0] - 0.03, loom_side * 0.04, top + 0.05)),
                to_world(frame, (xs[-1] + 0.03, loom_side * 0.04, top + 0.05)), 0.009, RUBBER)


    def build_inline(spec):
        bm = bmesh.new()
        n, pitch, zc = spec["cylinders"], spec["pitch"], spec["crank_z"]
        length = n * pitch + 0.10
        xs = [(i - (n - 1) * 0.5) * pitch for i in range(n)]
        front, back = length * 0.5, -length * 0.5

        # olejova vana a vypustna skrutka
        add_prism(bm, [(back + 0.03, -0.10, 0.0), (front - 0.03, -0.10, 0.0), (front - 0.03, 0.10, 0.0), (back + 0.03, 0.10, 0.0)],
                  [(back + 0.005, -0.14, 0.14), (front - 0.005, -0.14, 0.14), (front - 0.005, 0.14, 0.14), (back + 0.005, 0.14, 0.14)],
                  DARK, bev=0.01)
        add_cylinder(bm, 0.012, 0.02, along_z((back + 0.06, 0.0, 0.0)), CHROME, segments=6)

        # blok: sirsia spodna cast, horna cast s vypuklinami valcov po oboch bokoch
        add_box(bm, (length, 0.30, 0.10), (0.0, 0.0, 0.19), BLOCK, bev=0.015)
        add_box(bm, (length, 0.26, 0.22), (0.0, 0.0, 0.35), BLOCK, bev=0.02)
        for x in xs:
            for s in SIDES_LR:
                add_cylinder(bm, 0.042, 0.19, along_z((x, s * 0.13, 0.355)), BLOCK, segments=8, bev=0.01)

        # tesnenie, hlava, kryt ventilov s rebrami, skrutkami, cievkami, vieckom a napisom
        add_box(bm, (length + 0.004, 0.264, 0.008), (0.0, 0.0, 0.46), DARK)
        add_box(bm, (length - 0.01, 0.24, 0.10), (0.0, 0.0, 0.51), HEAD, bev=0.015)
        top = 0.66
        add_box(bm, (length - 0.04, 0.20, 0.10), (0.0, 0.0, 0.61), COVER, bev=0.025)
        for s in SIDES_LR:
            add_box(bm, (length - 0.14, 0.012, 0.012), (0.0, s * 0.07, top), COVER)
        for x in xs:
            for s in SIDES_LR:
                add_cylinder(bm, 0.007, 0.012, along_z((x, s * 0.108, 0.566)), CHROME, segments=6)
        add_coils(bm, xs, top)
        add_cylinder(bm, 0.025, 0.02, along_z((xs[0] + pitch * 0.5, -0.06, top + 0.005)), YEL, segments=10, bev=0.004)
        add_text(bm, spec["label"], 0.05, Matrix.Translation((front - 0.11, 0.1005, 0.61)) @ TEXT_SIDE_Y, TEXT)

        # sanie (-Y): zberne potrubie, rurky ku kazdemu valcu, skrtiaca klapka, hadica a filter
        plen_y, plen_z = -0.28, 0.53
        add_cylinder(bm, 0.05, length - 0.08, along_x((0.0, plen_y, plen_z)), INTAKE, segments=10, bev=0.01)
        add_box(bm, (length - 0.03, 0.012, 0.05), (0.0, -0.126, 0.50), INTAKE)
        for x in xs:
            add_rod(bm, (x, plen_y + 0.03, plen_z), (x, -0.13, 0.50), 0.022, INTAKE, segments=8)
        add_cylinder(bm, 0.035, 0.05, along_x((front - 0.015, plen_y, plen_z)), CHROME, segments=10)
        hose_end = (front + 0.07, plen_y - 0.03, plen_z + 0.10)
        add_rod(bm, (front + 0.01, plen_y, plen_z), hose_end, 0.033, RUBBER, segments=8)
        add_rod(bm, hose_end, (front + 0.11, plen_y - 0.05, plen_z + 0.16), 0.05, FILTER, segments=10)

        # vyfuk (+Y): priruba, rurka od kazdeho valca, zberna rura a zvod dole vzadu
        coll_y, coll_z = 0.23, 0.38
        add_box(bm, (length - 0.04, 0.012, 0.05), (0.0, 0.126, 0.50), EXHAUST)
        for x in xs:
            add_rod(bm, (x, 0.12, 0.50), (x, 0.20, 0.47), 0.02, EXHAUST, segments=8)
            add_rod(bm, (x, 0.20, 0.47), (x, coll_y, coll_z), 0.02, EXHAUST, segments=8)
        add_rod(bm, (xs[-1] + 0.02, coll_y, coll_z), (back - 0.04, coll_y, coll_z), 0.032, EXHAUST, segments=8)
        outlet = (back - 0.13, coll_y, coll_z - 0.13)
        add_rod(bm, (back - 0.04, coll_y, coll_z + 0.01), outlet, 0.032, EXHAUST, segments=8)
        add_rod(bm, outlet, (outlet[0] - 0.015, coll_y, outlet[2] - 0.015), 0.045, EXHAUST, segments=8)

        # predok s remenom
        build_front(bm, spec, front, (0.22, 0.38), 0.35)

        # zadna priruba k prevodovke, startér, olejovy filter, meradlo oleja, uchyty
        add_cylinder(bm, 0.17 + 0.01 * n / 2, 0.02, along_x((back - 0.01, 0.0, zc + 0.03)), BLOCK, segments=12, bev=0.005)
        add_cylinder(bm, 0.042, 0.16, along_x((back + 0.06, -0.17, 0.22)), DARK, segments=10, bev=0.006)
        add_cylinder(bm, 0.025, 0.10, along_x((back + 0.08, -0.17, 0.275)), PULLEY, segments=8)
        add_cylinder(bm, 0.04, 0.10, along_y((front - 0.10, -0.20, 0.24)), FILTER, segments=10, bev=0.008)
        add_rod(bm, (0.0, -0.15, 0.30), (0.0, -0.175, 0.70), 0.006, PULLEY)
        add_cylinder(bm, 0.018, 0.012, along_y((0.0, -0.175, 0.71)), YEL, segments=8)
        for s in SIDES_LR:
            add_box(bm, (0.08, 0.06, 0.07), (0.0, s * 0.18, 0.28), DARK, bev=0.01)
        info = dict(front=front, back=back, flange_r=0.17 + 0.01 * n / 2, flange_z=zc + 0.03)
        return finish_mesh(bm, "SM_Motor_" + spec["key"]), info


    # ---------------------------------------------------------------------------
    # V8: dve rady po 4 valce do V (90 stupnov), sanie v strede, velky okruhly vzduchovy filter
    # ---------------------------------------------------------------------------

    def build_v8(spec):
        bm = bmesh.new()
        pitch, zc = spec["pitch"], spec["crank_z"]
        length = 4 * pitch + 0.12
        base_xs = [(i - 1.5) * pitch for i in range(4)]
        front, back = length * 0.5, -length * 0.5

        add_prism(bm, [(back + 0.03, -0.12, 0.0), (front - 0.03, -0.12, 0.0), (front - 0.03, 0.12, 0.0), (back + 0.03, 0.12, 0.0)],
                  [(back + 0.005, -0.17, 0.14), (front - 0.005, -0.17, 0.14), (front - 0.005, 0.17, 0.14), (back + 0.005, 0.17, 0.14)],
                  DARK, bev=0.01)
        add_cylinder(bm, 0.012, 0.02, along_z((back + 0.06, 0.0, 0.0)), CHROME, segments=6)
        add_box(bm, (length, 0.36, 0.20), (0.0, 0.0, 0.24), BLOCK, bev=0.02)

        for s in SIDES_LR:
            # rada valcov naklonena o 45 stupnov; v jej suradniciach je Z pozdlz valcov, vonkajsia strana je Y = s
            frame = Matrix.Translation((0.0, 0.0, zc)) @ Matrix.Rotation(math.radians(-45.0 * s), 4, "X")
            xs = [x + 0.02 * s for x in base_xs]
            add_box(bm, (length - 0.02, 0.21, 0.22), (0.0, 0.0, 0.21), BLOCK, bev=0.02, frame=frame)
            for x in xs:
                add_cylinder(bm, 0.04, 0.18, frame @ along_z((x, s * 0.105, 0.21)), BLOCK, segments=8, bev=0.01)
            add_box(bm, (length - 0.02, 0.214, 0.008), (0.0, 0.0, 0.32), DARK, frame=frame)
            add_box(bm, (length - 0.03, 0.21, 0.09), (0.0, 0.0, 0.365), HEAD, bev=0.015, frame=frame)
            top = 0.50
            add_box(bm, (length - 0.07, 0.18, 0.09), (0.0, 0.0, 0.455), COVER, bev=0.025, frame=frame)
            for x in xs:
                for t in SIDES_LR:
                    add_cylinder(bm, 0.007, 0.012, frame @ along_z((x, t * 0.098, 0.416)), CHROME, segments=6)
            add_coils(bm, xs, top, frame=frame, loom_side=-s)

            # vyfukove zvody na vonkajsej strane
            add_box(bm, (length - 0.05, 0.012, 0.05), (0.0, s * 0.106, 0.36), EXHAUST, frame=frame)
            for x in xs:
                p0 = to_world(frame, (x, s * 0.10, 0.36))
                p1 = to_world(frame, (x, s * 0.17, 0.33))
                p2 = to_world(frame, (x, s * 0.19, 0.25))
                add_rod(bm, p0, p1, 0.02, EXHAUST, segments=8)
                add_rod(bm, p1, p2, 0.02, EXHAUST, segments=8)
            c0 = to_world(frame, (xs[-1] + 0.02, s * 0.19, 0.25))
            c1 = to_world(frame, (back - 0.04, s * 0.19, 0.25))
            add_rod(bm, c0, c1, 0.032, EXHAUST, segments=8)
            outlet = c1 + Vector((-0.09, 0.0, -0.13))
            add_rod(bm, c1 + Vector((0.0, 0.0, 0.01)), outlet, 0.032, EXHAUST, segments=8)
            add_rod(bm, outlet, outlet + Vector((-0.015, 0.0, -0.015)), 0.045, EXHAUST, segments=8)

            # sacie rurky z potrubia v strede k vnutornej strane hlavy
            for x in xs:
                port = to_world(frame, (x, -s * 0.10, 0.36))
                add_rod(bm, (x, s * 0.08, 0.60), port, 0.02, INTAKE, segments=8)

        # sacie potrubie, karburator a velky okruhly vzduchovy filter s napisom
        add_box(bm, (length - 0.10, 0.18, 0.09), (0.0, 0.0, 0.62), INTAKE, bev=0.02)
        add_cylinder(bm, 0.07, 0.06, along_z((0.0, 0.0, 0.69)), INTAKE, segments=12, bev=0.008)
        add_cylinder(bm, 0.18, 0.01, along_z((0.0, 0.0, 0.715)), CHROME, segments=16)
        add_cylinder(bm, 0.17, 0.06, along_z((0.0, 0.0, 0.75)), FILTER, segments=16, bev=0.005)
        for k in range(16):
            a = 2.0 * math.pi * (k + 0.5) / 16
            add_box(bm, (0.012, 0.012, 0.055), (0.172 * math.cos(a), 0.172 * math.sin(a), 0.75), DARK)
        add_cylinder(bm, 0.18, 0.02, along_z((0.0, 0.0, 0.79)), CHROME, segments=16, bev=0.008)
        add_cylinder(bm, 0.015, 0.03, along_z((0.0, 0.0, 0.81)), CHROME, segments=6)
        add_box(bm, (0.06, 0.012, 0.02), (0.0, 0.0, 0.825), CHROME, bev=0.004)
        add_text(bm, spec["label"], 0.11, Matrix.Translation((0.08, 0.0, 0.802)) @ TEXT_TOP, TEXT, depth=0.003)

        build_front(bm, spec, front, (0.34, 0.44), 0.40)

        add_cylinder(bm, 0.24, 0.02, along_x((back - 0.01, 0.0, zc + 0.04)), BLOCK, segments=12, bev=0.005)
        add_cylinder(bm, 0.045, 0.17, along_x((back + 0.07, -0.20, 0.20)), DARK, segments=10, bev=0.006)
        add_cylinder(bm, 0.027, 0.10, along_x((back + 0.09, -0.20, 0.26)), PULLEY, segments=8)
        add_cylinder(bm, 0.045, 0.11, along_y((front - 0.12, -0.21, 0.22)), FILTER, segments=10, bev=0.008)
        for s in SIDES_LR:
            add_box(bm, (0.08, 0.06, 0.07), (0.0, s * 0.21, 0.30), DARK, bev=0.01)
        info = dict(front=front, back=back, flange_r=0.24, flange_z=zc + 0.04)
        return finish_mesh(bm, "SM_Motor_" + spec["key"]), info


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
    # Materialy, scena, otacanie kladiek, export
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


    def engine_materials(spec):
        mats = []
        for slot, slot_name in enumerate(SLOT_NAMES):
            color, metallic, roughness = spec["colors"].get(slot) or SHARED.get(slot) or ALU
            mats.append(get_material("%s_%s" % (spec["key"], slot_name), color, metallic, roughness))
        return mats


    def add_materials(mesh, mats):
        for mat in mats:
            mesh.materials.append(mat)


    def add_spin(obj, ratio):
        # otacanie okolo X podla cisla snimku (prehraj animaciu medzernikom)
        fcurve = obj.driver_add("rotation_euler", 0)
        fcurve.driver.type = "SCRIPTED"
        fcurve.driver.expression = "frame * %.4f" % (-SPIN_SPEED * ratio)
    return dict(locals())


MOTORY = motory()


# ---------------------------------------------------------------------------
# Kabina: stavia sa v suradniciach sklopky, potom sa zvacsi na tahac; pivot = predny cap vyklapania
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
    # boky kabiny su rovne az hore (bez zuzovania)
    return CAB_HALF


# Kabina 3 (podla fotky: hladky moderny predok, tmava predna cast strechy so svetelnym pasom): dlhsia kabina so spacou castou vzadu, sikma strecha (stupa dozadu), velmi sklonene panoramaticke sklo
# (siaha az do rohov), siroka slnecna clona; vnutorny priestor vpredu (interier, volant, budiky) ostava rovnaky
EXT = 0.30                           # o kolko je kabina dlhsia dozadu (v suradniciach kabiny)
XR = CAB_X0 - EXT                    # zadna stena kabiny
Z_REAR, Z_FRONT = 2.95, 2.46         # vyska strechy vzadu a vpredu (strecha je sikma)
RAKE = 0.20                          # o kolko je horna hrana celneho skla za spodnou (velmi sklonene sklo)
ROOF_CF = 0.18                       # zaoblenie predneho rohu strechy
ROOF_FRONT = CAB_X1 - RAKE           # predna hrana strechy
ROOF_REAR = XR + 0.10                # zadna hrana strechy (zadna stena sa hore mierne nakloni dopredu)
SLOPE = (Z_REAR - Z_FRONT) / (ROOF_FRONT - ROOF_REAR)
BOTTOM_REAR = 0.88                   # spodok spacej casti (nad lavkou za kabinou)
WIN_TOP = 2.40                       # vrch bocnych okien (rovny, vodorovny)
STEP_X = 2.79                        # schodiky pod dverami


BULGE = 0.10                         # o kolko sa strecha prehne hore nad priamku (jemny obluk)


def roof_z(x):
    # vyska strechy v mieste x: sikma priamka dozadu stupajuca + jemny obluk (nad kabinou je strecha vyklenuta)
    t = (x - ROOF_REAR) / (ROOF_FRONT - ROOF_REAR)
    return Z_REAR - SLOPE * (x - ROOF_REAR) + BULGE * 4.0 * t * (1.0 - t)


def roof_tilt(x):
    # sklon strechy v mieste x (rad, kladny = strecha klesa dopredu)
    length = ROOF_FRONT - ROOF_REAR
    t = (x - ROOF_REAR) / length
    return math.atan(SLOPE - BULGE * 4.0 * (1.0 - 2.0 * t) / length)


def add_poly_panel(bm, corners, thickness, mat, inward, bev=0.0):
    # tenka stena z n rohov, hrubka smerom dnu
    outer = [bm.verts.new(c) for c in corners]
    inner = [bm.verts.new(c + inward * thickness) for c in corners]
    faces = [bm.faces.new(outer), bm.faces.new(inner[::-1])]
    for i in range(len(corners)):
        j = (i + 1) % len(corners)
        faces.append(bm.faces.new((outer[i], inner[i], inner[j], outer[j])))
    finish_shape(bm, faces, mat, bev)


def add_sections(bm, sections, mat):
    # teleso z rezov (rovnaky pocet bodov v kazdom reze), konce uzavrete
    rings = [[bm.verts.new(p) for p in sec] for sec in sections]
    n = len(rings[0])
    faces = [bm.faces.new(rings[0]), bm.faces.new(rings[-1][::-1])]
    for k in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i])))
    finish_shape(bm, faces, mat, 0.0)


def roof_shell(bm, c_rear):
    # vyklenuta strecha: rezy po dlzke kabiny, vrch sleduje obluk, hrany po bokoch zaoblene; vzadu obluk pokracuje dole
    # (zaoblena zadna hrana) a rohy v pudoryse su zrezane
    xa, xb, steps, rr = ROOF_REAR - 0.02, ROOF_FRONT - 0.12, 14, 0.08

    def section(x):
        d = x - xa
        drop = rr - math.sqrt(max(0.0, rr * rr - (rr - d) ** 2)) if d < rr else 0.0
        cut = max(0.0, c_rear - (x - ROOF_REAR))
        zt, zb = roof_z(x) + 0.02 - drop, roof_z(x) - 0.10
        cz = min(0.08, (zt - zb) * 0.6)
        wb, wt = y_side(zb) + 0.02 - cut, y_side(zt) + 0.01 - cut
        pts = [(-wb, zb), (wb, zb), (wt, zt - cz), (wt - cz * 0.4, zt - cz * 0.4), (wt - cz, zt),
               (-(wt - cz), zt), (-(wt - cz * 0.4), zt - cz * 0.4), (-wt, zt - cz)]
        return [Vector((x, y, z)) for y, z in pts]

    rear = [0.0, 0.015, 0.03, 0.05, 0.075, 0.10, 0.14, 0.18, 0.24]
    xs = [xa + d for d in rear] + [xa + 0.24 + (xb - xa - 0.24) * k / steps for k in range(1, steps + 1)]
    add_sections(bm, [section(x) for x in xs], PAINT)


def screen_x(z):
    # x celneho skla vo vyske z (v osi kabiny)
    return CAB_X1 - RAKE * (z - BELT) / (Z_FRONT - BELT)


def pillar_x(z, c_front=0.14):
    # predna hrana dveri (predny stlpik) vo vyske z: od zrezaneho rohu pri pase po zrezany roh na streche
    x_top = ROOF_FRONT - ROOF_CF
    return (CAB_X1 - c_front) + (x_top - (CAB_X1 - c_front)) * (z - BELT) / (roof_z(x_top) - BELT)


def roof_ring(x0, x1, dz, grow, c_front, c_rear):
    # obrys strechy (8 bodov ako plan()), kazdy bod vo vyske sikmej strechy; boky sa smerom hore zuzuju
    def z_at(x):
        return roof_z(x) + dz

    def half(x):
        return y_side(z_at(x)) + grow

    xa, xb, xc, xd = x0 + c_rear, x1 - c_front, x1, x0
    return [Vector((xa, -half(xa), z_at(xa))), Vector((xb, -half(xb), z_at(xb))),
            Vector((xc, -(half(xc) - c_front), z_at(xc))), Vector((xc, half(xc) - c_front, z_at(xc))),
            Vector((xb, half(xb), z_at(xb))), Vector((xa, half(xa), z_at(xa))),
            Vector((xd, half(xd) - c_rear, z_at(xd))), Vector((xd, -(half(xd) - c_rear), z_at(xd)))]


def at_z(p, q, z):
    # bod na usecke p -> q vo vyske z
    return p.lerp(q, (z - p.z) / (q.z - p.z))


def add_glass_wrap(bm, bottom, top, center, thickness=0.010):
    # suvisle sklo v tvare U (cez dvere, rohy a celo) bez priecnych ramov; dole a hore tenky ram, na koncoch ram stlpika
    n = len(bottom)
    segs = [inward_of(bottom[k], bottom[k + 1], center) for k in range(n - 1)]

    def offset(k):
        n1, n2 = segs[max(k - 1, 0)], segs[min(k, n - 2)]
        mid = (n1 + n2).normalized()
        return mid * (thickness / max(0.5, mid.dot(n1)))

    off = [offset(k) for k in range(n)]
    pb = [bm.verts.new(p) for p in bottom]
    pt = [bm.verts.new(p) for p in top]
    ib = [bm.verts.new(p + o) for p, o in zip(bottom, off)]
    it = [bm.verts.new(p + o) for p, o in zip(top, off)]
    faces = [bm.faces.new((pb[0], pt[0], it[0], ib[0])), bm.faces.new((pb[-1], ib[-1], it[-1], pt[-1]))]
    for k in range(n - 1):
        faces += [bm.faces.new((pb[k], pb[k + 1], pt[k + 1], pt[k])), bm.faces.new((ib[k + 1], ib[k], it[k], it[k + 1])),
                  bm.faces.new((pb[k], ib[k], ib[k + 1], pb[k + 1])), bm.faces.new((pt[k], pt[k + 1], it[k + 1], it[k]))]
    finish_shape(bm, faces, GLASS, 0.0)
    for k in range(n - 1):
        for line, inward in ((bottom, segs[k]), (top, segs[k])):
            add_box_between(bm, line[k] + inward * 0.012, line[k + 1] + inward * 0.012, 0.05, 0.035, DARK, bev=0.006)
    for k in (0, n - 1):
        inward = segs[max(k - 1, 0)] if k else segs[0]
        add_box_between(bm, bottom[k] + inward * 0.012, top[k] + inward * 0.012, 0.05, 0.035, DARK, bev=0.006)


def build_cab():
    bm = bmesh.new()
    h = CAB_HALF
    c_front, c_rear = 0.14, 0.16
    center = Vector(((XR + CAB_X1) * 0.5, 0.0, 0.0))
    gx = CAB_X1

    # spodok po podlahu je duty (pod nim je motor, chladic a ram): bocnice s podbehom, predny a zadny diel
    # so zrezanymi rohmi a podlaha; za podbehom je spodok vyssie (spaca cast visi nad lavkou)
    arch_r, bottom = 0.52, 0.62
    da = math.degrees(math.asin((bottom - CAB_WHEEL_R) / arch_r))
    arch = []
    for k in range(9):
        a = math.radians(180.0 - da - (180.0 - 2.0 * da) * k / 8)
        arch.append((CAB_ARCH_X + arch_r * math.cos(a), CAB_WHEEL_R + arch_r * math.sin(a)))
    xs1 = CAB_X1 - 0.16
    side = [(XR + c_rear, BOTTOM_REAR), (2.70, BOTTOM_REAR), (2.74, bottom)] + arch + [(xs1, bottom), (xs1, CAB_FLOOR), (XR + c_rear, CAB_FLOOR)]
    for s in SIDES_LR:
        add_extruded(bm, side, s * (h - 0.04), s * h, "XZ", PAINT)
    front = [(xs1, bottom), (CAB_X1 - 0.08, bottom), (CAB_X1, bottom + 0.08), (CAB_X1, CAB_FLOOR), (xs1, CAB_FLOOR)]
    rear = [(XR, BOTTOM_REAR), (XR + 0.20, BOTTOM_REAR), (XR + 0.20, CAB_FLOOR), (XR, CAB_FLOOR)]
    for outline, x_edge, chamfer in ((front, CAB_X1, c_front), (rear, XR, c_rear)):
        before = set(bm.faces)
        add_extruded(bm, outline, -h, h, "XZ", PAINT)
        edges = {e for f in bm.faces if f not in before for e in f.edges
                 if all(abs(v.co.x - x_edge) < 0.001 and abs(v.co.y) > h - 0.001 for v in e.verts)}
        bevel(bm, edges, chamfer, PAINT)
    yw = h - 0.08
    add_extruded(bm, [(XR + 0.04, -(yw - 0.12)), (XR + 0.16, -yw), (xs1, -yw), (xs1, yw), (XR + 0.16, yw), (XR + 0.04, yw - 0.12)],
                 CAB_FLOOR - 0.03, CAB_FLOOR, "XY", PAINT)
    add_extruded(bm, [(XR + 0.04, -(yw - 0.12)), (XR + 0.16, -yw), (2.70, -yw), (2.70, yw), (XR + 0.16, yw), (XR + 0.04, yw - 0.12)],
                 BOTTOM_REAR, BOTTOM_REAR + 0.03, "XY", DARK)

    # steny od podlahy po okna (duta kabina), po obryse so zrezanymi rohmi
    belt = plan(XR, CAB_X1, h, c_front, c_rear, BELT)
    low = plan(XR, CAB_X1, h, c_front, c_rear, CAB_FLOOR - 0.03)
    for i in range(8):
        j = (i + 1) % 8
        n = inward_of(low[i], low[j], center)
        add_quad_panel(bm, [low[i], low[j], belt[j], belt[i]], 0.03, PAINT, n)

    # horna cast: panoramaticke sklo (stred aj rohy), dvere s oknom lichobeznikoveho tvaru podla strechy,
    # spaca cast s velkym oknom, zadna stena s oknom
    roof = roof_ring(ROOF_REAR, ROOF_FRONT, 0.0, 0.0, ROOF_CF, c_rear)
    door_glass = {}
    for i in range(8):
        j = (i + 1) % 8
        a0, a1, b1, b0 = belt[i], belt[j], roof[j], roof[i]
        n = inward_of(a0, a1, center)
        if i in (5, 6, 7):                              # zadna stena: horna hrana pod zaoblenou strechou
            b1, b0 = at_z(a1, b1, b1.z - 0.06), at_z(a0, b0, b0.z - 0.06)
        if i in (1, 2, 3):                             # nad suvislym sklom tmavy pas (schovany pod strechou)
            add_quad_panel(bm, [at_z(a0, b0, WIN_TOP), at_z(a1, b1, WIN_TOP), b1, b0], 0.03, DARK, n, bev=0.004)
        elif i in (0, 4):                              # boky: zadny panel, okno spacej casti, dvere s oknom
            rb, fb, rt, ft = (belt[0], belt[1], roof[0], roof[1]) if i == 0 else (belt[5], belt[4], roof[5], roof[4])

            def B(x, rb=rb, fb=fb):
                return rb.lerp(fb, (x - rb.x) / (fb.x - rb.x))

            sgn = 1.0 if i == 4 else -1.0

            def T(x, sgn=sgn):
                # bod na hrane strechy (obluk) v mieste x
                z = roof_z(x)
                return Vector((x, sgn * y_side(z), z))

            def arc(xa, xb, count):
                # body na obluku od xa po xb bez krajnych bodov
                return [T(xa + (xb - xa) * k / (count + 1)) for k in range(1, count + 1)]

            add_poly_panel(bm, [rb, B(2.68), T(2.70)] + arc(2.70, rt.x, 1) + [rt], 0.03, PAINT, n, bev=0.004)
            q0, q1, q2, q3 = B(2.68), B(2.97), T(2.99), T(2.70)
            w0, w3 = at_z(q0, q3, BELT + 0.20), at_z(q0, q3, WIN_TOP)
            w1, w2 = at_z(q1, q2, BELT + 0.20), at_z(q1, q2, WIN_TOP)
            add_window(bm, w0, w1, w2, w3, n)
            add_quad_panel(bm, [q0, q1, w1, w0], 0.03, PAINT, n, bev=0.004)
            add_poly_panel(bm, [w3, w2, q2] + arc(2.99, 2.70, 2) + [q3], 0.03, PAINT, n, bev=0.004)
            d0, d1, d2, d3 = B(2.97), fb, ft, T(2.99)
            e0, e1 = at_z(d0, d3, WIN_TOP), at_z(d1, d2, WIN_TOP)
            door_glass[i] = (d0, d1, e1, e0)
            add_poly_panel(bm, [e0, e1, d2] + arc(ft.x, 2.99, 3) + [d3], 0.03, PAINT, n, bev=0.004)
            add_box_between(bm, e0.lerp(d3, 0.45) - n * 0.003, e1.lerp(d2, 0.45) - n * 0.003, 0.006, 0.006, DARK)
            add_box_between(bm, d0 + n * 0.02, d3 + n * 0.02, 0.07, 0.07, PAINT, bev=0.01)
        elif i == 6:                                   # zadna stena s oknom
            add_quad_panel(bm, [a0, a1, b1, b0], 0.03, PAINT, n, bev=0.004)
            mid = (BELT + Z_REAR) * 0.5 + 0.03
            lean = 0.10 / (Z_REAR - BELT)
            xw = XR + lean * (mid - BELT) - 0.003
            tilt = math.degrees(math.atan(lean))
            add_box(bm, (0.01, 1.0, 0.46), (xw, 0.0, mid), GLASS, rotation=(0.0, tilt, 0.0))
            add_box(bm, (0.008, 1.06, 0.52), (xw + 0.004, 0.0, mid), DARK, rotation=(0.0, tilt, 0.0))
            for y in (-0.60, 0.0, 0.60):
                zl = Z_REAR - 0.24
                add_box(bm, (0.016, 0.12, 0.04), (XR + lean * (zl - BELT) - 0.006, y, zl), LAMP_RED, bev=0.004, rotation=(0.0, tilt, 0.0))
        else:
            add_quad_panel(bm, [a0, a1, b1, b0], 0.03, PAINT, n, bev=0.004)

    # panoramaticke sklo v jednom celku: pravy bok - rohy - celo - lavy bok (bez ramov medzi dverami a celnym sklom)
    gr, gl = door_glass[0], door_glass[4]
    glass_bottom = [gr[0], gr[1], belt[2], belt[3], gl[1], gl[0]]
    glass_top = [gr[3], gr[2], at_z(belt[2], roof[2], WIN_TOP), at_z(belt[3], roof[3], WIN_TOP), gl[2], gl[3]]
    add_glass_wrap(bm, glass_bottom, glass_top, center)

    # sikma strecha; vpredu tmava zaoblena predna cast (clona) so svetelnym pasom, znackou a smerovkami, dve antenky, okno
    roof_shell(bm, c_rear)
    add_loft(bm, roof_ring(ROOF_FRONT - 0.14, ROOF_FRONT + 0.19, -0.14, 0.0, ROOF_CF, 0.02),
             roof_ring(ROOF_FRONT - 0.14, ROOF_FRONT + 0.16, 0.03, -0.02, ROOF_CF, 0.02), DARK, bev=0.012)
    vx, vz = ROOF_FRONT + 0.178, roof_z(ROOF_FRONT + 0.178) - 0.045
    add_box(bm, (0.014, 1.04, 0.05), (vx, 0.0, vz), LAMP_WHITE, bev=0.004, rotation=(0.0, -15.0, 0.0))
    add_cylinder(bm, 0.06, 0.016, place((vx + 0.006, 0.0, vz), (0.0, 75.0, 0.0)), CHROME, segments=10)
    add_cylinder(bm, 0.042, 0.018, place((vx + 0.008, 0.0, vz), (0.0, 75.0, 0.0)), DARK, segments=10)
    for y in (-0.80, 0.80):
        add_box(bm, (0.014, 0.10, 0.045), (vx - 0.004, y, vz), LAMP_OR, bev=0.004, rotation=(0.0, -15.0, 0.0))
    for y in (-0.80, 0.80):
        ax, az = ROOF_FRONT - 0.24, roof_z(ROOF_FRONT - 0.24) + 0.02
        add_box(bm, (0.06, 0.05, 0.03), (ax, y, az), DARK, bev=0.008)
        add_rod(bm, (ax, y, az), (ax + 0.035, y * 0.98, az + 0.34), 0.008, DARK, segments=5)
        add_cylinder(bm, 0.014, 0.03, along_z((ax + 0.035, y * 0.98, az + 0.35)), DARK, segments=6)
    hatch = Matrix.Translation((3.25, 0.0, roof_z(3.25) + 0.02)) @ Matrix.Rotation(roof_tilt(3.25), 4, "Y")
    add_box(bm, (0.32, 0.64, 0.012), (0.0, 0.0, 0.0), GLASS, frame=hatch)
    for dy in (0.34, -0.34):
        add_box(bm, (0.34, 0.03, 0.024), (0.0, dy, 0.006), DARK, bev=0.004, frame=hatch)
    for dx in (0.17, -0.17):
        add_box(bm, (0.03, 0.70, 0.024), (dx, 0.0, 0.006), DARK, bev=0.004, frame=hatch)

    # boky: linia pod oknami, kluka dveri, smerovka, lem podbehu, schodiky, zrkadla
    side_x0 = 2.90
    door_x1 = CAB_X1 - c_front - 0.03
    for s in SIDES_LR:
        yo = s * (h + 0.003)
        add_box(bm, (door_x1 - side_x0, 0.014, 0.020), ((door_x1 + side_x0) * 0.5, s * (h + 0.005), 1.24), CHROME, bev=0.005)
        add_box(bm, (door_x1 - 3.0, 0.012, 0.05), ((door_x1 + 3.0) * 0.5, s * (h + 0.004), 1.12), ACCENT, bev=0.004)
        add_box(bm, (door_x1 - XR - 0.20, 0.012, 0.045), ((door_x1 + XR + 0.10) * 0.5, s * (h + 0.004), 0.99), DARK, bev=0.004)
        for x in (2.97, door_x1):
            add_box(bm, (0.006, 0.006, BELT - 0.96), (x, yo, (BELT + 0.96) * 0.5), DARK)
        add_box(bm, (door_x1 - 2.97, 0.006, 0.006), ((door_x1 + 2.97) * 0.5, yo, 0.96), DARK)
        add_box(bm, (0.17, 0.012, 0.060), (3.08, s * (h + 0.008), 1.40), DARK, bev=0.006)
        add_box(bm, (0.14, 0.022, 0.030), (3.08, s * (h + 0.017), 1.40), CHROME, bev=0.006)
        add_box(bm, (0.05, 0.012, 0.05), (2.90, s * (h + 0.006), 1.10), LAMP_OR, bev=0.003, rotation=(0.0, 45.0, 0.0))
        add_box(bm, (0.065, 0.008, 0.065), (2.90, s * (h + 0.002), 1.10), DARK, rotation=(0.0, 45.0, 0.0))
        flare = [(arch_r - 0.005, s * (h - 0.01)), (arch_r + 0.08, s * (h - 0.01)),
                 (arch_r + 0.08, s * (h + 0.025)), (arch_r + 0.02, s * (h + 0.045))]
        add_transformed(bm, Matrix.Translation((CAB_ARCH_X, 0.0, CAB_WHEEL_R)), sweep_profile, flare, da, 180.0 - da, 5, DARK)
        # trojity schodik so zlabkami pod dverami
        for z in (0.50, 0.34):
            add_box(bm, (0.26, 0.19, 0.035), (STEP_X, s * (h - 0.09), z), DARK, bev=0.006)
            for k in range(4):
                add_box(bm, (0.24, 0.012, 0.012), (STEP_X, s * (h - 0.09) + s * (-0.07 + k * 0.046), z + 0.0245), BUMPER)
        for x in (STEP_X - 0.10, STEP_X + 0.10):
            add_box(bm, (0.02, 0.02, 0.46), (x, s * (h - 0.09), 0.50), DARK)
        # zrkadla: jedno rameno z predneho stlpika, telo vo farbe kabiny, siroky uhol dole
        mx, my, mz = pillar_x(2.0) + 0.065, h + 0.27, 1.97
        ux, uz = ROOF_FRONT - 0.02, roof_z(ROOF_FRONT - 0.02) - 0.07            # horne rameno z boku tmavej casti strechy
        add_box(bm, (0.08, 0.05, 0.08), (ux, s * (h + 0.012), uz), DARK, bev=0.012)
        add_rod(bm, (ux, s * (h + 0.012), uz), (mx - 0.02, s * (my - 0.04), mz + 0.12), 0.014, DARK, segments=6)
        lx, lz = pillar_x(BELT + 0.05), BELT + 0.06                                # dolne rameno z pasu pod sklom
        add_box(bm, (0.07, 0.05, 0.06), (lx, s * (h + 0.012), lz), DARK, bev=0.012)
        add_rod(bm, (lx, s * (h + 0.012), lz), (mx - 0.02, s * (my - 0.04), mz - 0.12), 0.012, DARK, segments=6)
        add_box(bm, (0.055, 0.13, 0.40), (mx, s * my, mz), DARK, bev=0.016)
        add_box(bm, (0.006, 0.11, 0.35), (mx - 0.0295, s * my, mz), CHROME)
        add_box(bm, (0.045, 0.12, 0.13), (mx, s * (my - 0.01), 1.66), DARK, bev=0.014)
        add_box(bm, (0.006, 0.10, 0.10), (mx - 0.0235, s * (my - 0.01), 1.66), CHROME)
        add_box(bm, (0.02, 0.05, 0.03), (mx + 0.0275, s * (my + 0.02), mz - 0.19), LAMP_OR, bev=0.004)
        # predne svetla: tenke sikme listy po stranach spodnej masky, smerovky na zrezanych rohoch, hmlovky
        blade = [(0.64, 0.80), (0.74, 0.80), (0.86, 1.12), (0.76, 1.16)]
        inner = [(0.675, 0.84), (0.715, 0.84), (0.805, 1.10), (0.765, 1.12)]
        add_extruded_yz(bm, [(s * y, z) for y, z in blade], gx, gx + 0.026, DARK, bev=0.006)
        add_extruded_yz(bm, [(s * y, z) for y, z in inner], gx + 0.020, gx + 0.034, LAMP_WHITE)
        add_box(bm, (0.014, 0.09, 0.08), (CAB_X1 - c_front * 0.5 + 0.004, s * (h - c_front * 0.5 + 0.004), 1.00),
                LAMP_OR, bev=0.004, rotation=(0.0, 0.0, s * 45.0))
        add_cylinder(bm, 0.040, 0.020, along_x((gx + 0.010, s * 0.68, 0.705)), CHROME, segments=8)
        add_cylinder(bm, 0.030, 0.020, along_x((gx + 0.018, s * 0.68, 0.705)), LAMP_WHITE, segments=8)
        # stierace na sklonenom skle
        add_rod(bm, (screen_x(BELT + 0.05) + 0.012, s * 0.06, BELT + 0.05), (screen_x(BELT + 0.13) + 0.012, s * 0.66, BELT + 0.13), 0.008, DARK)
    # pravy bok spacej casti: dvierka skrinky; lavy bok ma vtavene nasavanie (samostatny diel)
    add_box(bm, (0.30, 0.008, 0.34), (2.66, -(h + 0.004), 1.28), DARK, bev=0.004)
    add_box(bm, (0.26, 0.012, 0.30), (2.66, -(h + 0.006), 1.28), PAINT, bev=0.004)
    add_box(bm, (0.05, 0.016, 0.025), (2.76, -(h + 0.016), 1.30), CHROME, bev=0.004)

    # predok: tmavy pas pod sklom, perforovana horna mriezka a tmava stitok pod nou, siroka spodna maska s ryhami a znackou
    add_box(bm, (0.016, 1.66, 0.06), (gx + 0.006, 0.0, 1.52), DARK, bev=0.008)
    add_box(bm, (0.014, 0.92, 0.17), (gx + 0.006, 0.0, 1.26), ALU, bev=0.02)
    for k in range(5):
        add_box(bm, (0.018, 0.88, 0.006), (gx + 0.007, 0.0, 1.195 + k * 0.03), DARK)
    add_box(bm, (0.014, 0.30, 0.034), (gx + 0.005, 0.0, 1.14), ACCENT, bev=0.012)
    add_box(bm, (0.020, 1.20, 0.28), (gx + 0.008, 0.0, 0.90), DARK, bev=0.03)
    for k in range(15):
        add_box(bm, (0.026, 0.012, 0.25), (gx + 0.009, -0.56 + k * 0.08, 0.90), STEEL)
    for k in range(5):
        add_box(bm, (0.028, 1.14, 0.008), (gx + 0.010, 0.0, 0.80 + k * 0.055), DARK)
    for z in (0.765, 1.035):
        add_box(bm, (0.030, 1.24, 0.016), (gx + 0.010, 0.0, z), CHROME, bev=0.004)
    for y in (-0.615, 0.615):
        add_box(bm, (0.030, 0.016, 0.286), (gx + 0.010, y, 0.90), CHROME, bev=0.004)
    add_cylinder(bm, 0.085, 0.030, along_x((gx + 0.032, 0.0, 1.03)), CHROME, segments=12, bev=0.004)
    add_cylinder(bm, 0.068, 0.034, along_x((gx + 0.034, 0.0, 1.03)), DARK, segments=12)
    add_box(bm, (0.040, 0.13, 0.016), (gx + 0.040, 0.0, 1.03), CHROME, bev=0.003, rotation=(45.0, 0.0, 0.0))
    # na tahac: zvacsit, posunut, pivot do predneho capu vyklapania
    bmesh.ops.transform(bm, matrix=CAB_MATRIX, verts=bm.verts[:])
    lug_z = (CAB_OFFSET.z + bottom * CAB_SCALE - CAB_HINGE.z) * 0.5
    for s in SIDES_LR:
        for d in SIDES_LR:
            add_box(bm, (0.07, 0.012, 0.10), (0.0, s * RAIL_Y + d * 0.055, lug_z), FRAME, bev=0.003)
        mount = CAB_MOUNT - CAB_HINGE
        for d in SIDES_LR:
            add_box(bm, (0.10, 0.012, 0.11), (mount.x + 0.005, s * mount.y + d * 0.04, mount.z + 0.01), FRAME, bev=0.003)
        add_box(bm, (0.10, 0.10, 0.012), (mount.x + 0.005, s * mount.y, mount.z + 0.066), FRAME, bev=0.003)
    return finish_mesh(bm, "SM_Odt_kabina")


def build_intake():
    # nasavanie vzduchu vtavene do laveho boku kabiny (spodny zadny roh spacej casti): rama vo farbe kabiny a rebra;
    # pivot = predny cap kabiny, ako pri kabine
    bm = bmesh.new()
    h = CAB_HALF
    cx, cz = 2.69, 1.29
    y = h + 0.004
    add_box(bm, (0.30, 0.010, 0.52), (cx, y, cz), DARK, bev=0.004)
    for dz in (-0.27, 0.27):
        add_box(bm, (0.34, 0.030, 0.030), (cx, y + 0.012, cz + dz), PAINT, bev=0.008)
    for dx in (-0.16, 0.16):
        add_box(bm, (0.030, 0.030, 0.56), (cx + dx, y + 0.012, cz), PAINT, bev=0.008)
    for k in range(7):
        add_box(bm, (0.26, 0.016, 0.040), (cx, y + 0.012, cz - 0.21 + k * 0.07), BUMPER, bev=0.004, rotation=(-28.0, 0.0, 0.0))
    bmesh.ops.transform(bm, matrix=CAB_MATRIX, verts=bm.verts[:])
    return finish_mesh(bm, "SM_Odt_nasavanie")


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
    add_box(bm, (4.13 - XR - 0.18, 2.0 * h - 0.20, 0.01), ((XR + 0.18 + 4.13) * 0.5, 0.0, CAB_FLOOR + 0.005), SEAT)
    add_prism(bm, quad(2.75, 3.80, -0.24, 0.24, CAB_FLOOR), quad(2.85, 3.70, -0.19, 0.19, 1.30), INT, bev=0.02)
    add_box(bm, (0.01, 1.62, BELT - CAB_FLOOR), (XR + 0.035, 0.0, (BELT + CAB_FLOOR) * 0.5), INT)
    add_box(bm, (1.50, 2.0 * h - 0.30, 0.01), (3.20, 0.0, roof_z(3.20) - 0.06), INT, rotation=(0.0, math.degrees(roof_tilt(3.20)), 0.0))

    # palubna doska (bocny profil vytiahnuty na sirku kabiny)
    dash = [(4.19, CAB_FLOOR), (4.19, 1.60), (3.97, 1.645), (3.90, 1.56), (3.93, 1.30), (4.05, 1.15), (4.10, CAB_FLOOR)]
    add_extruded(bm, dash, -0.86, 0.86, "XZ", INT, bev=0.02)
    add_box(bm, (0.20, 0.50, 0.03), (4.06, -0.35, 1.655), INT, bev=0.01)
    for y in (-0.72, -0.05, 0.75):
        add_box(bm, (0.012, 0.12, 0.05), (3.905, y, 1.52), GAUGE, bev=0.004, rotation=(0.0, -20.0, 0.0))
    add_box(bm, (0.012, 0.18, 0.05), (3.915, -0.35, 1.40), GAUGE, bev=0.004, rotation=(0.0, -12.0, 0.0))

    # prostredna konzola natocena k vodicovi so spinacmi
    console = Matrix.Translation((3.96, 0.02, 1.46)) @ Matrix.Rotation(math.radians(-22.0), 4, "Z")
    add_box(bm, (0.26, 0.46, 0.30), (0.0, 0.0, 0.0), INT, bev=0.025, frame=console)
    for row in range(3):
        for col in range(4):
            mat = (LAMP_OR, GREEN, WHITE, LAMP_RED)[(row + col) % 4] if row == 0 else GAUGE
            add_box(bm, (0.01, 0.07, 0.04), (-0.13, -0.15 + col * 0.10, 0.07 - row * 0.08), mat, bev=0.004, frame=console)
    add_box(bm, (0.01, 0.30, 0.06), (-0.13, 0.0, -0.13), GAUGE, bev=0.004, frame=console)

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
    # spaca cast za sedadlami: lozko so skrinkou pod nim, matrac, vankuse, horne skrinky
    bx0, bx1 = XR + 0.10, 2.94
    bl, bc = bx1 - bx0, (bx0 + bx1) * 0.5
    add_box(bm, (bl, 2.0 * h - 0.20, 0.30), (bc, 0.0, CAB_FLOOR + 0.16), INT, bev=0.02)
    add_box(bm, (bl - 0.02, 2.0 * h - 0.28, 0.11), (bc, 0.0, CAB_FLOOR + 0.365), BEIGE, bev=0.035)
    for y in (-0.40, 0.40):
        add_box(bm, (0.17, 0.62, 0.07), (bx0 + 0.15, y, CAB_FLOOR + 0.455), WHITE, bev=0.03)
        add_box(bm, (0.20, 0.80, 0.32), (bx0 + 0.10, y * 1.15, 2.20), INT, bev=0.02)
    bmesh.ops.transform(bm, matrix=CAB_MATRIX, verts=bm.verts[:])
    return finish_mesh(bm, "SM_Odt_interier")


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
    bmesh.ops.scale(bm, vec=(CAB_SCALE, CAB_SCALE, CAB_SCALE), verts=bm.verts[:])
    return finish_mesh(bm, "SM_Odt_volant")


def build_needle(name, length):
    # rucicka budika: pivot v strede budika, toci sa okolo svojej osi Z, pri hodnote 0 smeruje hore
    bm = bmesh.new()
    add_box(bm, (length * 0.07, length, 0.003), (0.0, length * 0.38, 0.0), REDPAINT, bev=0.0)
    add_cylinder(bm, length * 0.12, 0.004, along_z((0.0, 0.0, 0.0)), DARK, segments=8)
    bmesh.ops.scale(bm, vec=(CAB_SCALE, CAB_SCALE, CAB_SCALE), verts=bm.verts[:])
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Posuvna tocna (pivot v strede spodku kolajnic, dosadne na vrch ramu; zarez sa otvara dozadu = -X)
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


FIFTH_RAIL_Y, FIFTH_RAIL_LEN = 0.40, 1.20
FIFTH_SLIDE = 0.28          # vozik s platnou sa posuva o +-0.28 m








# ---------------------------------------------------------------------------
# Pomocky
# ---------------------------------------------------------------------------

def add_transformed(bm, matrix, fn, *args, **kwargs):
    # vytvor tvar v pociatku a preloz/otoc ho maticou
    before = set(bm.verts)
    fn(bm, *args, **kwargs)
    bmesh.ops.transform(bm, matrix=matrix, verts=[v for v in bm.verts if v not in before])


def track_frame(origin, target):
    # osi dielu, ktory z bodu origin mieri osou -X na target (v kludovej polohe, otocenie len okolo Y)
    x_axis = -(Vector(target) - Vector(origin)).normalized()
    z_axis = Vector((-x_axis.z, 0.0, x_axis.x))
    return x_axis, z_axis


def to_local(point, origin, x_axis, z_axis):
    rel = Vector(point) - Vector(origin)
    return Vector((rel.dot(x_axis), 0.0, rel.dot(z_axis)))


def add_coil(bm, center, radius, z_top, z_bottom, turns, mat, wire=0.011):
    # spiralova hadica (vzduch / elektrina) visiaca zvislo
    steps = turns * 8
    pts = [Vector((center[0] + radius * math.cos(math.pi * k / 4.0), center[1] + radius * math.sin(math.pi * k / 4.0),
                   z_top - (z_top - z_bottom) * k / steps)) for k in range(steps + 1)]
    for a, b in zip(pts, pts[1:]):
        add_rod(bm, a, b, wire, mat, segments=5)
    return pts[0], pts[-1]


# ---------------------------------------------------------------------------
# Kolesa 22.5" s nabojom a bubnom (pivot na konci napravy, os Y, vonkajsia strana +Y)
# ---------------------------------------------------------------------------

RIM_R = 0.286
TIRE_W = 0.27


def add_arc_block(bm, a0, a1, y0, y1, r_in, r_out, mat, lean=0.0, chamfer=0.006):
    # blok dezenu: kus prstenca medzi uhlami a0..a1 a okrajmi y0..y1, vonkajsia plocha je zrazena; lean = sikme polozenie bloku
    def ang(a, y):
        return a + lean * (y - y0) / (y1 - y0)

    def pt(r, a, y):
        return bm.verts.new((r * math.cos(a), y, r * math.sin(a)))

    ya, yb = y0 + chamfer, y1 - chamfer
    i00, i10, i11, i01 = pt(r_in, ang(a0, y0), y0), pt(r_in, ang(a1, y0), y0), pt(r_in, ang(a1, y1), y1), pt(r_in, ang(a0, y1), y1)
    o00, o10, o11, o01 = pt(r_out, ang(a0, ya), ya), pt(r_out, ang(a1, ya), ya), pt(r_out, ang(a1, yb), yb), pt(r_out, ang(a0, yb), yb)
    faces = [bm.faces.new(v) for v in ((o00, o10, o11, o01), (i00, o00, o01, i01), (i10, i11, o11, o10),
                                       (i00, i10, o10, o00), (i01, o01, o11, i11), (i00, i01, i11, i10))]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    set_material(faces, mat)


DRIVE_TREAD_N = 30
DRIVE_TREAD_ROWS = (-0.082, 0.0, 0.082)
DRIVE_TREAD_ROW_W = 0.066


def add_truck_tire(bm, y, width=TIRE_W, tread=False):
    # tread = False: jednoduchy behun (predne kolesa); tread = True: zaberova guma s hrubymi blokmi v tvare V (zadne kolesa)
    if tread:
        step = 2.0 * math.pi / DRIVE_TREAD_N
        carc_r = WHEEL_R - 0.034
        add_ring(bm, carc_r, RIM_R + 0.02, width, y, DARK, 28, bev=width * 0.14)
        for row, yc in enumerate(DRIVE_TREAD_ROWS):
            lean = step * 0.55 * (1.0 if yc < 0.0 else -1.0 if yc > 0.0 else 0.0)
            shift = 0.5 * (row % 2)
            for i in range(DRIVE_TREAD_N):
                a0 = step * (i + shift) + step * 0.10
                add_arc_block(bm, a0, a0 + step * 0.80, y + yc - DRIVE_TREAD_ROW_W * 0.5, y + yc + DRIVE_TREAD_ROW_W * 0.5,
                              carc_r - 0.004, WHEEL_R, TIRE, lean, 0.008)
        for s in SIDES_LR:
            face = y + s * width * 0.5
            y0, y1 = (face - 0.001, face + 0.003) if s > 0 else (face - 0.003, face + 0.001)
            for k in range(24):
                a0 = 2.0 * math.pi * k / 24
                add_arc_block(bm, a0, a0 + 0.07, y0, y1, 0.395, 0.435 if k % 3 == 0 else 0.425, DARK, 0.0, 0.0005)
            add_ring(bm, 0.37, 0.362, 0.006, y + s * (width * 0.5 - 0.001), DARK, 28)
            add_ring(bm, RIM_R + 0.032, RIM_R - 0.012, 0.018, y + s * (width * 0.5 - 0.004), RIM, 20)
        add_ring(bm, RIM_R, RIM_R - 0.012, width - 0.03, y, RIM, 20)
        return
    add_ring(bm, WHEEL_R - 0.015, RIM_R + 0.02, width, y, TIRE, 26, bev=width * 0.16)
    for s in SIDES_LR:
        add_ring(bm, WHEEL_R, WHEEL_R - 0.035, width * 0.36, y + s * width * 0.24, TIRE, 26)   # behun s drazkou
        add_ring(bm, 0.445, 0.437, 0.006, y + s * (width * 0.5 - 0.001), DARK, 26)
        add_ring(bm, RIM_R + 0.032, RIM_R - 0.012, 0.018, y + s * (width * 0.5 - 0.004), RIM, 20)
    add_ring(bm, RIM_R, RIM_R - 0.012, width - 0.03, y, RIM, 20)


def add_wheel_disc(bm, y0, y1, holes):
    add_cylinder(bm, RIM_R - 0.01, y1 - y0, along_y((0.0, (y0 + y1) * 0.5, 0.0)), RIM, segments=20)
    ring_of(bm, 10, 0.215, y1 if holes > 0 else y0, 0.03, 0.006, DARK, segments=8, offset=0.5)


def add_hub_drum(bm, length=HUB_LEN):
    add_cylinder(bm, 0.22, 0.014, along_y((0.0, 0.007, 0.0)), STEEL, segments=16)
    add_cylinder(bm, 0.205, length - 0.03, along_y((0.0, 0.014 + (length - 0.03) * 0.5, 0.0)), FRAME, segments=16, bev=0.012)
    add_cylinder(bm, 0.13, 0.016, along_y((0.0, length - 0.008, 0.0)), STEEL, segments=12)


def add_truck_hub(bm, y):
    add_cylinder(bm, 0.125, 0.014, along_y((0.0, y + 0.007, 0.0)), STEEL, segments=16)
    ring_of(bm, 10, 0.1675, y + 0.01, 0.016, 0.02, CHROME, segments=6)
    add_cylinder(bm, 0.085, 0.05, along_y((0.0, y + 0.039, 0.0)), STEEL, segments=12, bev=0.008)
    add_cylinder(bm, 0.05, 0.02, along_y((0.0, y + 0.07, 0.0)), CHROME, segments=10, bev=0.006)


def build_wheel_single():
    # predne koleso (aj na vlecenej naprave)
    bm = bmesh.new()
    add_hub_drum(bm)
    add_truck_tire(bm, 0.08)
    add_wheel_disc(bm, HUB_LEN, HUB_LEN + 0.02, 1.0)
    add_truck_hub(bm, HUB_LEN + 0.02)
    return finish_mesh(bm, "SM_Odt_koleso_predne")


def build_wheel_dual():
    # zadne dvojkolesie na hnacej naprave (disky su k sebe chrbtom)
    bm = bmesh.new()
    add_hub_drum(bm)
    mid = HUB_LEN + 0.022
    add_truck_tire(bm, mid - 0.01 - TIRE_W * 0.5, tread=True)
    add_truck_tire(bm, mid + 0.01 + TIRE_W * 0.5, tread=True)
    add_wheel_disc(bm, HUB_LEN, mid, -1.0)
    add_wheel_disc(bm, mid, mid + 0.022, 1.0)
    add_truck_hub(bm, mid + 0.022)
    return finish_mesh(bm, "SM_Odt_koleso_zadne")


# ---------------------------------------------------------------------------
# Napravy (pivot v osi kolies), pohybuju sa s kolesami
# ---------------------------------------------------------------------------

def add_u_bolts(bm, y, z_top, z_bottom, dx, mat=STEEL):
    add_box(bm, (2.0 * dx + 0.05, 0.115, 0.02), (0.0, y, z_top), mat, bev=0.004)
    add_box(bm, (2.0 * dx + 0.05, 0.115, 0.02), (0.0, y, z_bottom), mat, bev=0.004)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, 0.009, z_top - z_bottom + 0.03, along_z((sx * dx, y + sy * 0.048, (z_top + z_bottom) * 0.5)), mat, segments=6)
            add_cylinder(bm, 0.015, 0.018, along_z((sx * dx, y + sy * 0.048, z_bottom - 0.02)), CHROME, segments=6)


def add_shock_bracket(bm, p, s):
    add_box(bm, (0.06, 0.04, 0.06), (p.x, s * p.y, p.z - 0.03), FRAME, bev=0.006)
    add_cylinder(bm, 0.012, 0.08, along_y((p.x, s * p.y, p.z)), CHROME, segments=6)


def build_steer_axle():
    # predna riadena naprava: I-nosnik so zniznym stredom (miesto pre motor), capy riadenia, sedla pier
    bm = bmesh.new()
    path = [(-KINGPIN_Y, 0.0), (-0.44, 0.0), (-0.27, -0.07), (0.27, -0.07), (0.44, 0.0), (KINGPIN_Y, 0.0)]
    add_extruded_yz(bm, beam_outline(path, [0.045] * 6, cap=0.0), -0.045, 0.045, FRAME, bev=0.01)
    for s in SIDES_LR:
        add_cylinder(bm, 0.055, 0.20, along_z((0.0, s * KINGPIN_Y, 0.0)), FRAME, segments=10, bev=0.01)
        add_cylinder(bm, 0.05, FRONT_SPINDLE - KINGPIN_Y + 0.04, along_y((0.0, s * (FRONT_SPINDLE + KINGPIN_Y - 0.04) * 0.5, 0.0)),
                     STEEL, segments=10)
        add_rod(bm, (-0.04, s * (KINGPIN_Y - 0.02), -0.08), (-0.22, s * 0.76, -0.06), 0.022, FRAME)
        # pero lezi na nosniku, navrchu prilozka a strmene, drziak tlmica
        add_box(bm, (0.12, 0.09, 0.018), (0.0, s * RAIL_Y, SPRING_SEAT + 0.016), STEEL, bev=0.004)
        add_u_bolts(bm, s * RAIL_Y, SPRING_SEAT + 0.035, -0.075, 0.05)
        add_shock_bracket(bm, FRONT_SHOCK_LOW, s)
    add_rod(bm, (-0.22, -0.76, -0.06), (-0.22, 0.76, -0.06), 0.02, STEEL, segments=8)
    return finish_mesh(bm, "SM_Odt_naprava_predna")


def build_drive_axle():
    # hnacia naprava s diferencialom (pastorok vpredu = pripojenie kardanu)
    bm = bmesh.new()
    add_cylinder(bm, 0.07, 2.0 * REAR_SPINDLE - 0.04, along_y((0.0, 0.0, 0.0)), FRAME, segments=12)
    add_cylinder(bm, 0.20, 0.30, along_x((0.0, 0.0, 0.0)), FRAME, segments=16, bev=0.08)
    add_cylinder(bm, 0.15, 0.05, along_x((-0.16, 0.0, 0.0)), FRAME, segments=14, bev=0.02)
    for k in range(8):
        a = 2.0 * math.pi * k / 8
        add_cylinder(bm, 0.01, 0.02, along_x((-0.19, 0.12 * math.cos(a), 0.12 * math.sin(a))), CHROME, segments=6)
    add_cone(bm, 0.13, 0.075, 0.24, along_x((0.27, 0.0, 0.0)), FRAME, segments=12, bev=0.01)
    add_cylinder(bm, 0.075, 0.02, along_x((PINION_X - 0.01, 0.0, 0.0)), STEEL, segments=12)
    for s in SIDES_LR:
        add_cylinder(bm, 0.095, 0.03, along_y((0.0, s * (REAR_SPINDLE - 0.035), 0.0)), STEEL, segments=12)
        add_u_bolts(bm, s * RAIL_Y, 0.08, ARM_CLAMP_Z - 0.045, 0.07)
        add_shock_bracket(bm, REAR_SHOCK_LOW, s)
    return finish_mesh(bm, "SM_Odt_naprava_hnacia")


def build_tag_axle():
    # vlecena (zdvihacia) naprava bez diferencialu, dvojmontaz kolies ako na hnacej
    bm = bmesh.new()
    add_cylinder(bm, 0.065, 2.0 * REAR_SPINDLE - 0.04, along_y((0.0, 0.0, 0.0)), FRAME, segments=12)
    add_box(bm, (0.16, 0.50, 0.10), (0.0, 0.0, 0.0), FRAME, bev=0.02)
    for s in SIDES_LR:
        add_cylinder(bm, 0.09, 0.03, along_y((0.0, s * (REAR_SPINDLE - 0.035), 0.0)), STEEL, segments=12)
        add_u_bolts(bm, s * RAIL_Y, 0.075, ARM_CLAMP_Z - 0.045, 0.07)
        add_shock_bracket(bm, REAR_SHOCK_LOW, s)
    return finish_mesh(bm, "SM_Odt_naprava_vlecena")


# ---------------------------------------------------------------------------
# Spojovacie diely: kazdy mieri na svoj protikus (Damped Track), takze sa sam natoci / natiahne
# ---------------------------------------------------------------------------

def spring_geometry():
    # x od napravy, z od zeme
    eye = Vector((SPRING_HALF, RAIL_Y, SPRING_EYE_Z))
    seat = Vector((0.0, RAIL_Y, WHEEL_R + SPRING_SEAT))
    return eye, seat, (seat - eye).length


def arm_geometry():
    # rameno: cap na rame pred napravou, prechadza pod napravou, za napravou nesie vankus (x od napravy)
    pivot = Vector((ARM_PIVOT.x, RAIL_Y, ARM_PIVOT.z))
    clamp = Vector((0.0, RAIL_Y, WHEEL_R + ARM_CLAMP_Z))
    x_axis, z_axis = track_frame(pivot, clamp)
    bag_bottom = Vector((-BAG_BEHIND, RAIL_Y, BAG_BOTTOM_Z))
    under_bag = bag_bottom - Vector((0.0, 0.0, 0.035))
    path = [Vector((0.0, 0.0, 0.0)), to_local(clamp, pivot, x_axis, z_axis), to_local(under_bag, pivot, x_axis, z_axis)]
    seat_local = to_local(bag_bottom, pivot, x_axis, z_axis)
    tilt = math.degrees(math.atan2(x_axis.z, x_axis.x))
    return path, seat_local, bag_bottom, tilt


def build_spring_half():
    # polovica listoveho pera: pivot v oku (na rame), mieri osou -X na stred pera na naprave
    bm = bmesh.new()
    _, _, length = spring_geometry()
    w = 0.08
    for i, start in enumerate((0.0, 0.35, 0.65)):
        pts = []
        for k in range(7):
            t = start + (1.0 - start) * k / 6.0
            pts.append((-length * t, -0.015 * math.sin(math.pi * t) - i * 0.017))
        add_extruded(bm, beam_outline(pts, [0.007] * 7, cap=0.3), -w * 0.5, w * 0.5, "XZ", FRAME, bev=0.002)
    add_cylinder(bm, 0.028, w + 0.01, along_y((0.0, 0.0, 0.0)), FRAME, segments=8)
    add_cylinder(bm, 0.015, w + 0.02, along_y((0.0, 0.0, 0.0)), DARK, segments=6)
    return bm


def build_shock_body():
    # spodna cast tlmica: pivot v spodnom oku, mieri osou +Z hore na horne oko
    bm = bmesh.new()
    L = SHOCK_PART
    add_cylinder(bm, 0.025, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.034, L - 0.04, along_z((0.0, 0.0, 0.02 + (L - 0.04) * 0.5)), DARK, segments=10, bev=0.006)
    add_cylinder(bm, 0.037, 0.02, along_z((0.0, 0.0, L - 0.02)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Odt_tlmic_valec")


def build_shock_rod():
    # horna cast tlmica: pivot v hornom oku, mieri osou -Z dole na spodne oko
    bm = bmesh.new()
    L = SHOCK_PART
    add_cylinder(bm, 0.025, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.013, L - 0.02, along_z((0.0, 0.0, -(L + 0.02) * 0.5)), CHROME, segments=8)
    add_cylinder(bm, 0.041, 0.12, along_z((0.0, 0.0, -0.085)), DARK, segments=10, bev=0.006)
    return finish_mesh(bm, "SM_Odt_tlmic_piestnica")


def build_trailing_arm():
    # vlecene rameno vzduchoveho perovania: pivot v cape na rame, mieri osou -X na bod pod napravou
    bm = bmesh.new()
    path, seat, _, tilt = arm_geometry()
    pts = [(p.x, p.z) for p in path]
    add_extruded(bm, beam_outline(pts, [0.045, 0.04, 0.032], cap=0.5), -0.05, 0.05, "XZ", FRAME, bev=0.008)
    add_cylinder(bm, 0.045, 0.11, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_box(bm, (0.24, 0.16, 0.012), (seat.x, 0.0, seat.z - 0.006), STEEL, bev=0.003, rotation=(0.0, tilt, 0.0))
    return finish_mesh(bm, "SM_Odt_rameno")


def build_air_bag():
    # vzduchovy vankus: pivot hore (pod ramom), mieri osou -Z dole na sedlo na ramene; vyska sa nataha (mierka Z)
    bm = bmesh.new()
    _, _, bottom, _ = arm_geometry()
    rest = FRAME_BOT - bottom.z
    add_box(bm, (0.28, 0.20, 0.02), (0.0, 0.0, -0.01), STEEL, bev=0.004)
    add_cylinder(bm, 0.12, 0.03, along_z((0.0, 0.0, -0.035)), STEEL, segments=12, bev=0.006)
    upper, lower = -0.05, -rest + 0.10
    mid = (upper + lower) * 0.5
    add_cylinder(bm, 0.145, mid - lower, along_z((0.0, 0.0, (mid + lower) * 0.5)), TIRE, segments=12, bev=0.04)
    add_cylinder(bm, 0.15, upper - mid, along_z((0.0, 0.0, (upper + mid) * 0.5)), TIRE, segments=12, bev=0.04)
    add_cylinder(bm, 0.135, 0.02, along_z((0.0, 0.0, mid)), DARK, segments=12)
    add_cylinder(bm, 0.095, 0.09, along_z((0.0, 0.0, -rest + 0.055)), STEEL, segments=12, bev=0.008)
    add_box(bm, (0.22, 0.15, 0.012), (0.0, 0.0, -rest + 0.006), STEEL, bev=0.003)
    return finish_mesh(bm, "SM_Odt_vankus")


def add_u_joint(bm, x, s):
    # priruba a krizovy klb kardanu (s = smer k hriadelu)
    add_cylinder(bm, 0.065, 0.02, along_x((x + s * 0.01, 0.0, 0.0)), STEEL, segments=10)
    for d in SIDES_LR:
        add_box(bm, (0.05, 0.03, 0.02), (x + s * 0.045, 0.0, d * 0.038), STEEL, bev=0.004)
        add_box(bm, (0.05, 0.02, 0.03), (x + s * 0.065, d * 0.038, 0.0), STEEL, bev=0.004)
    add_cylinder(bm, 0.012, 0.095, along_z((x + s * 0.055, 0.0, 0.0)), CHROME, segments=6)
    add_cylinder(bm, 0.012, 0.095, along_y((x + s * 0.055, 0.0, 0.0)), CHROME, segments=6)


def build_kardan_front(name, length):
    # predna cast kardanu: pivot na vystupe prevodovky, mieri osou -X na diferencial
    bm = bmesh.new()
    add_u_joint(bm, 0.0, -1.0)
    add_cylinder(bm, 0.045, length - 0.10, along_x((-(length + 0.10) * 0.5, 0.0, 0.0)), STEEL, segments=10)
    add_cylinder(bm, 0.05, 0.02, along_x((-0.11, 0.0, 0.0)), STEEL, segments=10)
    return finish_mesh(bm, name)


def build_kardan_rear():
    # zadna cast kardanu s posuvnou objimkou: pivot na prirube diferencialu, mieri osou +X na prevodovku
    bm = bmesh.new()
    add_u_joint(bm, 0.0, 1.0)
    add_cylinder(bm, 0.058, 0.90, along_x((0.55, 0.0, 0.0)), STEEL, segments=10, bev=0.006)
    add_cylinder(bm, 0.062, 0.04, along_x((0.98, 0.0, 0.0)), TIRE, segments=10)
    add_cylinder(bm, 0.008, 0.02, along_z((0.30, 0.0, 0.064)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Odt_kardan_zadny")


def build_cab_spring_body():
    # perovanie kabiny vzadu, spodna cast (mech s tlmicom): pivot v oku na rame, mieri osou +Z na oko na kabine
    bm = bmesh.new()
    add_cylinder(bm, 0.022, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.03, 0.04, along_z((0.0, 0.0, 0.03)), STEEL, segments=10)
    add_cylinder(bm, 0.06, 0.10, along_z((0.0, 0.0, 0.10)), TIRE, segments=12, bev=0.025)
    add_cylinder(bm, 0.045, 0.02, along_z((0.0, 0.0, 0.16)), STEEL, segments=12)
    return finish_mesh(bm, "SM_Odt_perovanie_kabiny_mech")


def build_cab_spring_rod():
    # horna cast: pivot v oku na kabine, mieri osou -Z na oko na rame
    bm = bmesh.new()
    add_cylinder(bm, 0.022, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.03, 0.05, along_z((0.0, 0.0, -0.035)), STEEL, segments=10)
    add_cylinder(bm, 0.012, 0.16, along_z((0.0, 0.0, -0.14)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Odt_perovanie_kabiny_piest")


# ---------------------------------------------------------------------------
# Ram (pre kazdy tahac iny): pivot = zem pod prvou prednou napravou
# ---------------------------------------------------------------------------

def frame_crossmembers(truck):
    xs = [0.77]
    rear = [x for kind, x in truck["axles"] if kind != "front"]
    xs += [x - BAG_BEHIND for x in rear]
    xs += [truck["fifth"] + 0.50, truck["fifth"] - 0.50]
    drive = rear[0]
    xs += [GEARBOX_OUT.x - 0.70 - k * 1.1 for k in range(4) if GEARBOX_OUT.x - 0.70 - k * 1.1 > drive + 0.80]
    result = []
    for x in sorted(xs, reverse=True):
        if all(abs(x - y) > 0.25 for y in result) and x > truck["rear_end"] + 0.30:
            result.append(x)
    return result


def build_frame(truck):
    bm = bmesh.new()
    x0, x1 = truck["rear_end"], FRAME_FRONT
    taper = 0.50
    zc = (FRAME_BOT + FRAME_TOP) * 0.5
    # pozdlzniky v tvare C (koniec vzadu zrezany zospodu)
    web = [(x1, FRAME_BOT), (x0 + taper, FRAME_BOT), (x0, FRAME_BOT + 0.12), (x0, FRAME_TOP), (x1, FRAME_TOP)]
    for s in SIDES_LR:
        add_extruded(bm, web, s * (RAIL_Y + 0.018), s * (RAIL_Y + 0.030), "XZ", FRAME, bev=0.003)
        add_box(bm, (x1 - x0, 0.06, 0.012), ((x0 + x1) * 0.5, s * RAIL_Y, FRAME_TOP - 0.006), FRAME, bev=0.003)
        add_box(bm, (x1 - x0 - taper, 0.06, 0.012), ((x0 + taper + x1) * 0.5, s * RAIL_Y, FRAME_BOT + 0.006), FRAME, bev=0.003)
        add_box_between(bm, (x0 + taper, s * RAIL_Y, FRAME_BOT + 0.006), (x0, s * RAIL_Y, FRAME_BOT + 0.126), 0.06, 0.012, FRAME)
        n = int((x1 - x0 - 0.4) / 0.45)
        for i in range(n + 1):
            add_cylinder(bm, 0.009, 0.006, along_y((x0 + 0.2 + i * 0.45, s * (RAIL_Y + 0.033), zc + 0.05)), DARK, segments=8)
    # priecniky (vzadu vyssie kvoli zrezanemu koncu)
    for x in frame_crossmembers(truck):
        add_box(bm, (0.06, 2.0 * RAIL_Y + 0.036, 0.14), (x, 0.0, zc), FRAME, bev=0.008)
    add_box(bm, (0.06, 2.0 * RAIL_Y + 0.036, 0.12), (x0 + 0.04, 0.0, FRAME_TOP - 0.07), FRAME, bev=0.008)
    add_box(bm, (0.012, 0.46, 0.10), (x0 + 0.004, 0.0, FRAME_TOP - 0.07), WHITE, bev=0.003)   # SPZ na konci ramu
    # zniezeny priecnik pod prevodovkou s gumenou podlozkou
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.012, 0.38), (-1.05, s * 0.355, 0.77), FRAME, bev=0.003)
    add_box(bm, (0.06, 0.72, 0.04), (-1.05, 0.0, 0.58), FRAME, bev=0.008)
    add_box(bm, (0.10, 0.16, 0.05), (-1.05, 0.0, 0.625), TIRE, bev=0.01)

    for s in SIDES_LR:
        y = s * RAIL_Y
        # predny cap vyklapania kabiny
        add_box(bm, (CAB_HINGE.x + 0.02 - 0.76, 0.08, 0.08), ((0.76 + CAB_HINGE.x + 0.02) * 0.5, y, CAB_HINGE.z), FRAME, bev=0.008)
        add_cylinder(bm, 0.02, 0.16, along_y((CAB_HINGE.x, y, CAB_HINGE.z)), CHROME, segments=8)
        # zadne uchytenie kabiny (konzola na boku ramu)
        mx, my = CAB_MOUNT.x, s * CAB_MOUNT.y
        add_box(bm, (0.08, CAB_MOUNT.y - RAIL_Y + 0.08, 0.03), (mx, s * (RAIL_Y + CAB_MOUNT.y + 0.10) * 0.5, CAB_MOUNT_LOW - 0.05),
                FRAME, bev=0.004)
        add_box(bm, (0.08, 0.012, 0.16), (mx, s * (RAIL_Y + 0.036), CAB_MOUNT_LOW - 0.02), FRAME, bev=0.003)
        for d in SIDES_LR:
            add_box(bm, (0.06, 0.012, 0.09), (mx, my + d * 0.035, CAB_MOUNT_LOW - 0.01), FRAME, bev=0.003)
        add_cylinder(bm, 0.012, 0.10, along_y((mx, my, CAB_MOUNT_LOW)), CHROME, segments=6)

        for kind, ax in truck["axles"]:
            if kind == "front":
                # zavesy listoveho pera (vpredu pevny, vzadu nausnica), gumovy doraz
                for x in (ax + SPRING_HALF, ax - SPRING_HALF):
                    z0 = SPRING_EYE_Z - 0.03
                    for d in SIDES_LR:
                        add_box(bm, (0.07, 0.01, FRAME_BOT - z0 + 0.01), (x, y + d * 0.05, (FRAME_BOT + z0) * 0.5), FRAME, bev=0.003)
                    add_cylinder(bm, 0.012, 0.12, along_y((x, y, SPRING_EYE_Z)), CHROME, segments=6)
                add_box(bm, (0.08, 0.08, 0.05), (ax, y, FRAME_BOT - 0.025), DARK, bev=0.012)
                up = FRONT_SHOCK_UP
            else:
                # zaves ramena vzduchoveho perovania
                for d in SIDES_LR:
                    add_box(bm, (0.12, 0.012, FRAME_BOT - ARM_PIVOT.z + 0.04),
                            (ax + ARM_PIVOT.x, y + d * 0.062, (FRAME_BOT + ARM_PIVOT.z - 0.04) * 0.5), FRAME, bev=0.004)
                add_box(bm, (0.012, 0.136, 0.12), (ax + ARM_PIVOT.x + 0.06, y, FRAME_BOT - 0.07), FRAME)
                add_cylinder(bm, 0.014, 0.15, along_y((ax + ARM_PIVOT.x, y, ARM_PIVOT.z)), CHROME, segments=6)
                up = REAR_SHOCK_UP
            # horny drziak tlmica na boku ramu
            add_box(bm, (0.09, 0.015, 0.11), (ax + up.x, s * (RAIL_Y + 0.037), up.z), FRAME, bev=0.004)
            add_cylinder(bm, 0.012, up.y - RAIL_Y, along_y((ax + up.x, s * (RAIL_Y + up.y) * 0.5, up.z)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Odt_%s_ram" % truck["cfg"])


# ---------------------------------------------------------------------------
# Predok na rame: naraznik a chladic (kabina sa nad nimi vyklapa)
# ---------------------------------------------------------------------------

def build_bumper():
    # naraznik 3: nizka siroka tmava "brada" pod maskou (podla fotky), zaoblene konce s vetracimi mriezkami, ryhovane schodiky,
    # SPZ v strede
    bm = bmesh.new()
    x1, hw = CAB_FRONT_X, CAB_HALF * CAB_SCALE
    outline = [(x1 - 0.28, -hw - 0.02), (x1 - 0.10, -hw - 0.02), (x1 + 0.00, -hw + 0.14), (x1 + 0.05, -0.62),
               (x1 + 0.07, 0.0), (x1 + 0.05, 0.62), (x1 + 0.00, hw - 0.14), (x1 - 0.10, hw + 0.02), (x1 - 0.28, hw + 0.02)]
    add_extruded(bm, outline, 0.54, 0.84, "XY", BUMPER, bev=0.04)
    lip = [(x1 - 0.24, -hw + 0.08), (x1 - 0.08, -hw + 0.08), (x1 + 0.02, -hw + 0.20), (x1 + 0.06, -0.60), (x1 + 0.08, 0.0),
           (x1 + 0.06, 0.60), (x1 + 0.02, hw - 0.20), (x1 - 0.08, hw - 0.08), (x1 - 0.24, hw - 0.08)]
    add_extruded(bm, lip, 0.42, 0.54, "XY", DARK, bev=0.015)
    add_box(bm, (0.012, 0.56, 0.12), (x1 + 0.076, 0.0, 0.69), DARK, bev=0.006)
    add_box(bm, (0.006, 0.52, 0.11), (x1 + 0.083, 0.0, 0.69), WHITE, bev=0.002)
    for s in SIDES_LR:
        # vetracie mriezky na koncoch a ryhovany schodik
        add_box(bm, (0.014, 0.36, 0.13), (x1 + 0.016, s * 0.88, 0.67), DARK, bev=0.008)
        for k in range(5):
            add_box(bm, (0.018, 0.32, 0.008), (x1 + 0.022, s * 0.88, 0.625 + k * 0.025), BUMPER)
        step_x = x1 - 0.14
        add_box(bm, (0.28, 0.40, 0.012), (step_x, s * 0.88, 0.846), DARK, bev=0.003)
        for k in range(5):
            add_box(bm, (0.26, 0.016, 0.012), (step_x, s * (0.88 - 0.16 + k * 0.08), 0.856), BUMPER)
        add_box(bm, (0.02, 0.07, 0.07), (x1 + 0.03, s * 0.58, 0.62), STEEL, bev=0.008)
        # drziaky na koniec ramu
        add_box(bm, (x1 - 0.27 - FRAME_FRONT + 0.03, 0.10, 0.12), ((FRAME_FRONT - 0.03 + x1 - 0.27) * 0.5, s * RAIL_Y, 0.80), FRAME, bev=0.006)
    # tazny cap v strede dole
    add_box(bm, (0.04, 0.16, 0.08), (x1 + 0.03, 0.0, 0.46), DARK, bev=0.008)
    add_cylinder(bm, 0.022, 0.12, along_z((x1 + 0.03, 0.0, 0.46)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Odt_naraznik")


def build_radiator():
    bm = bmesh.new()
    x = 0.69
    add_box(bm, (0.05, 0.66, 0.60), (x, 0.0, 1.04), DARK, bev=0.004)
    for z in (0.715, 1.365):
        add_box(bm, (0.07, 0.70, 0.05), (x, 0.0, z), STEEL, bev=0.008)
    for s in SIDES_LR:
        add_box(bm, (0.07, 0.025, 0.70), (x, s * 0.3475, 1.04), STEEL, bev=0.004)
        add_box(bm, (0.08, 0.04, 0.04), (x + 0.055, s * 0.30, 0.94), FRAME, bev=0.004)
    for i in range(9):
        add_box(bm, (0.052, 0.64, 0.006), (x, 0.0, 0.775 + i * 0.066), STEEL)
    # obal ventilatora a hadice k motoru
    add_transformed(bm, Matrix.Translation((x - 0.06, 0.0, 1.08)) @ Matrix.Rotation(math.radians(90.0), 4, "Z"),
                    add_ring, 0.27, 0.255, 0.06, 0.0, DARK, 16)
    for sy in SIDES_LR:
        for sz in SIDES_LR:
            add_rod(bm, (x - 0.06, sy * 0.185, 1.08 + sz * 0.185), (x - 0.025, sy * 0.25, 1.08 + sz * 0.25), 0.012, DARK)
    add_rod(bm, (x - 0.03, 0.26, 1.33), (x - 0.14, 0.20, 1.28), 0.03, TIRE)
    add_rod(bm, (x - 0.03, -0.26, 0.78), (x - 0.14, -0.20, 0.82), 0.03, TIRE)
    return finish_mesh(bm, "SM_Odt_chladic")


# ---------------------------------------------------------------------------
# Prislusenstvo na rame (pivot na osi ramu v strede dielu, alebo v pociatku tahaca)
# ---------------------------------------------------------------------------

def build_fuel_tank():
    # nadrz nafty, lava strana
    bm = bmesh.new()
    ty, tz, length = 0.76, 0.72, 1.20
    add_box(bm, (length, 0.62, 0.62), (0.0, ty, tz), ALU, bev=0.10)
    for x in (-0.38, 0.38):
        add_box(bm, (0.05, 0.64, 0.64), (x, ty, tz), DARK, bev=0.015)
        add_box(bm, (0.06, ty - 0.31 - RAIL_Y, 0.06), (x, (ty - 0.31 + RAIL_Y) * 0.5 + 0.015, tz + 0.16), FRAME, bev=0.004)
        add_box(bm, (0.08, 0.012, 0.30), (x, RAIL_Y + 0.036, 0.86), FRAME, bev=0.003)
    add_cylinder(bm, 0.05, 0.05, along_z((0.42, ty + 0.16, tz + 0.33)), STEEL, segments=10)
    add_cylinder(bm, 0.062, 0.025, along_z((0.42, ty + 0.16, tz + 0.365)), DARK, segments=10, bev=0.006)
    add_box(bm, (0.30, 0.02, 0.05), (-0.10, ty + 0.315, tz + 0.18), DARK, bev=0.004)
    return finish_mesh(bm, "SM_Odt_nadrz_nafta")


def build_adblue_tank():
    bm = bmesh.new()
    ty, tz = 0.70, 0.78
    add_box(bm, (0.40, 0.42, 0.46), (0.0, ty, tz), WHITE, bev=0.05)
    add_cylinder(bm, 0.045, 0.04, along_z((0.08, ty + 0.08, tz + 0.25)), STEEL, segments=10)
    add_cylinder(bm, 0.055, 0.025, along_z((0.08, ty + 0.08, tz + 0.28)), PAINT_BLUE, segments=10, bev=0.006)
    for x in (-0.12, 0.12):
        add_box(bm, (0.04, ty - 0.21 - RAIL_Y, 0.05), (x, (ty - 0.21 + RAIL_Y) * 0.5 + 0.015, tz + 0.12), FRAME, bev=0.004)
        add_box(bm, (0.06, 0.012, 0.22), (x, RAIL_Y + 0.036, 0.90), FRAME, bev=0.003)
    return finish_mesh(bm, "SM_Odt_nadrz_adblue")


def build_battery_box():
    # skrina baterii, prava strana
    bm = bmesh.new()
    add_box(bm, (0.62, 0.50, 0.36), (0.0, -0.70, 0.72), DARK, bev=0.03)
    add_box(bm, (0.58, 0.02, 0.30), (0.0, -0.955, 0.72), FRAME, bev=0.005)
    for x in (-0.20, 0.20):
        add_box(bm, (0.05, 0.02, 0.04), (x, -0.968, 0.84), STEEL, bev=0.004)
        add_box(bm, (0.05, 0.03, 0.30), (x, -0.44, 0.78), FRAME, bev=0.004)
    return finish_mesh(bm, "SM_Odt_baterie")


def build_air_tanks():
    # vzduchojemy, prava strana
    bm = bmesh.new()
    for z in (0.60, 0.88):
        add_cylinder(bm, 0.12, 0.62, along_x((0.0, -0.62, z)), STEEL, segments=12, bev=0.05)
        for x in (-0.20, 0.20):
            add_cylinder(bm, 0.125, 0.03, along_x((x, -0.62, z)), DARK, segments=12)
            add_box(bm, (0.04, 0.08, 0.04), (x, -0.47, z), FRAME, bev=0.004)
        add_cylinder(bm, 0.012, 0.04, along_z((0.25, -0.62, z - 0.13)), CHROME, segments=6)
    add_box(bm, (0.50, 0.012, 0.44), (0.0, -(RAIL_Y + 0.036), 0.74), FRAME, bev=0.003)
    return finish_mesh(bm, "SM_Odt_vzduchojemy")


def build_exhaust():
    # vyfuk: rura od motora pod ramom doprava do tlmica, ktory lezi pod autom vpravo; vyustka smeruje dole a von
    bm = bmesh.new()
    x, y, z = -0.88, -0.68, 0.64
    add_cylinder(bm, 0.12, 0.56, along_y((x, y, z)), STEEL, segments=12, bev=0.01)
    for dy in (-0.17, 0.0, 0.17):
        add_cylinder(bm, 0.126, 0.025, along_y((x, y + dy, z)), DARK, segments=12)
    add_cylinder(bm, 0.07, 0.03, along_y((x, y - 0.295, z)), CHROME, segments=10)
    add_rod(bm, (-0.55, -0.30, 0.72), (x, -0.30, 0.72), 0.06, STEEL, segments=10)
    add_rod(bm, (x, -0.30, 0.72), (x, -0.40, z), 0.06, STEEL, segments=10)
    add_rod(bm, (x, y - 0.29, z), (x - 0.02, -1.04, z - 0.03), 0.05, STEEL, segments=10)
    add_rod(bm, (x - 0.02, -1.04, z - 0.03), (x - 0.04, -1.10, 0.49), 0.05, STEEL, segments=10)
    add_rod(bm, (x - 0.037, -1.095, 0.52), (x - 0.045, -1.115, 0.45), 0.062, CHROME, segments=10)
    for dx in (-0.14, 0.14):
        add_box(bm, (0.05, 0.06, 0.10), (x + dx, -0.445, 0.78), FRAME, bev=0.004)
    return finish_mesh(bm, "SM_Odt_vyfuk")








def build_light_bar():
    # zadna cierna plastova lista s obdlznikovymi svetlami na koncoch (smerovka, cervene ryhovane sklo, cuvanie), zltou
    # spojkou vzduchu uprostred a SPZ (pivot na konci ramu)
    bm = bmesh.new()
    bx, bz = -0.04, 0.70
    add_box(bm, (0.10, 2.00, 0.14), (bx, 0.0, bz), BUMPER, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.05, 0.05, FRAME_BOT + 0.14 - bz), (0.03, s * RAIL_Y, (FRAME_BOT + 0.14 + bz) * 0.5), FRAME, bev=0.006)
        add_box(bm, (0.14, 0.10, 0.22), (bx, s * 1.0, bz), DARK, bev=0.02)
        xh, y = bx - 0.115, s * 0.83
        xl = xh - 0.0405
        add_box(bm, (0.07, 0.24, 0.21), (xh, y, bz), DARK, bev=0.012)
        add_box(bm, (0.012, 0.19, 0.045), (xl, y, bz + 0.075), LAMP_OR, bev=0.003)
        add_box(bm, (0.012, 0.19, 0.075), (xl, y, bz + 0.003), LAMP_RED, bev=0.003)
        for dz in (-0.022, 0.003, 0.028):
            add_box(bm, (0.016, 0.19, 0.006), (xl - 0.002, y, bz + dz), DARK)
        add_box(bm, (0.012, 0.19, 0.035), (xl, y, bz - 0.075), LAMP_WHITE, bev=0.003)
        add_box(bm, (0.045, 0.012, 0.045), (xh, y + s * 0.124, bz), RED, bev=0.003)
    add_box(bm, (0.07, 0.18, 0.14), (bx - 0.085, 0.0, bz - 0.01), YELLOW, bev=0.012)
    for dy in (-0.045, 0.045):
        add_cylinder(bm, 0.028, 0.02, along_x((bx - 0.125, dy, bz - 0.01)), DARK, segments=8)
    add_box(bm, (0.006, 0.46, 0.10), (bx - 0.065, 0.0, bz + 0.17), WHITE, bev=0.002)
    return finish_mesh(bm, "SM_Odt_zadna_lista")


def build_mudguard(y_in, y_out, mount):
    # blatnik nad kolesom so zasterkou: pivot v osi kolesa; mount "frame" = drziaky na ram, "axle" = na napravu
    bm = bmesh.new()
    r = WHEEL_R + 0.10
    sweep_profile(bm, [(r, y_in), (r, y_out), (r + 0.012, y_out), (r + 0.012, y_in)], 25.0, 155.0, 8, DARK)
    sweep_profile(bm, [(r - 0.02, y_out - 0.018), (r - 0.02, y_out), (r + 0.03, y_out), (r + 0.03, y_out - 0.018)],
                  25.0, 155.0, 8, DARK)
    back = math.radians(155.0)
    fx, fz = r * math.cos(back) + 0.004, r * math.sin(back)
    add_box(bm, (0.012, y_out - y_in - 0.04, fz + 0.33), (fx, (y_in + y_out) * 0.5, (fz - 0.33) * 0.5), TIRE, bev=0.004)
    for z in (-0.20, -0.13):
        add_box(bm, (0.016, y_out - y_in - 0.08, 0.012), (fx - 0.002, (y_in + y_out) * 0.5, z), TIRE, bev=0.003)
    for a in (70.0, 115.0):
        ca, sa = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        if mount == "frame":
            add_box_between(bm, (ca, y_in + 0.02, sa - 0.01), (ca, RAIL_Y + 0.035, FRAME_BOT + 0.12 - WHEEL_R), 0.04, 0.03, FRAME)
            add_box(bm, (0.08, 0.012, 0.12), (ca, RAIL_Y + 0.036, FRAME_BOT + 0.14 - WHEEL_R), FRAME, bev=0.003)
        else:
            add_box_between(bm, (ca, y_in + 0.005, sa - 0.01), (ca * 0.25, min(0.72, y_in - 0.02), 0.06), 0.035, 0.025, FRAME)
    return bm





def build_rear_fender(y_in, y_out, mount, lamps=False):
    # zadny blatnik: klenba s hlbokymi bocnymi lemami a velka gumova zasterka za kolesom, volitelne so svetlom priamo
    # na zasterke; pivot v osi kolesa
    bm = bmesh.new()
    r = WHEEL_R + 0.11
    a0, a1, steps = 8.0, 178.0, 12
    crown = [(r, y_in), (r + 0.02, y_in + 0.05), (r + 0.045, y_in + 0.12), (r + 0.045, y_out - 0.12), (r + 0.02, y_out - 0.05),
             (r, y_out), (r - 0.02, y_out), (r - 0.02, y_in)]
    sweep_profile(bm, crown, a0, a1, steps, BUMPER)
    for yo, yi in ((y_in, y_in + 0.028), (y_out - 0.028, y_out)):
        sweep_profile(bm, [(r - 0.02, yo), (r - 0.02, yi), (r - 0.15, yi), (r - 0.15, yo)], a0, a1, steps, BUMPER)
    back = math.radians(a1)
    fx, fz = r * math.cos(back), r * math.sin(back)
    w = y_out - y_in - 0.08
    yc = (y_in + y_out) * 0.5
    add_box(bm, (0.04, w, 0.05), (fx - 0.01, yc, fz - 0.02), BUMPER, bev=0.008)
    add_box(bm, (0.016, w, 0.40), (fx - 0.012, yc, fz - 0.22), DARK, bev=0.006)
    for dz in (-0.12, -0.20):
        add_box(bm, (0.02, w - 0.10, 0.012), (fx - 0.018, yc, fz + dz), DARK, bev=0.003)
    add_box(bm, (0.02, w - 0.12, 0.06), (fx - 0.018, yc, fz - 0.37), WHITE, bev=0.004)
    if lamps:
        # zadne svetlo priamo na blatniku: siroky obdlznik na zadnom obluku pri vonkajsom okraji, v polovici vysky blatnika
        # (zvonka oranzova smerovka, cervene ryhovane sklo, vnutri biele cuvanie)
        ly, lz = y_out - 0.23, fz + 0.12
        rl = r + 0.03
        xh = -rl * math.cos(math.asin(min(lz / rl, 0.99))) - 0.004 - 0.035
        xl = xh - 0.0405
        add_box(bm, (0.07, 0.37, 0.13), (xh, ly, lz), DARK, bev=0.012)
        add_box(bm, (0.012, 0.085, 0.095), (xl, ly + 0.1325, lz), LAMP_OR, bev=0.003)
        add_box(bm, (0.012, 0.17, 0.095), (xl, ly - 0.005, lz), LAMP_RED, bev=0.003)
        for dy in (-0.05, 0.0, 0.05):
            add_box(bm, (0.016, 0.006, 0.095), (xl - 0.002, ly - 0.005 + dy, lz), DARK)
        add_box(bm, (0.012, 0.07, 0.095), (xl, ly - 0.135, lz), LAMP_WHITE, bev=0.003)
        add_box(bm, (0.045, 0.012, 0.05), (xh, ly + 0.19, lz), RED, bev=0.003)
    for a in (70.0, 115.0):
        ca, sa = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
        if mount == "frame":
            add_box_between(bm, (ca, y_in + 0.02, sa - 0.01), (ca, RAIL_Y + 0.035, FRAME_BOT + 0.12 - WHEEL_R), 0.04, 0.03, FRAME)
            add_box(bm, (0.08, 0.012, 0.12), (ca, RAIL_Y + 0.036, FRAME_BOT + 0.14 - WHEEL_R), FRAME, bev=0.003)
        else:
            add_box_between(bm, (ca, y_in + 0.005, sa - 0.01), (ca * 0.25, 0.72, 0.06), 0.035, 0.025, FRAME)
    return bm


# ---------------------------------------------------------------------------
# Materialy, objekty, ovladace
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
            for key_name in ("Emission Color", "Emission"):
                if key_name in bsdf.inputs:
                    bsdf.inputs[key_name].default_value = color
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
    # kazdy diel sa exportuje samostatne v strede sveta, aby mal pivot na svojom mieste
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
    return con


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
        if mesh.users == 0 and mesh.get("odtahovky"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_"):
            bpy.data.curves.remove(curve)


def add_label(coll, text, location, mat):
    curve = bpy.data.curves.new("Menovka_" + text.split("\n")[0], "FONT")
    curve.body = text
    curve.size = 0.10
    curve.align_x = "CENTER"
    curve.materials.append(mat)
    obj = bpy.data.objects.new(curve.name, curve)
    coll.objects.link(obj)
    obj.location = location


def bounds(mesh):
    xs = [v.co.x for v in mesh.vertices]
    ys = [v.co.y for v in mesh.vertices]
    zs = [v.co.z for v in mesh.vertices]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def empty(coll, name, location, parent):
    obj = new_object(coll, name, None, location, parent)
    obj.empty_display_size = 0.04
    obj.hide_render = True
    return obj


def driver(obj, path, index, expression, variables):
    # variables: (meno, "TRANSFORM", (objekt, "LOC_Z")) | (meno, "PROP", (objekt, '["x"]')) | (meno, "DIST", (a, b))
    fcurve = obj.driver_add(path, index)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    for name, kind, data in variables:
        var = drv.variables.new()
        var.name = name
        if kind == "TRANSFORM":
            var.type = "TRANSFORMS"
            var.targets[0].id = data[0]
            var.targets[0].transform_type = data[1]
            var.targets[0].transform_space = "TRANSFORM_SPACE"
        elif kind == "PROP":
            var.type = "SINGLE_PROP"
            var.targets[0].id_type = "OBJECT"
            var.targets[0].id = data[0]
            var.targets[0].data_path = data[1]
        else:
            var.type = "LOC_DIFF"
            var.targets[0].id = data[0]
            var.targets[1].id = data[1]
    drv.expression = expression


def link_pair(coll, name, mesh_a, mesh_b, parent_a, point_a, parent_b, point_b, axis_a, axis_b):
    # dvojdielny prvok (tlmic, kardan): kazda cast je na svojom diele a mieri na bod na tom druhom
    part_a = new_object(coll, name + "_1", mesh_a, point_a, parent_a)
    part_b = new_object(coll, name + "_2", mesh_b, point_b, parent_b)
    aim_b = empty(coll, name + "_ciel_1", point_b, parent_b)
    aim_a = empty(coll, name + "_ciel_2", point_a, parent_a)
    track(part_a, aim_b, axis_a)
    track(part_b, aim_a, axis_b)
    return part_a, part_b


def set_prop(obj, name, value, low, high, description):
    obj[name] = value
    try:
        obj.id_properties_ui(name).update(min=low, max=high, soft_min=low, soft_max=high, description=description)
    except Exception:
        pass


def paint(obj, mat, index=PAINT):
    # vlastna farba laku pre tento tahac (material slotu je na objekte, mesh ostava spolocny)
    slot = obj.material_slots[index]
    slot.link = "OBJECT"
    slot.material = mat


# ---------------------------------------------------------------------------
# Diely
# ---------------------------------------------------------------------------

def drive_axle_x(truck):
    return next(x for kind, x in truck["axles"] if kind == "drive")


def kardan_rest_length(truck):
    pinion = Vector((drive_axle_x(truck) + PINION_X, 0.0, WHEEL_R))
    return (GEARBOX_OUT - pinion).length


def build_parts():
    parts = {}

    def put(mesh):
        parts[mesh.name[3:].split(".")[0]] = mesh

    def put_lr(bm, name):
        mirrored = mirror_y(bm)
        put(finish_mesh(bm, name + "_L"))
        put(finish_mesh(mirrored, name + "_P"))

    for fn in (build_cab, build_interior, build_steering_wheel, build_intake, build_cab_spring_body, build_cab_spring_rod,
               build_bumper, build_radiator, build_fuel_tank, build_adblue_tank,
               build_battery_box, build_air_tanks, build_exhaust,
               build_steer_axle, build_drive_axle, build_tag_axle, build_wheel_single, build_wheel_dual,
               build_shock_body, build_shock_rod, build_trailing_arm, build_air_bag, build_kardan_rear):
        put(fn())
    put(build_needle("SM_Odt_rucicka_velka", 0.065))
    put(build_needle("SM_Odt_rucicka_mala", 0.024))
    spring = build_spring_half()
    spring_rear = spring.copy()
    bmesh.ops.scale(spring_rear, vec=(-1.0, 1.0, 1.0), verts=spring_rear.verts[:])
    bmesh.ops.reverse_faces(spring_rear, faces=spring_rear.faces[:])
    put(finish_mesh(spring, "SM_Odt_pero_predna_cast"))
    put(finish_mesh(spring_rear, "SM_Odt_pero_zadna_cast"))
    put_lr(build_rear_fender(0.64, 1.29, "frame"), "SM_Odt_blatnik_zadny")
    put_lr(build_rear_fender(0.64, 1.29, "frame", True), "SM_Odt_blatnik_zadny_svetla")
    put_lr(build_rear_fender(0.64, 1.29, "axle", True), "SM_Odt_blatnik_vleceny")
    put_lr(build_mudguard(0.80, 1.16, "frame"), "SM_Odt_blatnik_predny")
    for maker in PART_MAKERS:
        maker(put, put_lr)
    for truck in CONFIGS:
        put(build_frame(truck))
        put(build_kardan_front("SM_Odt_%s_kardan_predny" % truck["cfg"], kardan_rest_length(truck) - 0.75))
    return parts


def build_engines():
    # nase motory R4 / R6 / V8 s prevodovkami; poloha konca vystupneho hriadela voci pivotu motora
    m = MOTORY
    engines = {}
    for spec in m["ENGINES"]:
        mats = m["engine_materials"](spec)
        builder = m["build_inline"] if spec["layout"] == "inline" else m["build_v8"]
        body_mesh, info = builder(spec)
        meshes = [body_mesh]
        crank_r = spec["pulleys"]["Klukova"][2]
        fan_mat = m["CHROME"] if spec["layout"] == "v" else m["DARK"]
        pulleys = []
        for pname, (y, z, r) in spec["pulleys"].items():
            mesh = m["build_pulley"]("SM_Motor_%s_Kladka_%s" % (spec["key"], pname), r,
                                     fan=spec["fan"] if pname == "Pumpa" else None, fan_mat=fan_mat,
                                     damper=pname == "Klukova", alt_fan=pname == "Alternator")
            ratio = crank_r / r * (-1.0 if pname == "Napinac" else 1.0)
            pulleys.append((pname, mesh, (info["front"] + 0.06, y, z), ratio))
            meshes.append(mesh)
        gb_mesh, out_x = m["build_gearbox"](spec, info)
        out_mesh = m["build_output"]("SM_Motor_%s_Vystup" % spec["key"])
        meshes += [gb_mesh, out_mesh]
        for mesh in meshes:
            m["add_materials"](mesh, mats)
            mesh["odtahovky"] = 1
        gb_loc = Vector((info["back"] - 0.02, 0.0, info["flange_z"]))
        tip = gb_loc + Vector((out_x + min(v.co.x for v in out_mesh.vertices), 0.0, 0.0))
        engines[spec["key"]] = dict(body=body_mesh, pulleys=pulleys, gearbox=gb_mesh, gb_loc=gb_loc, output=out_mesh,
                                    out_x=out_x, tip=tip)
    return engines


AXLE_MESH = {"front": "Odt_naprava_predna", "drive": "Odt_naprava_hnacia", "tag": "Odt_naprava_vlecena"}
ENGINE_KEYS = ("R4", "R6", "V8")


# ---------------------------------------------------------------------------
# Zostava jedneho tahaca
# ---------------------------------------------------------------------------

def build_truck(coll, truck, parts, mats, engines, motor):
    name = truck["name"]
    axles = truck["axles"]
    has_tag = any(kind == "tag" for kind, _ in axles)

    root = new_object(coll, name, None, (truck["x"], truck["y"], 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.0
    set_prop(root, "Vyska_podvozku", 0.0, -0.06, 0.10, "Dofuknutie / vypustenie vankusov v metroch (zadok hore / dole)")
    if has_tag:
        set_prop(root, "Zdvih_napravy", 0.0, 0.0, 1.0, "0 = vlecena naprava dole, 1 = zdvihnuta")
    set_prop(root, "Vyklopenie_kabiny", 0.0, 0.0, 1.0, "0 = kabina normalne, 1 = vyklopena dopredu")
    set_prop(root, "Kabina_klopenie", 0.0, -4.0, 4.0, "Kabina dopredu (+) / dozadu na perovani v stupnoch")
    set_prop(root, "Kabina_naklon", 0.0, -5.0, 5.0, "Kabina do strany na perovani v stupnoch")
    set_prop(root, "Riadenie", 0.0, -30.0, 30.0, "Natocenie prednych kolies v stupnoch (+ = dolava)")
    set_prop(root, "Motor", motor, 1, 3, "1 = R4, 2 = R6, 3 = V8")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    drive_i = next(i for i, (kind, _) in enumerate(axles) if kind == "drive")
    rear_xs = [x for kind, x in axles if kind != "front"]
    wheelbase = -axles[drive_i][1]
    ride_ref = -sum(rear_xs) / len(rear_xs)

    # --- teren pod kazdou napravou (animacia) a napravy ---
    terrain = []
    for i, (kind, ax) in enumerate(axles):
        t = empty(coll, "%s_teren_%d" % (name, i + 1), (ax, 0.0, WHEEL_R), root)
        t.empty_display_type = "PLAIN_AXES"
        t.empty_display_size = 0.3
        terrain.append(t)
    body_vars = [("fz", "TRANSFORM", (terrain[0], "LOC_Z")), ("rz", "TRANSFORM", (terrain[drive_i], "LOC_Z")),
                 ("fr", "TRANSFORM", (terrain[0], "ROT_X")), ("rr", "TRANSFORM", (terrain[drive_i], "ROT_X")),
                 prop("v", "Vyska_podvozku")]
    pitch = "%.3f * (rz - fz) / %.4f + v / %.4f" % (BODY_FOLLOW, wheelbase, ride_ref)
    roll = "%.3f * (fr + rr) * 0.5" % (BODY_FOLLOW * 0.7)
    axle_objs = []
    for i, (kind, ax) in enumerate(axles):
        axle = new_object(coll, "%s_naprava_%d" % (name, i + 1), parts[AXLE_MESH[kind]], (ax, 0.0, WHEEL_R), root)
        tv = [("t", "TRANSFORM", (terrain[i], "LOC_Z")), ("tr", "TRANSFORM", (terrain[i], "ROT_X"))]
        if kind == "tag":
            # zdvihnuta naprava ide k ramu (o LIFT_HEIGHT nad kludovu polohu voci ramu) a nakloni sa s nim
            lifted = "%.3f + %.3f * (fz - %.3f) + %.4f * (%s)" % (WHEEL_R + LIFT_HEIGHT, BODY_FOLLOW, WHEEL_R, -ax, pitch)
            lv = tv + body_vars + [prop("l", "Zdvih_napravy")]
            driver(axle, "location", 2, "(1 - l) * t + l * (%s)" % lifted, lv)
            driver(axle, "rotation_euler", 0, "(1 - l) * tr + l * %s" % roll, lv)
        else:
            driver(axle, "location", 2, "t", tv)
            driver(axle, "rotation_euler", 0, "tr", tv)
        axle_objs.append(axle)

    # --- odpruzeny ram: sleduje napravy len ciastocne (zvysok zoberu pera), vankuse dvihaju zadok ---
    body = new_object(coll, name + "_ram", parts["Odt_%s_ram" % truck["cfg"]], (0.0, 0.0, 0.0), root)
    driver(body, "location", 2, "%.3f * (fz - %.3f)" % (BODY_FOLLOW, WHEEL_R), body_vars)
    driver(body, "rotation_euler", 1, "atan(%s)" % pitch, body_vars)
    driver(body, "rotation_euler", 0, roll, body_vars)

    # --- kolesa, pera, ramena, vankuse, tlmice, blatniky ---
    path, seat_local, bag_bottom, _ = arm_geometry()
    bag_rest = FRAME_BOT - bag_bottom.z
    for i, (kind, ax) in enumerate(axles):
        axle = axle_objs[i]
        n = i + 1
        for s, side in ((1.0, "L"), (-1.0, "P")):
            rot = (0.0, 0.0, 0.0 if s > 0 else 180.0)
            if kind == "front":
                knuckle = empty(coll, "%s_cap_riadenia_%d_%s" % (name, n, side), (0.0, s * KINGPIN_Y, 0.0), axle)
                driver(knuckle, "rotation_euler", 2, "r * %.6f" % (DEG * (1.0 if i == 0 else 0.6)), [prop("r", "Riadenie")])
                new_object(coll, "%s_koleso_%d_%s" % (name, n, side), parts["Odt_koleso_predne"],
                           (0.0, s * (FRONT_SPINDLE - KINGPIN_Y), 0.0), knuckle, rot)
                target = empty(coll, "%s_pero_stred_%d_%s" % (name, n, side), (0.0, s * RAIL_Y, SPRING_SEAT), axle)
                half_f = new_object(coll, "%s_pero_%d_%s_1" % (name, n, side), parts["Odt_pero_predna_cast"],
                                    (ax + SPRING_HALF, s * RAIL_Y, SPRING_EYE_Z), body)
                half_r = new_object(coll, "%s_pero_%d_%s_2" % (name, n, side), parts["Odt_pero_zadna_cast"],
                                    (ax - SPRING_HALF, s * RAIL_Y, SPRING_EYE_Z), body)
                track(half_f, target, "TRACK_NEGATIVE_X")
                track(half_r, target, "TRACK_X")
                low, up = FRONT_SHOCK_LOW, FRONT_SHOCK_UP
                if i > 0:
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts["Odt_blatnik_predny_" + side],
                               (ax, 0.0, WHEEL_R), body)
            else:
                wheel = "Odt_koleso_zadne"
                spindle = REAR_SPINDLE
                new_object(coll, "%s_koleso_%d_%s" % (name, n, side), parts[wheel], (0.0, s * spindle, 0.0), axle, rot)
                aim = empty(coll, "%s_rameno_ciel_%d_%s" % (name, n, side), (0.0, s * RAIL_Y, ARM_CLAMP_Z), axle)
                arm = new_object(coll, "%s_rameno_%d_%s" % (name, n, side), parts["Odt_rameno"],
                                 (ax + ARM_PIVOT.x, s * RAIL_Y, ARM_PIVOT.z), body)
                track(arm, aim, "TRACK_NEGATIVE_X")
                seat_aim = empty(coll, "%s_vankus_ciel_%d_%s" % (name, n, side), tuple(seat_local), arm)
                bag_top = (ax + bag_bottom.x, s * RAIL_Y, FRAME_BOT)
                bag = new_object(coll, "%s_vankus_%d_%s" % (name, n, side), parts["Odt_vankus"], bag_top, body)
                track(bag, seat_aim, "TRACK_NEGATIVE_Z")
                # vyska vankusa = vzdialenost bodu na rame a sedla na ramene (samostatny bod, aby sa necital sam)
                top_aim = empty(coll, "%s_vankus_hore_%d_%s" % (name, n, side), bag_top, body)
                driver(bag, "scale", 2, "d / %.4f" % bag_rest, [("d", "DIST", (top_aim, seat_aim))])
                low, up = REAR_SHOCK_LOW, REAR_SHOCK_UP
                if kind == "drive":
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts[("Odt_blatnik_zadny_" if has_tag else "Odt_blatnik_zadny_svetla_") + side],
                               (ax, 0.0, WHEEL_R), body)
                else:
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts["Odt_blatnik_vleceny_" + side],
                               (0.0, 0.0, 0.0), axle)
            link_pair(coll, "%s_tlmic_%d_%s" % (name, n, side), parts["Odt_tlmic_valec"], parts["Odt_tlmic_piestnica"],
                      axle, Vector((low.x, s * low.y, low.z)), body, Vector((ax + up.x, s * up.y, up.z)),
                      "TRACK_Z", "TRACK_NEGATIVE_Z")

    # --- kardan medzi prevodovkou (ram) a diferencialom (hnacia naprava), posuvny ---
    link_pair(coll, name + "_kardan", parts["Odt_%s_kardan_predny" % truck["cfg"]], parts["Odt_kardan_zadny"],
              body, GEARBOX_OUT, axle_objs[drive_i], Vector((PINION_X, 0.0, 0.0)), "TRACK_NEGATIVE_X", "TRACK_X")

    # --- nase motory s prevodovkami: vsetky tri su na mieste, vlastnost Motor ukaze jeden ---
    for index, engine_key in enumerate(ENGINE_KEYS):
        e = engines[engine_key]
        objs = []
        engine = new_object(coll, "%s_motor_%s" % (name, engine_key), e["body"], GEARBOX_OUT - e["tip"], body)
        objs.append(engine)
        for pname, mesh, location, ratio in e["pulleys"]:
            pulley = new_object(coll, "%s_%s_kladka_%s" % (name, engine_key, pname), mesh, location, engine)
            MOTORY["add_spin"](pulley, ratio)
            objs.append(pulley)
        gearbox = new_object(coll, "%s_%s_prevodovka" % (name, engine_key), e["gearbox"], e["gb_loc"], engine)
        output = new_object(coll, "%s_%s_vystup" % (name, engine_key), e["output"], (e["out_x"], 0.0, 0.0), gearbox)
        MOTORY["add_spin"](output, 1.0)
        objs += [gearbox, output]
        for obj in objs:
            for path_name in ("hide_viewport", "hide_render"):
                driver(obj, path_name, -1, "m != %d" % (index + 1), [prop("m", "Motor")])

    # --- diely na rame ---
    tank_x = truck["tank_x"]
    for part_name, location in (("Odt_naraznik", (0.0, 0.0, 0.0)), ("Odt_chladic", (0.0, 0.0, 0.0)),
                                ("Odt_nadrz_nafta", (tank_x, 0.0, 0.0)), ("Odt_nadrz_adblue", (tank_x - 0.86, 0.0, 0.0)),
                                ("Odt_baterie", (tank_x + 0.20, 0.0, 0.0)), ("Odt_vzduchojemy", (tank_x - 0.55, 0.0, 0.0)),
                                ("Odt_vyfuk", (0.0, 0.0, 0.0))):
        new_object(coll, part_name.replace("Odt_", name + "_"), parts[part_name], location, body)
    BUILDERS[truck["variant"]](coll, truck, parts, body, root, prop, mats)

    # --- kabina: vlastne perovanie (klopenie, naklon) a vyklapanie dopredu okolo predneho capu ---
    cab = new_object(coll, name + "_kabina", parts["Odt_kabina"], CAB_HINGE, body)
    cab_vars = [prop("t", "Vyklopenie_kabiny"), prop("p", "Kabina_klopenie"), prop("n", "Kabina_naklon"),
                ("br", "TRANSFORM", (body, "ROT_X"))]
    driver(cab, "rotation_euler", 1, "t * %.3f + (1 - t) * p * %.6f" % (CAB_TILT, DEG), cab_vars)
    driver(cab, "rotation_euler", 0, "(1 - t) * (n * %.6f + 0.6 * br)" % DEG, cab_vars)
    paint(cab, mats[truck["paint"]])
    paint(cab, mats[truck["accent"]], ACCENT)
    new_object(coll, name + "_kabina_doplnky", parts["Odt_od_kabina_" + truck["style"]], (0.0, 0.0, 0.0), cab)
    new_object(coll, name + "_interier", parts["Odt_interier"], (0.0, 0.0, 0.0), cab)
    paint(new_object(coll, name + "_nasavanie", parts["Odt_nasavanie"], (0.0, 0.0, 0.0), cab), mats[truck["paint"]])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        low = Vector((CAB_MOUNT.x, s * CAB_MOUNT.y, CAB_MOUNT_LOW))
        up = Vector((CAB_MOUNT.x, s * CAB_MOUNT.y, CAB_MOUNT.z)) - CAB_HINGE
        for part in link_pair(coll, "%s_perovanie_kabiny_%s" % (name, side), parts["Odt_perovanie_kabiny_mech"],
                              parts["Odt_perovanie_kabiny_piest"], body, low, cab, up, "TRACK_Z", "TRACK_NEGATIVE_Z"):
            # pri vyklapani sa zadne uchytenie odopne (mech ostane na rame, piest na kabine)
            driver(part, 'constraints["%s"].influence' % part.constraints[0].name, -1, "max(0, 1 - t * 8)",
                   [prop("t", "Vyklopenie_kabiny")])

    wheel_frame = Matrix.Translation(CAB_MATRIX @ WHEEL_CENTER) @ STEERING.to_3x3().to_4x4()
    steering = place_spinning(coll, name + "_volant", parts["Odt_volant"], wheel_frame, cab)
    driver(steering, "rotation_euler", 2, "%.5f + r * %.6f" % (steering.rotation_euler[2], DEG * STEER_RATIO),
           [prop("r", "Riadenie")])
    needles = []
    for gauge_name, offset, radius, _, idle in GAUGES:
        g = gauge_frame(offset) @ Matrix.Translation((0.0, 0.0, 0.012))
        frame = Matrix.Translation(CAB_MATRIX @ g.to_translation()) @ g.to_3x3().to_4x4()
        mesh = parts["Odt_rucicka_velka" if radius > 0.05 else "Odt_rucicka_mala"]
        needles.append((gauge_name, place_spinning(coll, "%s_rucicka_%s" % (name, gauge_name), mesh, frame, cab), idle))

    animate(truck, root, terrain, needles, has_tag)
    return root


def animate(truck, root, terrain, needles, has_tag):
    # jazda cez nerovnosti (zadne napravy ich prejdu neskor), potom ukazka ovladacov
    bumps = [(1, 0.0, 0.0), (12, 0.05, 4.0), (24, -0.03, -3.0), (36, 0.06, -5.0), (48, -0.02, 3.0), (60, 0.0, 0.0)]
    for i, (_, ax) in enumerate(truck["axles"]):
        delay = int(round(-ax * 4.0))
        amp = 1.0 if i == 0 else 0.8
        key(terrain[i], "location", 2, [(f + delay, WHEEL_R + z * amp) for f, z, _ in bumps])
        key(terrain[i], "rotation_euler", 0, [(f + delay, math.radians(r * amp)) for f, _, r in bumps])

    def keys(prop_name, frames):
        for frame, value in frames:
            root[prop_name] = value
            root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)

    keys("Riadenie", [(1, 0.0), (20, 18.0), (45, -18.0), (70, 0.0)])
    keys("Kabina_klopenie", [(1, 0.0), (10, 1.2), (22, -1.0), (34, 1.4), (46, -0.8), (58, 0.6), (70, 0.0)])
    keys("Kabina_naklon", [(1, 0.0), (14, -1.5), (28, 2.0), (42, -1.8), (56, 1.2), (70, 0.0)])
    keys("Vyska_podvozku", [(1, 0.0), (95, 0.0), (115, 0.10), (135, 0.10), (155, -0.06), (170, -0.06), (185, 0.0)])
    if has_tag:
        keys("Zdvih_napravy", [(1, 0.0), (195, 0.0), (215, 1.0), (240, 1.0), (258, 0.0)])
    keys("Vyklopenie_kabiny", [(1, 0.0), (265, 0.0), (305, 1.0), (340, 1.0), (378, 0.0)])
    ANIMATORS[truck["variant"]](truck, root, keys)
    for gauge_name, needle, idle in needles:
        z0 = needle.rotation_euler[2]
        if gauge_name in ("rychlost", "otacky"):
            peak = 0.30 if gauge_name == "rychlost" else 0.55
            key(needle, "rotation_euler", 2, [(1, z0 + gauge_angle(idle)), (40, z0 + gauge_angle(peak)), (80, z0 + gauge_angle(idle))])
        else:
            needle.rotation_euler[2] = z0 + gauge_angle(idle)


# ---------------------------------------------------------------------------
# Nadstavby: spolocne veci (suradnice v sustave ramu: x dopredu, z od zeme; ram ma vrch v z = 1.08)
# ---------------------------------------------------------------------------

BED_Z = 1.40                       # horny povrch podlahy nadstavby
BODY_HALF = 1.25                   # polovicna sirka nadstavby (2.50 m)
CRANE_FRONT = -2.35                # predna hrana nadstavby, ked je za kabinou zeriav (drevo, valnik s rukou)
BODY_FRONT = {"ploso_eu": -1.40, "ploso_us": -1.40, "tazka_eu": -1.40, "tazka_us": -1.40}
BUILDERS = {}                      # kluc nadstavby -> funkcia, ktora ju postavi na aute
ANIMATORS = {}                     # kluc nadstavby -> funkcia, ktora nastavi animaciu ovladacov
PART_MAKERS = []                   # funkcie (put, put_lr), ktore vyrobia diely nadstavieb
CATALOG_EXTRA = []                 # (nadpis, [nazvy dielov]) do katalogu
SCENE_EXTRAS = []                  # funkcie (coll, parts, mats), ktore pridaju do sceny dalsie veci (kontajnery)
DOC_EXTRA = []                     # riadky dokumentacie


def body_front(variant):
    return BODY_FRONT[variant]


def body_rear(cfg):
    return cfg["rear_end"] - 0.10


def body_length(variant, cfg):
    return body_front(variant) - body_rear(cfg)


def shift_mesh(mesh, offset):
    mesh.transform(Matrix.Translation(Vector(offset)))


def build_underrun():
    # zadny naraznik (ochrana proti podbehnutiu) so SPZ a odrazkami; pivot na zadnej rovine nadstavby v osi, z od zeme
    bm = bmesh.new()
    add_box(bm, (0.10, 2.30, 0.12), (-0.28, 0.0, 0.62), FRAME, bev=0.012)
    add_box(bm, (0.04, 2.30, 0.02), (-0.335, 0.0, 0.69), STEEL)
    for s in SIDES_LR:
        add_box(bm, (0.30, 0.08, 0.10), (-0.14, s * 0.78, 0.66), FRAME, bev=0.008)
        add_box(bm, (0.10, 0.08, 0.45), (-0.06, s * 0.78, 0.92), FRAME, bev=0.008)
        add_box(bm, (0.012, 0.16, 0.06), (-0.337, s * 1.05, 0.62), RED, bev=0.003)
        add_box(bm, (0.012, 0.10, 0.04), (-0.337, s * 0.30, 0.62), LAMP_RED, bev=0.003)
    add_box(bm, (0.012, 0.52, 0.11), (-0.337, 0.0, 0.62), WHITE, bev=0.003)
    return finish_mesh(bm, "SM_Odt_zadny_naraznik")


def build_side_guard_bm(cfg):
    # bocna ochrana medzi prednou a zadnou napravou (lavy bok), pivot v pociatku ramu
    axles = cfg["axles"]
    first_front = [x for kind, x in axles if kind == "front"][-1]
    first_rear = [x for kind, x in axles if kind != "front"][0]
    x0, x1 = first_front - 0.80 if first_front < -0.5 else -0.95, first_rear + 0.78
    bm = bmesh.new()
    length, xc = x0 - x1, (x0 + x1) * 0.5
    for z in (0.46, 0.62):
        add_box(bm, (length, 0.04, 0.08), (xc, 1.21, z), FRAME, bev=0.006)
    n = max(2, int(length / 1.3))
    for k in range(n + 1):
        x = x1 + 0.12 + k * (length - 0.24) / n
        add_box(bm, (0.05, 0.05, 0.86), (x, 1.21, 0.90), FRAME, bev=0.006)
    return bm


def build_toolbox():
    # skrinka na naradie pod nadstavbou (lava strana), pivot v strede dna
    bm = bmesh.new()
    add_box(bm, (0.80, 0.46, 0.40), (0.0, 0.0, 0.20), DARK, bev=0.03)
    add_box(bm, (0.76, 0.012, 0.34), (0.0, 0.232, 0.20), FRAME, bev=0.005)
    add_box(bm, (0.10, 0.03, 0.05), (0.0, 0.245, 0.30), STEEL, bev=0.005)
    for dx in (-0.30, 0.30):
        add_box(bm, (0.04, 0.012, 0.06), (dx, 0.238, 0.30), STEEL, bev=0.003)
    return finish_mesh(bm, "SM_Odt_naradie_skrinka")


# ---------------------------------------------------------------------------
# Hydraulicke valce: teleskopicky valec z n stupnov (dlzka stupna ell); vonkajsi stupen mieri na ciel (os +Z),
# dalsie stupne sa podla vzdialenosti vysuvaju: poloha k-teho stupna = (d - ell) * k / (n - 1)
# ---------------------------------------------------------------------------

def build_cyl_stage(prefix, k, n, ell, radii, name_mat=None):
    bm = bmesh.new()
    r = radii[k]
    add_cylinder(bm, r, ell, along_z((0.0, 0.0, ell * 0.5)), STEEL if k == 0 else CHROME, segments=10, bev=0.004)
    if k == 0:
        add_cylinder(bm, r * 1.08, 0.04, along_z((0.0, 0.0, 0.02)), DARK, segments=10)
        add_cylinder(bm, r * 0.75, r * 2.6, along_y((0.0, 0.0, -0.02)), DARK, segments=8)
        add_box(bm, (r * 1.5, r * 2.0, 0.10), (0.0, 0.0, 0.05), DARK, bev=0.004)
    if k == n - 1:
        add_cylinder(bm, r * 1.25, 0.05, along_z((0.0, 0.0, ell - 0.01)), STEEL, segments=10)
        add_cylinder(bm, r * 0.85, r * 3.0, along_y((0.0, 0.0, ell + 0.03)), DARK, segments=8)
    return finish_mesh(bm, "SM_Odt_valec_%s_%d" % (prefix, k))


def cylinder_family(put, prefix, n, ell, r0):
    radii = [r0 * (1.0 - 0.16 * k) for k in range(n)]
    for k in range(n):
        put(build_cyl_stage(prefix, k, n, ell, radii))


def telescope(coll, name, parts, prefix, n, ell, base_parent, base_pt, aim_parent, aim_pt, vars_extra=None):
    # postavi teleskopicky valec; vrati (zaklad, ciel)
    base = new_object(coll, name + "_1", parts["Odt_valec_%s_0" % prefix], base_pt, base_parent)
    aim = empty(coll, name + "_ciel", aim_pt, aim_parent)
    track(base, aim, "TRACK_Z")
    for k in range(1, n):
        stage = new_object(coll, "%s_%d" % (name, k + 1), parts["Odt_valec_%s_%d" % (prefix, k)], (0.0, 0.0, 0.0), base)
        driver(stage, "location", 2, "(d - %.4f) * %.4f" % (ell, k / (n - 1.0)), [("d", "DIST", (base, aim))])
    return base, aim


def accent(obj, truck, mats):
    # akcentova farba nadstavby (na objekte, mesh ostava spolocny)
    paint(obj, mats[truck["accent"]], ACCENT)
    return obj


def extend_driver(obj, path, index, add_expr, variables):
    # pripoji k existujucemu driveru dalsi clen vyrazu a premenne (iba vlastnosti objektu: (meno, "PROP", (objekt, '["x"]')))
    drv = obj.animation_data.drivers.find(path, index=index).driver
    for name, kind, data in variables:
        var = drv.variables.new()
        var.name = name
        var.type = "SINGLE_PROP"
        var.targets[0].id_type = "OBJECT"
        var.targets[0].id = data[0]
        var.targets[0].data_path = data[1]
    drv.expression = "%s + (%s)" % (drv.expression, add_expr)


# ---------------------------------------------------------------------------
# Spolocne pre odtahovky: pocet stupnov teleskopu, doplnky na kabine a podvozku podla stylu (eu / us)
# ---------------------------------------------------------------------------

def tele_stages(dmin, dmax):
    # dlzka stupna a pocet stupnov teleskopickeho valca pre rozsah vzdialenosti dmin az dmax (stupne sa prekryvaju aspon z 18 %)
    ell = dmin * 0.985
    n = max(2, int(math.ceil((dmax - ell) / (0.82 * ell))) + 1)
    return n, ell


def diamond(bm, x0, x1, y0, y1, z, mat=STEEL, step=0.13):
    # imitacia rifladeho plechu: radky malych sikmych listiek v obdlzniku (os X - os Y) vo vyske z
    ix = max(1, int((x1 - x0) / step))
    iy = max(1, int((y1 - y0) / step))
    for i in range(ix):
        for j in range(iy):
            x = x0 + (i + 0.5) * (x1 - x0) / ix
            y = y0 + (j + 0.5) * (y1 - y0) / iy
            add_box(bm, (0.055, 0.012, 0.006), (x, y, z + 0.003), mat, rotation=(0.0, 0.0, 45.0 if (i + j) % 2 else -45.0))


def cab_local(p):
    return (p[0] - CAB_HINGE.x, p[1] - CAB_HINGE.y, p[2] - CAB_HINGE.z)


def build_cab_extras(style):
    # doplnky na streche kabiny (pivot ako kabina), osadene na skutocny hrebien strechy (z = 3.71 v x = -0.8, strecha klesa dopredu):
    # eu = dva oranzove majaky, us = siroka svetelna lista na styroch nohach
    bm = bmesh.new()
    xr, zr = -0.80, 3.71
    if style == "eu":
        for s in SIDES_LR:
            add_cylinder(bm, 0.15, 0.12, along_z(cab_local((xr, s * 0.60, zr + 0.01))), DARK, segments=10, bev=0.004)
            add_cylinder(bm, 0.12, 0.15, along_z(cab_local((xr, s * 0.60, zr + 0.13))), LAMP_OR, segments=10, bev=0.01)
            add_cylinder(bm, 0.05, 0.03, along_z(cab_local((xr, s * 0.60, zr + 0.22))), DARK, segments=8)
    else:
        add_box(bm, (0.34, 1.60, 0.12), cab_local((xr - 0.02, 0.0, zr + 0.01)), DARK, bev=0.008)
        for s in SIDES_LR:
            for dx in (-0.12, 0.12):
                add_box(bm, (0.06, 0.06, 0.16), cab_local((xr - 0.02 + dx, s * 0.62, zr - 0.06)), STEEL, bev=0.004)
        for k in range(8):
            y = -0.70 + 0.20 * k
            add_box(bm, (0.28, 0.17, 0.10), cab_local((xr - 0.02, y, zr + 0.12)), LAMP_OR if k % 4 != 1 else LAMP_WHITE, bev=0.012)
        for s in SIDES_LR:
            add_box(bm, (0.32, 0.06, 0.12), cab_local((xr - 0.02, s * 0.83, zr + 0.08)), DARK, bev=0.008)
            add_cylinder(bm, 0.018, 0.30, along_z(cab_local((xr + 0.12, s * 0.50, zr + 0.14))), CHROME, segments=6)
    return finish_mesh(bm, "SM_Odt_od_kabina_" + style)


def build_us_extras():
    # americky styl na rame: dva chromove vertikalne kominy za kabinou a naraznikova mriez (bull bar) vpredu
    bm = bmesh.new()
    for s in SIDES_LR:
        add_cylinder(bm, 0.07, 2.45, along_z((-1.28, s * 1.05, 2.30)), CHROME, segments=10, bev=0.004)
        add_cylinder(bm, 0.085, 0.10, along_z((-1.28, s * 1.05, 3.56)), STEEL, segments=10)
        add_box(bm, (0.20, 0.42, 0.06), (-1.28, s * 0.84, 1.10), DARK, bev=0.006)
        for z in (1.50, 2.10, 2.70):
            add_box(bm, (0.14, 0.04, 0.05), (-1.20, s * 1.05, z), STEEL, bev=0.004)
            add_cylinder(bm, 0.075, 0.03, along_z((-1.28, s * 1.05, z)), STEEL, segments=10)
        add_rod(bm, (1.36, s * 0.62, 0.58), (1.36, s * 0.62, 1.38), 0.035, CHROME, segments=8)
        add_rod(bm, (1.36, s * 0.62, 1.38), (1.36, s * 0.10, 1.38), 0.032, CHROME, segments=8)
        add_rod(bm, (1.36, s * 0.62, 0.62), (1.28, s * 0.62, 0.62), 0.028, CHROME, segments=8)
    add_rod(bm, (1.36, 0.0, 0.58), (1.36, 0.0, 1.38), 0.035, CHROME, segments=8)
    add_rod(bm, (1.36, -0.62, 0.98), (1.36, 0.62, 0.98), 0.030, CHROME, segments=8)
    add_rod(bm, (1.36, -0.62, 1.38), (1.36, 0.62, 1.38), 0.032, CHROME, segments=8)
    for z in (0.62, 1.38):
        add_cylinder(bm, 0.05, 0.03, along_x((1.285, 0.0, z)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Odt_od_us_doplnky")


D2R = 0.017453


def hose(bm, k, x0, x1, z, ys=(-0.08, 0.08), sag=0.0):
    for y in ys:
        add_rod(bm, (x0, y * k, z), (x1, y * k, z), 0.019 * k, DARK, segments=6)
        add_cylinder(bm, 0.026 * k, 0.04 * k, along_x((x0 + 0.02 * k, y * k, z)), STEEL, segments=6)
        add_cylinder(bm, 0.026 * k, 0.04 * k, along_x((x1 - 0.02 * k, y * k, z)), STEEL, segments=6)
    for x in (x0 + 0.3 * k, (x0 + x1) * 0.5, x1 - 0.3 * k):
        add_box(bm, (0.04 * k, 0.28 * k, 0.03 * k), (x, 0.0, z + 0.02 * k), STEEL, bev=0.004)


def grease(bm, p, k, axis="y"):
    # maznica na klbe
    add_cylinder(bm, 0.012 * k, 0.04 * k, along_z((p[0], p[1], p[2] + 0.02 * k)), CHROME, segments=6)
    add_cylinder(bm, 0.018 * k, 0.012 * k, along_z((p[0], p[1], p[2] + 0.045 * k)), YELLOW, segments=6)


def pin(bm, p, r, length, k):
    # cap klbu: ocelovy valec s vekami a maznicou
    add_cylinder(bm, r * k, length * k, along_y(p), CHROME, segments=10)
    for s in SIDES_LR:
        add_cylinder(bm, r * 1.35 * k, 0.02 * k, along_y((p[0], p[1] + s * length * 0.5 * k, p[2])), DARK, segments=10)
        add_cylinder(bm, r * 0.45 * k, 0.014 * k, along_y((p[0], p[1] + s * (length * 0.5 + 0.012) * k, p[2])), STEEL, segments=6)


def segment(bm, k, length, t0, t1, half_w, mat, stripes=False):
    # nosnik: lichobeznikovy prierez, hrubka v Y; t0 = polovicne vysky pri pivote (dole, hore), t1 = na konci
    pts = [(-0.14 * k, -t0[0] * k), (length, -t1[0] * k), (length, t1[1] * k), (-0.14 * k, t0[1] * k)]
    add_extruded(bm, pts, -half_w * k, half_w * k, "XZ", mat, bev=0.014)
    for y in (-half_w * 0.55, half_w * 0.55):
        add_box(bm, (length - 0.4 * k, 0.012, 0.012), (length * 0.5 - 0.06 * k, y * k, (t0[1] + t1[1]) * 0.5 * k + 0.004), STEEL)
    if stripes:
        for i in range(5):
            add_box(bm, (0.05 * k, (half_w * 2 + 0.01) * k, (t1[0] + t1[1]) * k + 0.01), (length - 0.30 * k + 0.07 * k * i, 0.0, 0.0),
                    YELLOW if i % 2 == 0 else DARK, bev=0.002)


def od_shared_parts(put, put_lr):
    put(build_toolbox())
    put(build_cab_extras("eu"))
    put(build_cab_extras("us"))
    put(build_us_extras())
    for cfg in CONFIGS:
        put_lr(build_side_guard_bm(cfg), "SM_Odt_bocna_ochrana_%s" % cfg["cfg"])


PART_MAKERS.append(od_shared_parts)

# ---------------------------------------------------------------------------
# Plosinova odtahovka (rollback): sklopny podram s odsuvnou plosinou (cap vzadu na rame), navijak s lanom a hakom,
# odtahovane auto. Najprv sa podram sklopi (zadok dolu), potom plosina zjazdi po podrame sikmo dole az na zem a navijak vytiahne auto.
# Dva styly: eu (nizky tlakovy ram, oranzovy/zlty) a us (vysoky rebrik z chromovych rur, kominy, bull bar, cervena).
# ---------------------------------------------------------------------------

PL_FRONT = -1.55                     # predna hrana plosiny
PL_ZP, PL_BOT, PL_THICK = 1.22, 1.36, 0.20     # os klbu naklapania, spodok plosiny, hrubka
PL_KEEP = 0.90                       # kolko plosiny ostane na podrame po odsune (menej = plosina vyjde dalej = mensi sklon)
PL_WEDGE = 1.25                      # dlzka skoseneho konca plosiny
PL_CARS = {"4x2": dict(L=3.40, wb=2.15, fo=0.55, w=1.62, h=1.42, rw=0.28, paint=PAINT_BLUE),
           "6x2": dict(L=4.50, wb=2.70, fo=0.85, w=1.78, h=1.45, rw=0.31, paint=PAINT_RED)}


def pl_geo(cfg):
    # rozmery a uhol sklopenia: spicka skoseneho konca plosiny sa po odsune dotkne zeme
    x_br = cfg["rear_end"] - 0.10
    xp = x_br + 0.40
    lb = PL_FRONT - x_br
    slide = lb - PL_KEEP                 # po odsune ostane pred klbom este PL_KEEP - 0.40 m plosiny
    xr, xf = -0.40, lb - 0.40
    zb = PL_BOT - PL_ZP
    zt = zb + PL_THICK
    th = 0.3
    for _ in range(60):
        th = math.asin(min(0.9, (PL_ZP + (zb + 0.03) * math.cos(th)) / (-xr + slide)))
    return dict(xp=xp, x_br=x_br, lb=lb, slide=slide, theta=th, xr=xr, xf=xf, zb=zb, zt=zt)


def pl_bed_matrix(g, t, s):
    # plosina (suradnice v osi klbu, rest) -> ram, pri sklone t a odsune s
    return (Matrix.Translation((g["xp"], 0.0, PL_ZP)) @ Euler((0.0, -g["theta"] * t, 0.0), "XYZ").to_matrix().to_4x4()
            @ Matrix.Translation((-g["slide"] * s, 0.0, 0.0)))


def pl_tilt_cyl(g):
    # naklapaci valce (dva v kanali medzi nosnikmi): zaklad B na rame, ucho A na podrame
    ax = 0.45 * g["lb"]
    a_rel = Vector((ax, 0.28, -0.02))
    b = Vector((g["xp"] + ax + 1.20, 0.28, 1.14))
    ds = []
    for i in range(41):
        th = g["theta"] * i / 40.0
        a = Vector((g["xp"] + a_rel.x * math.cos(th) - a_rel.z * math.sin(th), 0.28, PL_ZP + a_rel.x * math.sin(th) + a_rel.z * math.cos(th)))
        ds.append((a - b).length)
    n, ell = tele_stages(min(ds), max(ds))
    return dict(a_rel=a_rel, b=b, n=n, ell=ell, dmin=min(ds), dmax=max(ds))


def pl_slide_cyl(g):
    d0 = max(1.6, 0.48 * g["lb"])
    base_x = g["xf"] - 0.15
    n, ell = tele_stages(d0, d0 + g["slide"])
    return dict(base=Vector((base_x, 0.0, -0.02)), aim=Vector((base_x - d0, 0.0, -0.02)), n=n, ell=ell, d0=d0, dmax=d0 + g["slide"])


def build_pl_bed(cfg, style):
    # plosina: pivot v osi klbu (v kludovej polohe), x dopredu; spodok z = zb, vrch z = zt; zadny koniec skoseny na zem
    g = pl_geo(cfg)
    eu = style == "eu"
    bm = bmesh.new()
    xr, xf, zb, zt = g["xr"], g["xf"], g["zb"], g["zt"]
    prof = [(xr, zb + 0.03), (xr + 0.10, zb), (xf, zb), (xf, zt), (xr + PL_WEDGE, zt)]
    add_extruded(bm, prof, -1.15, 1.15, "XZ", ALU if eu else GALV, bev=0.005)
    side = [(xr, zb + 0.03), (xr + 0.10, zb), (xf, zb), (xf, zt + 0.05), (xr + PL_WEDGE, zt + 0.05)]
    for s in SIDES_LR:
        add_extruded(bm, side, s * 1.15, s * 1.25, "XZ", ACCENT, bev=0.006)
        for x in [xr + PL_WEDGE + 0.35 + 0.80 * k for k in range(int((xf - xr - PL_WEDGE - 1.6) / 0.80) + 1)]:
            add_box(bm, (0.16, 0.06, 0.012), (x, s * 1.20, zt + 0.056), DARK, bev=0.004)
            add_box(bm, (0.10, 0.025, 0.03), (x, s * 1.12, zt + 0.01), STEEL, bev=0.004)
        add_box(bm, (xf - xr - 0.4, 0.14, 0.04), ((xf + xr) * 0.5 + 0.1, s * 0.50, zb - 0.02), STEEL, bev=0.004)
    for k in range(int((xf - xr - PL_WEDGE - 1.4) / 0.26)):
        add_box(bm, (0.030, 2.10, 0.010), (xr + PL_WEDGE + 0.30 + 0.26 * k, 0.0, zt + 0.005), STEEL if eu else ALU)
    for k in range(int(PL_WEDGE / 0.22)):
        x = xr + 0.14 + 0.22 * k
        zz = zb + 0.03 + (zt - zb - 0.03) * (x - xr) / PL_WEDGE
        add_box(bm, (0.03, 2.10, 0.010), (x, 0.0, zz + 0.004), STEEL, bev=0.002, rotation=(0.0, -math.degrees(math.atan2(zt - zb - 0.03, PL_WEDGE)), 0.0))
    add_box(bm, (xf - xr - PL_WEDGE - 1.2, 0.16, 0.006), ((xr + PL_WEDGE + xf - 1.2) * 0.5, 0.0, zt + 0.003), DARK)
    if not eu:
        for yy in (-0.65, 0.65):
            add_box(bm, (xf - xr - PL_WEDGE - 1.2, 0.05, 0.012), ((xr + PL_WEDGE + xf - 1.2) * 0.5, yy, zt + 0.006), STEEL, bev=0.003)
        diamond(bm, xr + PL_WEDGE + 0.2, xf - 1.3, -1.10, -0.80, zt, STEEL, 0.15)
        diamond(bm, xr + PL_WEDGE + 0.2, xf - 1.3, 0.80, 1.10, zt, STEEL, 0.15)
    for s in SIDES_LR:
        add_box(bm, (0.04, 0.14, 0.05), (xr + 0.02, s * 1.09, zb + 0.05), LAMP_RED, bev=0.004)
        add_box(bm, (0.05, 0.08, 0.07), (xr + 0.05, s * 1.19, zb + 0.06), STEEL, bev=0.004)
        add_cylinder(bm, 0.025, 0.07, along_y((xr + 0.05, s * 1.19, zb + 0.08)), CHROME, segments=8)
        for k in range(5):
            add_box(bm, (0.03, 0.10, 0.04), (xr + 0.25 + 0.20 * k, s * 1.255, zb + 0.10 + 0.012 * k), RED if k % 2 == 0 else WHITE, bev=0.002)
    return finish_mesh(bm, "SM_Odt_od_plosina_%s_%s" % (style, cfg["cfg"]))


def build_pl_rack(style):
    # celna stena plosiny (ochrana kabiny): pivot v strede prednej hrany plosiny na vrchu podlahy (x dozadu od hrany je zaporne)
    eu = style == "eu"
    bm = bmesh.new()
    hr = 1.00 if eu else 1.40
    for s in SIDES_LR:
        if eu:
            add_box(bm, (0.12, 0.12, hr), (-0.06, s * 1.10, hr * 0.5), ACCENT, bev=0.012)
        else:
            add_rod(bm, (-0.06, s * 1.12, 0.0), (-0.06, s * 1.12, hr), 0.055, CHROME, segments=10)
            add_box(bm, (0.16, 0.16, 0.06), (-0.06, s * 1.12, 0.03), STEEL, bev=0.006)
    if eu:
        add_box(bm, (0.12, 2.34, 0.12), (-0.06, 0.0, hr), ACCENT, bev=0.012)
        add_box(bm, (0.05, 2.12, 0.14), (-0.06, 0.0, 0.07), ACCENT, bev=0.01)
        add_box(bm, (0.05, 2.12, hr - 0.30), (-0.06, 0.0, 0.14 + (hr - 0.30) * 0.5), ACCENT, bev=0.01)
        for y in (-0.72, 0.0, 0.72):
            add_box(bm, (0.052, 0.46, 0.34), (-0.06, y, 0.52), DARK, bev=0.01)
        for k in (0, 1, 4, 5):
            add_box(bm, (0.09, 0.22, 0.07), (0.0, -0.92 + 0.368 * k, hr + 0.09), LAMP_OR, bev=0.01)
    else:
        for z in (0.40, 0.90, hr):
            add_rod(bm, (-0.06, -1.12, z), (-0.06, 1.12, z), 0.045 if z == hr else 0.035, CHROME, segments=10)
        add_box(bm, (0.06, 2.10, 0.42), (-0.06, 0.0, 0.22), GALV, bev=0.008)
        diamond(bm, -0.14, -0.10, -1.0, 1.0, 0.43, STEEL, 0.14)
        for k in range(-8, 9):
            add_rod(bm, (-0.06, k * 0.13, 0.43), (-0.06, k * 0.13, hr - 0.02), 0.014, STEEL, segments=6)
        for s in SIDES_LR:
            add_box(bm, (0.14, 0.50, 0.07), (-0.02, s * 0.72, hr + 0.07), DARK, bev=0.01)
        for k in (0, 1, 6, 7):
            add_box(bm, (0.12, 0.17, 0.08), (0.04, -0.70 + 0.20 * k, hr + 0.07), LAMP_OR if k % 4 != 1 else LAMP_WHITE, bev=0.01)
    # drziak haku a retaze (vlavo na zadnej strane steny)
    add_box(bm, (0.12, 0.30, 0.04), (0.04, -0.52, 0.50), STEEL, bev=0.005)
    add_cylinder(bm, 0.025, 0.12, along_x((0.06, -0.52, 0.50)), CHROME, segments=8)
    for s in SIDES_LR:
        add_box(bm, (0.10, 0.10, 0.08), (0.0, s * 1.10, hr - 0.14), STEEL, bev=0.008)
    return finish_mesh(bm, "SM_Odt_od_celna_stena_" + style)


def build_pl_winch(style):
    # navijak (pevna cast, maly): ram, hydromotor, drziak haku, lanova vodiaca kladka; pivot na podlahe v strede, dozadu je -X; buben je zvlast
    eu = style == "eu"
    bm = bmesh.new()
    # polica na celnej stene (stena je +0.22 pred stredom navijaka) s dvoma konzolami
    add_box(bm, (0.54, 0.90, 0.04), (-0.05, 0.0, -0.02), FRAME, bev=0.006)
    for s in SIDES_LR:
        add_extruded(bm, [(0.22, -0.04), (-0.18, -0.04), (0.22, -0.38)], s * 0.40 - 0.02, s * 0.40 + 0.02, "XZ", FRAME, bev=0.004)
    add_box(bm, (0.36, 0.80, 0.04), (0.0, 0.0, 0.02), FRAME, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.26, 0.04, 0.30), (0.0, s * 0.34, 0.19), ACCENT, bev=0.008)
        add_cylinder(bm, 0.045, 0.06, along_y((0.0, s * 0.375, 0.22)), STEEL, segments=8)
    add_box(bm, (0.18, 0.14, 0.14), (0.02, 0.45, 0.16), DARK if eu else CHROME, bev=0.012)
    add_cylinder(bm, 0.06, 0.18, along_y((0.0, 0.47, 0.24)), DARK, segments=8, bev=0.006)
    add_box(bm, (0.08, 0.70, 0.03), (-0.08, 0.0, 0.07), STEEL, bev=0.003)
    # drziak haku: stlpik s doskou pri vodiacej kladke vlavo
    add_box(bm, (0.05, 0.05, 0.40), (-0.26, -0.20, 0.22), STEEL, bev=0.004)
    add_box(bm, (0.14, 0.12, 0.03), (-0.26, -0.20, 0.43), STEEL, bev=0.004)
    add_cylinder(bm, 0.015, 0.08, along_x((-0.26, -0.20, 0.46)), CHROME, segments=8)
    # lanova vodiaca kladka (vzadu pri podlahe) a vodiace puzdra
    add_cylinder(bm, 0.045, 0.28, along_y((-0.28, 0.0, 0.08)), STEEL, segments=8, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.08, 0.04, 0.10), (-0.28, s * 0.16, 0.07), DARK, bev=0.004)
        add_box(bm, (0.03, 0.03, 0.08), (-0.28, s * 0.19, 0.12), STEEL, bev=0.003)
    return finish_mesh(bm, "SM_Odt_od_navijak_" + style)


def build_pl_drum():
    # buben navijaka (otaca sa okolo Y): lano navinute, dve cela
    bm = bmesh.new()
    add_cylinder(bm, 0.10, 0.50, along_y((0.0, 0.0, 0.0)), STEEL, segments=12, bev=0.004)
    add_cylinder(bm, 0.12, 0.40, along_y((0.0, 0.0, 0.0)), DARK, segments=12)
    for s in SIDES_LR:
        add_cylinder(bm, 0.16, 0.03, along_y((0.0, s * 0.26, 0.0)), STEEL, segments=12, bev=0.004)
    for k in range(6):
        a = 2.0 * math.pi * k / 6.0
        add_box(bm, (0.02, 0.40, 0.008), (0.122 * math.cos(a), 0.0, 0.122 * math.sin(a)), GALV, rotation=(0.0, -math.degrees(a), 0.0))
    return finish_mesh(bm, "SM_Odt_od_navijak_buben")


def build_pl_hook():
    # hak na lane: pivot v oku (hore); retaz, hak s poistkou
    bm = bmesh.new()
    add_box(bm, (0.08, 0.05, 0.08), (0.0, 0.0, -0.04), STEEL, bev=0.008)
    for i in range(3):
        add_box(bm, (0.03, 0.06 if i % 2 else 0.02, 0.06), (0.0, 0.0, -0.11 - i * 0.055), DARK, bev=0.004)
    add_box(bm, (0.10, 0.10, 0.12), (0.0, 0.0, -0.36), RED, bev=0.01)
    add_rod(bm, (0.0, 0.0, -0.42), (0.0, 0.0, -0.52), 0.032, STEEL, segments=8)
    cx, cz, r = 0.11, -0.52, 0.11
    pts = [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))) for a in (180, 215, 250, 285, 320, 350)]
    for a, b in zip(pts, pts[1:]):
        add_rod(bm, (a[0], 0.0, a[1]), (b[0], 0.0, b[1]), 0.030, STEEL, segments=8)
    add_box(bm, (0.012, 0.05, 0.05), (pts[-1][0] + 0.012, 0.0, pts[-1][1] + 0.045), DARK, bev=0.002)
    return finish_mesh(bm, "SM_Odt_od_hak")


def build_pl_cable():
    bm = bmesh.new()
    add_cylinder(bm, 0.014, 1.0, along_z((0.0, 0.0, 0.5)), DARK, segments=6)
    return finish_mesh(bm, "SM_Odt_od_lano")


def build_pl_rails(cfg):
    # sklopny podram (dva nosniky s valcekmi, priecniky, cap, ucha valcov); pivot v osi klbu, x dopredu
    g = pl_geo(cfg)
    bm = bmesh.new()
    xf = g["xf"]
    zb = g["zb"]
    x0, x1 = -0.30, xf - 0.08
    for s in SIDES_LR:
        add_box(bm, (x1 - x0, 0.16, 0.26), ((x0 + x1) * 0.5, s * 0.50, zb - 0.13), FRAME, bev=0.012)
        add_box(bm, (x1 - x0, 0.02, 0.20), ((x0 + x1) * 0.5, s * 0.59, zb - 0.13), ACCENT, bev=0.004)
        for k in range(int((x1 - x0) / 0.60) + 1):
            x = x0 + 0.15 + k * 0.60
            if x < x1 - 0.10:
                add_cylinder(bm, 0.050, 0.10, along_y((x, s * 0.50, zb - 0.01)), STEEL, segments=10, bev=0.004)
        add_cylinder(bm, 0.09, 0.14, along_y((-0.22, s * 0.50, zb - 0.02)), STEEL, segments=12, bev=0.006)
        add_box(bm, (0.14, 0.05, 0.22), (g["xr"] + 0.0 + 0.40 + 0.0 + 0.0, s * 0.64, -0.01), STEEL, bev=0.004)
    for k in range(int((x1 - x0) / 0.70) + 1):
        x = x0 + 0.20 + k * 0.70
        if x < x1 - 0.10:
            add_box(bm, (0.08, 0.84, 0.07), (x, 0.0, zb - 0.07), FRAME, bev=0.006)
    add_cylinder(bm, 0.07, 1.46, along_y((0.0, 0.0, 0.0)), CHROME, segments=12)
    for s in SIDES_LR:
        add_cylinder(bm, 0.09, 0.03, along_y((0.0, s * 0.74, 0.0)), DARK, segments=12)
    t = pl_tilt_cyl(g)
    sc = pl_slide_cyl(g)
    ax = t["a_rel"].x
    for s in SIDES_LR:
        add_box(bm, (0.16, 0.04, 0.12), (ax, s * 0.28, -0.04), STEEL, bev=0.004)
        add_cylinder(bm, 0.030, 0.12, along_y((ax, s * 0.28, -0.02)), CHROME, segments=8)
    add_box(bm, (0.30, 0.60, 0.05), (ax, 0.0, -0.08), FRAME, bev=0.006)
    add_box(bm, (0.16, 0.30, 0.12), (sc["base"].x, 0.0, -0.02), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Odt_od_podram_" + cfg["cfg"])


def build_pl_base(cfg, style):
    # pevne diely na rame: noznice cepu klbu, konzoly naklapacich valcov, gumove dosadacie podlozky, ramove priecky
    g = pl_geo(cfg)
    bm = bmesh.new()
    t = pl_tilt_cyl(g)
    for s in SIDES_LR:
        add_box(bm, (0.34, 0.06, 0.34), (g["xp"], s * 0.64, 1.25), ACCENT, bev=0.01)
        add_box_between(bm, (g["xp"] + 0.12, s * 0.64, 1.10), (g["xp"] - 0.22, s * 0.52, 0.86), 0.08, 0.12, FRAME, bev=0.006)
        add_box(bm, (0.30, 0.16, 0.04), (g["xp"], s * 0.58, 1.10), FRAME, bev=0.004)
        add_box(bm, (0.20, 0.10, 0.08), (t["b"].x, s * 0.28, 1.11), STEEL, bev=0.005)
        add_cylinder(bm, 0.03, 0.12, along_y((t["b"].x, s * 0.28, 1.14)), CHROME, segments=8)
    add_box(bm, (0.26, 0.74, 0.04), (t["b"].x, 0.0, 1.10), FRAME, bev=0.005)
    xs = [g["xp"] + 0.90 + k * 0.9 * g["lb"] / 4.0 for k in range(4)]
    for x in xs:
        for s in SIDES_LR:
            add_box(bm, (0.20, 0.20, 0.02), (x, s * 0.50, 1.09), TIRE, bev=0.003)
    add_box(bm, (0.08, 1.34, 0.10), (g["x_br"] + 0.06, 0.0, 0.92), FRAME, bev=0.008)
    return finish_mesh(bm, "SM_Odt_od_podstavec_%s_%s" % (style, cfg["cfg"]))


def build_od_car(size):
    # odtahovane auto (pivot v strede medzi nap ravami vo vyske osi, predok +X); vsetko okrem kolies
    c = PL_CARS[size]
    L, wb, fo, w, h, rw = c["L"], c["wb"], c["fo"], c["w"], c["h"], c["rw"]
    xf, xr = wb * 0.5 + fo, -(L - wb * 0.5 - fo)
    zb0, zroof = -rw + 0.17, h - rw
    bm = bmesh.new()
    prof = [(xr, zb0), (xf, zb0), (xf, 0.04), (xf - 0.30, 0.30), (wb * 0.5 - 0.35, 0.36), (wb * 0.5 - 0.95, zroof),
            (-wb * 0.5 + 0.30, zroof), (-wb * 0.5 - 0.50, 0.40), (xr, 0.34)]
    add_extruded(bm, prof, -w * 0.5 + 0.04, w * 0.5 - 0.04, "XZ", c["paint"], bev=0.012)
    add_box(bm, (L, w, 0.14), ((xf + xr) * 0.5, 0.0, zb0 + 0.07), c["paint"], bev=0.02)
    for s in SIDES_LR:
        win = [(wb * 0.5 - 0.42, 0.40), (wb * 0.5 - 0.92, zroof - 0.07), (-wb * 0.5 + 0.38, zroof - 0.07), (-wb * 0.5 - 0.38, 0.44)]
        add_extruded(bm, win, s * (w * 0.5 - 0.043), s * (w * 0.5 - 0.034), "XZ", GLASS, bev=0.0)
        add_box(bm, (0.06, 0.10, 0.04), (wb * 0.5 - 0.50, s * (w * 0.5 + 0.02), 0.38), DARK, bev=0.006)
        add_cylinder(bm, rw + 0.04, 0.012, along_y((wb * 0.5, s * (w * 0.5 - 0.035), 0.0)), DARK, segments=12)
        add_cylinder(bm, rw + 0.04, 0.012, along_y((-wb * 0.5, s * (w * 0.5 - 0.035), 0.0)), DARK, segments=12)
        add_box(bm, (0.04, 0.22, 0.09), (xf - 0.01, s * (w * 0.5 - 0.24), 0.08), LAMP_WHITE, bev=0.006)
        add_box(bm, (0.04, 0.22, 0.08), (xr + 0.01, s * (w * 0.5 - 0.24), 0.14), LAMP_RED, bev=0.006)
    ws = [(wb * 0.5 - 0.35, 0.36), (wb * 0.5 - 0.95, zroof), (wb * 0.5 - 0.92, zroof - 0.06), (wb * 0.5 - 0.40, 0.38)]
    add_extruded(bm, ws, -w * 0.5 + 0.12, w * 0.5 - 0.12, "XZ", GLASS)
    add_box(bm, (0.10, w - 0.04, 0.12), (xf + 0.02, 0.0, zb0 + 0.10), DARK, bev=0.02)
    add_box(bm, (0.10, w - 0.04, 0.12), (xr - 0.02, 0.0, zb0 + 0.10), DARK, bev=0.02)
    add_box(bm, (0.03, 0.50, 0.12), (xf + 0.01, 0.0, 0.0), DARK, bev=0.006)
    add_box(bm, (0.014, 0.36, 0.09), (xf + 0.075, 0.0, zb0 + 0.10), WHITE, bev=0.003)
    add_box(bm, (0.04, 0.10, 0.04), (xf + 0.05, 0.0, zb0 + 0.02), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Odt_od_auto_" + size)


def build_od_car_wheel(size):
    c = PL_CARS[size]
    rw = c["rw"]
    bm = bmesh.new()
    add_cylinder(bm, rw, 0.20, along_y((0.0, 0.0, 0.0)), TIRE, segments=14, bev=0.015)
    add_cylinder(bm, rw * 0.62, 0.21, along_y((0.0, 0.0, 0.0)), RIM, segments=10)
    add_cylinder(bm, rw * 0.22, 0.23, along_y((0.0, 0.0, 0.0)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Odt_od_auto_koleso_" + size)


def pl_rail_path(g, car):
    # stredy osi kolies auta pri vytahovani: zem -> skosenie plosiny -> paluba (offset povrchu o polomer kolesa); body (x, z) v rame
    m = pl_bed_matrix(g, 1.0, 1.0)

    def w(x, z):
        v = m @ Vector((x, 0.0, z))
        return Vector((v.x, v.z))

    tip = w(g["xr"], g["zb"] + 0.03)
    pts = [Vector((tip.x - 30.0, 0.0)), tip, w(g["xr"] + PL_WEDGE, g["zt"]), w(g["xf"], g["zt"])]
    rw = car["rw"]
    lines = []
    for a, b in zip(pts, pts[1:]):
        d = (b - a).normalized()
        n = Vector((-d.y, d.x))
        lines.append((a + n * rw, d))

    def meet(l1, l2):
        (p1, d1), (p2, d2) = l1, l2
        det = d1.x * (-d2.y) - d1.y * (-d2.x)
        t = ((p2.x - p1.x) * (-d2.y) - (p2.y - p1.y) * (-d2.x)) / det
        return p1 + d1 * t

    path = [lines[0][0], meet(lines[0], lines[1]), meet(lines[1], lines[2]), lines[2][0] + lines[2][1] * (pts[3] - pts[2]).length]
    return path, pts


def path_point(path, s):
    # bod na lomenej ciare v dlzke obluka s
    acc = 0.0
    for a, b in zip(path, path[1:]):
        seg = (b - a).length
        if acc + seg >= s or b is path[-1]:
            return a + (b - a) * min(1.0, max(0.0, (s - acc) / seg))
        acc += seg
    return path[-1]


def path_length(path):
    return sum((b - a).length for a, b in zip(path, path[1:]))


def path_param(path, p):
    # dlzka obluka najblizsieho bodu lomenej ciary k bodu p
    best, best_s, acc = 1e9, 0.0, 0.0
    for a, b in zip(path, path[1:]):
        d = b - a
        t = max(0.0, min(1.0, (p - a).dot(d) / d.length_squared))
        q = a + d * t
        if (q - p).length < best:
            best, best_s = (q - p).length, acc + d.length * t
        acc += d.length
    return best_s


def car_pose(path, s_front, wb):
    # predna os na ciare v dlzke s_front, zadna os o rozvor za nou
    f = path_point(path, s_front)
    lo, hi = max(0.0, s_front - wb * 1.6), s_front
    for _ in range(50):
        mid = (lo + hi) * 0.5
        if (path_point(path, mid) - f).length > wb:
            lo = mid
        else:
            hi = mid
    r = path_point(path, (lo + hi) * 0.5)
    return f, r


def pl_parts(put, put_lr):
    put(build_pl_winch("eu"))
    put(build_pl_winch("us"))
    put(build_pl_drum())
    put(build_pl_hook())
    put(build_pl_cable())
    put(build_pl_rack("eu"))
    put(build_pl_rack("us"))
    for size in PL_CARS:
        put(build_od_car(size))
        put(build_od_car_wheel(size))
    for cfg in CONFIGS:
        if cfg["cfg"] not in PL_CARS:
            continue
        g = pl_geo(cfg)
        put(build_pl_rails(cfg))
        t, sc = pl_tilt_cyl(g), pl_slide_cyl(g)
        cylinder_family(put, "pt" + cfg["cfg"], t["n"], t["ell"], 0.050)
        cylinder_family(put, "ps" + cfg["cfg"], sc["n"], sc["ell"], 0.070)
        for style in ("eu", "us"):
            put(build_pl_bed(cfg, style))
            put(build_pl_base(cfg, style))


def pl_timeline():
    # casovy plan animacie (snimky): sklon, odsun, hak k autu, vytiahnutie auta, odsun spat, sklon spat
    return dict(tilt0=450, tilt1=500, slide0=500, slide1=590, hook0=590, hook1=620, pull0=620, pull1=740, back0=740, back1=800, down0=800, down1=850)


PL_RIGS = {}


def pl_rig(coll, truck, parts, body, root, prop, mats):
    cfg, name, style = truck["cfg"], truck["name"], truck["style"]
    g = pl_geo(truck)
    car = PL_CARS[cfg]
    set_prop(root, "Plosina_sklon", 0.0, 0.0, 1.0, "Sklopenie podramu: 0 = rovno, 1 = zadok dole o %.0f st. (spicka plosiny sa po odsune dotkne zeme)" % math.degrees(g["theta"]))
    set_prop(root, "Plosina_odsun", 0.0, 0.0, 1.0, "Odsun plosiny po podrame dozadu: 0 = zasunuta, 1 = odsunuta o %.2f m" % g["slide"])
    set_prop(root, "Hak_k_autu", 0.0, 0.0, 1.0, "Hak: 0 = v drziaku pri navijaku, 1 = na tazne oko auta (lano sa vyvijaha)")
    accent(new_object(coll, name + "_podstavec", parts["Odt_od_podstavec_%s_%s" % (style, cfg)], (0.0, 0.0, 0.0), body), truck, mats)
    pivot = empty(coll, name + "_plosina_klb", (g["xp"], 0.0, PL_ZP), body)
    pivot.empty_display_type = "ARROWS"
    pivot.empty_display_size = 0.4
    driver(pivot, "rotation_euler", 1, "%.6f * t" % -g["theta"], [prop("t", "Plosina_sklon")])
    rails = new_object(coll, name + "_podram", parts["Odt_od_podram_" + cfg], (0.0, 0.0, 0.0), pivot)
    bed = accent(new_object(coll, name + "_plosina", parts["Odt_od_plosina_%s_%s" % (style, cfg)], (0.0, 0.0, 0.0), pivot), truck, mats)
    driver(bed, "location", 0, "%.5f * s" % -g["slide"], [prop("s", "Plosina_odsun")])
    xf, zt = g["xf"], g["zt"]
    accent(rails, truck, mats)
    accent(new_object(coll, name + "_celna_stena", parts["Odt_od_celna_stena_" + style], (xf, 0.0, zt), bed), truck, mats)
    zw = (1.00 if style == "eu" else 1.40) + 0.10          # navijak je navrchu celnej steny (vrch hornej priecky + police)
    winch = accent(new_object(coll, name + "_navijak", parts["Odt_od_navijak_" + style], (xf - 0.31, 0.0, zt + zw), bed), truck, mats)
    drum = new_object(coll, name + "_navijak_buben", parts["Odt_od_navijak_buben"], (0.0, 0.0, 0.22), winch)
    fair = empty(coll, name + "_navijak_vodiaca", (-0.28, 0.0, 0.12), winch)
    holder = empty(coll, name + "_hak_drziak", (xf - 0.31 - 0.26, -0.20, zt + zw + 0.48), bed)
    hook = new_object(coll, name + "_hak", parts["Odt_od_hak"], (0.0, 0.0, 0.0), holder)
    hook.scale = (0.6, 0.6, 0.6)
    con = hook.constraints.new("COPY_LOCATION")
    con.name = "Na_aute"
    cable = new_object(coll, name + "_lano", parts["Odt_od_lano"], (0.0, 0.0, 0.0), fair)
    track(cable, hook, "TRACK_Z")
    driver(cable, "scale", 2, "d", [("d", "DIST", (fair, hook))])
    d0 = Vector((-0.26 + 0.28, -0.20, 0.48 - 0.12)).length
    driver(drum, "rotation_euler", 1, "-(d - %.4f) / 0.12" % d0, [("d", "DIST", (fair, hook))])
    t, sc = pl_tilt_cyl(g), pl_slide_cyl(g)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        telescope(coll, "%s_valec_naklapania_%s" % (name, side), parts, "pt" + cfg, t["n"], t["ell"], body,
                  (t["b"].x, s * 0.28, 1.14), pivot, (t["a_rel"].x, s * 0.28, t["a_rel"].z))
    telescope(coll, name + "_valec_odsunu", parts, "ps" + cfg, sc["n"], sc["ell"], rails, tuple(sc["base"]), bed, tuple(sc["aim"]))
    new_object(coll, name + "_naradie_skrinka", parts["Odt_naradie_skrinka"], (truck["tank_x"] - 1.62, 0.98, 0.62), body)
    new_object(coll, name + "_naradie_skrinka_P", parts["Odt_naradie_skrinka"], (truck["tank_x"] - 1.62, -0.98, 0.62), body, (0.0, 0.0, 180.0))
    for side in ("L", "P"):
        new_object(coll, "%s_bocna_ochrana_%s" % (name, side), parts["Odt_bocna_ochrana_%s_%s" % (cfg, side)], (0.0, 0.0, 0.0), body)
    if style == "us":
        new_object(coll, name + "_us_doplnky", parts["Odt_od_us_doplnky"], (0.0, 0.0, 0.0), body)
    # odtahovane auto: volne v scene (dieta korena), polohu a otacanie kolies nesu kluce po snimkach
    auto = new_object(coll, name + "_auto", parts["Odt_od_auto_" + cfg], (0.0, 0.0, 0.0), root)
    wheels = []
    for i, (dx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        wheels.append(new_object(coll, "%s_auto_koleso_%d" % (name, i + 1), parts["Odt_od_auto_koleso_" + cfg],
                                 (dx * car["wb"] * 0.5, sy * (car["w"] * 0.5 - 0.10), 0.0), auto, (0.0, 0.0, 0.0 if sy > 0 else 180.0)))
    eye = empty(coll, name + "_auto_oko", (car["wb"] * 0.5 + car["fo"] + 0.05, 0.0, -car["rw"] + 0.19), auto)
    con.target = eye
    driver(hook, 'constraints["Na_aute"].influence', -1, "k", [prop("k", "Hak_k_autu")])
    PL_RIGS[name] = dict(g=g, car=car, auto=auto, wheels=wheels)


def pl_animate_car(truck, root):
    # kluce auta po snimkach (v suradniciach ramu): na zemi -> vytahovanie po plosine -> na plosine pri odsune a sklopeni spat
    rig = PL_RIGS[truck["name"]]
    g, car, auto = rig["g"], rig["car"], rig["auto"]
    tl = pl_timeline()
    path, surf = pl_rail_path(g, car)
    wb, fo, rw = car["wb"], car["fo"], car["rw"]
    m_end = pl_bed_matrix(g, 1.0, 1.0)
    f_end = m_end @ Vector((g["xf"] - 1.10 - fo, 0.0, g["zt"] + rw))
    s_end = path_param(path, Vector((f_end.x, f_end.z)))
    s_start = path_param(path, Vector((surf[1].x - 1.3 - fo, rw)))

    def ease(u):
        return u * u * (3.0 - 2.0 * u)

    def pose(sf):
        f, r = car_pose(path, sf, wb)
        c = (f + r) * 0.5
        return c, -math.atan2(f.y - r.y, f.x - r.x)

    c0, y0 = pose(s_start)
    seq = [(1, c0.x, c0.y, y0, s_start), (tl["pull0"], c0.x, c0.y, y0, s_start)]
    for f in range(tl["pull0"] + 2, tl["pull1"], 2):
        sf = s_start + (s_end - s_start) * ease((f - tl["pull0"]) / float(tl["pull1"] - tl["pull0"]))
        c, ry = pose(sf)
        seq.append((f, c.x, c.y, ry, sf))
    c1, y1 = pose(s_end)
    seq.append((tl["pull1"], c1.x, c1.y, y1, s_end))
    local = m_end.inverted() @ (Matrix.Translation((c1.x, 0.0, c1.y)) @ Euler((0.0, y1, 0.0), "XYZ").to_matrix().to_4x4())
    for f in range(tl["pull1"] + 2, tl["down1"] + 1, 2):
        if f <= tl["back0"]:
            t, s = 1.0, 1.0
        elif f <= tl["back1"]:
            t, s = 1.0, 1.0 - ease((f - tl["back0"]) / float(tl["back1"] - tl["back0"]))
        else:
            t, s = 1.0 - ease((f - tl["down0"]) / float(tl["down1"] - tl["down0"])), 0.0
        m = pl_bed_matrix(g, t, s) @ local
        tr = m.to_translation()
        seq.append((f, tr.x, tr.z, math.atan2(m[0][2], m[0][0]), None))
    seq.append((900, seq[-1][1], seq[-1][2], seq[-1][3], None))
    travel, wheel_keys = 0.0, []
    for f, x, z, ry, sf in seq:
        if sf is not None:
            travel = sf - s_start
        wheel_keys.append((f, travel / rw))
    key(auto, "location", 0, [(f, x) for f, x, z, ry, sf in seq])
    key(auto, "location", 2, [(f, z) for f, x, z, ry, sf in seq])
    key(auto, "rotation_euler", 1, [(f, ry) for f, x, z, ry, sf in seq])
    for wheel in rig["wheels"]:
        key(wheel, "rotation_euler", 1, wheel_keys)


def animate_pl(truck, root, keys):
    tl = pl_timeline()
    keys("Plosina_sklon", [(1, 0.0), (tl["tilt0"], 0.0), (tl["tilt1"], 1.0), (tl["down0"], 1.0), (tl["down1"], 0.0)])
    keys("Plosina_odsun", [(1, 0.0), (tl["slide0"], 0.0), (tl["slide1"], 1.0), (tl["back0"], 1.0), (tl["back1"], 0.0)])
    keys("Hak_k_autu", [(1, 0.0), (tl["hook0"], 0.0), (tl["hook1"], 1.0)])
    pl_animate_car(truck, root)


BUILDERS["ploso_eu"] = pl_rig
BUILDERS["ploso_us"] = pl_rig
ANIMATORS["ploso_eu"] = animate_pl
ANIMATORS["ploso_us"] = animate_pl
PART_MAKERS.append(pl_parts)


def _pl_doc():
    lines = [
        "",
        "PLOSINOVA ODTAHOVKA (Plosinova_EU_xxx a Plosinova_US_xxx na podvozkoch 4x2 a 6x2; us = vysoka celna stena z chromovych rur, kominy za kabinou, bull bar, svetelna lista, cervena farba):",
        "  Sklopny podram: prazdny objekt <Auto>_plosina_klb (pivot v osi klbu vzadu na rame, os Y, otaca sa o -Plosina_sklon x uhol, zadok ide dole). Jeho deti:",
        "    podram (diel Odt_od_podram_<podvozok>: dva nosniky s valcekmi, priecniky, cap), plosina (Odt_od_plosina_<styl>_<podvozok>, pohyb v X o -Plosina_odsun x odsun),",
        "    valce odsunu (zaklad na podrame vpredu). Plosina ma na zadnom konci skosenie (%.2f m) a spicka sa po odsune dotkne zeme." % PL_WEDGE,
        "  Dieta plosiny: celna stena (pivot na prednej hrane na podlahe), navijak (maly, navrchu celnej steny: pivot na jeho polici v strede, 0.31 m za prednou hranou a 1.10 m (eu) / 1.50 m (us) nad podlahou), jeho buben (otaca sa podla vzdialenosti haku),",
        "    prazdny objekt navijak_vodiaca (vystup lana, zaklad lana) a hak_drziak (miesto haku v pokoji).",
        "  Lano (Odt_od_lano, jednotkova dlzka v +Z): zaklad na vodiacej kladke, mieri (track Z) na hak, mierka Z = vzdialenost vodiacej kladky a haku.",
        "  Hak (Odt_od_hak) je dieta hak_drziak; constraint Copy Location 'Na_aute' (cielom je prazdny objekt auto_oko = tazne oko auta) ma vplyv = vlastnost Hak_k_autu (0 = v drziaku, 1 = na aute).",
        "  Naklapacie valce (dva, v kanali medzi nosnikmi): zaklad na rame, ciel na podrame; valec odsunu: zaklad na podrame, ciel na plosine (teleskop: stupen k = (d - dlzka stupna) x k / (n - 1) po +Z).",
        "  Auto (Odt_od_auto_<podvozok>, dieta korena, pivot v strede medzi napravami vo vyske osi, predok +X) a jeho 4 kolesa: poloha, sklon a otacanie kolies su kluce po snimkach",
        "    (vytahovanie po plosine 620 az 740, potom jazda na plosine pri odsune a sklopeni spat). Auto nie je sucastou odtahovky, volne ho presun / zmaz.",
        "  Vlastnosti: Plosina_sklon (0 az 1), Plosina_odsun (0 az 1), Hak_k_autu (0 az 1). Animacia (snimky 450 az 900): sklopenie, odsun, hak k autu, vytiahnutie auta, odsun spat, sklopenie spat.",
    ]
    for cfg in CONFIGS:
        if cfg["cfg"] not in PL_CARS:
            continue
        g = pl_geo(cfg)
        t, sc = pl_tilt_cyl(g), pl_slide_cyl(g)
        c = PL_CARS[cfg["cfg"]]
        lines.append("  %s: klb v (%.2f, 0, %.2f), plosina %.2f m (x od %.2f do %.2f od klbu), odsun %.2f m, sklon %.1f st.; valec naklapania %d stupnov po %.2f m (%.2f az %.2f m), odsunu %d stupnov po %.2f m (%.2f az %.2f m); auto %.2f m, rozvor %.2f m" % (
            cfg["cfg"], g["xp"], PL_ZP, g["lb"], g["xr"], g["xf"], g["slide"], math.degrees(g["theta"]), t["n"], t["ell"], t["dmin"], t["dmax"],
            sc["n"], sc["ell"], sc["d0"], sc["dmax"], c["L"], c["wb"]))
    return lines


DOC_EXTRA += _pl_doc()
CATALOG_EXTRA.append(("PLOSINOVA ODTAHOVKA", ["Odt_od_plosina_%s_%s" % (st, c) for st in ("eu", "us") for c in PL_CARS] +
                      ["Odt_od_podram_%s" % c for c in PL_CARS] + ["Odt_od_podstavec_%s_%s" % (st, c) for st in ("eu", "us") for c in PL_CARS] +
                      ["Odt_od_celna_stena_eu", "Odt_od_celna_stena_us", "Odt_od_navijak_eu", "Odt_od_navijak_us", "Odt_od_navijak_buben", "Odt_od_hak", "Odt_od_lano"] +
                      ["Odt_od_auto_%s" % c for c in PL_CARS] + ["Odt_od_auto_koleso_%s" % c for c in PL_CARS] +
                      ["Odt_valec_%s%s_%d" % (p, c, k) for c in PL_CARS for p in ("pt", "ps") for k in range(6)]))
CATALOG_EXTRA.append(("DOPLNKY STYLU", ["Odt_od_kabina_eu", "Odt_od_kabina_us", "Odt_od_us_doplnky", "Odt_naradie_skrinka"]))

# ---------------------------------------------------------------------------
# Tazka vyprostovacia odtahovka na kamiony: paluba so skrinami po stranach, za kabinou otocny zeriav s teleskopickym ramenom a hakom
# (eu: zeriav 360 st. s vysuvnymi podperami na podstavci, jeden hak; us: silne rameno s dvoma hakmi), vzadu podjazdove rameno s kolebkou
# a dve zadne podpery. Dva styly: eu (zlte/oranzove, zalozky na valcoch zaluzie) a us (cervene/modre, chrom, vysoke skrine s rifl. plechom).
# ---------------------------------------------------------------------------

TZ_CX = -2.45                                  # os zeriavu (podstavca)
TZ_PED, TZ_PED_Z = 0.55, FRAME_TOP + 0.04      # vyska podstavca, jeho spodok
TZ_P = Vector((0.25, 0.0, 1.05))               # klb ramena voci kolone (pivot kolony je na vrchu podstavca)
TZ_DECK_X0, TZ_DECK_Z = -3.00, 1.42            # predna hrana zadnej paluby, vrch paluby
TZ_BOOM = {"6x2": dict(lb=3.6, li=2.7, ext=2.4), "8x2": dict(lb=4.2, li=3.2, ext=3.0)}
TZ_DROP = 3.2                                  # spustenie haku o (m)
TZ_UNDER_MIN, TZ_UNDER_MAX = -10.0, 22.0       # podjazdove rameno: klesnutie k zemi / zdvih (st.)
TZ_UL, TZ_UI = 1.15, 1.10                      # dlzka podjazdoveho ramena a jeho vysuvu
TZ_LEG_DROP = 0.65                             # zadne podpery: vysun (z kludovej polohy 0.65 m nad zemou po zem)


def tz_rear(cfg):
    return cfg["rear_end"] - 0.02


def tz_locker_len(cfg):
    return (TZ_DECK_X0 - 0.10) - (cfg["rear_end"] + 1.55)


def tz_doors(cfg):
    return int(tz_locker_len(cfg) / 0.90)


def tz_hoist(cfg):
    # zdvihove valce ramena (dva): zaklad B na kolone, ucho A na ramene; rozsah vzdialenosti pri zdvihu -5 az 75 st.
    b = TZ_BOOM[cfg["cfg"]]
    a_rel = Vector((0.45 * b["lb"], 0.28, -0.30))
    bb = Vector((-0.20, 0.28, 0.40))
    ds = []
    for i in range(41):
        e = math.radians(-5.0 + 80.0 * i / 40.0)
        a = Vector((TZ_P.x + a_rel.x * math.cos(e) - a_rel.z * math.sin(e), 0.28, TZ_P.z + a_rel.x * math.sin(e) + a_rel.z * math.cos(e)))
        ds.append((a - bb).length)
    n, ell = tele_stages(min(ds), max(ds))
    return dict(a_rel=a_rel, b=bb, n=n, ell=ell, dmin=min(ds), dmax=max(ds))


def tz_under_geo(cfg):
    h = Vector((cfg["rear_end"] + 0.60, 0.0, 0.66))
    a_rel = Vector((-0.80, 0.0, 0.16))
    bb = Vector((h.x - 0.35, 0.0, 1.24))
    ds = []
    for i in range(41):
        e = math.radians(TZ_UNDER_MIN + (TZ_UNDER_MAX - TZ_UNDER_MIN) * i / 40.0)
        a = Vector((h.x + a_rel.x * math.cos(e) + a_rel.z * math.sin(e), 0.0, h.z - a_rel.x * math.sin(e) + a_rel.z * math.cos(e)))
        ds.append((a - bb).length)
    n, ell = tele_stages(min(ds), max(ds))
    return dict(h=h, a_rel=a_rel, b=bb, n=n, ell=ell, dmin=min(ds), dmax=max(ds))


def build_tz_deck(cfg, style):
    # zadna paluba (od x = -3.0 po koniec ramu): hlinikova/pozinkovana doska, bocne listy, ziebra, opora pre rameno v kludovej polohe
    eu = style == "eu"
    bm = bmesh.new()
    xr = tz_rear(cfg)
    x0 = TZ_DECK_X0
    ln, xc = x0 - xr, (x0 + xr) * 0.5
    add_box(bm, (ln, 2.44, 0.05), (xc, 0.0, TZ_DECK_Z - 0.025), ALU if eu else GALV, bev=0.004)
    add_box(bm, (ln, 2.20, 0.10), (xc, 0.0, TZ_DECK_Z - 0.10), FRAME, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (ln, 0.10, 0.22), (xc, s * 1.22, TZ_DECK_Z - 0.11), ACCENT, bev=0.008)
    for k in range(int(ln / 0.8) + 1):
        add_box(bm, (0.08, 2.0, 0.08), (x0 - 0.15 - 0.8 * k, 0.0, TZ_DECK_Z - 0.20), FRAME, bev=0.005)
    for k in range(int((ln - 0.6) / 0.30)):
        add_box(bm, (0.03, 1.40, 0.010), (x0 - 0.30 - 0.30 * k, 0.0, TZ_DECK_Z + 0.005), STEEL if eu else ALU)
    if not eu:
        diamond(bm, xr + 0.5, x0 - 0.3, -0.55, 0.55, TZ_DECK_Z, STEEL, 0.19)
    for k in range(int(ln / 1.0)):
        for s in SIDES_LR:
            add_box(bm, (0.14, 0.07, 0.010), (x0 - 0.5 - 1.0 * k, s * 1.20, TZ_DECK_Z + 0.005), DARK, bev=0.003)
    # opora ramena v kludovej polohe (stlpik s V-lozom)
    b = TZ_BOOM[cfg["cfg"]]
    xp = TZ_CX + TZ_P.x - b["lb"] + 0.40
    zp = TZ_PED_Z + TZ_PED + TZ_P.z - 0.30
    add_box(bm, (0.16, 0.40, zp - TZ_DECK_Z - 0.08), (xp, 0.0, (zp + TZ_DECK_Z) * 0.5 - 0.04), FRAME, bev=0.008)
    for s in SIDES_LR:
        add_box(bm, (0.14, 0.05, 0.22), (xp, s * 0.19, zp - 0.04), STEEL, bev=0.005)
        add_box(bm, (0.20, 0.07, 0.04), (xp, s * 0.22, zp + 0.06), TIRE, bev=0.004)
    add_box(bm, (0.30, 0.60, 0.05), (xp, 0.0, TZ_DECK_Z + 0.025), FRAME, bev=0.006)
    return finish_mesh(bm, "SM_Odt_tz_paluba_%s_%s" % (style, cfg["cfg"]))


def build_tz_locker(cfg, style):
    # skrina (lava strana): vonkajsia stena v y = 1.25, otvory pre dvere (dvere su zvlast); put_lr ju zrkadli
    eu = style == "eu"
    bm = bmesh.new()
    ln = tz_locker_len(cfg)
    x1 = TZ_DECK_X0 - 0.10
    xc = x1 - ln * 0.5
    z0, z1 = TZ_DECK_Z, 2.34
    add_box(bm, (ln, 0.47, z1 - z0), (xc, 1.015, (z0 + z1) * 0.5), ACCENT if eu else GALV, bev=0.012)
    add_box(bm, (ln + 0.06, 0.55, 0.04), (xc, 1.00, z1 + 0.02), ALU, bev=0.006)
    for k in range(tz_doors(cfg)):
        x = x1 - 0.20 - 0.90 * (k + 0.5) + 0.20
        add_box(bm, (0.84, 0.03, 0.76), (x, 1.245, z1 - 0.50), DARK, bev=0.004)
        add_box(bm, (0.78, 0.02, 0.03), (x, 1.236, z1 - 0.50), STEEL)
        add_box(bm, (0.26, 0.02, 0.18), (x, 1.236, z1 - 0.72), TIRE if eu else STEEL, bev=0.004)
    if not eu:
        diamond(bm, xc - ln * 0.5 + 0.05, xc + ln * 0.5 - 0.05, 0.80, 1.22, z1 + 0.04, STEEL, 0.17)
        add_box(bm, (ln, 0.02, 0.05), (xc, 1.255, z0 + 0.10), CHROME, bev=0.003)
        add_box(bm, (ln, 0.02, 0.05), (xc, 1.255, z1 - 0.06), CHROME, bev=0.003)
    for k in range(tz_doors(cfg) + 1):
        add_box(bm, (0.04, 0.05, z1 - z0 - 0.06), (x1 - 0.90 * k, 1.25, (z0 + z1) * 0.5), STEEL if eu else CHROME, bev=0.004)
    for x in (x1 - 0.30, x1 - ln + 0.30):
        add_box(bm, (0.28, 0.12, 0.08), (x, 1.12, z1 + 0.04 + (0.0 if eu else 0.0)), LAMP_OR, bev=0.012)
    return bm


def build_tz_door(style):
    # dvere skrine (lava strana): pivot na hornom okraji v strede sirky (os X), dvere visia dole (-Z), vonkajsia strana +Y
    eu = style == "eu"
    bm = bmesh.new()
    w, h = 0.86, 0.76
    add_box(bm, (w, 0.03, h), (0.0, 0.015, -h * 0.5), ALU if eu else GALV, bev=0.005)
    if eu:
        for k in range(9):
            add_box(bm, (w - 0.02, 0.014, 0.035), (0.0, 0.036, -0.06 - 0.082 * k), STEEL, bev=0.003)
        add_box(bm, (w, 0.05, 0.05), (0.0, 0.03, -h + 0.02), DARK, bev=0.005)
        add_box(bm, (0.20, 0.03, 0.04), (0.0, 0.065, -h + 0.08), STEEL, bev=0.005)
    else:
        for i in range(5):
            for j in range(4):
                x = -0.34 + 0.17 * i
                z = -0.12 - 0.18 * j
                add_box(bm, (0.06, 0.008, 0.012), (x, 0.034, z), STEEL, rotation=(0.0, 45.0 if (i + j) % 2 else -45.0, 0.0))
        add_box(bm, (w, 0.02, 0.04), (0.0, 0.035, -h + 0.03), CHROME, bev=0.003)
        add_rod(bm, (-0.12, 0.06, -h + 0.16), (0.12, 0.06, -h + 0.16), 0.014, CHROME, segments=6)
        for s in SIDES_LR:
            add_box(bm, (0.04, 0.05, 0.06), (s * 0.12, 0.045, -h + 0.16), CHROME, bev=0.004)
    add_cylinder(bm, 0.018, w + 0.04, along_x((0.0, 0.0, 0.0)), CHROME, segments=6)
    return bm


def build_tz_pedestal(style):
    # podstavec zeriavu na rame (pivot = os zeriavu na vrchu ramu); eu: s vysuvnymi podperami (priecnik), us: tazky pevny podstavec
    bm = bmesh.new()
    top = TZ_PED
    add_box(bm, (0.95, 1.30, 0.34), (0.0, 0.0, 0.17), ACCENT, bev=0.02)
    add_box(bm, (0.78, 0.96, top - 0.40), (-0.02, 0.0, 0.34 + (top - 0.40) * 0.5), ACCENT, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.04, top - 0.40), (0.40, s * 0.32, 0.34 + (top - 0.40) * 0.5), STEEL, bev=0.004)
    add_box(bm, (0.80, 1.10, 0.06), (0.0, 0.0, top - 0.03), STEEL, bev=0.01)
    add_cylinder(bm, 0.32, 0.04, along_z((0.0, 0.0, top)), DARK, segments=14)
    for i in range(10):
        a = 2.0 * math.pi * i / 10
        add_cylinder(bm, 0.018, 0.03, along_z((0.30 * math.cos(a), 0.30 * math.sin(a), top + 0.03)), STEEL, segments=6)
    if style == "eu":
        add_box(bm, (0.80, 2.38, 0.24), (0.05, 0.0, 0.24), FRAME, bev=0.012)
        for s in SIDES_LR:
            add_box(bm, (0.84, 0.05, 0.30), (0.05, s * 1.215, 0.24), DARK, bev=0.006)
            add_rod(bm, (-0.12, s * 0.45, 0.42), (-0.12, s * 1.20, 0.42), 0.022, CHROME, segments=8)
    else:
        for s in SIDES_LR:
            add_box(bm, (0.95, 0.10, 0.40), (0.0, s * 0.62, 0.20), FRAME, bev=0.01)
            add_box(bm, (0.14, 0.14, 0.50), (0.40, s * 0.62, 0.30), CHROME, bev=0.012)
            add_box(bm, (1.0, 0.04, 0.10), (0.0, s * 0.66, 0.36), STEEL, bev=0.004)
        diamond(bm, -0.38, 0.38, -0.45, 0.45, 0.34, STEEL, 0.16)
    return finish_mesh(bm, "SM_Odt_tz_podstavec_" + style)


def build_tz_beam():
    bm = bmesh.new()
    add_box(bm, (0.30, 1.20, 0.20), (0.0, 0.65, 0.0), ACCENT, bev=0.008)
    add_box(bm, (0.44, 0.14, 0.34), (0.0, 1.20, 0.05), STEEL, bev=0.006)
    add_box(bm, (0.04, 0.10, 0.04), (0.12, 0.50, 0.14), DARK, bev=0.003)
    add_rod(bm, (-0.05, 0.10, 0.12), (-0.05, 1.10, 0.12), 0.012, DARK, segments=6)
    return bm


def build_tz_foot():
    bm = bmesh.new()
    add_cylinder(bm, 0.075, 0.68, along_z((0.0, 0.0, -0.28)), STEEL, segments=10)
    add_cylinder(bm, 0.095, 0.04, along_z((0.0, 0.0, 0.04)), DARK, segments=10)
    add_cylinder(bm, 0.095, 0.04, along_z((0.0, 0.0, -0.60)), DARK, segments=10)
    add_cylinder(bm, 0.06, 0.30, along_x((0.0, 0.0, 0.0)), STEEL, segments=10)
    grease(bm, (0.0, 0.0, 0.06), 1.0)
    return finish_mesh(bm, "SM_Odt_tz_noha")


def build_tz_piston():
    bm = bmesh.new()
    add_cylinder(bm, 0.05, 1.05, along_z((0.0, 0.0, -0.425)), CHROME, segments=10)
    add_cylinder(bm, 0.07, 0.03, along_z((0.0, 0.0, -0.965)), STEEL, segments=10)
    add_box(bm, (0.44, 0.44, 0.05), (0.0, 0.0, -1.00), DARK, bev=0.01)
    add_box(bm, (0.32, 0.32, 0.02), (0.0, 0.0, -1.035), TIRE, bev=0.004)
    return finish_mesh(bm, "SM_Odt_tz_noha_piest")


def build_tz_turret(style):
    # otocna kolona (pivot na vrchu podstavca, os Z): ucha pre klb ramena v TZ_P, ucha valcov, ventilovy blok, ovladac
    eu = style == "eu"
    bm = bmesh.new()
    add_cylinder(bm, 0.36, 0.10, along_z((0.0, 0.0, 0.05)), STEEL, segments=16, bev=0.008)
    for i in range(14):
        a = 2.0 * math.pi * i / 14
        add_cylinder(bm, 0.02, 0.03, along_z((0.33 * math.cos(a), 0.33 * math.sin(a), 0.115)), DARK, segments=6)
    add_cylinder(bm, 0.30, 0.14, along_z((0.0, 0.0, 0.17)), ACCENT, segments=14, bev=0.01)
    add_box(bm, (0.62, 0.84, 1.00), (0.04, 0.0, 0.74), ACCENT, bev=0.03)
    add_box(bm, (0.16, 0.34, 0.40), (-0.34, 0.0, 0.50), DARK, bev=0.012)
    for i, mat in enumerate((RED, YELLOW, GREEN, WHITE, RED, YELLOW)):
        add_box(bm, (0.04, 0.05, 0.06), (-0.44, -0.15 + 0.06 * i, 0.62), mat, bev=0.004)
    for s in SIDES_LR:
        ear = [(0.02, 1.42), (0.46, 1.42), (0.46, 0.84), (0.36, 0.56), (0.10, 0.56), (0.02, 0.84)]
        add_extruded(bm, ear, s * 0.27, s * 0.33, "XZ", STEEL, bev=0.006)
        add_box(bm, (0.14, 0.06, 0.24), (-0.20, s * 0.28, 0.40), STEEL, bev=0.005)
        add_cylinder(bm, 0.03, 0.16, along_y((-0.20, s * 0.28, 0.40)), CHROME, segments=8)
    pin(bm, (TZ_P.x, 0.0, TZ_P.z), 0.06, 0.74, 1.0)
    if eu:
        add_box(bm, (0.12, 0.30, 0.34), (0.12, -0.50, 0.46), DARK, bev=0.01)
        for k, mat in enumerate((RED, YELLOW, GREEN)):
            add_rod(bm, (0.12, -0.50 + 0.08 * (k - 1), 0.62), (0.12, -0.50 + 0.08 * (k - 1), 0.76), 0.012, DARK, segments=6)
            add_box(bm, (0.04, 0.04, 0.04), (0.12, -0.50 + 0.08 * (k - 1), 0.78), mat, bev=0.004)
    else:
        add_box(bm, (0.64, 0.86, 0.04), (0.04, 0.0, 1.26), CHROME, bev=0.004)
        add_box(bm, (0.64, 0.86, 0.04), (0.04, 0.0, 0.40), CHROME, bev=0.004)
        add_cylinder(bm, 0.12, 0.40, along_y((-0.05, 0.0, 0.30)), DARK, segments=10)
    return finish_mesh(bm, "SM_Odt_tz_kolona_" + style)


def build_tz_boom(cfg, style):
    # rameno (zakladny dielec): pivot v klbe, x po dlzke, tvar nosnika; ucha valcov zdvihu, hadice, vodiace dosky na konci
    b = TZ_BOOM[cfg["cfg"]]
    lb = b["lb"]
    bm = bmesh.new()
    segment(bm, 1.0, lb, (0.29, 0.30), (0.27, 0.27), 0.23, ACCENT)
    for s in SIDES_LR:
        lug = [(0.40 * lb, -0.28), (0.50 * lb, -0.28), (0.48 * lb, -0.52), (0.45 * lb, -0.64), (0.42 * lb, -0.64), (0.40 * lb, -0.52)]
        add_extruded(bm, lug, s * 0.17, s * 0.22, "XZ", STEEL, bev=0.005)
        add_cylinder(bm, 0.03, 0.14, along_y((0.45 * lb, s * 0.28, -0.30)), CHROME, segments=8)
    pin(bm, (0.0, 0.0, 0.0), 0.06, 0.62, 1.0)
    grease(bm, (0.30, 0.25, 0.20), 1.0)
    hose(bm, 1.0, 0.45, lb - 0.30, 0.22, ys=(-0.255, 0.255))
    add_box(bm, (0.14, 0.52, 0.62), (lb, 0.0, 0.0), STEEL, bev=0.012)
    for s in SIDES_LR:
        add_box(bm, (0.30, 0.03, 0.20), (lb - 0.05, s * 0.255, -0.12), DARK, bev=0.005)
    if style == "us":
        add_box(bm, (0.9, 0.48, 0.02), (lb * 0.6, 0.0, 0.31), CHROME, bev=0.003)
    return finish_mesh(bm, "SM_Odt_tz_rameno_%s_%s" % (style, cfg["cfg"]))


def build_tz_boom_ext(cfg, style):
    # vysuvny dielec: pivot na zaciatku (vnutri zakladneho dielca), x po dlzke; na konci hlava s kladkami a pracovnymi svetlami
    b = TZ_BOOM[cfg["cfg"]]
    li = b["li"]
    bm = bmesh.new()
    segment(bm, 1.0, li, (0.22, 0.23), (0.20, 0.20), 0.18, STEEL, stripes=True)
    add_box(bm, (0.30, 0.46, 0.44), (li, 0.0, 0.0), ACCENT, bev=0.012)
    for s in SIDES_LR:
        add_box(bm, (0.26, 0.04, 0.50), (li + 0.12, s * 0.20, -0.10), STEEL, bev=0.006)
    if style == "eu":
        add_cylinder(bm, 0.17, 0.30, along_y((li + 0.14, 0.0, -0.14)), DARK, segments=14, bev=0.008)
        add_cylinder(bm, 0.05, 0.38, along_y((li + 0.14, 0.0, -0.14)), CHROME, segments=8)
    else:
        for yy in (-0.11, 0.11):
            add_cylinder(bm, 0.17, 0.16, along_y((li + 0.14, yy, -0.14)), DARK, segments=14, bev=0.008)
        add_cylinder(bm, 0.05, 0.46, along_y((li + 0.14, 0.0, -0.14)), CHROME, segments=8)
    for s in SIDES_LR:
        add_box(bm, (0.12, 0.16, 0.08), (li - 0.10, s * 0.10, 0.27), LAMP_WHITE, bev=0.01)
        add_box(bm, (0.10, 0.06, 0.12), (li - 0.10, s * 0.10, 0.22), DARK, bev=0.006)
    add_box(bm, (0.12, 0.16, 0.06), (li + 0.12, 0.0, 0.24), LAMP_OR, bev=0.01)
    return finish_mesh(bm, "SM_Odt_tz_vysun_%s_%s" % (style, cfg["cfg"]))


def build_tz_hook():
    # hak (pivot hore): zavesny clanok, kratka retaz, blok s kladkou, hak (spolu asi 0.7 m)
    bm = bmesh.new()
    add_box(bm, (0.10, 0.06, 0.10), (0.0, 0.0, -0.05), STEEL, bev=0.008)
    for i in range(3):
        add_box(bm, (0.035, 0.07 if i % 2 else 0.025, 0.06), (0.0, 0.0, -0.13 - i * 0.05), DARK, bev=0.004)
    add_box(bm, (0.14, 0.12, 0.16), (0.0, 0.0, -0.36), ACCENT, bev=0.012)
    add_cylinder(bm, 0.03, 0.14, along_y((0.0, 0.0, -0.34)), CHROME, segments=8)
    add_rod(bm, (0.0, 0.0, -0.44), (0.0, 0.0, -0.54), 0.034, STEEL, segments=8)
    cx, cz, r = 0.13, -0.54, 0.13
    pts = [(cx + r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))) for a in (180, 215, 250, 285, 320, 350)]
    for a, b in zip(pts, pts[1:]):
        add_rod(bm, (a[0], 0.0, a[1]), (b[0], 0.0, b[1]), 0.034, STEEL, segments=8)
    add_box(bm, (0.012, 0.05, 0.05), (pts[-1][0] + 0.012, 0.0, pts[-1][1] + 0.05), DARK, bev=0.002)
    add_box(bm, (0.04, 0.03, 0.12), (cx - 0.07, 0.0, -0.44), RED, bev=0.003)
    return finish_mesh(bm, "SM_Odt_tz_hak")


def build_tz_cable():
    bm = bmesh.new()
    add_cylinder(bm, 0.016, 1.0, along_z((0.0, 0.0, -0.5)), DARK, segments=6)
    return finish_mesh(bm, "SM_Odt_tz_lano")


def build_tz_leg():
    # zadna podpera: puzdro (pivot hore, z = spodok paluby), v nom ide piest dole
    bm = bmesh.new()
    add_box(bm, (0.26, 0.26, 0.60), (0.0, 0.0, -0.30), ACCENT, bev=0.012)
    add_box(bm, (0.34, 0.34, 0.05), (0.0, 0.0, -0.02), STEEL, bev=0.006)
    add_box(bm, (0.10, 0.28, 0.10), (-0.16, 0.0, -0.10), DARK, bev=0.006)
    return finish_mesh(bm, "SM_Odt_tz_zadna_podpera")


def build_tz_leg_piston():
    # piest zadnej podpery (pivot = hore na puzdre): v kludovej polohe visi podlozka tesne pod puzdrom (0.69 pod pivotom)
    bm = bmesh.new()
    add_cylinder(bm, 0.055, 0.62, along_z((0.0, 0.0, -0.31)), CHROME, segments=10)
    add_cylinder(bm, 0.075, 0.03, along_z((0.0, 0.0, -0.63)), STEEL, segments=10)
    add_box(bm, (0.40, 0.40, 0.05), (0.0, 0.0, -0.665), DARK, bev=0.01)
    add_box(bm, (0.30, 0.30, 0.02), (0.0, 0.0, -0.70), TIRE, bev=0.004)
    return finish_mesh(bm, "SM_Odt_tz_zadna_podpera_piest")


def build_tz_under_arm(style):
    # podjazdove rameno (zakladny dielec): pivot v klbe, mieri do -X (dozadu)
    bm = bmesh.new()
    add_box(bm, (TZ_UL, 0.26, 0.28), (-TZ_UL * 0.5 + 0.05, 0.0, 0.0), ACCENT if style == "eu" else FRAME, bev=0.012)
    add_cylinder(bm, 0.07, 0.40, along_y((0.0, 0.0, 0.0)), CHROME, segments=10)
    for s in SIDES_LR:
        add_cylinder(bm, 0.09, 0.03, along_y((0.0, s * 0.21, 0.0)), DARK, segments=10)
    add_box(bm, (0.16, 0.30, 0.10), (-0.80, 0.0, 0.18), STEEL, bev=0.006)
    add_cylinder(bm, 0.03, 0.34, along_y((-0.80, 0.0, 0.18)), CHROME, segments=8)
    add_box(bm, (0.30, 0.34, 0.30), (-TZ_UL + 0.10, 0.0, 0.0), STEEL, bev=0.01)
    return finish_mesh(bm, "SM_Odt_tz_podjazd_rameno_" + style)


def build_tz_under_ext():
    bm = bmesh.new()
    add_box(bm, (TZ_UI, 0.20, 0.22), (-TZ_UI * 0.5, 0.0, 0.0), STEEL, bev=0.01)
    for k in range(4):
        add_box(bm, (0.06, 0.205, 0.225), (-0.30 - 0.22 * k, 0.0, 0.0), YELLOW if k % 2 == 0 else DARK, bev=0.002)
    return finish_mesh(bm, "SM_Odt_tz_podjazd_vysun")


def build_tz_cradle(style):
    # kolebka na osi vozidla (pivot = koniec vysuvu, os Y priecna): priecnik, dve ramena s gumovymi podlozkami, retazove oko
    eu = style == "eu"
    bm = bmesh.new()
    add_box(bm, (0.16, 2.30, 0.16), (-0.08, 0.0, 0.0), ACCENT if eu else CHROME, bev=0.012)
    add_box(bm, (0.30, 0.30, 0.30), (-0.05, 0.0, 0.0), STEEL, bev=0.01)
    for s in SIDES_LR:
        add_box(bm, (0.10, 0.12, 0.38), (-0.10, s * 0.92, 0.22), STEEL, bev=0.008)
        add_box(bm, (0.60, 0.26, 0.10), (-0.38, s * 0.92, 0.44), TIRE, bev=0.01, rotation=(0.0, 0.0, 0.0))
        add_box_between(bm, (-0.10, s * 0.92, 0.26), (-0.60, s * 0.92, 0.40), 0.12, 0.08, STEEL, bev=0.006)
        add_box(bm, (0.16, 0.14, 0.14), (-0.08, s * 1.12, 0.0), STEEL, bev=0.01)
        add_rod(bm, (-0.08, s * 1.12, 0.0), (-0.08, s * 1.12, -0.32), 0.016, DARK, segments=6)
        add_box(bm, (0.06, 0.06, 0.06), (-0.08, s * 1.12, -0.34), STEEL, bev=0.006)
        if not eu:
            add_box_between(bm, (-0.05, s * 0.50, 0.08), (-0.55, s * 0.50, 0.44), 0.10, 0.10, CHROME, bev=0.006)
    add_cylinder(bm, 0.05, 0.12, along_x((-0.16, 0.0, 0.0)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Odt_tz_kolebka_" + style)


def build_tz_under_holder(cfg):
    # drziak podjazdoveho ramena na rame (klb, ucho valca) - v suradniciach ramu
    ug = tz_under_geo(cfg)
    h, bb = ug["h"], ug["b"]
    bm = bmesh.new()
    for s in SIDES_LR:
        add_box(bm, (0.30, 0.05, 0.34), (h.x, s * 0.17, h.z + 0.04), STEEL, bev=0.006)
        add_box(bm, (0.30, 0.05, 0.08), (h.x + 0.05, s * 0.17, h.z + 0.24), FRAME, bev=0.004)
    add_box(bm, (0.50, 0.46, 0.06), (h.x, 0.0, h.z + 0.24), FRAME, bev=0.006)
    add_box(bm, (0.20, 0.36, 0.06), (bb.x, 0.0, bb.z - 0.03), STEEL, bev=0.006)
    add_cylinder(bm, 0.03, 0.30, along_y((bb.x, 0.0, bb.z - 0.10)), CHROME, segments=8)
    add_box(bm, (0.12, 0.60, 0.50), (cfg["rear_end"] + 0.55, 0.0, 1.05), FRAME, bev=0.006)
    return finish_mesh(bm, "SM_Odt_tz_podjazd_drziak_" + cfg["cfg"])


def build_tz_rear(cfg, style):
    # zadna priecka s koncovymi svetlami a SPZ (pri konci paluby); us: dalsi cerveno-bily pas a chromovane rohy
    eu = style == "eu"
    xr = tz_rear(cfg)
    bm = bmesh.new()
    add_box(bm, (0.16, 2.46, 0.20), (xr - 0.07, 0.0, 1.20), ACCENT if eu else CHROME, bev=0.012)
    for s in SIDES_LR:
        add_box(bm, (0.04, 0.34, 0.14), (xr - 0.16, s * 0.98, 1.20), DARK, bev=0.012)
        add_box(bm, (0.012, 0.10, 0.10), (xr - 0.18, s * 1.10, 1.20), LAMP_OR, bev=0.003)
        add_box(bm, (0.012, 0.16, 0.10), (xr - 0.18, s * 0.97, 1.20), LAMP_RED, bev=0.003)
        add_box(bm, (0.012, 0.07, 0.10), (xr - 0.18, s * 0.85, 1.20), LAMP_WHITE, bev=0.003)
    add_box(bm, (0.012, 0.52, 0.11), (xr - 0.16, 0.0, 1.20), WHITE, bev=0.003)
    if not eu:
        for s in SIDES_LR:
            add_rod(bm, (xr - 0.10, s * 1.12, 1.30), (xr - 0.10, s * 1.12, 2.35), 0.035, CHROME, segments=8)
            add_box(bm, (0.10, 0.34, 0.14), (xr - 0.10, s * 1.12, 2.42), DARK, bev=0.012)
            add_box(bm, (0.012, 0.28, 0.10), (xr - 0.16, s * 1.12, 2.42), LAMP_RED, bev=0.003)
            add_box(bm, (0.012, 0.28, 0.10), (xr - 0.04, s * 1.12, 2.42), LAMP_OR, bev=0.003)
            add_box(bm, (0.14, 0.10, 0.06), (xr - 0.10, s * 1.12, 1.40), CHROME, bev=0.006)
    for k in range(9):
        add_box(bm, (0.012, 0.14, 0.04), (xr - 0.155, -0.56 + 0.14 * k, 1.31), RED if k % 2 == 0 else WHITE, bev=0.002)
    return finish_mesh(bm, "SM_Odt_tz_zadok_%s_%s" % (style, cfg["cfg"]))


def build_tz_rear_winch(cfg, style):
    # zadny navijak (maly, nepohyblivy): ram, buben s lanom, hydromotor, vodiaca kladka; v suradniciach ramu
    xr = tz_rear(cfg)
    bm = bmesh.new()
    xw = xr + 0.80
    zc = TZ_DECK_Z + 0.20
    add_box(bm, (0.44, 0.70, 0.04), (xw, 0.0, TZ_DECK_Z + 0.02), FRAME, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.30, 0.04, 0.30), (xw, s * 0.31, TZ_DECK_Z + 0.19), ACCENT, bev=0.008)
    add_cylinder(bm, 0.09, 0.56, along_y((xw, 0.0, zc)), STEEL, segments=12, bev=0.004)
    add_cylinder(bm, 0.11, 0.44, along_y((xw, 0.0, zc)), DARK, segments=12)
    for s in SIDES_LR:
        add_cylinder(bm, 0.15, 0.03, along_y((xw, s * 0.24, zc)), STEEL, segments=12, bev=0.004)
    add_box(bm, (0.18, 0.14, 0.14), (xw, 0.44, TZ_DECK_Z + 0.14), DARK, bev=0.012)
    add_cylinder(bm, 0.04, 0.30, along_y((xw - 0.30, 0.0, TZ_DECK_Z + 0.07)), STEEL, segments=8, bev=0.004)
    add_rod(bm, (xw - 0.28, 0.0, TZ_DECK_Z + 0.11), (xr - 0.25, 0.0, TZ_DECK_Z + 0.09), 0.012, DARK, segments=6)
    return finish_mesh(bm, "SM_Odt_tz_navijak_zadny_" + cfg["cfg"])


def tz_parts(put, put_lr):
    put(build_tz_hook())
    put(build_tz_cable())
    put(build_tz_leg())
    put(build_tz_leg_piston())
    put(build_tz_under_ext())
    put_lr(build_tz_beam(), "SM_Odt_tz_podpera")
    put(build_tz_foot())
    put(build_tz_piston())
    for style in ("eu", "us"):
        put(build_tz_pedestal(style))
        put(build_tz_turret(style))
        put_lr(build_tz_door(style), "SM_Odt_tz_dvere_" + style)
        put(build_tz_under_arm(style))
        put(build_tz_cradle(style))
        for cfg in CONFIGS:
            if cfg["cfg"] not in TZ_BOOM:
                continue
            put(build_tz_deck(cfg, style))
            put_lr(build_tz_locker(cfg, style), "SM_Odt_tz_skrina_%s_%s" % (style, cfg["cfg"]))
            put(build_tz_boom(cfg, style))
            put(build_tz_boom_ext(cfg, style))
            put(build_tz_rear(cfg, style))
    for cfg in CONFIGS:
        if cfg["cfg"] not in TZ_BOOM:
            continue
        put(build_tz_under_holder(cfg))
        put(build_tz_rear_winch(cfg, ""))
        h, u = tz_hoist(cfg), tz_under_geo(cfg)
        cylinder_family(put, "tzh" + cfg["cfg"], h["n"], h["ell"], 0.075)
        cylinder_family(put, "tzu" + cfg["cfg"], u["n"], u["ell"], 0.060)


def tz_rig(coll, truck, parts, body, root, prop, mats):
    cfg, name, style = truck["cfg"], truck["name"], truck["style"]
    eu = style == "eu"
    b = TZ_BOOM[cfg]
    xr = tz_rear(truck)
    pr, pe, pl, ps = ("Zeriav_otocenie", "Zeriav_zdvih", "Zeriav_vysun", "Hak_spustenie") if eu else ("Strela_otocenie", "Strela_zdvih", "Strela_vysun", "Hak1_spustenie")
    set_prop(root, "Podpery", 0.0, 0.0, 1.0, ("0 = zasunute; 0 az 0.35 nosniky podstavca sa vysunu do strany, 0.35 az 0.6 nohy sa otocia o 180 st. dolu, " if eu else "")
             + "zadne podpery sa spustaju na zem (do 0.9), 0.9 az 1 pritlacenie (podvozok sa nadvihne o 8 cm)")
    set_prop(root, pr, 180.0, 0.0, 360.0, "Otocenie ramena okolo zvisle osi v stupnoch (0 = dopredu, 90 = vlavo, 180 = dozadu = ulozene, 270 = vpravo)")
    set_prop(root, pe, 3.0, -5.0, 75.0, "Zdvih ramena v stupnoch (3 = ulozene na opore)")
    set_prop(root, pl, 0.0, 0.0, 1.0, "Vysun ramena (0 az %.1f m)" % b["ext"])
    set_prop(root, ps, 0.0, 0.0, 1.0, "Spustenie %s (0 = hore, 1 = spusteny o %.1f m)" % ("haku" if eu else "prveho haku", TZ_DROP))
    if not eu:
        set_prop(root, "Hak2_spustenie", 0.0, 0.0, 1.0, "Spustenie druheho haku (0 = hore, 1 = spusteny o %.1f m)" % (TZ_DROP - 0.4))
    set_prop(root, "Podjazd_zdvih", 0.0, TZ_UNDER_MIN, TZ_UNDER_MAX, "Podjazdove rameno okolo klbu vzadu v stupnoch (kladne = zdvih, zaporne = k zemi)")
    set_prop(root, "Podjazd_vysun", 0.0, 0.0, 1.0, "Vysun podjazdoveho ramena (0 az %.2f m)" % (TZ_UI - 0.15))
    set_prop(root, "Skrine", 0.0, 0.0, 1.0, "Dvere skrin: 0 = zatvorene, 1 = otvorene (100 st.)")
    new_object(coll, name + "_paluba", parts["Odt_tz_paluba_%s_%s" % (style, cfg)], (0.0, 0.0, 0.0), body)
    accent(bpy.data.objects[name + "_paluba"], truck, mats)
    new_object(coll, name + "_zadok", parts["Odt_tz_zadok_%s_%s" % (style, cfg)], (0.0, 0.0, 0.0), body)
    accent(bpy.data.objects[name + "_zadok"], truck, mats)
    new_object(coll, name + "_navijak_zadny", parts["Odt_tz_navijak_zadny_" + cfg], (0.0, 0.0, 0.0), body)
    accent(bpy.data.objects[name + "_navijak_zadny"], truck, mats)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        accent(new_object(coll, "%s_skrina_%s" % (name, side), parts["Odt_tz_skrina_%s_%s_%s" % (style, cfg, side)], (0.0, 0.0, 0.0), body), truck, mats)
        x1 = TZ_DECK_X0 - 0.10
        for k in range(tz_doors(truck)):
            door = new_object(coll, "%s_skrina_dvere_%s_%d" % (name, side, k + 1), parts["Odt_tz_dvere_%s_%s" % (style, side)],
                              (x1 - 0.90 * (k + 0.5), s * 1.26, 2.22), body)
            driver(door, "rotation_euler", 0, "%.0f * d * 1.75" % s, [prop("d", "Skrine")])
        new_object(coll, "%s_bocna_ochrana_%s" % (name, side), parts["Odt_bocna_ochrana_%s_%s" % (cfg, side)], (0.0, 0.0, 0.0), body)
    ped = accent(new_object(coll, name + "_podstavec", parts["Odt_tz_podstavec_" + style], (TZ_CX, 0.0, TZ_PED_Z), body), truck, mats)
    if eu:
        for s, side in ((1.0, "L"), (-1.0, "P")):
            beam = accent(new_object(coll, "%s_podpera_%s" % (name, side), parts["Odt_tz_podpera_" + side], (0.05 + s * 0.17, 0.0, 0.24), ped), truck, mats)
            driver(beam, "location", 1, "%.3f * (-0.22 + 1.17 * min(1, p / 0.35))" % s, [prop("p", "Podpery")])
            hinge = empty(coll, "%s_noha_klb_%s" % (name, side), (0.0, s * 1.20, 0.0), beam)
            driver(hinge, "rotation_euler", 0, "%.5f * (1 - min(1, max(0, (p - 0.35) / 0.25)))" % (s * math.pi), [prop("p", "Podpery")])
            foot = new_object(coll, "%s_noha_%s" % (name, side), parts["Odt_tz_noha"], (0.0, 0.0, 0.0), hinge)
            piston = new_object(coll, "%s_noha_piest_%s" % (name, side), parts["Odt_tz_noha_piest"], (0.0, 0.0, 0.0), foot)
            driver(piston, "location", 2, "-0.31 * min(1, max(0, (p - 0.6) / 0.3)) - 0.08 * max(0, (p - 0.9) / 0.1)", [prop("p", "Podpery")])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        leg = accent(new_object(coll, "%s_zadna_podpera_%s" % (name, side), parts["Odt_tz_zadna_podpera"], (cfg_rear(truck) + 0.55, s * 1.00, TZ_DECK_Z - 0.08), body), truck, mats)
        piston = new_object(coll, "%s_zadna_podpera_piest_%s" % (name, side), parts["Odt_tz_zadna_podpera_piest"], (0.0, 0.0, 0.0), leg)
        lo = 0.40 if eu else 0.05
        driver(piston, "location", 2, "-%.3f * min(1, max(0, (p - %.2f) / %.2f)) - 0.08 * max(0, (p - 0.9) / 0.1)" % (TZ_LEG_DROP, lo, 0.9 - lo),
               [prop("p", "Podpery")])
    extend_driver(body, "location", 2, "0.08 * max(0, (pp - 0.9) / 0.1)", [("pp", "PROP", (root, '["Podpery"]'))])
    # otocna kolona -> rameno -> vysuvny dielec -> zaves haku
    turret = accent(new_object(coll, name + "_kolona", parts["Odt_tz_kolona_" + style], (0.0, 0.0, TZ_PED), ped), truck, mats)
    driver(turret, "rotation_euler", 2, "o * %.6f" % D2R, [prop("o", pr)])
    boom = accent(new_object(coll, name + "_rameno", parts["Odt_tz_rameno_%s_%s" % (style, cfg)], tuple(TZ_P), turret), truck, mats)
    driver(boom, "rotation_euler", 1, "-v * %.6f" % D2R, [prop("v", pe)])
    ext = accent(new_object(coll, name + "_vysun", parts["Odt_tz_vysun_%s_%s" % (style, cfg)], (b["lb"] - b["li"] + 0.35, 0.0, 0.0), boom), truck, mats)
    driver(ext, "location", 0, "%.4f + t * %.4f" % (b["lb"] - b["li"] + 0.35, b["ext"]), [prop("t", pl)])
    hang = empty(coll, name + "_hak_zaves", (b["li"] + 0.14, 0.0, -0.34 if eu else -0.36), ext)
    driver(hang, "rotation_euler", 1, "v * %.6f" % D2R, [prop("v", pe)])
    hooks = [("", "Hak_spustenie" if eu else "Hak1_spustenie", 0.0, TZ_DROP, 1.30 if eu else 1.40)]
    if not eu:
        hooks.append(("2", "Hak2_spustenie", 0.28, TZ_DROP - 0.4, 1.10))
    for suffix, pname, dy, drop, sc in hooks:
        hang2 = empty(coll, "%s_hak_zaves%s" % (name, suffix or "1"), (0.0, dy if not eu else 0.0, 0.0), hang)
        hook = new_object(coll, "%s_hak%s" % (name, suffix or "1"), parts["Odt_tz_hak"], (0.0, 0.0, 0.0), hang2)
        hook.scale = (sc, sc, sc)
        driver(hook, "location", 2, "-h * %.3f" % drop, [prop("h", pname)])
        cable = new_object(coll, "%s_lano%s" % (name, suffix or "1"), parts["Odt_tz_lano"], (0.0, 0.0, 0.0), hang2)
        driver(cable, "scale", 2, "0.04 + h * %.3f" % drop, [prop("h", pname)])
    h = tz_hoist(truck)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        telescope(coll, "%s_valec_zdvih_%s" % (name, side), parts, "tzh" + cfg, h["n"], h["ell"], turret,
                  (h["b"].x, s * 0.28, h["b"].z), boom, (h["a_rel"].x, s * 0.28, h["a_rel"].z))
    # podjazdove rameno
    ug = tz_under_geo(truck)
    new_object(coll, name + "_podjazd_drziak", parts["Odt_tz_podjazd_drziak_" + cfg], (0.0, 0.0, 0.0), body)
    arm = accent(new_object(coll, name + "_podjazd_rameno", parts["Odt_tz_podjazd_rameno_" + style], tuple(ug["h"]), body), truck, mats)
    driver(arm, "rotation_euler", 1, "z * %.6f" % D2R, [prop("z", "Podjazd_zdvih")])
    uext = new_object(coll, name + "_podjazd_vysun", parts["Odt_tz_podjazd_vysun"], (-0.10, 0.0, 0.0), arm)
    driver(uext, "location", 0, "-0.10 - p * %.3f" % (TZ_UI - 0.15), [prop("p", "Podjazd_vysun")])
    cradle = accent(new_object(coll, name + "_podjazd_kolebka", parts["Odt_tz_kolebka_" + style], (-TZ_UI, 0.0, 0.0), uext), truck, mats)
    telescope(coll, name + "_valec_podjazd", parts, "tzu" + cfg, ug["n"], ug["ell"], body, tuple(ug["b"]), arm, tuple(ug["a_rel"]))
    if not eu:
        new_object(coll, name + "_us_doplnky", parts["Odt_od_us_doplnky"], (0.0, 0.0, 0.0), body)


def cfg_rear(truck):
    return truck["rear_end"]


def animate_tz(truck, root, keys):
    eu = truck["style"] == "eu"
    keys("Podpery", [(1, 0.0), (460, 0.0), (490, 0.35), (515, 0.6), (545, 0.9), (560, 1.0), (850, 1.0), (860, 0.9), (875, 0.6), (885, 0.35), (900, 0.0)])
    keys("Skrine", [(1, 0.0), (470, 0.0), (500, 1.0), (840, 1.0), (870, 0.0)])
    pr, pe, pl, ps = ("Zeriav_otocenie", "Zeriav_zdvih", "Zeriav_vysun", "Hak_spustenie") if eu else ("Strela_otocenie", "Strela_zdvih", "Strela_vysun", "Hak1_spustenie")
    keys(pr, [(1, 180.0), (570, 180.0), (620, 120.0), (700, 120.0), (760, 240.0), (820, 240.0), (860, 180.0)])
    keys(pe, [(1, 3.0), (570, 3.0), (620, 40.0), (700, 52.0), (760, 30.0), (820, 45.0), (860, 3.0)])
    keys(pl, [(1, 0.0), (630, 0.0), (680, 0.8), (740, 0.4), (790, 0.9), (830, 0.0)])
    keys(ps, [(1, 0.0), (690, 0.0), (730, 0.9), (760, 0.2), (800, 0.7), (830, 0.0)])
    if not eu:
        keys("Hak2_spustenie", [(1, 0.0), (700, 0.0), (740, 0.8), (770, 0.1), (810, 0.6), (835, 0.0)])
    keys("Podjazd_zdvih", [(1, 0.0), (560, 0.0), (600, -10.0), (650, -10.0), (700, 16.0), (760, 16.0), (800, 0.0)])
    keys("Podjazd_vysun", [(1, 0.0), (570, 0.0), (620, 1.0), (740, 1.0), (790, 0.0)])


BUILDERS["tazka_eu"] = tz_rig
BUILDERS["tazka_us"] = tz_rig
ANIMATORS["tazka_eu"] = animate_tz
ANIMATORS["tazka_us"] = animate_tz
PART_MAKERS.append(tz_parts)


def _tz_doc():
    lines = [
        "",
        "TAZKA ODTAHOVKA (Tazka_EU_xxx a Tazka_US_xxx na podvozkoch 6x2 a 8x2): zadna paluba (od x = %.2f po koniec ramu) so skrinami po stranach (x od %.2f dozadu), za kabinou otocny zeriav," % (TZ_DECK_X0, TZ_DECK_X0 - 0.10),
        "  vzadu podjazdove rameno s kolebkou, dve zadne podpery, zadny navijak (nepohyblivy). eu: zeriav ma na podstavci dve vysuvne podpery, skrine maju zaluziove dvere, jeden hak;",
        "  us: tazky pevny podstavec, skrine z pozinku s riflovanym plechom a chromom, dva haky (dve kladky), svetelne stlpiky vzadu, kominy a bull bar na kabine, svetelna lista na streche.",
        "  Kinematika (kazdy diel je dieta predosleho): podstavec (dieta ramu, os x = %.2f, spodok z = %.2f) -> kolona (okolo Z o Zeriav_otocenie, us: Strela_otocenie)" % (TZ_CX, TZ_PED_Z),
        "  -> rameno (okolo Y o -zdvih, pivot v %s od kolony; ulozene 3 st. smerom dozadu na opore) -> vysuvny dielec (posun v X o vysun x dlzka vysunu)" % tuple([tuple(round(v, 2) for v in TZ_P)]),
        "  -> zaves haku (otaca sa o +zdvih, aby hak visel zvisle) -> hak (posun v -Z o spustenie x %.1f m) a lano (mierka Z = 0.04 + spustenie x %.1f)." % (TZ_DROP, TZ_DROP),
        "  Zdvihove valce ramena (dva, teleskop): zaklad na kolone, ciel na ramene. Podpery: eu = nosnik (pohyb v Y), klb nohy (otocenie okolo X o 180 st.), noha a piest (ako pri hydraulickej ruke),",
        "    plus dve zadne podpery (puzdro pri konci paluby, piest ide o %.2f m dole); Podpery 0 az 1 (0.9 az 1 = pritlacenie, podvozok sa nadvihne o 8 cm)." % TZ_LEG_DROP,
        "  Podjazdove rameno: klb vzadu pod ramom (otocenie okolo Y o Podjazd_zdvih st., kladne = zdvih konca, -10 az 22), vysuvny dielec (posun v -X o Podjazd_vysun x %.2f m), kolebka (dieta vysuvu)," % (TZ_UI - 0.15),
        "    valec zdvihu (teleskop): zaklad na rame pod palubou, ciel na ramene. Dvere skrin: otacaju sa okolo hornej hrany (os X) o 100 st. von (vlastnost Skrine).",
        "  Vlastnosti: Podpery, %s (st.), %s (st.), %s (0 az 1), %s (0 az 1), Podjazd_zdvih (st.), Podjazd_vysun, Skrine; us ma aj Hak2_spustenie." % (
            "Zeriav_otocenie / Strela_otocenie", "Zeriav_zdvih / Strela_zdvih", "Zeriav_vysun / Strela_vysun", "Hak_spustenie / Hak1_spustenie"),
        "  Animacia (snimky 450 az 900): podpery, skrine, rameno sa zdvihne, otaca a vysuva, haky sa spustaju, podjazdove rameno klesne, vysunie sa a zdvihne, potom vsetko spat.",
    ]
    for cfg in CONFIGS:
        if cfg["cfg"] not in TZ_BOOM:
            continue
        b, h, u = TZ_BOOM[cfg["cfg"]], tz_hoist(cfg), tz_under_geo(cfg)
        lines.append("  %s: rameno %.1f m + vysun %.1f m (dielec %.1f m), %d skrin dveri na strane po 0.90 m, valec zdvihu %d stupnov po %.2f m (%.2f az %.2f m), podjazd klb v (%.2f, 0, %.2f), valec podjazdu %d stupnov po %.2f m (%.2f az %.2f m), zadok paluby x = %.2f" % (
            cfg["cfg"], b["lb"], b["ext"], b["li"], tz_doors(cfg), h["n"], h["ell"], h["dmin"], h["dmax"], u["h"].x, u["h"].z, u["n"], u["ell"], u["dmin"], u["dmax"], tz_rear(cfg)))
    return lines


DOC_EXTRA += _tz_doc()
CATALOG_EXTRA.append(("TAZKA ODTAHOVKA - ZAKLAD", ["Odt_tz_podstavec_eu", "Odt_tz_podstavec_us", "Odt_tz_kolona_eu", "Odt_tz_kolona_us", "Odt_tz_podpera_L", "Odt_tz_podpera_P",
                                                    "Odt_tz_noha", "Odt_tz_noha_piest", "Odt_tz_zadna_podpera", "Odt_tz_zadna_podpera_piest", "Odt_tz_hak", "Odt_tz_lano",
                                                    "Odt_tz_dvere_eu_L", "Odt_tz_dvere_eu_P", "Odt_tz_dvere_us_L", "Odt_tz_dvere_us_P", "Odt_tz_podjazd_vysun",
                                                    "Odt_tz_podjazd_rameno_eu", "Odt_tz_podjazd_rameno_us", "Odt_tz_kolebka_eu", "Odt_tz_kolebka_us"]))
CATALOG_EXTRA.append(("TAZKA ODTAHOVKA - PODLA PODVOZKU", ["Odt_tz_%s_%s_%s" % (p, st, c) for c in TZ_BOOM for st in ("eu", "us") for p in ("paluba", "rameno", "vysun", "zadok")]
                      + ["Odt_tz_skrina_%s_%s_%s" % (st, c, side) for c in TZ_BOOM for st in ("eu", "us") for side in ("L", "P")]
                      + ["Odt_tz_navijak_zadny_%s" % c for c in TZ_BOOM] + ["Odt_tz_podjazd_drziak_%s" % c for c in TZ_BOOM]
                      + ["Odt_valec_%s%s_%d" % (p, c, k) for c in TZ_BOOM for p in ("tzh", "tzu") for k in range(6)]))


def DOC_LINES(engines):
    def vec(v):
        return "(%.3f, %.3f, %.3f)" % tuple(v)

    _, seat_local, bag_bottom, _ = arm_geometry()
    lines = [
        "MOTORY: nase R4 / R6 / V8 s prevodovkami (diely su v skripte Motory). Koniec vystupneho hriadela kazdej",
        "  prevodovky je na rame v %s, takze kazdy motor sedi na ten isty kardan. Vlastnost Motor = 1 / 2 / 3." % vec(GEARBOX_OUT),
    ]
    for engine_key in ENGINE_KEYS:
        lines.append("  Motor %s: pivot motora na rame v %s" % (engine_key, vec(GEARBOX_OUT - engines[engine_key]["tip"])))
    lines += [
        "",
        "AKO JE TO POSKLADANE (kolekcie Plosinova_EU_4x2 ... Tazka_US_8x2, suradnice od pociatku auta = zem pod prvou prednou napravou):",
        "  <Auto>_xxx (prazdny objekt) - posuvaj nim cele auto, vlastnosti = ovladanie (popis na zaciatku skriptu).",
        "  Napravy: pivot v osi kolies (z = %.3f). Predne kolesa su na capoch riadenia (y = +-%.2f), zadne na koncoch naprav." % (
            WHEEL_R, KINGPIN_Y),
        "  <Auto>_ram (odpruzena cast): z = %.1f x pohyb prvej napravy, sklon podla hnacej napravy + vyska vankusov. Nadstavba je dieta ramu." % BODY_FOLLOW,
        "  Predne pera, zadne ramena, vankuse, tlmice, kardan, kabina (vyklapanie, perovanie), volant a budiky - ako pri tahacoch.",
        "  Kabina: pivot = predny cap vyklapania %s (na rame). Vyklopenie = otocenie okolo Y o %.0f st." % (
            vec(CAB_HINGE), math.degrees(CAB_TILT)),
        "  Blatniky: pivot v osi kolesa; zadne svetla su priamo na poslednom zadnom blatniku. Vyfuk je pod autom vpravo.",
        "  Prave diely _P su zrkadlove, kolesa vpravo otoc o 180 st. okolo Z.",
        "  Pevny ram (vrch ramu z = %.2f): nadstavba odtahovky je na nom ulozena, siroka najviac %.2f m." % (FRAME_TOP, 2 * BODY_HALF),
        "  Zadny naraznik (ochrana proti podbehnutiu) na konci ramu, bocna ochrana medzi napravami, skrinka na naradie vlavo (plosinove odtahovky aj vpravo).",
    ]
    lines += DOC_EXTRA
    lines += ["V Unreali: kazdy par 'mieri na' urob cez Find Look at Rotation (alebo Look At v Control Rig / Animation Blueprinte)."]
    for truck in CONFIGS:
        lines.append("Podvozok %s: napravy x = %s, koniec ramu x = %.2f" % (
            truck["cfg"], ", ".join("%.2f" % x for _, x in truck["axles"]), truck["rear_end"]))
    return lines


CATALOG = [
    ("KABINA", ["Odt_kabina", "Odt_interier", "Odt_volant", "Odt_rucicka_velka", "Odt_rucicka_mala", "Odt_nasavanie",
                "Odt_perovanie_kabiny_mech", "Odt_perovanie_kabiny_piest"]),
    ("RAMY A PREDOK", ["Odt_4x2_ram", "Odt_6x2_ram", "Odt_8x2_ram", "Odt_naraznik", "Odt_chladic"]),
    ("PRISLUSENSTVO", ["Odt_nadrz_nafta", "Odt_nadrz_adblue", "Odt_baterie", "Odt_vzduchojemy", "Odt_vyfuk"]),
    ("BLATNIKY", ["Odt_blatnik_zadny_L", "Odt_blatnik_zadny_P", "Odt_blatnik_zadny_svetla_L", "Odt_blatnik_zadny_svetla_P", "Odt_blatnik_vleceny_L",
                  "Odt_blatnik_vleceny_P", "Odt_blatnik_predny_L", "Odt_blatnik_predny_P"]),
    ("NAPRAVY A PEROVANIE", ["Odt_naprava_predna", "Odt_naprava_hnacia", "Odt_naprava_vlecena", "Odt_koleso_predne",
                             "Odt_koleso_zadne", "Odt_pero_predna_cast", "Odt_pero_zadna_cast", "Odt_tlmic_valec",
                             "Odt_tlmic_piestnica", "Odt_rameno", "Odt_vankus"]),
    ("KARDANY", ["Odt_4x2_kardan_predny", "Odt_6x2_kardan_predny", "Odt_8x2_kardan_predny", "Odt_kardan_zadny"]),
    ("SPOLOCNE NA NADSTAVBY", ["Odt_zadny_naraznik", "Odt_naradie_skrinka", "Odt_4x2_bocna_ochrana_L", "Odt_6x2_bocna_ochrana_L",
                               "Odt_8x2_bocna_ochrana_L"]),
]


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)
    mats = [get_material(*m) for m in MATERIALS]

    parts = build_parts()
    for mesh in parts.values():
        mesh["odtahovky"] = 1
        for mat in mats:
            mesh.materials.append(mat)
    engines = build_engines()

    roots = []
    for truck in TRUCKS:
        if truck["variant"] not in BUILDERS:
            continue
        roots.append(build_truck(child_collection(coll, truck["name"]), truck, parts, mats, engines, truck["motor"]))
    for extra in SCENE_EXTRAS:
        extra(coll, parts, mats)
    scene.frame_start, scene.frame_end = 1, 900
    scene.frame_set(1)

    # --- katalog dielov ---
    kit = child_collection(coll, "Odtahovky_diely")
    lines = ["Odtahovky - diely (rozmery X x Y x Z v metroch). Predok = +X, lava = +Y.", ""]
    y_cursor = 3.5
    for title, keys in CATALOG + CATALOG_EXTRA:
        keys = [k for k in keys if k in parts]
        depth = max(bounds(parts[k])[1][1] - bounds(parts[k])[1][0] for k in keys)
        row_y = y_cursor + depth * 0.5
        add_label(kit, title, (-2.5, row_y, 0.001), mats[DARK])
        x = -1.0
        lines.append("== %s ==" % title)
        for k in keys:
            mesh = parts[k]
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            slot = max(x1 - x0, 1.2)
            new_object(kit, "Diel_" + k[4:], mesh, (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0))
            add_label(kit, "%s\n%.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0), (x + slot * 0.5, row_y - depth * 0.5 - 0.2, 0.001),
                      mats[DARK])
            lines.append("%-34s %.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0))
            x += slot + 0.35
        lines.append("")
        y_cursor += depth + 0.9

    lines += DOC_LINES(engines)

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for key_name, mesh in parts.items():
            export_mesh(coll, mesh, "SM_" + key_name)
        with open(os.path.join(EXPORT_DIR, "Odtahovky.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    select_only(roots[0])
    print("\n".join(lines))


main()
