# Stylizovana low poly stavebnica kamiona a navesu (skladacka ako Scrap Mechanic) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Stavebnica_kamion":
#   - katalog: kazdy diel samostatne, s menovkou (rady: ram, napravy, kolesa, blatniky, naves...)
#   - ukazka: tahac s plochym navesom a vedla neho naves na drevo (klanicovy), poskladane z tych istych
#     dielov - len aby bolo vidiet, ako to do seba zapada. Dlzku navesu, pocet naprav atd. si urcis sam.
# Ziadny diel nie je cely celok - ram sa sklada z nosnikov a priecnikov, naprava z diferencialu, rurok,
# nabojov, pruzin a tlmicov, naves z nosnikov, priecnikov, podlahy, napravy, perovania atd.
#
# PRAVIDLO: pivot kazdeho dielu je v bode, kde sa prichyti (dosadacia plocha). Presne polohy su v subore
# Stavebnica_kamion.txt. Predok = +X, lava strana = +Y. Diely s _L su na lavu stranu, _P na pravu.
# Pri prehravani animacie (medzernik) sa tocia kolesa a kardany.
# Do priecinka Stavebnica_kamion v domovskom priecinku ulozi FBX kazdeho dielu (pre Unreal).
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Stavebnica_kamion"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Stavebnica_kamion")

