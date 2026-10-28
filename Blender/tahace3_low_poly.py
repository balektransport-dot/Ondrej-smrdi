# Stylizovane low poly tahace 3 (4x2, 6x2 a 8x2) pre Blender 3.0 a novsi: ten isty podvozok, kolesa s dezenom, nadrze, blatniky
# a zadne svetla ako v skriptoch Tahace a Tahace2, ale kabina a naraznik podla fotky moderneho tahaca: hladky predok s tenkymi sikmymi
# svetlami, perforovana horna mriezka, siroka spodna maska so znackou, tmava predna cast strechy so svetelnym pasom, panoramaticke sklo,
# sikma strecha so spacou castou vzadu; nasavanie je vtavene do boku kabiny, vyfuk je pod autom vpravo. Biely lak s farebnym pasom.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Tahace3":
#   Tahac3_4x2, Tahac3_6x2, Tahac3_8x2 - hotove tahace (kazdy v svojej podkolekcii), umiestnene vedla tahacov z Tahace a Tahace2 (y = -28 / -32.5 / -37).
#   Tahace3_diely - kazdy diel samostatne s menovkou.
# Ovladanie (vlastnosti na objekte tahaca, napr. "Tahac3_6x2": panel N -> Item, alebo Object -> Custom Properties):
#   Vyska_podvozku    - dofuknutie / vypustenie vankusov: zadok sa zdvihne alebo spusti (-0.06 az 0.10 m)
#   Zdvih_napravy     - zdvihnutie vlecenej napravy 0 = dole, 1 = hore (6x2 a 8x2)
#   Vyklopenie_kabiny - 0 = normalne, 1 = vyklopena dopredu (vidno motor)
#   Kabina_klopenie, Kabina_naklon - pohyb kabiny na jej perovani v stupnoch (brzdenie, zakruta)
#   Riadenie          - natocenie prednych kolies v stupnoch (volant sa toci s nimi)
#   Posun_tocne       - posun tocne dopredu / dozadu v metroch (-0.30 az 0.30)
#   Motor             - 1 = R4, 2 = R6, 3 = V8 (nase motory s prevodovkami, vsetky sedia na rovnaky kardan)
# Ked pustis animaciu (medzernik): jazda cez nerovnosti so zatacanim, kabina sa hojda, zvysenie a znizenie,
# zdvihnutie napravy, vyklopenie kabiny, posun tocne; volant, kladky motora a rucicky budikov sa hybu.
# Predok = +X, lava strana = +Y. Pociatok tahaca = zem pod prvou prednou napravou.
# Do priecinka Tahace3 v domovskom priecinku ulozi FBX kazdeho dielu a subor Tahace3.txt.
# Skript sa da spustit znova: stare diely sa nahradia novymi. Da sa spustit aj spolu so skriptom Tahace (nazvy sa nebiju).

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Tahace3"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Tahace3")

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
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, PAINT, ALU, BUMPER, GLASS, SEAT, LAMP_OR, LAMP_RED, LAMP_WHITE, RED,
 WHITE, REDPAINT, INT, GAUGE, BEIGE, GREEN, PAINT_BLUE, PAINT_TEAL, PAINT_RED, YELLOW,
 PAINT_WHITE, ACC_BLUE, ACC_ORANGE, ACC_GREEN) = range(29)
SIDES_LR = (-1.0, 1.0)
PLATE = FRAME              # platna tocne
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

TRUCKS = [
    {"name": "Tahac3_4x2", "axles": [("front", 0.0), ("drive", -3.60)], "rear_end": -4.70, "fifth": -3.30,
     "tank_x": -1.60, "paint": PAINT_WHITE, "accent": ACC_BLUE, "y": -28.0},
    {"name": "Tahac3_6x2", "axles": [("front", 0.0), ("drive", -3.30), ("tag", -4.65)], "rear_end": -5.75, "fifth": -3.75,
     "tank_x": -1.50, "paint": PAINT_WHITE, "accent": ACC_ORANGE, "y": -32.5},
    {"name": "Tahac3_8x2", "axles": [("front", 0.0), ("front", -1.95), ("drive", -4.75), ("tag", -6.10)], "rear_end": -7.20,
     "fifth": -5.20, "tank_x": -3.13, "paint": PAINT_WHITE, "accent": ACC_GREEN, "y": -37.0},
]


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
    return finish_mesh(bm, "SM_Tahac3_kabina")


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
    return finish_mesh(bm, "SM_Tahac3_nasavanie")


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
    return finish_mesh(bm, "SM_Tahac3_interier")


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
    return finish_mesh(bm, "SM_Tahac3_volant")


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