# (nazov, farba, kovovost, drsnost, svietivost)
MATERIALS = [
    ("SK_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0),
    ("SK_Ocel", (0.45, 0.46, 0.48, 1.0), 0.7, 0.40, 0.0),
    ("SK_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0),
    ("SK_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0),
    ("SK_Disk", (0.80, 0.80, 0.77, 1.0), 0.3, 0.35, 0.0),
    ("SK_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0),
    ("SK_Plast", (0.025, 0.025, 0.028, 1.0), 0.0, 0.60, 0.0),
    ("SK_Vzduchojem", (0.30, 0.32, 0.36, 1.0), 0.5, 0.40, 0.0),
    ("SK_Kardan", (0.58, 0.59, 0.61, 1.0), 0.7, 0.35, 0.0),
    ("SK_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0),
    ("SK_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0),
    ("SK_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0),
    ("SK_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0),
    ("SK_Drevo", (0.36, 0.22, 0.11, 1.0), 0.0, 0.70, 0.0),
    ("SK_Drevo_tmave", (0.28, 0.16, 0.08, 1.0), 0.0, 0.70, 0.0),
    ("SK_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0),
    ("SK_Siva", (0.45, 0.47, 0.50, 1.0), 0.4, 0.45, 0.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, PLASTIC, AIR, SHAFT, LAMP_OR, LAMP_RED, LAMP_WHITE, RED,
 WOOD, WOOD2, WHITE, GREY) = range(17)
PLATE = FRAME            # platna tocne
SIDES_LR = (-1.0, 1.0)

# --- standard tahaca (m) ---
WHEEL_R = 0.525          # polomer kolesa
RAIL_Y = 0.43            # vonkajsia strana nosnika ramu od stredu (ram je siroky 0.86)
RAIL_H = 0.26            # vyska nosnika ramu
SPRING_Y = 0.39          # os pruziny od stredu (pod stredom nosnika)
SEAT = 0.25              # sedlo pruziny pod spodkom ramu
AXLE_SEAT = 0.11         # sedlo pruziny nad osou napravy
HANG = SEAT + AXLE_SEAT  # os napravy pod spodkom ramu
FRAME_Z = WHEEL_R + HANG # spodok ramu nad zemou
FRONT_HUB_Y = 0.88       # priruba cepu riadenej napravy od stredu
DIFF_HALF = 0.25         # priruby diferencialu od stredu
TUBE_LEN = 0.493         # rurka napravy (od diferencialu po naboj)
HUB_LEN = 0.20           # naboj s bubnom (od priruby napravy po dosadaciu plochu kolesa)
REAR_HUB_Y = DIFF_HALF + TUBE_LEN
FRONT_TRACK = FRONT_HUB_Y + HUB_LEN - 0.08   # stred predneho kolesa od stredu
REAR_TRACK = REAR_HUB_Y + HUB_LEN + 0.022   # stred dvojmontaze od stredu

# --- standard navesu (m) ---
TR_BEAM_Y = 0.50         # os hlavneho nosnika navesu od stredu
TR_SIDE_Y = 1.25         # vonkajsia strana obvodoveho nosnika (naves je siroky 2.5)
TR_SHALLOW = 0.20        # vyska nosnika vpredu (nad tocnou)
TR_DEEP = 0.50           # vyska nosnika vzadu
KINGPIN_DECK = 0.212     # horna plocha nosnikov nad spodkom dosky kralovskeho capu
TR_AXLE_DROP = 0.562     # os napravy navesu pod spodkom hlbokeho nosnika


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


def shift(bm, offset):
    # posun celeho dielu (presun pivotu na dosadaciu plochu)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts[:])


# ---------------------------------------------------------------------------
# Kolesa: pivot v strede dosadacej plochy disku (na osi), os otacania Y, vonkajsia strana na +Y
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
    # jednoduche koleso: disk vonku (+Y), naboj s chromovymi maticami
    bm = bmesh.new()
    out = 0.15
    add_truck_tire(bm, 0.0)
    add_cylinder(bm, 0.27, 0.02, along_y((0.0, out - 0.06, 0.0)), RIM, segments=20)
    ring_of(bm, 10, 0.205, out - 0.048, 0.035, 0.006, DARK, segments=10, offset=0.5)
    add_cylinder(bm, 0.12, 0.06, along_y((0.0, out - 0.05, 0.0)), STEEL, segments=16, bev=0.008)
    ring_of(bm, 10, 0.095, out - 0.012, 0.011, 0.025, CHROME)
    add_cone(bm, 0.045, 0.07, 0.05, along_y((0.0, out - 0.03, 0.0)), CHROME, segments=12, bev=0.006)
    shift(bm, (0.0, -(out - 0.07), 0.0))
    return finish_mesh(bm, "SM_Koleso")


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
    shift(bm, (0.0, 0.022, 0.0))
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
# Ram tahaca
#   Nosnik: pivot v strede dlzky, na vonkajsej strane, dole (lavy nosnik; pravy = otoc o 180 st.)
#   Priecniky: pivot v strede, dole (z = 0 je spodok ramu)
# ---------------------------------------------------------------------------

def add_bolt_y(bm, x, y, z, s=1.0, r=0.01):
    # hlava skrutky na ploche kolmej na Y (s = smer von)
    add_cylinder(bm, r, 0.01, along_y((x, y + s * 0.003, z)), CHROME, segments=6)


def build_rail(length):
    bm = bmesh.new()
    h = RAIL_H
    # C-nosnik: stojina vonku (y = 0), pasnice dnu (-Y)
    add_box(bm, (length, 0.014, h), (0.0, -0.007, h * 0.5), FRAME, bev=0.004)
    for z in (0.008, h - 0.008):
        add_box(bm, (length, 0.075, 0.016), (0.0, -0.0375, z), FRAME, bev=0.004)
    # spojovacie plechy na oboch koncoch (dva nosniky za sebou vytvoria cely spoj)
    for s in SIDES_LR:
        x = s * (length * 0.5 - 0.06)
        add_box(bm, (0.12, 0.008, 0.20), (x, 0.004, h * 0.5), FRAME, bev=0.003)
        for dz in (-0.06, 0.06):
            add_bolt_y(bm, x + s * 0.02, 0.008, h * 0.5 + dz)
    # rad otvorov/skrutiek kazdych 25 cm (pre prichytenie dalsich dielov)
    n = int(round(length / 0.25))
    for i in range(1, n):
        x = -length * 0.5 + i * 0.25
        if abs(abs(x) - length * 0.5) > 0.13:
            add_cylinder(bm, 0.012, 0.008, along_y((x, 0.001, h * 0.5)), DARK, segments=8)
    name = "SM_Nosnik_ramu_" + ("%gm" % length).replace(".", "_")
    return finish_mesh(bm, name)


def build_crossmember():
    bm = bmesh.new()
    h = RAIL_H
    inner = RAIL_Y - 0.014
    add_box(bm, (0.10, 2.0 * inner, 0.15), (0.0, 0.0, h * 0.55), FRAME, bev=0.012)
    add_box(bm, (0.13, 2.0 * (RAIL_Y - 0.09), 0.02), (0.0, 0.0, h * 0.55 + 0.08), FRAME, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.28, 0.008, h - 0.05), (0.0, s * (RAIL_Y - 0.018), h * 0.5), FRAME, bev=0.003)
        for dx in (-0.10, 0.0, 0.10):
            for dz in (-0.07, 0.07):
                add_bolt_y(bm, dx, s * RAIL_Y, h * 0.5 + dz, s)
    return finish_mesh(bm, "SM_Priecnik_ramu")


def build_front_crossmember():
    # predne celo ramu s taznym okom; pivot = predny koniec nosnikov (x = 0), dole v strede
    bm = bmesh.new()
    h = RAIL_H
    add_box(bm, (0.02, 2.0 * RAIL_Y, h * 0.8), (0.01, 0.0, h * 0.5), FRAME, bev=0.005)
    for s in SIDES_LR:
        add_box(bm, (0.14, 0.008, h - 0.06), (-0.07, s * (RAIL_Y - 0.018), h * 0.5), FRAME, bev=0.003)
        for dx in (-0.10, -0.04):
            for dz in (-0.06, 0.06):
                add_bolt_y(bm, dx, s * RAIL_Y, h * 0.5 + dz, s)
        for dz in (-0.07, 0.07):
            add_cylinder(bm, 0.012, 0.012, along_x((0.024, s * 0.30, h * 0.5 + dz)), STEEL, segments=6)
    add_box(bm, (0.12, 0.08, 0.08), (0.07, 0.0, h * 0.5), STEEL, bev=0.012)
    add_ring_loop(bm, (0.175, 0.0, h * 0.5), 0.05, STEEL, rod_r=0.018)
    return finish_mesh(bm, "SM_Priecnik_predny")


def build_rear_crossmember():
    # zadny naraznik ramu s odrazkami; pivot = zadny koniec nosnikov (x = 0), dole v strede
    bm = bmesh.new()
    h = RAIL_H
    add_box(bm, (0.14, 2.0 * RAIL_Y + 0.20, 0.20), (-0.05, 0.0, h * 0.5), FRAME, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.20, 0.008, h - 0.06), (0.10, s * (RAIL_Y - 0.018), h * 0.5), FRAME, bev=0.003)
        for dx in (0.06, 0.14):
            for dz in (-0.06, 0.06):
                add_bolt_y(bm, dx, s * RAIL_Y, h * 0.5 + dz, s)
        add_box(bm, (0.008, 0.12, 0.045), (-0.122, s * 0.40, h * 0.5), RED, bev=0.003)
        for dz in (-0.05, 0.05):
            add_cylinder(bm, 0.012, 0.012, along_x((-0.122, s * 0.20, h * 0.5 + dz)), STEEL, segments=6)
    return finish_mesh(bm, "SM_Priecnik_zadny")


# ---------------------------------------------------------------------------
# Perovanie
#   Pruzina: pivot v strede pruziny na spodku ramu (zavesy dosadnu pod nosnik), sedlo je SEAT pod nim
#   Tlmic: pivot na doske, ktora dosadne na bok ramu (lavy; pravy je zrkadlovy)
# ---------------------------------------------------------------------------

def build_leaf_spring(name, half, leaves, eye_z):
    bm = bmesh.new()
    w = 0.08
    z0 = -SEAT + (leaves - 1) * 0.02 + 0.009        # stred hlavneho listu
    k = (eye_z - z0) / (half * half)
    for i in range(leaves):
        f = 1.0 - 0.75 * i / leaves
        path = []
        for j in range(7):
            x = half * f * (j / 3.0 - 1.0)
            path.append((x, z0 - i * 0.02 + k * x * x))
        add_extruded(bm, beam_outline(path, [0.009] * 7, cap=0.3), -w * 0.5, w * 0.5, "XZ", FRAME, bev=0.003)
    add_box(bm, (0.03, w + 0.01, 0.02 * leaves + 0.02), (0.0, 0.0, -SEAT + 0.01 * leaves), STEEL, bev=0.005)
    for s in SIDES_LR:
        x = s * half
        add_cylinder(bm, 0.032, w + 0.01, along_y((x, 0.0, eye_z)), FRAME, segments=8)
        add_cylinder(bm, 0.013, w + 0.12, along_y((x, 0.0, eye_z)), CHROME, segments=6)
        for d in SIDES_LR:
            add_box(bm, (0.09, 0.012, -eye_z + 0.03), (x, d * 0.052, (eye_z - 0.03) * 0.5), FRAME, bev=0.004)
        add_box(bm, (0.16, 0.12, 0.02), (x, 0.0, -0.01), FRAME, bev=0.004)
    # strmene okolo napravy: horna doska, 4 svorniky, spodna doska, matice
    z_top = z0 + 0.009
    z_bot = -HANG - 0.077
    dx = 0.09
    add_box(bm, (2.0 * dx + 0.05, 0.155, 0.025), (0.0, 0.0, z_top + 0.0125), STEEL, bev=0.005)
    add_box(bm, (2.0 * dx + 0.05, 0.155, 0.02), (0.0, 0.0, z_bot - 0.01), STEEL, bev=0.005)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, 0.011, z_top - z_bot + 0.06, along_z((sx * dx, sy * 0.066, (z_top + z_bot) * 0.5)), STEEL, segments=6)
            add_cylinder(bm, 0.018, 0.02, along_z((sx * dx, sy * 0.066, z_bot - 0.03)), CHROME, segments=6)
    return finish_mesh(bm, name)


SHOCK_LOW = Vector((0.25, 0.09, -0.39))   # spodne oko tlmica voci jeho pivotu (na naprave)


def build_shock():
    bm = bmesh.new()
    up = Vector((0.0, 0.045, 0.0))
    low = SHOCK_LOW.copy()
    mid = low.lerp(up, 0.55)
    add_rod(bm, low, mid, 0.035, DARK, segments=8)
    add_rod(bm, mid, up, 0.015, CHROME, segments=6)
    add_rod(bm, low.lerp(up, 0.62), low.lerp(up, 0.88), 0.042, DARK, segments=8)
    for p in (low, up):
        add_cylinder(bm, 0.028, 0.05, along_y(p), DARK, segments=8)
    add_box(bm, (0.10, 0.015, 0.12), (0.0, 0.0075, 0.0), FRAME, bev=0.004)
    add_cylinder(bm, 0.013, 0.075, along_y((0.0, 0.0375, 0.0)), CHROME, segments=6)
    for dz in (-0.04, 0.04):
        add_bolt_y(bm, -0.03, 0.015, dz)
    return bm


# ---------------------------------------------------------------------------
# Napravy (pivot v osi kolies, v strede). Sedla pruzin su AXLE_SEAT nad osou na Y = +-SPRING_Y,
# drziaky tlmicov na Y = +-0.52. Naboje sa pripajaju na priruby na koncoch.
# ---------------------------------------------------------------------------

def add_axle_mounts(bm, y_spring, y_shock, s):
    add_box(bm, (0.16, 0.12, 0.05), (0.0, s * y_spring, AXLE_SEAT - 0.025), FRAME, bev=0.006)
    add_box(bm, (0.07, 0.05, 0.05), (0.0, s * y_shock, 0.085), FRAME, bev=0.006)
    add_cylinder(bm, 0.013, 0.08, along_y((0.0, s * y_shock, 0.10)), CHROME, segments=6)


def add_flange_y(bm, y, s, r=0.10, bolts=8):
    # priruba na konci napravy (plocha na y, telo smerom k stredu)
    add_cylinder(bm, r, 0.015, along_y((0.0, y - s * 0.0075, 0.0)), STEEL, segments=12, bev=0.003)
    for k in range(bolts):
        a = 2.0 * math.pi * (k + 0.5) / bolts
        add_cylinder(bm, 0.009, 0.01, along_y((r * 0.78 * math.cos(a), y - s * 0.02, r * 0.78 * math.sin(a))), CHROME, segments=6)


def build_front_axle():
    bm = bmesh.new()
    kp = 0.84
    path = [(-kp, 0.0), (-0.60, 0.01), (0.60, 0.01), (kp, 0.0)]
    add_extruded_yz(bm, beam_outline(path, [0.05] * 4, cap=0.0), -0.045, 0.045, FRAME, bev=0.012)
    for s in SIDES_LR:
        # otocny cap, tehlica s cepom a prirubou pre naboj
        add_cylinder(bm, 0.055, 0.22, along_z((0.0, s * kp, 0.0)), FRAME, segments=10, bev=0.012)
        for z in (-0.115, 0.115):
            add_cylinder(bm, 0.035, 0.012, along_z((0.0, s * kp, z)), STEEL, segments=8)
        add_cylinder(bm, 0.06, FRONT_HUB_Y - kp, along_y((0.0, s * (kp + FRONT_HUB_Y) * 0.5, 0.0)), STEEL, segments=10)
        add_flange_y(bm, s * FRONT_HUB_Y, s)
        # riadiace rameno, brzdovy valec
        add_rod(bm, (-0.05, s * kp, -0.09), (-0.20, s * 0.76, -0.04), 0.025, FRAME, segments=6)
        add_cylinder(bm, 0.032, 0.05, along_z((-0.20, s * 0.76, -0.04)), STEEL, segments=8)
        add_box(bm, (0.10, 0.04, 0.10), (-0.07, s * 0.68, 0.08), FRAME, bev=0.008)
        add_cylinder(bm, 0.07, 0.10, along_x((-0.13, s * 0.68, 0.12)), DARK, segments=12, bev=0.012)
        # sedlo pruziny, podlozka pod strmene, drziak tlmica
        add_axle_mounts(bm, SPRING_Y, 0.52, s)
        add_box(bm, (0.16, 0.12, 0.037), (0.0, s * SPRING_Y, -0.0585), FRAME, bev=0.005)
    add_rod(bm, (-0.20, -0.76, -0.04), (-0.20, 0.76, -0.04), 0.022, STEEL, segments=8)
    return finish_mesh(bm, "SM_Naprava_riadena")


def build_differential():
    bm = bmesh.new()
    add_cylinder(bm, 0.08, 2.0 * DIFF_HALF, along_y((0.0, 0.0, 0.0)), FRAME, segments=10)
    for s in SIDES_LR:
        add_flange_y(bm, s * DIFF_HALF, s)
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
    return finish_mesh(bm, "SM_Diferencial")


def build_axle_tube():
    # rurka hnanej napravy (lava): pivot na prirube pri diferenciali, ide von (+Y) po naboj
    bm = bmesh.new()
    add_cylinder(bm, 0.075, TUBE_LEN, along_y((0.0, TUBE_LEN * 0.5, 0.0)), FRAME, segments=10)
    add_flange_y(bm, 0.0, -1.0)
    add_flange_y(bm, TUBE_LEN, 1.0)
    add_cylinder(bm, 0.09, 0.03, along_y((0.0, 0.43 - DIFF_HALF, 0.0)), FRAME, segments=10)
    s_y, sh_y, br_y = SPRING_Y - DIFF_HALF, 0.52 - DIFF_HALF, 0.66 - DIFF_HALF
    add_box(bm, (0.16, 0.12, 0.05), (0.0, s_y, AXLE_SEAT - 0.025), FRAME, bev=0.006)
    add_box(bm, (0.07, 0.05, 0.05), (0.0, sh_y, 0.085), FRAME, bev=0.006)
    add_cylinder(bm, 0.013, 0.08, along_y((0.0, sh_y, 0.10)), CHROME, segments=6)
    # brzdovy valec s pruzinovym zasobnikom (vzadu)
    add_box(bm, (0.12, 0.05, 0.06), (-0.12, br_y, 0.06), FRAME, bev=0.006)
    add_cylinder(bm, 0.075, 0.10, along_x((-0.20, br_y, 0.09)), DARK, segments=12, bev=0.012)
    add_cylinder(bm, 0.07, 0.08, along_x((-0.29, br_y, 0.09)), DARK, segments=12, bev=0.012)
    return bm


def build_hub():
    # naboj s brzdovym bubnom: pivot na prirube napravy, ide von (+Y), koleso dosadne na y = HUB_LEN
    bm = bmesh.new()
    add_cylinder(bm, 0.225, 0.012, along_y((0.0, 0.006, 0.0)), STEEL, segments=16)
    add_cylinder(bm, 0.21, 0.168, along_y((0.0, 0.096, 0.0)), FRAME, segments=16, bev=0.012)
    for y in (0.05, 0.09):
        add_cylinder(bm, 0.218, 0.014, along_y((0.0, y, 0.0)), FRAME, segments=16)
    add_cylinder(bm, 0.13, 0.02, along_y((0.0, HUB_LEN - 0.01, 0.0)), STEEL, segments=16, bev=0.004)
    return finish_mesh(bm, "SM_Naboj_bubon")


# ---------------------------------------------------------------------------
# Blatniky: pivot v strede dosky, ktora dosadne na bok ramu,
# L = vonkajsia strana +Y (lava strana auta), P = zrkadlovo (prava strana)
# ---------------------------------------------------------------------------

FENDER_R = 0.62           # vnutorny polomer blatnika
FENDER_PLATE_Z = 0.48     # doska vzpier nad stredom kolesa


def add_marker(bm, angle, y, r=0.59):
    # oranzove obrysove svetlo na vonkajsom lemu
    frame = on_arc(angle)
    add_box(bm, (0.075, 0.012, 0.045), (0.0, y + 0.006, r), CHROME, bev=0.004, frame=frame)
    add_box(bm, (0.06, 0.01, 0.032), (0.0, y + 0.014, r), LAMP_OR, bev=0.003, frame=frame)


def add_fender_stays(bm, y_edge, plate_y, angles, zc=FENDER_PLATE_Z):
    # dve vzpery z blatnika na dosku, ktora dosadne na bok ramu
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
    shift(bm, (0.0, FRONT_TRACK - RAIL_Y, -FENDER_PLATE_Z))
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
    shift(bm, (0.0, REAR_TRACK - RAIL_Y, -FENDER_PLATE_Z))
    return bm


# ---------------------------------------------------------------------------
# Vzduchojemy: pivot v strede dosky, ktora dosadne na bok ramu, nadrze idu do +Y
# ---------------------------------------------------------------------------

def build_air_tanks():
    bm = bmesh.new()
    zc, r, length = -0.24, 0.15, 0.80
    tanks = (0.20, 0.53)
    # doska na ram a dve ramena
    add_box(bm, (0.62, 0.012, 0.22), (0.0, 0.006, 0.0), FRAME, bev=0.004)
    for sx in SIDES_LR:
        for sz in SIDES_LR:
            add_cylinder(bm, 0.011, 0.01, along_y((sx * 0.26, 0.016, sz * 0.07)), CHROME, segments=6)
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
# Naves. Pri dieloch ramu navesu je z = 0 vrch hlavnych nosnikov (pod podlahou).
#   Hlavny nosnik: pivot v strede dlzky, na osi nosnika, hore
#   Obvodovy nosnik: pivot na vonkajsej strane, z = 0 (lavy; pravy = otoc o 180 st.)
#   Priecnik, podlaha, zadny priecnik: pivot v strede, z = 0
# ---------------------------------------------------------------------------

def add_i_beam(bm, length, h):
    add_box(bm, (length, 0.15, 0.02), (0.0, 0.0, -0.01), FRAME, bev=0.004)
    add_box(bm, (length, 0.012, h - 0.04), (0.0, 0.0, -h * 0.5), FRAME)
    add_box(bm, (length, 0.15, 0.02), (0.0, 0.0, -h + 0.01), FRAME, bev=0.004)


def add_stiffener(bm, x, h):
    for s in SIDES_LR:
        add_box(bm, (0.012, 0.064, h - 0.045), (x, s * 0.039, -h * 0.5), FRAME)


def build_trailer_beam(h, length, name):
    bm = bmesh.new()
    add_i_beam(bm, length, h)
    n = int(round(length / 0.5))
    for i in range(n + 1):
        x = max(min(-length * 0.5 + i * 0.5, length * 0.5 - 0.006), -length * 0.5 + 0.006)
        add_stiffener(bm, x, h)
    return finish_mesh(bm, name)


def build_trailer_transition():
    # prechod z plytkeho nosnika (vpredu, +X) na hlboky (vzadu), dlzka 1 m
    bm = bmesh.new()
    d = TR_DEEP - TR_SHALLOW
    add_box(bm, (1.0, 0.15, 0.02), (0.0, 0.0, -0.01), FRAME, bev=0.004)
    web = [(0.5, -0.02), (-0.5, -0.02), (-0.5, -TR_DEEP + 0.02), (0.5, -TR_SHALLOW + 0.02)]
    add_extruded(bm, web, -0.006, 0.006, "XZ", FRAME)
    slope = math.hypot(1.0, d)
    add_box(bm, (slope + 0.01, 0.15, 0.02), (0.0, 0.0, -(TR_SHALLOW + TR_DEEP) * 0.5 + 0.01), FRAME, bev=0.004,
            rotation=(0.0, -math.degrees(math.atan2(d, 1.0)), 0.0))
    for x in (0.494, 0.0, -0.494):
        add_stiffener(bm, x, TR_SHALLOW + (0.5 - x) * d)
    return finish_mesh(bm, "SM_Nosnik_navesu_prechod")


def build_trailer_crossmember():
    bm = bmesh.new()
    e = TR_SIDE_Y - 0.014
    profile = [(-e, 0.0), (e, 0.0), (e, -0.06), (0.6, -0.12), (-0.6, -0.12), (-e, -0.06)]
    add_extruded_yz(bm, profile, -0.035, 0.035, FRAME, bev=0.006)
    return finish_mesh(bm, "SM_Priecnik_navesu")


def build_side_rail(length):
    bm = bmesh.new()
    add_box(bm, (length, 0.012, 0.16), (0.0, -0.006, -0.04), FRAME)
    for z in (0.034, -0.114):
        add_box(bm, (length, 0.05, 0.012), (0.0, -0.025, z), FRAME, bev=0.003)
    add_box(bm, (length, 0.014, 0.03), (0.0, 0.007, -0.08), STEEL, bev=0.004)
    # vrecka na stlpiky kazdych 50 cm
    n = int(round(length / 0.5))
    for i in range(n):
        x = -length * 0.5 + 0.25 + i * 0.5
        add_box(bm, (0.07, 0.035, 0.10), (x, 0.0175, -0.015), FRAME, bev=0.005)
        add_box(bm, (0.045, 0.02, 0.004), (x, 0.0175, 0.0355), DARK)
    name = "SM_Obvodovy_nosnik_" + ("%gm" % length).replace(".", "_")
    return finish_mesh(bm, name)


def build_floor():
    # 1 m drevenej podlahy (12 dosiek), lezi na nosnikoch a priecnikoch
    bm = bmesh.new()
    for i in range(12):
        y = -1.20 + 0.10 + 0.20 * i
        add_box(bm, (0.996, 0.194, 0.04), (0.0, y, 0.02), WOOD if i % 2 == 0 else WOOD2, bev=0.006)
    return finish_mesh(bm, "SM_Podlaha_navesu_1m")


def build_kingpin_plate():
    # doska s kralovskym capom: pivot v osi capu na spodnej ploche dosky (dosadne na platnu tocne)
    bm = bmesh.new()
    add_box(bm, (1.5, 1.15, 0.012), (0.15, 0.0, 0.006), FRAME, bev=0.003)
    lip = 0.25
    add_box(bm, (lip, 1.15, 0.012), (0.90 + lip * 0.5 * math.cos(math.radians(15.0)), 0.0,
                                      0.006 + lip * 0.5 * math.sin(math.radians(15.0))), FRAME, bev=0.003,
            rotation=(0.0, -15.0, 0.0))
    for y in (-0.25, 0.0, 0.25):
        add_box(bm, (1.4, 0.012, 0.20), (0.15, y, 0.112), FRAME)
    add_box(bm, (0.012, 0.85, 0.20), (-0.20, 0.0, 0.112), FRAME)
    add_box(bm, (0.012, 0.85, 0.20), (0.50, 0.0, 0.112), FRAME)
    for i in range(7):
        x = -0.60 + 0.06 + i * 0.235
        for s in SIDES_LR:
            add_cylinder(bm, 0.01, 0.008, along_z((x, s * 0.40, 0.016)), CHROME, segments=6)
    add_cylinder(bm, 0.026, 0.085, along_z((0.0, 0.0, -0.0425)), CHROME, segments=10)
    add_cylinder(bm, 0.033, 0.018, along_z((0.0, 0.0, -0.062)), CHROME, segments=10)
    return finish_mesh(bm, "SM_Kralovsky_cap_navesu")


# ---------------------------------------------------------------------------
# Podvozok navesu. Pivot podpier a perovania je na spodku hlbokeho nosnika (z = 0).
# ---------------------------------------------------------------------------

def build_landing_gear():
    bm = bmesh.new()
    for s in SIDES_LR:
        y = s * TR_BEAM_Y
        add_box(bm, (0.30, 0.20, 0.02), (0.0, y, -0.01), FRAME, bev=0.004)
        for dx in (-0.11, 0.11):
            for dy in (-0.07, 0.07):
                add_cylinder(bm, 0.012, 0.012, along_z((dx, y + dy, -0.024)), CHROME, segments=6)
        add_box(bm, (0.12, 0.12, 0.60), (0.0, y, -0.32), FRAME, bev=0.012)
        foot = TR_AXLE_DROP + WHEEL_R          # spodok patky je na zemi
        add_box(bm, (0.09, 0.09, foot - 0.64), (0.0, y, -(0.60 + foot - 0.04) * 0.5), STEEL, bev=0.008)
        add_box(bm, (0.26, 0.22, 0.04), (0.0, y, -foot + 0.02), FRAME, bev=0.01)
        add_rod(bm, (0.0, y, -0.45), (0.55, y, -0.02), 0.02, FRAME, segments=6)
        add_box(bm, (0.12, 0.12, 0.02), (0.55, y, -0.01), FRAME, bev=0.004)
    for s in SIDES_LR:
        add_rod(bm, (0.0, -0.44 * s, -0.50), (0.0, 0.44 * s, -0.08), 0.018, FRAME, segments=6)
    add_rod(bm, (0.0, -0.44, -0.22), (0.0, 0.44, -0.22), 0.02, STEEL, segments=8)
    # prevodovka podpier s prilozenou klukou (lava strana)
    add_box(bm, (0.14, 0.10, 0.16), (0.0, TR_BEAM_Y + 0.11, -0.22), FRAME, bev=0.012)
    add_cylinder(bm, 0.02, 0.05, along_y((0.0, TR_BEAM_Y + 0.185, -0.25)), STEEL, segments=8)
    add_rod(bm, (0.0, TR_BEAM_Y + 0.21, -0.25), (0.0, TR_BEAM_Y + 0.21, -0.50), 0.012, STEEL, segments=6)
    add_cylinder(bm, 0.02, 0.08, along_y((0.0, TR_BEAM_Y + 0.25, -0.50)), DARK, segments=8)
    return finish_mesh(bm, "SM_Podpery_navesu")


def build_suspension_arm():
    # zaves + vlecene rameno + strmene + tlmic (bez vankusa); os napravy je TR_AXLE_DROP pod pivotom
    bm = bmesh.new()
    za = -TR_AXLE_DROP
    for d in SIDES_LR:
        add_box(bm, (0.16, 0.012, 0.44), (0.50, d * 0.062, -0.22), FRAME, bev=0.004)
    add_box(bm, (0.26, 0.16, 0.02), (0.50, 0.0, -0.01), FRAME, bev=0.004)
    add_box(bm, (0.012, 0.136, 0.30), (0.58, 0.0, -0.16), FRAME)
    add_cylinder(bm, 0.045, 0.11, along_y((0.50, 0.0, -0.40)), DARK, segments=10)
    add_cylinder(bm, 0.015, 0.16, along_y((0.50, 0.0, -0.40)), CHROME, segments=6)
    path = [(0.50, -0.40), (0.22, -0.60), (0.0, za - 0.121), (BAG_X, -0.60)]
    add_extruded(bm, beam_outline(path, [0.045, 0.045, 0.045, 0.04], cap=0.5), -0.05, 0.05, "XZ", FRAME, bev=0.008)
    add_box(bm, (0.24, 0.16, 0.012), (BAG_X, 0.0, -BAG_H - 0.006), STEEL, bev=0.003)   # sedlo vankusa
    # strmene napravy
    z_top = za + 0.075
    add_box(bm, (0.24, 0.155, 0.025), (0.0, 0.0, z_top + 0.0125), STEEL, bev=0.005)
    add_box(bm, (0.24, 0.155, 0.02), (0.0, 0.0, -0.75), STEEL, bev=0.005)
    for sx in SIDES_LR:
        for sy in SIDES_LR:
            add_cylinder(bm, 0.011, z_top + 0.75 + 0.05, along_z((sx * 0.09, sy * 0.066, (z_top - 0.75) * 0.5)), STEEL, segments=6)
            add_cylinder(bm, 0.018, 0.02, along_z((sx * 0.09, sy * 0.066, -0.77)), CHROME, segments=6)
    # tlmic
    up, low = Vector((0.42, 0.085, -0.12)), Vector((0.10, 0.085, za - 0.08))
    add_box(bm, (0.06, 0.03, 0.06), (0.45, 0.08, -0.12), FRAME, bev=0.005)
    add_rod(bm, low, low.lerp(up, 0.55), 0.03, DARK, segments=8)
    add_rod(bm, low.lerp(up, 0.55), up, 0.013, CHROME, segments=6)
    add_cylinder(bm, 0.013, 0.07, along_y((low.x, 0.085, low.z)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Rameno_perovania")


BAG_X = -0.32          # vankus je za osou napravy
BAG_H = 0.548          # vyska vankusa (od spodku nosnika po sedlo na ramene)


def build_air_bag():
    # vzduchovy vankus: pivot hore v strede (pod nosnikom), spodok dosadne na sedlo ramena
    bm = bmesh.new()
    add_box(bm, (0.30, 0.20, 0.02), (0.0, 0.0, -0.01), STEEL, bev=0.004)
    for sx in SIDES_LR:
        add_cylinder(bm, 0.012, 0.012, along_z((sx * 0.12, 0.0, -0.026)), CHROME, segments=6)
    add_cylinder(bm, 0.14, 0.035, along_z((0.0, 0.0, -0.0375)), GREY, segments=12, bev=0.008)
    add_cylinder(bm, 0.155, 0.17, along_z((0.0, 0.0, -0.14)), TIRE, segments=12, bev=0.045)
    add_cylinder(bm, 0.142, 0.02, along_z((0.0, 0.0, -0.228)), DARK, segments=12)
    add_cylinder(bm, 0.148, 0.16, along_z((0.0, 0.0, -0.315)), TIRE, segments=12, bev=0.045)
    add_cylinder(bm, 0.105, 0.13, along_z((0.0, 0.0, -0.455)), GREY, segments=12, bev=0.01)
    add_cylinder(bm, 0.112, 0.02, along_z((0.0, 0.0, -0.40)), STEEL, segments=12)
    add_box(bm, (0.22, 0.16, 0.028), (0.0, 0.0, -BAG_H + 0.014), STEEL, bev=0.004)
    # pripojka vzduchu
    add_cylinder(bm, 0.015, 0.03, along_z((0.08, 0.04, -0.04)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Vzduchovy_vankus")


def build_trailer_light_bumper():
    # zadny naraznik so svetlami (ako na fotke): pivot hore v strede (spodok hlbokych nosnikov)
    bm = bmesh.new()
    zb, half = -0.30, TR_SIDE_Y
    add_box(bm, (0.12, 2.0 * half, 0.16), (-0.04, 0.0, zb), GREY, bev=0.02)
    xr = -0.10
    for s in SIDES_LR:
        y = s * TR_BEAM_Y
        add_box(bm, (0.20, 0.16, 0.015), (0.0, y, -0.0075), FRAME, bev=0.003)
        add_box(bm, (0.08, 0.10, -zb - 0.08), (0.0, y, (zb + 0.08) * 0.5), FRAME, bev=0.008)
        # svetla na zadnej ploche: oranzove (smerovka) von, cervene, biele (cuvacie) dnu
        add_box(bm, (0.008, 0.40, 0.12), (xr - 0.002, s * 1.02, zb), DARK)
        for yy, width, mat in ((1.17, 0.08, LAMP_OR), (1.02, 0.20, LAMP_RED), (0.87, 0.08, LAMP_WHITE)):
            add_box(bm, (0.01, width - 0.008, 0.10), (xr - 0.007, s * yy, zb), mat, bev=0.003)
        # obrysove svetlo na drziaku na konci
        add_rod(bm, (-0.04, s * (half - 0.02), zb + 0.03), (-0.04, s * (half + 0.08), zb + 0.03), 0.008, CHROME)
        add_box(bm, (0.035, 0.03, 0.025), (-0.04, s * (half + 0.095), zb + 0.03), LAMP_OR, bev=0.005)
        # sikma vzpera k nosniku
        add_rod(bm, (-0.04, s * 0.80, zb + 0.08), (0.22, s * 0.55, -0.02), 0.018, GREY, segments=8)
        add_box(bm, (0.10, 0.08, 0.012), (0.22, s * 0.55, -0.006), FRAME, bev=0.003)
    # drziak SPZ s osvetlenim
    add_box(bm, (0.01, 0.52, 0.11), (xr - 0.004, 0.0, zb), WHITE, bev=0.003)
    add_box(bm, (0.03, 0.10, 0.03), (xr - 0.015, 0.0, zb + 0.07), DARK, bev=0.004)
    return finish_mesh(bm, "SM_Naraznik_navesu_svetla")


def build_trailer_axle():
    bm = bmesh.new()
    add_cylinder(bm, 0.075, 2.0 * REAR_HUB_Y, along_y((0.0, 0.0, 0.0)), FRAME, segments=10)
    for s in SIDES_LR:
        add_flange_y(bm, s * REAR_HUB_Y, s)
        y = s * 0.66
        add_box(bm, (0.10, 0.05, 0.06), (-0.11, y, 0.05), FRAME, bev=0.006)
        add_cylinder(bm, 0.065, 0.09, along_x((-0.17, y, 0.09)), DARK, segments=12, bev=0.012)
        add_cylinder(bm, 0.06, 0.07, along_x((-0.25, y, 0.09)), DARK, segments=12, bev=0.012)
        add_cylinder(bm, 0.09, 0.025, along_y((0.0, s * 0.30, 0.0)), FRAME, segments=10)
    return finish_mesh(bm, "SM_Naprava_navesu")


# ---------------------------------------------------------------------------
# Prislusenstvo navesu
# ---------------------------------------------------------------------------

def build_trailer_fender():
    # plochy blatnik nad dvojmontazou: pivot hore v strede (dosadne pod naves), drziaky na vnutornej strane (-Y)
    bm = bmesh.new()
    add_box(bm, (0.90, 0.70, 0.012), (0.0, 0.0, -0.30), PLASTIC, bev=0.004)
    ang = math.degrees(math.atan2(0.15, 0.20))
    for s in SIDES_LR:
        add_box(bm, (0.255, 0.70, 0.012), (s * 0.55, 0.0, -0.375), PLASTIC, bev=0.004, rotation=(0.0, s * ang, 0.0))
    add_box(bm, (0.90, 0.012, 0.05), (0.0, 0.35, -0.325), PLASTIC, bev=0.004)
    for x in (-0.30, 0.30):
        add_box(bm, (0.04, 0.04, 0.30), (x, -0.30, -0.15), STEEL, bev=0.006)
        add_box(bm, (0.10, 0.08, 0.012), (x, -0.30, -0.006), STEEL, bev=0.003)
    return finish_mesh(bm, "SM_Blatnik_navesu")


def build_trailer_bumper():
    # zadna zabrana proti podbehnutiu: pivot hore v strede (spodok hlbokych nosnikov)
    bm = bmesh.new()
    for s in SIDES_LR:
        y = s * TR_BEAM_Y
        add_box(bm, (0.20, 0.16, 0.015), (0.0, y, -0.0075), FRAME, bev=0.003)
        add_box(bm, (0.08, 0.10, 0.64), (0.0, y, -0.32), FRAME, bev=0.008)
        add_rod(bm, (0.0, y, -0.55), (0.45, y, -0.02), 0.02, FRAME, segments=6)
        add_box(bm, (0.12, 0.12, 0.015), (0.45, y, -0.0075), FRAME, bev=0.003)
    add_box(bm, (0.12, 2.40, 0.14), (-0.02, 0.0, -0.64), FRAME, bev=0.012)
    for i in range(8):
        add_box(bm, (0.008, 0.30, 0.10), (-0.084, -1.05 + 0.30 * i, -0.64), RED if i % 2 == 0 else WHITE)
    return finish_mesh(bm, "SM_Naraznik_navesu")


def build_trailer_rear_sill():
    # zadny priecnik navesu: pivot hore v strede na konci nosnikov (x = 0), ide dozadu (-X)
    bm = bmesh.new()
    add_box(bm, (0.10, 2.0 * TR_SIDE_Y, 0.20), (-0.05, 0.0, -0.06), FRAME, bev=0.01)
    for i in range(9):
        add_cylinder(bm, 0.01, 0.01, along_x((-0.103, -1.0 + 0.25 * i, 0.0)), CHROME, segments=6)
    add_box(bm, (0.03, 0.10, 0.04), (-0.115, 0.0, -0.13), DARK, bev=0.005)
    add_box(bm, (0.006, 0.07, 0.015), (-0.13, 0.0, -0.13), LAMP_WHITE)
    return finish_mesh(bm, "SM_Zadny_priecnik_navesu")


def build_trailer_light():
    # zadne svetlo (lave): pivot na prednej ploche, ktora dosadne na zadny priecnik, ide dozadu (-X)
    bm = bmesh.new()
    add_box(bm, (0.06, 0.42, 0.12), (-0.03, 0.0, 0.0), DARK, bev=0.01)
    for y, width, mat in ((0.12, 0.14, LAMP_RED), (-0.02, 0.10, LAMP_OR), (-0.14, 0.08, LAMP_WHITE)):
        add_box(bm, (0.014, width, 0.08), (-0.064, y, 0.0), mat, bev=0.004)
    add_box(bm, (0.008, 0.06, 0.02), (-0.064, 0.12, -0.05), RED)
    return bm


def build_side_guard():
    # bocna zabrana 2 m: pivot hore v strede na vonkajsej strane (pod obvodovym nosnikom)
    bm = bmesh.new()
    for z in (-0.45, -0.85):
        add_box(bm, (2.0, 0.03, 0.10), (0.0, -0.015, z), STEEL, bev=0.008)
    for x in (-0.80, 0.80):
        add_box(bm, (0.05, 0.04, 0.90), (x, -0.05, -0.45), FRAME, bev=0.006)
        add_box(bm, (0.12, 0.10, 0.012), (x, -0.05, -0.006), FRAME, bev=0.003)
    return finish_mesh(bm, "SM_Bocna_zabrana_2m")


# ---------------------------------------------------------------------------
# Naves na drevo (klanicovy). Pouziva rovnake hlavne nosniky, napravy a kolesa ako plochy naves.
#   Lavica, celo: pivot v strede dole (z = 0 = vrch hlavnych nosnikov), dosadnu navrch nosnikov
#   Klanica: pivot v strede pata klanice na vrchu lavice (vystuha smeruje dnu; pravu otoc o 180 st.)
#   Uzky priecnik: pivot v strede hore (z = 0), vojde medzi hlavne nosniky
#   Oblukovy blatnik: pivot v strede dosky, ktora dosadne na stojinu hlavneho nosnika
# ---------------------------------------------------------------------------

STAKE_Y = TR_SIDE_Y - 0.07     # os klanice od stredu
BUNK_H = 0.14                  # vyska lavice (klanica stoji na jej vrchu)
TR_FENDER_Z = TR_AXLE_DROP + TR_DEEP - 0.30   # doska oblukoveho blatnika nad osou kolesa


def add_beam_clamps(bm, x=0.0):
    # uchyty lavice/cela na hornu pasnicu hlavnych nosnikov
    for s in SIDES_LR:
        for d in SIDES_LR:
            y = s * TR_BEAM_Y + d * 0.082
            add_box(bm, (0.20, 0.012, 0.08), (x, y, -0.03), FRAME, bev=0.003)
            for dx in (-0.06, 0.06):
                add_bolt_y(bm, x + dx, y + d * 0.006, -0.045, d)


def build_log_bunk():
    bm = bmesh.new()
    add_box(bm, (0.16, 2.0 * TR_SIDE_Y - 0.02, BUNK_H), (0.0, 0.0, BUNK_H * 0.5), FRAME, bev=0.012)
    add_box(bm, (0.17, 2.0 * STAKE_Y - 0.30, 0.012), (0.0, 0.0, BUNK_H + 0.004), STEEL, bev=0.003)
    for s in SIDES_LR:
        add_box(bm, (0.19, 0.17, BUNK_H + 0.01), (0.0, s * STAKE_Y, BUNK_H * 0.5), FRAME, bev=0.012)
        add_box(bm, (0.11, 0.11, 0.006), (0.0, s * STAKE_Y, BUNK_H + 0.006), DARK)
    add_beam_clamps(bm)
    return finish_mesh(bm, "SM_Lavica_klanicova")


def build_stake(height, name):
    bm = bmesh.new()
    top = 0.14
    add_box(bm, (0.10, 0.10, height - top), (0.0, 0.0, (height - top) * 0.5), FRAME, bev=0.01)
    add_box(bm, (0.085, 0.085, top), (0.0, 0.0, height - top * 0.5), FRAME, bev=0.025)
    add_box(bm, (0.14, 0.14, 0.03), (0.0, 0.0, 0.015), STEEL, bev=0.006)
    # koleno: dve vystuhy dnu (-Y) a patka na lavici
    for x in (-0.035, 0.035):
        add_extruded_yz(bm, [(-0.05, 0.03), (-0.05, 0.48), (-0.36, 0.03)], x - 0.006, x + 0.006, FRAME, bev=0.003)
    add_box(bm, (0.10, 0.32, 0.014), (0.0, -0.20, 0.007), STEEL, bev=0.003)
    for y in (-0.16, -0.30):
        add_cylinder(bm, 0.011, 0.01, along_z((0.0, y, 0.018)), CHROME, segments=6)
    return finish_mesh(bm, name)


def build_headboard():
    # celo navesu: plech vpredu (+X), vzpery dozadu na hlavne nosniky
    bm = bmesh.new()
    h = 2.2
    half = TR_SIDE_Y
    add_box(bm, (0.16, 2.0 * half, BUNK_H), (0.0, 0.0, BUNK_H * 0.5), FRAME, bev=0.012)
    add_box(bm, (0.12, 2.0 * half, 0.12), (0.0, 0.0, h - 0.06), FRAME, bev=0.012)
    post_h = h - 0.12 - BUNK_H
    for y in (-(half - 0.06), 0.0, half - 0.06):
        add_box(bm, (0.12 if y else 0.08, 0.12 if y else 0.08, post_h), (0.0, y, BUNK_H + post_h * 0.5), FRAME, bev=0.012)
    add_box(bm, (0.012, 2.0 * half - 0.22, post_h), (0.054, 0.0, BUNK_H + post_h * 0.5), FRAME, bev=0.003)
    for z in (0.75, 1.35, 1.85):
        add_box(bm, (0.06, 2.0 * half - 0.24, 0.05), (-0.02, 0.0, z), FRAME, bev=0.006)
    for s in SIDES_LR:
        # zrazene horne rohy
        add_extruded_yz(bm, [(s * (half - 0.12), h - 0.12), (s * (half - 0.12), h - 0.40), (s * (half - 0.40), h - 0.12)],
                        -0.05, 0.05, FRAME, bev=0.004)
        add_rod(bm, (-0.06, s * TR_BEAM_Y, 1.55), (-0.85, s * TR_BEAM_Y, 0.03), 0.04, FRAME, segments=8)
        add_box(bm, (0.22, 0.16, 0.03), (-0.85, s * TR_BEAM_Y, 0.015), FRAME, bev=0.006)
        add_box(bm, (0.012, 0.10, 0.12), (-0.08, s * TR_BEAM_Y, 1.55), FRAME, bev=0.003)
    add_beam_clamps(bm)
    return finish_mesh(bm, "SM_Celo_navesu")


def build_narrow_crossmember():
    bm = bmesh.new()
    w = 2.0 * (TR_BEAM_Y - 0.006)
    for z in (-0.046, -0.154):
        add_box(bm, (0.08, w, 0.012), (0.0, 0.0, z), FRAME, bev=0.003)
    add_box(bm, (0.012, w, 0.10), (0.0, 0.0, -0.10), FRAME)
    for s in SIDES_LR:
        add_box(bm, (0.16, 0.01, 0.12), (0.0, s * (TR_BEAM_Y - 0.011), -0.10), FRAME, bev=0.003)
        for dx in (-0.05, 0.05):
            for dz in (-0.07, -0.13):
                add_bolt_y(bm, dx, s * (TR_BEAM_Y + 0.006), dz, s)
    return finish_mesh(bm, "SM_Priecnik_navesu_uzky")


def build_trailer_arch_fender(mudflap):
    # oblukovy blatnik nad dvojmontazou navesu (lavy), doska na stojine hlavneho nosnika
    bm = bmesh.new()
    half_w = 0.345
    fender_shell(bm, half_w, 15.0, 165.0, 8, (-0.14, 0.14))
    plate_y = -(REAR_TRACK - (TR_BEAM_Y + 0.006))
    add_fender_stays(bm, -0.30, plate_y, (60.0, 120.0), TR_FENDER_Z)
    if mudflap:
        xb = (FENDER_R + 0.012) * math.cos(math.radians(165.0))
        add_box(bm, (0.035, 0.68, 0.035), (xb, 0.0, 0.15), STEEL, bev=0.006)
        add_box(bm, (0.012, 0.64, 0.56), (xb, 0.0, -0.14), TIRE, bev=0.004)
        for y in (-0.2, 0.0, 0.2):
            add_box(bm, (0.016, 0.16, 0.012), (xb - 0.002, y, -0.36), TIRE, bev=0.003)
        for s in SIDES_LR:
            add_box(bm, (0.008, 0.10, 0.04), (xb - 0.008, s * 0.20, -0.28), RED, bev=0.003)
    shift(bm, (0.0, -plate_y, -TR_FENDER_Z))
    return bm


# ---------------------------------------------------------------------------
# Scena: katalog dielov s menovkami + ukazka poskladaneho tahaca s navesom, export
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


def add_spin(obj, index, expression):
    fcurve = obj.driver_add("rotation_euler", index)
    fcurve.driver.type = "SCRIPTED"
    fcurve.driver.expression = expression


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
        if mesh.users == 0 and mesh.get("stavebnica_kamion"):
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


WHEEL_SPIN = "frame * 0.06"
SHAFT_SPIN = "frame * 0.21"
SPINS = {"Koleso": (1, WHEEL_SPIN), "Koleso_dvojite": (1, WHEEL_SPIN),
         "Kardan_1m": (0, SHAFT_SPIN), "Kardan_1_5m": (0, SHAFT_SPIN), "Kardan_2m": (0, SHAFT_SPIN)}


def build_parts():
    parts = {}

    def put(mesh):
        parts[mesh.name[3:]] = mesh

    def put_lr(bm, name):
        mirrored = mirror_y(bm)
        put(finish_mesh(bm, name + "_L"))
        put(finish_mesh(mirrored, name + "_P"))

    for length in (0.5, 1.0, 2.0):
        put(build_rail(length))
    put(build_crossmember())
    put(build_front_crossmember())
    put(build_rear_crossmember())
    put(build_leaf_spring("SM_Pruzina_listova", 0.70, 4, -0.08))
    put(build_leaf_spring("SM_Pruzina_listova_tazka", 0.75, 6, -0.06))
    put_lr(build_shock(), "SM_Tlmic")
    put(build_front_axle())
    put(build_differential())
    put_lr(build_axle_tube(), "SM_Rurka_napravy")
    put(build_hub())
    put(build_wheel_front())
    put(build_wheel_dual())
    for length, tag in ((1.0, "1m"), (1.5, "1_5m"), (2.0, "2m")):
        put(build_kardan("SM_Kardan_" + tag, length))
    put(build_fifth_wheel())
    put(build_air_tanks())
    for builder, name in ((build_front_fender, "SM_Blatnik_predny"), (build_rear_fender, "SM_Blatnik_zadny")):
        put_lr(builder(False), name)
        put_lr(builder(True), name + "_svetla")
    for h, kind in ((TR_SHALLOW, "plytky"), (TR_DEEP, "hlboky")):
        for length in (1.0, 2.0):
            put(build_trailer_beam(h, length, "SM_Nosnik_navesu_%s_%dm" % (kind, length)))
    put(build_trailer_transition())
    put(build_trailer_crossmember())
    for length in (1.0, 2.0):
        put(build_side_rail(length))
    put(build_floor())
    put(build_trailer_rear_sill())
    put(build_kingpin_plate())
    put(build_landing_gear())
    put(build_suspension_arm())
    put(build_air_bag())
    put(build_trailer_axle())
    put(build_trailer_fender())
    put(build_trailer_bumper())
    put(build_trailer_light_bumper())
    put_lr(build_trailer_light(), "SM_Zadne_svetlo_navesu")
    put(build_side_guard())
    put(build_log_bunk())
    put(build_stake(1.5, "SM_Klanica_1_5m"))
    put(build_stake(2.0, "SM_Klanica_2m"))
    put(build_headboard())
    put(build_narrow_crossmember())
    put_lr(build_trailer_arch_fender(False), "SM_Blatnik_navesu_oblukovy")
    put_lr(build_trailer_arch_fender(True), "SM_Blatnik_navesu_oblukovy_zasterka")
    return parts


CATALOG = [
    ("RAM TAHACA", ["Nosnik_ramu_0_5m", "Nosnik_ramu_1m", "Nosnik_ramu_2m", "Priecnik_ramu", "Priecnik_predny",
                    "Priecnik_zadny"]),
    ("PEROVANIE A NAPRAVY", ["Pruzina_listova", "Pruzina_listova_tazka", "Tlmic_L", "Tlmic_P", "Naprava_riadena",
                             "Diferencial", "Rurka_napravy_L", "Rurka_napravy_P", "Naboj_bubon"]),
    ("KOLESA, KARDAN, TOCNA", ["Koleso", "Koleso_dvojite", "Kardan_1m", "Kardan_1_5m", "Kardan_2m", "Tocna",
                               "Vzduchojemy"]),
    ("BLATNIKY", ["Blatnik_predny_L", "Blatnik_predny_P", "Blatnik_predny_svetla_L", "Blatnik_predny_svetla_P",
                  "Blatnik_zadny_L", "Blatnik_zadny_P", "Blatnik_zadny_svetla_L", "Blatnik_zadny_svetla_P"]),
    ("NAVES - RAM", ["Nosnik_navesu_plytky_1m", "Nosnik_navesu_plytky_2m", "Nosnik_navesu_prechod",
                     "Nosnik_navesu_hlboky_1m", "Nosnik_navesu_hlboky_2m", "Priecnik_navesu", "Obvodovy_nosnik_1m",
                     "Obvodovy_nosnik_2m", "Podlaha_navesu_1m", "Zadny_priecnik_navesu", "Kralovsky_cap_navesu"]),
    ("NAVES - PODVOZOK A DOPLNKY", ["Podpery_navesu", "Rameno_perovania", "Vzduchovy_vankus", "Naprava_navesu",
                                    "Blatnik_navesu", "Naraznik_navesu", "Naraznik_navesu_svetla",
                                    "Zadne_svetlo_navesu_L", "Zadne_svetlo_navesu_P", "Bocna_zabrana_2m"]),
    ("NAVES NA DREVO", ["Lavica_klanicova", "Klanica_1_5m", "Klanica_2m", "Celo_navesu", "Priecnik_navesu_uzky",
                        "Blatnik_navesu_oblukovy_L", "Blatnik_navesu_oblukovy_P", "Blatnik_navesu_oblukovy_zasterka_L",
                        "Blatnik_navesu_oblukovy_zasterka_P"]),
]


def demo_layout():
    # ukazka: zoznam (diel, poloha, otocenie okolo Z v stupnoch, tocenie)
    items = []
    fz = FRAME_Z

    def add(key, loc, rot_z=0.0, spin=None, rot_y=0.0):
        items.append((key, loc, (0.0, rot_y, rot_z), spin))

    # ram tahaca 5.5 m: nosniky 2 + 2 + 1 + 0.5 m
    for length, x in ((2.0, 1.75), (2.0, -0.25), (1.0, -1.75), (0.5, -2.50)):
        key = "Nosnik_ramu_" + ("%gm" % length).replace(".", "_")
        add(key, (x, RAIL_Y, fz))
        add(key, (x, -RAIL_Y, fz), 180.0)
    for x in (1.30, 0.20, -0.80, -1.95):
        add("Priecnik_ramu", (x, 0.0, fz))
    add("Priecnik_predny", (2.75, 0.0, fz))
    add("Priecnik_zadny", (-2.75, 0.0, fz))

    # napravy, perovanie, naboje, kolesa
    fx, rx, az = 1.95, -1.55, fz - HANG
    for x, spring in ((fx, "Pruzina_listova"), (rx, "Pruzina_listova_tazka")):
        for s in SIDES_LR:
            add(spring, (x, s * SPRING_Y, fz))
        add("Tlmic_L", (x - 0.25, RAIL_Y, fz + 0.13))
        add("Tlmic_P", (x - 0.25, -RAIL_Y, fz + 0.13))
    add("Naprava_riadena", (fx, 0.0, az))
    add("Diferencial", (rx, 0.0, az))
    add("Rurka_napravy_L", (rx, DIFF_HALF, az))
    add("Rurka_napravy_P", (rx, -DIFF_HALF, az))
    for x, hub_y, wheel in ((fx, FRONT_HUB_Y, "Koleso"), (rx, REAR_HUB_Y, "Koleso_dvojite")):
        add("Naboj_bubon", (x, hub_y, az))
        add("Naboj_bubon", (x, -hub_y, az), 180.0)
        add(wheel, (x, hub_y + HUB_LEN, az), 0.0, (1, WHEEL_SPIN))
        add(wheel, (x, -(hub_y + HUB_LEN), az), 180.0, (1, "-" + WHEEL_SPIN))
    plate_z = WHEEL_R + FENDER_PLATE_Z
    add("Blatnik_predny_L", (fx, RAIL_Y, plate_z))
    add("Blatnik_predny_P", (fx, -RAIL_Y, plate_z))
    add("Blatnik_zadny_svetla_L", (rx, RAIL_Y, plate_z))
    add("Blatnik_zadny_svetla_P", (rx, -RAIL_Y, plate_z))
    add("Vzduchojemy", (0.0, -RAIL_Y, fz + 0.13), 180.0)

    # kardan od diferencialu dopredu (mierne sklopeny)
    pinion = Vector((rx + 0.40, 0.0, az))
    tilt = math.asin((0.70 - pinion.z) / 2.0)
    add("Kardan_2m", (pinion.x + 2.0 * math.cos(tilt), 0.0, 0.70), 0.0, (0, SHAFT_SPIN), -math.degrees(tilt))

    # tocna na rame a naves (kralovsky cap v zamku tocne)
    tocna = Vector((-1.25, 0.0, fz + RAIL_H))
    add("Tocna", tuple(tocna))
    kp = tocna + Vector((-0.03, 0.0, 0.23))
    deck = kp.z + KINGPIN_DECK
    deep = deck - TR_DEEP

    def tx(x):
        return kp.x + x

    add("Kralovsky_cap_navesu", tuple(kp))
    beams = (("plytky_2m", -0.1), ("plytky_1m", -1.6), ("prechod", -2.6),
             ("hlboky_2m", -4.1), ("hlboky_2m", -6.1), ("hlboky_2m", -8.1), ("hlboky_2m", -10.1))
    for kind, x in beams:
        for s in SIDES_LR:
            add("Nosnik_navesu_" + kind, (tx(x), s * TR_BEAM_Y, deck))
    for i in range(24):
        add("Priecnik_navesu", (tx(0.75 - 0.5 * i), 0.0, deck))
    for x in (-0.1, -2.1, -4.1, -6.1, -8.1, -10.1):
        add("Obvodovy_nosnik_2m", (tx(x), TR_SIDE_Y, deck))
        add("Obvodovy_nosnik_2m", (tx(x), -TR_SIDE_Y, deck), 180.0)
    for i in range(12):
        add("Podlaha_navesu_1m", (tx(0.4 - i), 0.0, deck))
    add("Zadny_priecnik_navesu", (tx(-11.1), 0.0, deck))
    add("Zadne_svetlo_navesu_L", (tx(-11.2), 1.0, deck - 0.06))
    add("Zadne_svetlo_navesu_P", (tx(-11.2), -1.0, deck - 0.06))
    add("Naraznik_navesu", (tx(-10.95), 0.0, deep))
    add("Podpery_navesu", (tx(-3.6), 0.0, deep))
    for x in (-4.9, -6.9):
        add("Bocna_zabrana_2m", (tx(x), TR_SIDE_Y, deck - 0.12))
        add("Bocna_zabrana_2m", (tx(x), -TR_SIDE_Y, deck - 0.12), 180.0)
    for x in (-8.6, -9.91):
        ax = tx(x)
        for s in SIDES_LR:
            add("Rameno_perovania", (ax, s * TR_BEAM_Y, deep))
            add("Vzduchovy_vankus", (ax + BAG_X, s * TR_BEAM_Y, deep))
        add("Naprava_navesu", (ax, 0.0, WHEEL_R))
        add("Naboj_bubon", (ax, REAR_HUB_Y, WHEEL_R))
        add("Naboj_bubon", (ax, -REAR_HUB_Y, WHEEL_R), 180.0)
        add("Koleso_dvojite", (ax, REAR_HUB_Y + HUB_LEN, WHEEL_R), 0.0, (1, WHEEL_SPIN))
        add("Koleso_dvojite", (ax, -(REAR_HUB_Y + HUB_LEN), WHEEL_R), 180.0, (1, "-" + WHEEL_SPIN))
        add("Blatnik_navesu", (ax, REAR_TRACK, deck - 0.09))
        add("Blatnik_navesu", (ax, -REAR_TRACK, deck - 0.09), 180.0)

    # naves na drevo vedla (stoji na podperach), rovnaky ram 12 m
    oy = -5.0
    kp2 = Vector((kp.x, oy, kp.z))

    def lx(x):
        return kp2.x + x

    add("Kralovsky_cap_navesu", tuple(kp2))
    for kind, x in beams:
        for s in SIDES_LR:
            add("Nosnik_navesu_" + kind, (lx(x), oy + s * TR_BEAM_Y, deck))
    for i in range(11):
        add("Priecnik_navesu_uzky", (lx(-1.0 - i), oy, deck))
    add("Celo_navesu", (lx(0.55), oy, deck))
    for x in (-1.3, -3.3, -5.3, -7.3, -9.3, -10.95):
        add("Lavica_klanicova", (lx(x), oy, deck))
        add("Klanica_2m", (lx(x), oy + STAKE_Y, deck + BUNK_H))
        add("Klanica_2m", (lx(x), oy - STAKE_Y, deck + BUNK_H), 180.0)
    add("Podpery_navesu", (lx(-3.6), oy, deep))
    for x, fender in ((-8.6, "Blatnik_navesu_oblukovy"), (-9.91, "Blatnik_navesu_oblukovy_zasterka")):
        ax = lx(x)
        for s in SIDES_LR:
            add("Rameno_perovania", (ax, oy + s * TR_BEAM_Y, deep))
            add("Vzduchovy_vankus", (ax + BAG_X, oy + s * TR_BEAM_Y, deep))
        add("Naprava_navesu", (ax, oy, WHEEL_R))
        add("Naboj_bubon", (ax, oy + REAR_HUB_Y, WHEEL_R))
        add("Naboj_bubon", (ax, oy - REAR_HUB_Y, WHEEL_R), 180.0)
        add("Koleso_dvojite", (ax, oy + REAR_HUB_Y + HUB_LEN, WHEEL_R), 0.0, (1, WHEEL_SPIN))
        add("Koleso_dvojite", (ax, oy - (REAR_HUB_Y + HUB_LEN), WHEEL_R), 180.0, (1, "-" + WHEEL_SPIN))
        plate = TR_BEAM_Y + 0.006
        add(fender + "_L", (ax, oy + plate, WHEEL_R + TR_FENDER_Z))
        add(fender + "_P", (ax, oy - plate, WHEEL_R + TR_FENDER_Z))
    add("Naraznik_navesu_svetla", (lx(-11.06), oy, deep))
    return items


RULES = """
PRAVIDLA SKLADANIA (predok = +X, lava strana = +Y, rozmery v metroch)
Kazdy diel ma pivot v bode, kde sa prichyti. Diely _L idu na lavu stranu, _P na pravu.
Diely bez _L/_P, ktore maju vonkajsiu stranu (+Y), na pravu stranu otoc o 180 st. okolo Z.

TAHAC
  Nosnik_ramu_*: pivot = stred dlzky, vonkajsia strana, spodok. Lavy na y = +{ry}, pravy na y = -{ry} (otoc 180).
                 Nosniky sa daju za seba (konce maju polovice spojovacich plechov). Vyska {rh}.
  Priecnik_ramu: pivot = stred, spodok ramu. Priecnik_predny / _zadny: pivot = koniec nosnikov, spodok ramu.
  Pruzina_listova (_tazka): pivot = stred pruziny na spodku ramu, y = +-{sy}. Sedlo napravy je {seat} pod nim.
  Naprava_riadena, Diferencial: pivot = os kolies v strede, {hang} pod spodkom ramu (rovno pod pruzinami).
  Rurka_napravy_L/P: pivot = priruba diferencialu, y = +-{dh}. Konci na y = +-{rhy} (tam ide naboj).
  Tlmic_L/P: pivot = doska na boku ramu, {sx} za osou napravy, 0.13 nad spodkom ramu.
  Naboj_bubon: pivot = priruba napravy (riadena y = +-{fhy}, hnana y = +-{rhy}). Koleso dosadne o {hub} dalej von.
  Koleso / Koleso_dvojite: pivot = dosadacia plocha disku na osi. Tocia sa okolo Y.
  Kardan_*: pivot = predna priruba, hriadel ide dozadu (-X). Priruba diferencialu je (0.40, 0, 0) od jeho pivotu.
  Blatniky: pivot = doska, ktora dosadne na bok ramu, nad osou kolesa o {fpz}, x = os napravy.
  Vzduchojemy: pivot = doska na boku ramu (stred dosky 0.13 nad spodkom ramu).
  Tocna: pivot = spodok kolajnic na vrchu ramu. Kralovsky cap navesu ide do bodu (-0.03, 0, 0.23) od pivotu tocne.

NAVES (z = 0 = vrch hlavnych nosnikov, podlaha je nad tym 0.04)
  Kralovsky_cap_navesu: pivot = os capu na spodku dosky; vrch nosnikov je {kpd} nad nim.
  Nosnik_navesu_*: pivot = stred dlzky na osi nosnika, hore. y = +-{tby}. Plytky (vpredu) {sh}, hlboky {dp},
                   prechod 1 m (plytky koniec vpredu +X).
  Obvodovy_nosnik_*: pivot = vonkajsia strana hore, y = +-{tsy} (pravy otoc 180).
  Priecnik_navesu, Podlaha_navesu_1m: pivot = stred, z = 0. Zadny_priecnik_navesu: pivot = koniec nosnikov.
  Zadne_svetlo_navesu_L/P: pivot = predna plocha, dosadne na zadny priecnik (0.10 za koncom nosnikov).
  Podpery_navesu, Rameno_perovania, Vzduchovy_vankus, Naraznik_navesu(_svetla): pivot = spodok hlbokeho
                   nosnika ({dp} pod z = 0), y = +-{tby}.
  Rameno_perovania: os napravy je {drop} pod jeho pivotom, priamo pod nim.
  Vzduchovy_vankus: pivot hore v strede; daj ho {bx} m za os napravy, spodok dosadne na sedlo ramena.
  Naprava_navesu: pivot = os kolies, naboje na y = +-{rhy} (rovnake ako hnana naprava tahaca).
  Blatnik_navesu: pivot hore v strede nad kolesom, drziaky na vnutornej strane (pravy otoc 180).
  Bocna_zabrana_2m: pivot hore na vonkajsej strane pod obvodovym nosnikom (pravu otoc 180).

NAVES NA DREVO (rovnake hlavne nosniky, napravy, perovanie, kolesa a podpery ako plochy naves)
  Lavica_klanicova, Celo_navesu: pivot v strede dole, polozia sa navrch hlavnych nosnikov (z = 0).
  Klanica_*: pivot v strede pata, na vrchu lavice: y = +-{sty}, z = {bh}. Vystuha ide dnu, pravu otoc 180.
  Priecnik_navesu_uzky: pivot v strede hore (z = 0), vojde medzi hlavne nosniky.
  Blatnik_navesu_oblukovy(_zasterka)_L/P: pivot = doska na stojine hlavneho nosnika (y = +-{wy}),
                   {tfz} nad osou kolesa, x = os napravy. Verzia so zasterkou patri na poslednu napravu.
  Kolko lavic, akeho dlheho navesu a kolko naprav, je na tebe.
""".format(ry=RAIL_Y, rh=RAIL_H, sy=SPRING_Y, seat=SEAT, hang=HANG, dh=DIFF_HALF, rhy=REAR_HUB_Y, sx=0.25,
           fhy=FRONT_HUB_Y, hub=HUB_LEN, fpz=FENDER_PLATE_Z, kpd=KINGPIN_DECK, tby=TR_BEAM_Y, sh=TR_SHALLOW,
           dp=TR_DEEP, tsy=TR_SIDE_Y, drop=TR_AXLE_DROP, bx=-BAG_X, sty=STAKE_Y, bh=BUNK_H,
           wy=TR_BEAM_Y + 0.006, tfz=round(TR_FENDER_Z, 3))


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    catalog = child_collection(coll, "Katalog_dielov")
    demo = child_collection(coll, "Ukazka_kamion_navesy")
    clear_collection(coll)
    mats = [get_material(*m) for m in MATERIALS]

    parts = build_parts()
    for key, mesh in parts.items():
        base = "SM_" + key
        if mesh.name != base:
            old = bpy.data.meshes.get(base)
            if old is not None and old.users == 0:
                bpy.data.meshes.remove(old)
                mesh.name = base
        mesh["stavebnica_kamion"] = 1
        for mat in mats:
            mesh.materials.append(mat)

    # katalog: rady dielov s menovkami (zacina za ukazkou, smerom +Y)
    lines = ["Stavebnica kamion + naves - rozmery dielov (dlzka X x sirka Y x vyska Z):", ""]
    y_cursor, gap = 3.2, 0.45
    for title, keys in CATALOG:
        lines.append("== %s ==" % title)
        depth = max(bounds(parts[k])[1][1] - bounds(parts[k])[1][0] for k in keys)
        row_y = y_cursor + depth * 0.5
        add_label(catalog, title, (-12.5, row_y, 0.001), mats[DARK])
        catalog.objects[-1].location.x -= 1.2
        x = -12.0
        for key in keys:
            mesh = parts[key]
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            obj = bpy.data.objects.new(key, mesh)
            catalog.objects.link(obj)
            slot = max(x1 - x0, 1.5)          # miesto aj pre menovku
            obj.location = (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0)
            if key in SPINS:
                add_spin(obj, *SPINS[key])
            add_label(catalog, "%s\n%.2f x %.2f x %.2f" % (key, x1 - x0, y1 - y0, z1 - z0),
                      (x + slot * 0.5, row_y - depth * 0.5 - 0.25, 0.001), mats[DARK])
            lines.append("%-26s %.2f x %.2f x %.2f" % (key, x1 - x0, y1 - y0, z1 - z0))
            x += slot + gap
        lines.append("")
        y_cursor += depth + 1.0

    # ukazka poskladaneho tahaca s navesom
    for key, loc, rot, spin in demo_layout():
        obj = bpy.data.objects.new("Ukazka_" + key, parts[key])
        demo.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = [math.radians(a) for a in rot]
        if spin:
            add_spin(obj, *spin)

    lines.append(RULES)
    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for key, mesh in parts.items():
            export_mesh(coll, mesh, "SM_" + key)
        with open(os.path.join(EXPORT_DIR, "Stavebnica_kamion.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    print("\n".join(lines))


main()