def build_fifth_rails():
    # kolajnice so zubami a dorazmi: pevne na rame, pivot v strede spodku (na vrchu ramu)
    bm = bmesh.new()
    rail_y, rail_len = FIFTH_RAIL_Y, FIFTH_RAIL_LEN
    for s in SIDES_LR:
        add_box(bm, (rail_len, 0.10, 0.06), (0.0, s * rail_y, 0.03), DARK, bev=0.008)
        for k in range(17):
            x = -0.48 + k * 0.06
            add_box(bm, (0.03, 0.035, 0.012), (x, s * (rail_y - 0.025), 0.064), PLATE)
        for x in (-rail_len * 0.5 + 0.02, rail_len * 0.5 - 0.02):
            add_box(bm, (0.04, 0.12, 0.09), (x, s * rail_y, 0.045), DARK, bev=0.006)
        for x in (-0.45, 0.0, 0.45):
            add_cylinder(bm, 0.012, 0.012, along_z((x, s * (rail_y + 0.03), 0.062)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Tahac3_tocna_kolajnice")


def build_fifth_top():
    # vozik, platna, zamok a uvolnovacia tyc: posuva sa po kolajniciach v osi X (pivot rovnaky ako kolajnice)
    bm = bmesh.new()
    rail_y = FIFTH_RAIL_Y
    add_box(bm, (0.55, 0.92, 0.035), (0.0, 0.0, 0.0775), PLATE, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.45, 0.14, 0.05), (0.0, s * rail_y, 0.085), PLATE, bev=0.008)
        add_box(bm, (0.30, 0.10, 0.08), (0.0, s * 0.33, 0.135), PLATE, bev=0.01)
        add_cylinder(bm, 0.03, 0.14, along_y((0.0, s * 0.33, 0.17)), STEEL, segments=10)
        for x in (-0.18, 0.18):
            add_cylinder(bm, 0.01, 0.012, along_z((x, s * 0.44, 0.1)), CHROME, segments=6)
        # zaistovaci kolik posuvu (zapada do zubov)
        add_box(bm, (0.05, 0.04, 0.05), (0.20, s * (rail_y - 0.05), 0.10), STEEL, bev=0.006)

    # platna so zrazenymi hranami a mazacimi drazkami v tvare U
    add_extruded(bm, plate_outline(), 0.17, 0.23, "XY", PLATE, bev=0.022)
    for r in (0.17, 0.25, 0.33):
        add_extruded(bm, arc_band(r + 0.018, r, -145.0, 145.0), 0.226, 0.236, "XY", DARK)

    # zamok na konci zarezu a uvolnovacia tyc s okom a cervenou rukovatou (lava strana, ako pri vodicovi)
    add_box(bm, (0.04, 0.08, 0.05), (0.02, 0.0, 0.195), STEEL, bev=0.006)
    add_box(bm, (0.10, 0.06, 0.05), (0.0, 0.36, 0.15), PLATE, bev=0.008)
    handle_end = (0.30, 0.66, 0.12)
    add_rod(bm, (0.0, 0.36, 0.15), handle_end, 0.012, STEEL, segments=8)
    loop_c = (handle_end[0] + 0.03, handle_end[1] + 0.05, handle_end[2])
    add_ring_loop(bm, loop_c, 0.055, STEEL)
    add_box(bm, (0.05, 0.03, 0.03), (loop_c[0] + 0.02, loop_c[1] + 0.05, loop_c[2]), RED, bev=0.006)
    return finish_mesh(bm, "SM_Tahac3_tocna_platna")


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
    return finish_mesh(bm, "SM_Tahac3_koleso_predne")


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
    return finish_mesh(bm, "SM_Tahac3_koleso_zadne")


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
    return finish_mesh(bm, "SM_Tahac3_naprava_predna")


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
    return finish_mesh(bm, "SM_Tahac3_naprava_hnacia")


def build_tag_axle():
    # vlecena (zdvihacia) naprava bez diferencialu, dvojmontaz kolies ako na hnacej
    bm = bmesh.new()
    add_cylinder(bm, 0.065, 2.0 * REAR_SPINDLE - 0.04, along_y((0.0, 0.0, 0.0)), FRAME, segments=12)
    add_box(bm, (0.16, 0.50, 0.10), (0.0, 0.0, 0.0), FRAME, bev=0.02)
    for s in SIDES_LR:
        add_cylinder(bm, 0.09, 0.03, along_y((0.0, s * (REAR_SPINDLE - 0.035), 0.0)), STEEL, segments=12)
        add_u_bolts(bm, s * RAIL_Y, 0.075, ARM_CLAMP_Z - 0.045, 0.07)
        add_shock_bracket(bm, REAR_SHOCK_LOW, s)
    return finish_mesh(bm, "SM_Tahac3_naprava_vlecena")


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
    return finish_mesh(bm, "SM_Tahac3_tlmic_valec")


def build_shock_rod():
    # horna cast tlmica: pivot v hornom oku, mieri osou -Z dole na spodne oko
    bm = bmesh.new()
    L = SHOCK_PART
    add_cylinder(bm, 0.025, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.013, L - 0.02, along_z((0.0, 0.0, -(L + 0.02) * 0.5)), CHROME, segments=8)
    add_cylinder(bm, 0.041, 0.12, along_z((0.0, 0.0, -0.085)), DARK, segments=10, bev=0.006)
    return finish_mesh(bm, "SM_Tahac3_tlmic_piestnica")


def build_trailing_arm():
    # vlecene rameno vzduchoveho perovania: pivot v cape na rame, mieri osou -X na bod pod napravou
    bm = bmesh.new()
    path, seat, _, tilt = arm_geometry()
    pts = [(p.x, p.z) for p in path]
    add_extruded(bm, beam_outline(pts, [0.045, 0.04, 0.032], cap=0.5), -0.05, 0.05, "XZ", FRAME, bev=0.008)
    add_cylinder(bm, 0.045, 0.11, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_box(bm, (0.24, 0.16, 0.012), (seat.x, 0.0, seat.z - 0.006), STEEL, bev=0.003, rotation=(0.0, tilt, 0.0))
    return finish_mesh(bm, "SM_Tahac3_rameno")


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
    return finish_mesh(bm, "SM_Tahac3_vankus")


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
    return finish_mesh(bm, "SM_Tahac3_kardan_zadny")


def build_cab_spring_body():
    # perovanie kabiny vzadu, spodna cast (mech s tlmicom): pivot v oku na rame, mieri osou +Z na oko na kabine
    bm = bmesh.new()
    add_cylinder(bm, 0.022, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.03, 0.04, along_z((0.0, 0.0, 0.03)), STEEL, segments=10)
    add_cylinder(bm, 0.06, 0.10, along_z((0.0, 0.0, 0.10)), TIRE, segments=12, bev=0.025)
    add_cylinder(bm, 0.045, 0.02, along_z((0.0, 0.0, 0.16)), STEEL, segments=12)
    return finish_mesh(bm, "SM_Tahac3_perovanie_kabiny_mech")


def build_cab_spring_rod():
    # horna cast: pivot v oku na kabine, mieri osou -Z na oko na rame
    bm = bmesh.new()
    add_cylinder(bm, 0.022, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.03, 0.05, along_z((0.0, 0.0, -0.035)), STEEL, segments=10)
    add_cylinder(bm, 0.012, 0.16, along_z((0.0, 0.0, -0.14)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Tahac3_perovanie_kabiny_piest")


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
    return finish_mesh(bm, "SM_%s_ram" % truck["name"])


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
    return finish_mesh(bm, "SM_Tahac3_naraznik")


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
    return finish_mesh(bm, "SM_Tahac3_chladic")


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
    return finish_mesh(bm, "SM_Tahac3_nadrz_nafta")


def build_adblue_tank():
    bm = bmesh.new()
    ty, tz = 0.70, 0.78
    add_box(bm, (0.40, 0.42, 0.46), (0.0, ty, tz), WHITE, bev=0.05)
    add_cylinder(bm, 0.045, 0.04, along_z((0.08, ty + 0.08, tz + 0.25)), STEEL, segments=10)
    add_cylinder(bm, 0.055, 0.025, along_z((0.08, ty + 0.08, tz + 0.28)), PAINT_BLUE, segments=10, bev=0.006)
    for x in (-0.12, 0.12):
        add_box(bm, (0.04, ty - 0.21 - RAIL_Y, 0.05), (x, (ty - 0.21 + RAIL_Y) * 0.5 + 0.015, tz + 0.12), FRAME, bev=0.004)
        add_box(bm, (0.06, 0.012, 0.22), (x, RAIL_Y + 0.036, 0.90), FRAME, bev=0.003)
    return finish_mesh(bm, "SM_Tahac3_nadrz_adblue")


def build_battery_box():
    # skrina baterii, prava strana
    bm = bmesh.new()
    add_box(bm, (0.62, 0.50, 0.36), (0.0, -0.70, 0.72), DARK, bev=0.03)
    add_box(bm, (0.58, 0.02, 0.30), (0.0, -0.955, 0.72), FRAME, bev=0.005)
    for x in (-0.20, 0.20):
        add_box(bm, (0.05, 0.02, 0.04), (x, -0.968, 0.84), STEEL, bev=0.004)
        add_box(bm, (0.05, 0.03, 0.30), (x, -0.44, 0.78), FRAME, bev=0.004)
    return finish_mesh(bm, "SM_Tahac3_baterie")


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
    return finish_mesh(bm, "SM_Tahac3_vzduchojemy")


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
    return finish_mesh(bm, "SM_Tahac3_vyfuk")


def build_catwalk():
    # lavka za kabinou (ryhovany plech) na nozickach na rame
    bm = bmesh.new()
    x0, x1, z = -1.55, -0.95, 1.17
    add_box(bm, (x1 - x0, 1.40, 0.025), ((x0 + x1) * 0.5, 0.0, z), ALU, bev=0.004)
    for i in range(6):
        for j in range(13):
            add_box(bm, (0.045, 0.012, 0.004), (x0 + 0.05 + i * 0.10, -0.66 + j * 0.11, z + 0.014), ALU,
                    rotation=(0.0, 0.0, 45.0 if (i + j) % 2 else -45.0))
    for x in (x0 + 0.06, x1 - 0.06):
        for s in SIDES_LR:
            add_box(bm, (0.04, 0.04, z - FRAME_TOP), (x, s * RAIL_Y, (z + FRAME_TOP) * 0.5), FRAME)
    return finish_mesh(bm, "SM_Tahac3_lavka")


def build_coils():
    # stojan s hadicami na naves: cervena (vzduch), zlta (brzda), cierna (elektrina)
    bm = bmesh.new()
    px, py, top = -1.52, 0.30, 2.10
    add_box(bm, (0.06, 0.06, top - 1.18), (px, py, (top + 1.18) * 0.5), FRAME, bev=0.006)
    add_box(bm, (0.05, 0.72, 0.05), (px, py - 0.33, top - 0.02), FRAME, bev=0.006)
    add_box(bm, (0.04, 0.64, 0.03), (px, py - 0.30, 1.36), FRAME, bev=0.004)
    for y, mat in ((-0.28, REDPAINT), (-0.08, YELLOW), (0.12, DARK)):
        a, b = add_coil(bm, (px - 0.08, y), 0.065, top - 0.09, 1.50, 8, mat)
        add_rod(bm, (px, y, top - 0.045), a, 0.011, mat)
        add_rod(bm, b, (px - 0.02, y, 1.41), 0.011, mat)
        add_box(bm, (0.06, 0.07, 0.05), (px - 0.02, y, 1.395), mat if mat != DARK else STEEL, bev=0.008)
    return finish_mesh(bm, "SM_Tahac3_hadice")


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
    return finish_mesh(bm, "SM_Tahac3_zadna_lista")


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
        if mesh.users == 0 and mesh.get("tahace3"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_Tahac3"):
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
               build_bumper, build_radiator, build_fifth_rails, build_fifth_top, build_fuel_tank, build_adblue_tank,
               build_battery_box, build_air_tanks, build_exhaust, build_catwalk, build_coils,
               build_steer_axle, build_drive_axle, build_tag_axle, build_wheel_single, build_wheel_dual,
               build_shock_body, build_shock_rod, build_trailing_arm, build_air_bag, build_kardan_rear):
        put(fn())
    put(build_needle("SM_Tahac3_rucicka_velka", 0.065))
    put(build_needle("SM_Tahac3_rucicka_mala", 0.024))
    spring = build_spring_half()
    spring_rear = spring.copy()
    bmesh.ops.scale(spring_rear, vec=(-1.0, 1.0, 1.0), verts=spring_rear.verts[:])
    bmesh.ops.reverse_faces(spring_rear, faces=spring_rear.faces[:])
    put(finish_mesh(spring, "SM_Tahac3_pero_predna_cast"))
    put(finish_mesh(spring_rear, "SM_Tahac3_pero_zadna_cast"))
    put_lr(build_rear_fender(0.64, 1.29, "frame"), "SM_Tahac3_blatnik_zadny")
    put_lr(build_rear_fender(0.64, 1.29, "frame", True), "SM_Tahac3_blatnik_zadny_svetla")
    put_lr(build_rear_fender(0.64, 1.29, "axle", True), "SM_Tahac3_blatnik_vleceny")
    put_lr(build_mudguard(0.80, 1.16, "frame"), "SM_Tahac3_blatnik_predny")
    for truck in TRUCKS:
        put(build_frame(truck))
        put(build_kardan_front("SM_%s_kardan_predny" % truck["name"], kardan_rest_length(truck) - 0.75))
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
            mesh["tahace3"] = 1
        gb_loc = Vector((info["back"] - 0.02, 0.0, info["flange_z"]))
        tip = gb_loc + Vector((out_x + min(v.co.x for v in out_mesh.vertices), 0.0, 0.0))
        engines[spec["key"]] = dict(body=body_mesh, pulleys=pulleys, gearbox=gb_mesh, gb_loc=gb_loc, output=out_mesh,
                                    out_x=out_x, tip=tip)
    return engines


AXLE_MESH = {"front": "Tahac3_naprava_predna", "drive": "Tahac3_naprava_hnacia", "tag": "Tahac3_naprava_vlecena"}
ENGINE_KEYS = ("R4", "R6", "V8")


# ---------------------------------------------------------------------------
# Zostava jedneho tahaca
# ---------------------------------------------------------------------------

def build_truck(coll, truck, parts, mats, engines, motor):
    name = truck["name"]
    axles = truck["axles"]
    has_tag = any(kind == "tag" for kind, _ in axles)

    root = new_object(coll, name, None, (0.0, truck["y"], 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.0
    set_prop(root, "Vyska_podvozku", 0.0, -0.06, 0.10, "Dofuknutie / vypustenie vankusov v metroch (zadok hore / dole)")
    if has_tag:
        set_prop(root, "Zdvih_napravy", 0.0, 0.0, 1.0, "0 = vlecena naprava dole, 1 = zdvihnuta")
    set_prop(root, "Vyklopenie_kabiny", 0.0, 0.0, 1.0, "0 = kabina normalne, 1 = vyklopena dopredu")
    set_prop(root, "Kabina_klopenie", 0.0, -4.0, 4.0, "Kabina dopredu (+) / dozadu na perovani v stupnoch")
    set_prop(root, "Kabina_naklon", 0.0, -5.0, 5.0, "Kabina do strany na perovani v stupnoch")
    set_prop(root, "Riadenie", 0.0, -30.0, 30.0, "Natocenie prednych kolies v stupnoch (+ = dolava)")
    set_prop(root, "Posun_tocne", 0.0, -FIFTH_SLIDE, FIFTH_SLIDE, "Posun tocne dopredu (+) / dozadu (-) v metroch")
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
    body = new_object(coll, name + "_ram", parts[name + "_ram"], (0.0, 0.0, 0.0), root)
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
                new_object(coll, "%s_koleso_%d_%s" % (name, n, side), parts["Tahac3_koleso_predne"],
                           (0.0, s * (FRONT_SPINDLE - KINGPIN_Y), 0.0), knuckle, rot)
                target = empty(coll, "%s_pero_stred_%d_%s" % (name, n, side), (0.0, s * RAIL_Y, SPRING_SEAT), axle)
                half_f = new_object(coll, "%s_pero_%d_%s_1" % (name, n, side), parts["Tahac3_pero_predna_cast"],
                                    (ax + SPRING_HALF, s * RAIL_Y, SPRING_EYE_Z), body)
                half_r = new_object(coll, "%s_pero_%d_%s_2" % (name, n, side), parts["Tahac3_pero_zadna_cast"],
                                    (ax - SPRING_HALF, s * RAIL_Y, SPRING_EYE_Z), body)
                track(half_f, target, "TRACK_NEGATIVE_X")
                track(half_r, target, "TRACK_X")
                low, up = FRONT_SHOCK_LOW, FRONT_SHOCK_UP
                if i > 0:
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts["Tahac3_blatnik_predny_" + side],
                               (ax, 0.0, WHEEL_R), body)
            else:
                wheel = "Tahac3_koleso_zadne"
                spindle = REAR_SPINDLE
                new_object(coll, "%s_koleso_%d_%s" % (name, n, side), parts[wheel], (0.0, s * spindle, 0.0), axle, rot)
                aim = empty(coll, "%s_rameno_ciel_%d_%s" % (name, n, side), (0.0, s * RAIL_Y, ARM_CLAMP_Z), axle)
                arm = new_object(coll, "%s_rameno_%d_%s" % (name, n, side), parts["Tahac3_rameno"],
                                 (ax + ARM_PIVOT.x, s * RAIL_Y, ARM_PIVOT.z), body)
                track(arm, aim, "TRACK_NEGATIVE_X")
                seat_aim = empty(coll, "%s_vankus_ciel_%d_%s" % (name, n, side), tuple(seat_local), arm)
                bag_top = (ax + bag_bottom.x, s * RAIL_Y, FRAME_BOT)
                bag = new_object(coll, "%s_vankus_%d_%s" % (name, n, side), parts["Tahac3_vankus"], bag_top, body)
                track(bag, seat_aim, "TRACK_NEGATIVE_Z")
                # vyska vankusa = vzdialenost bodu na rame a sedla na ramene (samostatny bod, aby sa necital sam)
                top_aim = empty(coll, "%s_vankus_hore_%d_%s" % (name, n, side), bag_top, body)
                driver(bag, "scale", 2, "d / %.4f" % bag_rest, [("d", "DIST", (top_aim, seat_aim))])
                low, up = REAR_SHOCK_LOW, REAR_SHOCK_UP
                if kind == "drive":
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts[("Tahac3_blatnik_zadny_" if has_tag else "Tahac3_blatnik_zadny_svetla_") + side],
                               (ax, 0.0, WHEEL_R), body)
                else:
                    new_object(coll, "%s_blatnik_%d_%s" % (name, n, side), parts["Tahac3_blatnik_vleceny_" + side],
                               (0.0, 0.0, 0.0), axle)
            link_pair(coll, "%s_tlmic_%d_%s" % (name, n, side), parts["Tahac3_tlmic_valec"], parts["Tahac3_tlmic_piestnica"],
                      axle, Vector((low.x, s * low.y, low.z)), body, Vector((ax + up.x, s * up.y, up.z)),
                      "TRACK_Z", "TRACK_NEGATIVE_Z")

    # --- kardan medzi prevodovkou (ram) a diferencialom (hnacia naprava), posuvny ---
    link_pair(coll, name + "_kardan", parts[name + "_kardan_predny"], parts["Tahac3_kardan_zadny"],
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
    for part_name, location in (("Tahac3_naraznik", (0.0, 0.0, 0.0)), ("Tahac3_chladic", (0.0, 0.0, 0.0)),
                                ("Tahac3_nadrz_nafta", (tank_x, 0.0, 0.0)), ("Tahac3_nadrz_adblue", (tank_x - 0.86, 0.0, 0.0)),
                                ("Tahac3_baterie", (tank_x + 0.20, 0.0, 0.0)), ("Tahac3_vzduchojemy", (tank_x - 0.55, 0.0, 0.0)),
                                ("Tahac3_vyfuk", (0.0, 0.0, 0.0)), ("Tahac3_lavka", (0.0, 0.0, 0.0)),
                                ("Tahac3_hadice", (0.0, 0.0, 0.0))):
        new_object(coll, part_name.replace("Tahac3_", name + "_"), parts[part_name], location, body)
    rails = new_object(coll, name + "_tocna_kolajnice", parts["Tahac3_tocna_kolajnice"], (truck["fifth"], 0.0, FRAME_TOP), body)
    top = new_object(coll, name + "_tocna_platna", parts["Tahac3_tocna_platna"], (0.0, 0.0, 0.0), rails)
    driver(top, "location", 0, "p", [prop("p", "Posun_tocne")])

    # --- kabina: vlastne perovanie (klopenie, naklon) a vyklapanie dopredu okolo predneho capu ---
    cab = new_object(coll, name + "_kabina", parts["Tahac3_kabina"], CAB_HINGE, body)
    cab_vars = [prop("t", "Vyklopenie_kabiny"), prop("p", "Kabina_klopenie"), prop("n", "Kabina_naklon"),
                ("br", "TRANSFORM", (body, "ROT_X"))]
    driver(cab, "rotation_euler", 1, "t * %.3f + (1 - t) * p * %.6f" % (CAB_TILT, DEG), cab_vars)
    driver(cab, "rotation_euler", 0, "(1 - t) * (n * %.6f + 0.6 * br)" % DEG, cab_vars)
    paint(cab, mats[truck["paint"]])
    paint(cab, mats[truck["accent"]], ACCENT)
    new_object(coll, name + "_interier", parts["Tahac3_interier"], (0.0, 0.0, 0.0), cab)
    paint(new_object(coll, name + "_nasavanie", parts["Tahac3_nasavanie"], (0.0, 0.0, 0.0), cab), mats[truck["paint"]])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        low = Vector((CAB_MOUNT.x, s * CAB_MOUNT.y, CAB_MOUNT_LOW))
        up = Vector((CAB_MOUNT.x, s * CAB_MOUNT.y, CAB_MOUNT.z)) - CAB_HINGE
        for part in link_pair(coll, "%s_perovanie_kabiny_%s" % (name, side), parts["Tahac3_perovanie_kabiny_mech"],
                              parts["Tahac3_perovanie_kabiny_piest"], body, low, cab, up, "TRACK_Z", "TRACK_NEGATIVE_Z"):
            # pri vyklapani sa zadne uchytenie odopne (mech ostane na rame, piest na kabine)
            driver(part, 'constraints["%s"].influence' % part.constraints[0].name, -1, "max(0, 1 - t * 8)",
                   [prop("t", "Vyklopenie_kabiny")])

    wheel_frame = Matrix.Translation(CAB_MATRIX @ WHEEL_CENTER) @ STEERING.to_3x3().to_4x4()
    steering = place_spinning(coll, name + "_volant", parts["Tahac3_volant"], wheel_frame, cab)
    driver(steering, "rotation_euler", 2, "%.5f + r * %.6f" % (steering.rotation_euler[2], DEG * STEER_RATIO),
           [prop("r", "Riadenie")])
    needles = []
    for gauge_name, offset, radius, _, idle in GAUGES:
        g = gauge_frame(offset) @ Matrix.Translation((0.0, 0.0, 0.012))
        frame = Matrix.Translation(CAB_MATRIX @ g.to_translation()) @ g.to_3x3().to_4x4()
        mesh = parts["Tahac3_rucicka_velka" if radius > 0.05 else "Tahac3_rucicka_mala"]
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
    keys("Posun_tocne", [(1, 0.0), (385, 0.0), (405, FIFTH_SLIDE), (425, -FIFTH_SLIDE), (445, 0.0)])
    for gauge_name, needle, idle in needles:
        z0 = needle.rotation_euler[2]
        if gauge_name in ("rychlost", "otacky"):
            peak = 0.30 if gauge_name == "rychlost" else 0.55
            key(needle, "rotation_euler", 2, [(1, z0 + gauge_angle(idle)), (40, z0 + gauge_angle(peak)), (80, z0 + gauge_angle(idle))])
        else:
            needle.rotation_euler[2] = z0 + gauge_angle(idle)


CATALOG = [
    ("KABINA", ["Tahac3_kabina", "Tahac3_interier", "Tahac3_volant", "Tahac3_rucicka_velka", "Tahac3_rucicka_mala", "Tahac3_nasavanie",
                "Tahac3_perovanie_kabiny_mech", "Tahac3_perovanie_kabiny_piest"]),
    ("RAMY A PREDOK", ["Tahac3_4x2_ram", "Tahac3_6x2_ram", "Tahac3_8x2_ram", "Tahac3_naraznik", "Tahac3_chladic"]),
    ("PRISLUSENSTVO", ["Tahac3_tocna_kolajnice", "Tahac3_tocna_platna", "Tahac3_nadrz_nafta", "Tahac3_nadrz_adblue", "Tahac3_baterie",
                       "Tahac3_vzduchojemy", "Tahac3_vyfuk", "Tahac3_lavka", "Tahac3_hadice"]),
    ("BLATNIKY", ["Tahac3_blatnik_zadny_L", "Tahac3_blatnik_zadny_P", "Tahac3_blatnik_zadny_svetla_L", "Tahac3_blatnik_zadny_svetla_P", "Tahac3_blatnik_vleceny_L", "Tahac3_blatnik_vleceny_P",
                  "Tahac3_blatnik_predny_L", "Tahac3_blatnik_predny_P"]),
    ("NAPRAVY A PEROVANIE", ["Tahac3_naprava_predna", "Tahac3_naprava_hnacia", "Tahac3_naprava_vlecena", "Tahac3_koleso_predne",
                             "Tahac3_koleso_zadne", "Tahac3_pero_predna_cast", "Tahac3_pero_zadna_cast", "Tahac3_tlmic_valec",
                             "Tahac3_tlmic_piestnica", "Tahac3_rameno", "Tahac3_vankus"]),
    ("KARDANY", ["Tahac3_4x2_kardan_predny", "Tahac3_6x2_kardan_predny", "Tahac3_8x2_kardan_predny", "Tahac3_kardan_zadny"]),
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
        mesh["tahace3"] = 1
        for mat in mats:
            mesh.materials.append(mat)
    engines = build_engines()

    roots = []
    for index, truck in enumerate(TRUCKS):
        roots.append(build_truck(child_collection(coll, truck["name"]), truck, parts, mats, engines, index + 1))
    scene.frame_start, scene.frame_end = 1, 450
    scene.frame_set(1)

    # --- katalog dielov ---
    kit = child_collection(coll, "Tahace3_diely")
    lines = ["Tahace 2 - diely (rozmery X x Y x Z v metroch). Predok = +X, lava = +Y.", ""]
    y_cursor = 3.5
    for title, keys in CATALOG:
        depth = max(bounds(parts[k])[1][1] - bounds(parts[k])[1][0] for k in keys)
        row_y = y_cursor + depth * 0.5
        add_label(kit, title, (-2.5, row_y, 0.001), mats[DARK])
        x = -1.0
        lines.append("== %s ==" % title)
        for k in keys:
            mesh = parts[k]
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            slot = max(x1 - x0, 1.2)
            new_object(kit, "Diel_" + k[7:], mesh, (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0))
            add_label(kit, "%s\n%.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0), (x + slot * 0.5, row_y - depth * 0.5 - 0.2, 0.001),
                      mats[DARK])
            lines.append("%-30s %.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0))
            x += slot + 0.35
        lines.append("")
        y_cursor += depth + 0.9

    def vec(v):
        return "(%.3f, %.3f, %.3f)" % tuple(v)

    _, seat_local, bag_bottom, _ = arm_geometry()
    lines += [
        "MOTORY: nase R4 / R6 / V8 s prevodovkami (diely su v skripte Motory). Koniec vystupneho hriadela kazdej",
        "  prevodovky je na rame v %s, takze kazdy motor sedi na ten isty kardan. Vlastnost Motor = 1 / 2 / 3." % vec(GEARBOX_OUT),
    ]
    for engine_key in ENGINE_KEYS:
        lines.append("  Motor %s: pivot motora na rame v %s" % (engine_key, vec(GEARBOX_OUT - engines[engine_key]["tip"])))
    lines += [
        "",
        "AKO JE TO POSKLADANE (hierarchia v kolekciach Tahac3_4x2 / 6x2 / 8x2), suradnice od pociatku tahaca:",
        "  Tahac3_xxx (prazdny objekt) - posuvaj nim cely tahac, vlastnosti = ovladanie (popis na zaciatku skriptu).",
        "  Napravy: pivot v osi kolies (z = %.3f). Predne kolesa su na capoch riadenia (y = +-%.2f), zadne na koncoch naprav." % (
            WHEEL_R, KINGPIN_Y),
        "  Tahac3_xxx_ram (odpruzena cast): z = %.1f x pohyb prvej napravy, sklon podla hnacej napravy + vyska vankusov." % BODY_FOLLOW,
        "  Predne pera: dve casti na stranu, oka na rame v x napravy +-%.2f, z %.2f, mieria na stred pera %s (od napravy)." % (
            SPRING_HALF, SPRING_EYE_Z, vec((0, RAIL_Y, SPRING_SEAT))),
        "  Zadne ramena: cap na rame v x napravy + %.2f, z %.2f; mieria osou -X na bod %s pod napravou." % (
            ARM_PIVOT.x, ARM_PIVOT.z, vec((0, RAIL_Y, ARM_CLAMP_Z))),
        "  Vankuse: hore na rame (x napravy %.2f, z %.2f), mieria osou -Z na sedlo na ramene %s;" % (
            bag_bottom.x, FRAME_BOT, vec(seat_local)),
        "    vysku natiahni mierkou Z = vzdialenost / %.3f." % (FRAME_BOT - bag_bottom.z),
        "  Tlmice: valec na naprave mieri osou +Z na horne oko na rame, piestnica z horneho oka mieri osou -Z dole.",
        "  Kardan: predna cast na rame %s mieri osou -X na diferencial, zadna cast %s (od hnacej napravy) mieri +X." % (
            vec(GEARBOX_OUT), vec((PINION_X, 0, 0))),
        "  Kabina: pivot = predny cap vyklapania %s (na rame). Vyklopenie = otocenie okolo Y o %.0f st." % (
            vec(CAB_HINGE), math.degrees(CAB_TILT)),
        "    Interier a nasavanie maju rovnaky pivot ako kabina (daj ich na to iste miesto).",
        "    Zadne perovanie kabiny: mech na rame %s mieri +Z na oko na kabine %s; pri vyklopeni sa odopne." % (
            vec((CAB_MOUNT.x, CAB_MOUNT.y, CAB_MOUNT_LOW)), vec(CAB_MOUNT)),
        "    Kabina 3: dlhsia o %.2f m (vzadu spaca cast s lozkom), jemne vyklenuta sikma strecha, panoramaticke sklo sklonene o %.2f m, tmava predna cast strechy" % (EXT * CAB_SCALE, RAKE * CAB_SCALE),
        "      so svetelnym pasom, znackou a smerovkami, dve antenky; nasavanie vzduchu je vtavene do laveho boku kabiny (diel Tahac3_nasavanie, pivot ako kabina).",
        "    Farby: kabina je biela, akcentova farba (pas po boku, stitok pod mriezkou) je na kazdom tahaci ina - nastavuje sa na objekte kabiny (slot TH3_Akcent_modry).",
        "    Vyfuk: tlmic pod autom vpravo za prednou napravou, vyustka smeruje dole von (diel Tahac3_vyfuk, pivot v pociatku tahaca).",
        "  Tocna: kolajnice na vrchu ramu (z %.2f), platna sa posuva v osi X o +-%.2f m." % (FRAME_TOP, FIFTH_SLIDE),
        "  Blatniky: pivot v osi kolesa. Zadny a predny (2. naprava 8x2) na rame, vleceny na naprave (zdviha sa s nou).",
        "    Zadne svetla su priamo na poslednom zadnom blatniku (4x2: Tahac3_blatnik_zadny_svetla, 6x2 a 8x2: Tahac3_blatnik_vleceny); SPZ je na konci ramu.",
        "  Prave diely _P su zrkadlove, kolesa vpravo otoc o 180 st. okolo Z.",
        "V Unreali: kazdy par 'mieri na' urob cez Find Look at Rotation (alebo Look At v Control Rig / Animation Blueprinte).",
    ]
    for truck in TRUCKS:
        lines.append("%s: napravy x = %s, tocna x = %.2f, koniec ramu x = %.2f" % (
            truck["name"], ", ".join("%.2f" % x for _, x in truck["axles"]), truck["fifth"], truck["rear_end"]))

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for key_name, mesh in parts.items():
            export_mesh(coll, mesh, "SM_" + key_name)
        with open(os.path.join(EXPORT_DIR, "Tahace3.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    select_only(roots[0])
    print("\n".join(lines))


main()
