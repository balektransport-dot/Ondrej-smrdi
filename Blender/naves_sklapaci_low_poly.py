# Stylizovane low poly sklapacie navesy (2 az 3 napravy na vzduchovych vankusoch, korba v tvare U, teleskopicky valec vpredu) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Naves_sklapaci":
#   Sklapac_8_0, Sklapac_9_0, Sklapac_10_0, Sklapac_11_0 - hotove sklapacie navesy rozne velke (kazdy v svojej podkolekcii):
#       stredovy ram a podvozok ako pri plate (kralovsky cap, elektricke podpery, napravy na vankusoch, blatniky, rezerva, naradie; bez bocnych listov a zabran),
#       oceľova korba v tvare U so skosenymi rohmi, rebrami, prednou stenou a zadnym celom na hornych zavesoch,
#       teleskopicky valec (6 stupnov) pred prednou stenou, ktory korbu zdvihne az o 45 st.
#   Sklapac_diely - kazdy diel samostatne s menovkou (spolocne diely raz, diely podla velkosti pre kazdu velkost zvlast).
# Velkosti su v zozname VARIANTS nizsie (celkova dlzka navesu v m, najmenej 8.0): 8.0 m = 2 napravy, korba 7.2 m, boky 1.35 m (okolo 22 m3);
#   9.0 m = 3 napravy, korba 8.2 m, boky 1.50 m; 10.0 m, boky 1.65 m; 11.0 m, boky 1.80 m (okolo 42 m3). Kazda velkost ma inu farbu korby.
# Ovladanie (vlastnosti na hlavnom objekte navesu, napr. "Sklapac_9_0": panel N -> Item, alebo Object -> Custom Properties):
#   Sklopenie       - 0 = korba lezi, 1 = vyklopena (45 st.; pri najdlhsich 42 st.)
#   Zadne_celo      - 0 = zatvorene, 1 = otvorene o 72 st. dozadu a hore (horne zavesy)
#   Vyska_podvozku  - dofuknutie / vypustenie vankusov: zadok sa zdvihne alebo spusti (-0.06 az 0.10 m)
#   Zdvih_napravy   - zdvihnutie prvej napravy 0 = dole, 1 = hore (rovnako ako ovladac na boku navesu so sipkami hore / dole)
#   Podpery         - 0 = zdvihnute (naves na tahaci), 1 = spustene na zem (elektricke podpery, bez kliky)
#   Rezerva_L, Rezerva_P - 1 = rezervne koleso lezi vodorovne pod ramom za kolesami v kosi, 0 = prazdny kos
# Ked pustis animaciu (medzernik): jazda cez nerovnosti, zvysenie a znizenie, zdvih napravy, podpery a nakoniec sklopenie korby s otvorenim zadneho cela.
# Predok = +X, lava strana = +Y. Pociatok navesu = zem pod kralovskym capom (king pin).
# Zapriahnutie k nasim tahacom: spodok navesu pri cape je vo vyske 1.31 m = vrch tocne tahaca,
# takze hlavny objekt navesu staci dat na miesto capu v tocni (z = 0).
# Do priecinka Naves_sklapaci v domovskom priecinku ulozi FBX kazdeho dielu a textovy subor s popisom skladania.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Naves_sklapaci"
PFX_LEN = len("Sklapac_")
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Naves_sklapaci")
# druh navesu a dlzky (m), ktore sa vytvoria; dalsiu dlzku pridas do zoznamu (najmenej 8.0)
TRAILER_TYPE = "sklapac"
NAME_PREFIX = "Sklapac"
VARIANTS = [8.0, 9.0, 10.0, 11.0]

# (nazov, farba, kovovost, drsnost, svietivost, priehladnost)
MATERIALS = [
    ("NP_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0, 1.0),
    ("NP_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0, 1.0),
    ("NP_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0, 1.0),
    ("NP_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("NP_Disk", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("NP_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("NP_Hlinik", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("NP_Plachta", (0.05, 0.16, 0.42, 1.0), 0.0, 0.65, 0.0, 1.0),
    ("NP_Strecha", (0.78, 0.79, 0.78, 1.0), 0.0, 0.60, 0.0, 1.0),
    ("NP_Drevo", (0.36, 0.24, 0.14, 1.0), 0.0, 0.80, 0.0, 1.0),
    ("NP_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("NP_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("NP_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0, 1.0),
    ("NP_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("NP_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0, 1.0),
    ("NP_Cervena", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("NP_Zlta", (0.85, 0.60, 0.03, 1.0), 0.0, 0.45, 0.0, 1.0),
    ("NP_Plast", (0.13, 0.135, 0.145, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("NS_Kasa_modra", (0.10, 0.22, 0.45, 1.0), 0.3, 0.45, 0.0, 1.0),
    ("NS_Kasa_oranzova", (0.85, 0.36, 0.04, 1.0), 0.3, 0.45, 0.0, 1.0),
    ("NS_Kasa_zelena", (0.08, 0.38, 0.17, 1.0), 0.3, 0.45, 0.0, 1.0),
    ("NS_Kasa_zlta", (0.90, 0.68, 0.05, 1.0), 0.3, 0.45, 0.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, ALU, CURTAIN, ROOF, WOOD, LAMP_OR, LAMP_RED, LAMP_WHITE, RED, WHITE,
 REDPAINT, YELLOW, PLAST, BOX0, BOX1, BOX2, BOX3) = range(22)
SIDES_LR = (-1.0, 1.0)

# kolesa 385/65 R22.5 (jednoduche siroke), pivot na konci napravy
WHEEL_R = 0.525
RIM_R = 0.286
TIRE_W = 0.385
HUB_LEN = 0.20
SPINDLE = 0.86

# skrina (m)
HALF_W = 1.275             # polovica sirky 2.55 m
X_FRONT, X_REAR = 1.60, -12.00      # dlzka 13.6 m, cap 1.6 m za celom
FLOOR_TOP = 1.41
FLOOR_BOT = 1.38
COUPLING_Z = 1.31          # spodok platne s capom = vrch tocne tahaca
BEAM_Y = 0.52              # hlavne nosniky ramu
RAIL_Y = BEAM_Y            # (rovnaky nazov ako pri tahacoch, pouzivaju ho spolocne diely)
FRAME_BOT = 0.80           # spodok nosnikov nad napravami (tu su zavesy ramien a vankuse)
BEAM_DEEP_BOT = 0.96       # spodok nosnikov v hlbokej casti (nad napravami)
RAIL_BOT = 1.29            # spodok bocnej obruby
ROOF_RAIL_BOT, ROOF_RAIL_TOP = 3.93, 4.05
ROOF_PEAK = 4.09

# plachta z dielikov (harmonika)
CURTAIN_Y = 1.255
CURTAIN_BOT, CURTAIN_TOP = 1.42, 3.92
CURTAIN_FRONT, CURTAIN_REAR = 1.555, -11.88
CURTAIN_PANELS = 66
CURTAIN_W = (CURTAIN_FRONT - CURTAIN_REAR) / CURTAIN_PANELS
CURTAIN_FOLD = 1.48        # uhol zlozenia dielika pri odsunutej plachte (rad, 85 st.)
POSTS_X = (-2.20, -5.60, -9.00)

# zadne dvere: cap je za rohom, takze sa dvere otvoria o 270 st. a lahnu na bok
DOOR_HINGE_X = X_REAR - 0.045
DOOR_HINGE_Y = HALF_W + 0.04
DOOR_OPEN = 4.712

# podpery
LEG_X = -2.40
LEG_Y = 0.60
LEG_TRAVEL = 0.34          # o kolko sa noha vysunie (z 0.34 m nad zemou na zem)

# napravy a vzduchove perovanie (x od napravy, z od zeme)
AXLES = (-6.40, -7.71, -9.02)
ARM_PIVOT = Vector((0.60, BEAM_Y, 0.62))
ARM_CLAMP_Z = -0.12
BAG_BEHIND = 0.32
BAG_BOTTOM_Z = 0.50
BAG_TOP_Z = 0.82
SHOCK_LOW = Vector((-0.12, 0.66, 0.0))      # od napravy
SHOCK_UP = Vector((0.20, 0.62, 0.88))       # x od napravy, z od zeme
SHOCK_PART = 0.34
LIFT_HEIGHT = 0.15
BODY_FOLLOW = 0.6
DEG = 0.017453
SPARE_Z = 1.10 - TIRE_W * 0.5      # rezerva lezi vodorovne pod ramom: stred kolesa (vyska nad zemou)
SPARE_Y = 0.60                     # dve rezervy vedla seba: stredy kolies v y = +-0.60
AXLE_GAP = 1.31
Y_POS = -14.0              # poloha navesa v scene (vedla tahacov)
# sklapaci naves: rozmery podla velkosti (vyska bokov, sklon, farba) a geometria sklapania
HZ = 1.44                  # os zavesu korby nad zemou (vzadu na rame)
BOX_FRONT = 1.00           # predna plocha korby (svetove x, od capu)
BOX_FLOOR = 0.08           # vrch podlahy korby nad osou zavesu
CYL_BX, CYL_BZ = 1.50, 1.46        # zaklad valca na rame vpredu (x od capu, vyska)
GATE_OPEN = 1.25           # otvorenie zadneho cela (rad, 72 st.)
# dlzka navesu: (vyska bokov, sklon korby v st., farba korby 0 az 3)
TIP_SIZES = {8.0: (1.35, 45.0, 0), 9.0: (1.50, 45.0, 1), 10.0: (1.65, 43.0, 2), 11.0: (1.80, 42.0, 3)}
TIP_HW, TIP_ANGLE, BOX_MAT = 1.35, 0.7854, BOX0
HINGE_X, U_FRONT, A_U, A_V = -6.0, 7.0, 7.2, 1.3
CYL_N, CYL_ELL = 6, 1.4


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
# Spolocne pomocky a diely prevzate z tahacov (kolesa, vankuse, ramena, tlmice, blatniky, ovladace)
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






def add_hub_drum(bm, length=HUB_LEN):
    add_cylinder(bm, 0.22, 0.014, along_y((0.0, 0.007, 0.0)), STEEL, segments=16)
    add_cylinder(bm, 0.205, length - 0.03, along_y((0.0, 0.014 + (length - 0.03) * 0.5, 0.0)), FRAME, segments=16, bev=0.012)
    add_cylinder(bm, 0.13, 0.016, along_y((0.0, length - 0.008, 0.0)), STEEL, segments=12)


def add_truck_hub(bm, y):
    add_cylinder(bm, 0.125, 0.014, along_y((0.0, y + 0.007, 0.0)), STEEL, segments=16)
    ring_of(bm, 10, 0.1675, y + 0.01, 0.016, 0.02, CHROME, segments=6)
    add_cylinder(bm, 0.085, 0.05, along_y((0.0, y + 0.039, 0.0)), STEEL, segments=12, bev=0.008)
    add_cylinder(bm, 0.05, 0.02, along_y((0.0, y + 0.07, 0.0)), CHROME, segments=10, bev=0.006)


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


def build_shock_body():
    # spodna cast tlmica: pivot v spodnom oku, mieri osou +Z hore na horne oko
    bm = bmesh.new()
    L = SHOCK_PART
    add_cylinder(bm, 0.025, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.034, L - 0.04, along_z((0.0, 0.0, 0.02 + (L - 0.04) * 0.5)), DARK, segments=10, bev=0.006)
    add_cylinder(bm, 0.037, 0.02, along_z((0.0, 0.0, L - 0.02)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Sklapac_tlmic_valec")


def build_shock_rod():
    # horna cast tlmica: pivot v hornom oku, mieri osou -Z dole na spodne oko
    bm = bmesh.new()
    L = SHOCK_PART
    add_cylinder(bm, 0.025, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=8)
    add_cylinder(bm, 0.013, L - 0.02, along_z((0.0, 0.0, -(L + 0.02) * 0.5)), CHROME, segments=8)
    add_cylinder(bm, 0.041, 0.12, along_z((0.0, 0.0, -0.085)), DARK, segments=10, bev=0.006)
    return finish_mesh(bm, "SM_Sklapac_tlmic_piestnica")


def build_trailing_arm():
    # vlecene rameno vzduchoveho perovania: pivot v cape na rame, mieri osou -X na bod pod napravou
    bm = bmesh.new()
    path, seat, _, tilt = arm_geometry()
    pts = [(p.x, p.z) for p in path]
    add_extruded(bm, beam_outline(pts, [0.045, 0.04, 0.032], cap=0.5), -0.05, 0.05, "XZ", FRAME, bev=0.008)
    add_cylinder(bm, 0.045, 0.11, along_y((0.0, 0.0, 0.0)), DARK, segments=10)
    add_box(bm, (0.24, 0.16, 0.012), (seat.x, 0.0, seat.z - 0.006), STEEL, bev=0.003, rotation=(0.0, tilt, 0.0))
    return finish_mesh(bm, "SM_Sklapac_rameno")


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
    return finish_mesh(bm, "SM_Sklapac_vankus")


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



# ---------------------------------------------------------------------------
# Ram: dva nosniky (plytke vpredu, hlboke nad napravami), priecniky, vyloznik, bocne listy, zavesy naprav
# ---------------------------------------------------------------------------

XBEAMS_SHALLOW = (1.45, 1.00, 0.58, -0.58)


def build_frame():
    bm = bmesh.new()
    web = [(1.52, FLOOR_BOT)] + BEAM_BOTTOM + [(BEAM_BOTTOM[-1][0], FLOOR_BOT)]
    xe = BEAM_BOTTOM[-1][0]
    for s in SIDES_LR:
        add_extruded(bm, web, s * BEAM_Y - 0.008, s * BEAM_Y + 0.008, "XZ", FRAME)
        add_box(bm, (1.52 - xe, 0.12, 0.016), ((1.52 + xe) * 0.5, s * BEAM_Y, FLOOR_BOT - 0.008), FRAME, bev=0.002)
        for (xa, za), (xb, zb) in zip(BEAM_BOTTOM, BEAM_BOTTOM[1:]):
            add_box_between(bm, (xa, s * BEAM_Y, za + 0.008), (xb, s * BEAM_Y, zb + 0.008), 0.12, 0.016, FRAME)
    for x in XBEAMS_SHALLOW:
        add_box(bm, (0.07, 2.0 * BEAM_Y - 0.10, 0.07), (x, 0.0, FLOOR_BOT - 0.035), FRAME, bev=0.006)
    for x in XBEAMS_DEEP:
        add_box(bm, (0.07, 2.0 * BEAM_Y - 0.10, 0.12), (x, 0.0, FLOOR_BOT - 0.06), FRAME, bev=0.006)
    add_box(bm, (0.10, 2.0 * BEAM_Y + 0.12, 0.12), (X_REAR + 0.22, 0.0, FLOOR_BOT - 0.06), FRAME, bev=0.008)
    # zavesy ramien vzduchoveho perovania, horne drziaky tlmicov, gumove dorazy
    for ax in AXLES:
        for s in SIDES_LR:
            y = s * RAIL_Y
            for d in SIDES_LR:
                add_box(bm, (0.12, 0.012, FRAME_BOT - ARM_PIVOT.z + 0.04),
                        (ax + ARM_PIVOT.x, y + d * 0.062, (FRAME_BOT + ARM_PIVOT.z - 0.04) * 0.5), FRAME, bev=0.004)
            add_box(bm, (0.012, 0.136, 0.12), (ax + ARM_PIVOT.x + 0.06, y, FRAME_BOT - 0.07), FRAME)
            add_cylinder(bm, 0.014, 0.15, along_y((ax + ARM_PIVOT.x, y, ARM_PIVOT.z)), CHROME, segments=6)
            add_box(bm, (0.09, 0.015, 0.11), (ax + SHOCK_UP.x, s * (RAIL_Y + 0.037), SHOCK_UP.z), FRAME, bev=0.004)
            add_cylinder(bm, 0.012, SHOCK_UP.y - RAIL_Y, along_y((ax + SHOCK_UP.x, s * (RAIL_Y + SHOCK_UP.y) * 0.5, SHOCK_UP.z)),
                         CHROME, segments=6)
            add_box(bm, (0.08, 0.08, 0.05), (ax, y, FRAME_BOT - 0.025), DARK, bev=0.012)
    # zavesy korby vzadu (dve konzoly s cepom) a podstavec valca sklapania vpredu
    for s in SIDES_LR:
        add_box(bm, (0.24, 0.06, 0.30), (HINGE_X, s * 0.66, HZ - 0.06), STEEL, bev=0.008)
        add_cylinder(bm, 0.05, 0.16, along_y((HINGE_X, s * 0.70, HZ)), CHROME, segments=10)
        add_box(bm, (0.20, 0.06, 0.16), (CYL_BX, s * 0.12, CYL_BZ - 0.06), STEEL, bev=0.006)
    add_box(bm, (0.20, 1.28, 0.10), (HINGE_X - 0.05, 0.0, 1.35), FRAME, bev=0.008)
    add_box(bm, (0.40, 0.80, 0.10), (CYL_BX - 0.05, 0.0, 1.38), FRAME, bev=0.008)
    add_cylinder(bm, 0.035, 0.34, along_y((CYL_BX, 0.0, CYL_BZ)), CHROME, segments=10)
    return finish_mesh(bm, "SM_Sklapac_ram")


def build_floor():
    bm = bmesh.new()
    add_box(bm, (FLOOR_LEN, 2.0 * (HALF_W - 0.10), 0.03), (FLOOR_MID, 0.0, FLOOR_BOT + 0.015), WOOD)
    for k in range(-5, 6):
        add_box(bm, (FLOOR_LEN - 0.1, 0.006, 0.002), (FLOOR_MID, k * 0.21, FLOOR_TOP + 0.0005), DARK)
    return finish_mesh(bm, "SM_Sklapac_podlaha")


def build_kingpin_plate():
    # cap (king pin) s doskou: spodok dosky je presne vo vyske vrchu tocne tahaca
    bm = bmesh.new()
    add_box(bm, (0.90, 0.90, 0.04), (0.0, 0.0, COUPLING_Z + 0.02), STEEL, bev=0.012)
    add_cylinder(bm, 0.0254, 0.12, along_z((0.0, 0.0, COUPLING_Z - 0.04)), CHROME, segments=10, bev=0.004)
    add_cylinder(bm, 0.055, 0.02, along_z((0.0, 0.0, COUPLING_Z - 0.01)), STEEL, segments=12)
    for s in SIDES_LR:
        add_box(bm, (0.80, 0.04, 0.03), (0.0, s * 0.40, COUPLING_Z + 0.055), FRAME, bev=0.004)
        add_box(bm, (0.04, 0.80, 0.03), (s * 0.40, 0.0, COUPLING_Z + 0.055), FRAME, bev=0.004)
    return finish_mesh(bm, "SM_Sklapac_cap_deska")


# ---------------------------------------------------------------------------
# Celo, zadny portal, dvere, strecha, stlpiky, plachta
# ---------------------------------------------------------------------------

def build_front():
    bm = bmesh.new()
    xf = X_FRONT
    zc = (FLOOR_TOP + ROOF_RAIL_BOT) * 0.5
    zh = ROOF_RAIL_BOT - FLOOR_TOP
    add_box(bm, (0.04, 2.0 * (HALF_W - 0.04), zh), (xf - 0.02, 0.0, zc), WHITE, bev=0.004)
    for k in range(-4, 5):
        add_box(bm, (0.03, 0.04, zh - 0.12), (xf + 0.015, k * 0.25, zc), ALU, bev=0.004)
    for z in (1.85, 3.20):
        add_box(bm, (0.03, 2.2, 0.05), (xf + 0.015, 0.0, z), ALU, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.12, 0.10, zh), (xf - 0.06, s * (HALF_W - 0.05), zc), ALU, bev=0.008)
        add_box(bm, (0.02, 0.14, 0.05), (xf + 0.01, s * 1.13, ROOF_RAIL_BOT - 0.07), LAMP_WHITE, bev=0.004)
        add_box(bm, (0.012, 0.14, 0.04), (xf + 0.006, s * 0.90, FLOOR_TOP + 0.14), RED, bev=0.002)
    add_box(bm, (0.14, 2.0 * HALF_W - 0.004, 0.12), (xf - 0.07, 0.0, (ROOF_RAIL_BOT + ROOF_RAIL_TOP) * 0.5), ALU, bev=0.008)
    # zasuvky na prepojenie s tahacom: dva vzduchove hlavice a elektricka zasuvka
    add_box(bm, (0.08, 0.34, 0.24), (xf + 0.04, 0.55, 2.35), DARK, bev=0.012)
    for y, mat in ((0.45, REDPAINT), (0.56, YELLOW)):
        add_cylinder(bm, 0.025, 0.08, along_x((xf + 0.10, y, 2.35)), mat, segments=8, bev=0.004)
    add_cylinder(bm, 0.045, 0.08, along_x((xf + 0.10, 0.68, 2.35)), DARK, segments=10, bev=0.006)
    add_cylinder(bm, 0.025, 0.02, along_x((xf + 0.15, 0.68, 2.35)), STEEL, segments=8)
    add_front_apron(bm)
    return finish_mesh(bm, "SM_Sklapac_celo")


def build_portal():
    # zadny ram: dva stlpy, horna a spodna priecka a ocka pre zavesy dveri
    bm = bmesh.new()
    xp = X_REAR + 0.06
    zc = (FLOOR_TOP + ROOF_RAIL_BOT) * 0.5
    for s in SIDES_LR:
        add_box(bm, (0.12, 0.10, ROOF_RAIL_BOT - FLOOR_TOP), (xp, s * (HALF_W - 0.05), zc), ALU, bev=0.008)
        for z in (1.60, 2.67, 3.74):
            add_box_between(bm, (xp, s * (HALF_W - 0.02), z), (DOOR_HINGE_X, s * DOOR_HINGE_Y, z), 0.04, 0.09, STEEL, bev=0.004)
        add_box(bm, (0.04, 0.06, 0.16), (xp - 0.07, s * (HALF_W - 0.05), 1.60), STEEL, bev=0.004)
    add_box(bm, (0.12, 2.0 * HALF_W - 0.004, 0.12), (xp, 0.0, (ROOF_RAIL_BOT + ROOF_RAIL_TOP) * 0.5), ALU, bev=0.008)
    add_box(bm, (0.12, 2.0 * HALF_W - 0.004, 0.12), (xp, 0.0, 1.35), ALU, bev=0.008)
    add_rear_apron(bm)
    return finish_mesh(bm, "SM_Sklapac_zadny_portal")


DOOR_W = 1.31
DOOR_Z0, DOOR_Z1 = 1.45, 3.92


def build_door():
    # lave dvere: pivot v zavese (os Z), listok sa tiahne do -Y, vonkajsia strana (kluky) smeruje do -X
    bm = bmesh.new()
    zm, zh = (DOOR_Z0 + DOOR_Z1) * 0.5, DOOR_Z1 - DOOR_Z0
    add_box(bm, (0.046, DOOR_W, 0.07), (0.0, -DOOR_W * 0.5, DOOR_Z0 + 0.035), ALU, bev=0.006)
    add_box(bm, (0.046, DOOR_W, 0.07), (0.0, -DOOR_W * 0.5, DOOR_Z1 - 0.035), ALU, bev=0.006)
    for y in (-0.035, -DOOR_W + 0.035):
        add_box(bm, (0.05, 0.07, zh), (0.0, y, zm), ALU, bev=0.006)
    add_box(bm, (0.02, DOOR_W - 0.12, zh - 0.12), (0.0, -DOOR_W * 0.5, zm), ROOF)
    for k in range(1, 6):
        add_box(bm, (0.03, 0.03, zh - 0.14), (-0.01, -0.07 - k * (DOOR_W - 0.14) / 6.0, zm), ALU, bev=0.004)
    # zavesy
    for z in (1.60, 2.67, 3.74):
        add_cylinder(bm, 0.024, 0.14, along_z((0.0, 0.0, z)), STEEL, segments=10)
    add_cylinder(bm, 0.011, zh - 0.1, along_z((0.0, 0.0, zm)), CHROME, segments=6)
    # zamykacia tyc s rukovatou a vodiacimi objimkami
    yl = -DOOR_W + 0.17
    add_cylinder(bm, 0.012, zh - 0.20, along_z((-0.04, yl, zm)), CHROME, segments=6)
    for z in (DOOR_Z0 + 0.25, zm, DOOR_Z1 - 0.25):
        add_box(bm, (0.035, 0.05, 0.06), (-0.03, yl, z), STEEL, bev=0.004)
    add_box(bm, (0.04, 0.16, 0.03), (-0.075, yl + 0.07, DOOR_Z0 + 0.14), STEEL, bev=0.006)
    add_box(bm, (0.03, 0.06, 0.05), (-0.04, yl, DOOR_Z0 + 0.14), STEEL, bev=0.004)
    # cervenobiely pas pre viditelnost
    for k in range(10):
        add_box(bm, (0.012, 0.13, 0.10), (-0.03, -0.065 - k * 0.13, DOOR_Z0 + 0.14), RED if k % 2 == 0 else WHITE, bev=0.002)
    return bm


def roof_z(y):
    return ROOF_RAIL_TOP + (ROOF_PEAK - ROOF_RAIL_TOP) * (1.0 - (y / (HALF_W - 0.02)) ** 2)


def build_roof():
    bm = bmesh.new()
    ys = [-(HALF_W - 0.02) + 2.0 * (HALF_W - 0.02) * k / 8.0 for k in range(9)]
    upper = [(y, roof_z(y)) for y in ys]
    lower = [(y, roof_z(y) - 0.02) for y in reversed(ys)]
    add_extruded_yz(bm, upper + lower, X_REAR - 0.01, X_FRONT + 0.02, ROOF)
    for s in SIDES_LR:
        add_box(bm, (X_FRONT - X_REAR + 0.02, 0.08, 0.12), ((X_FRONT + X_REAR) * 0.5, s * (HALF_W - 0.042),
                (ROOF_RAIL_BOT + ROOF_RAIL_TOP) * 0.5), ALU, bev=0.006)
        add_box(bm, (X_FRONT - X_REAR - 0.1, 0.02, 0.03), ((X_FRONT + X_REAR) * 0.5, s * (HALF_W + 0.002), ROOF_RAIL_BOT - 0.015), DARK)
    # obluky pod strechou
    inner = [(y, roof_z(y) - 0.07) for y in reversed(ys)]
    outer = [(y, roof_z(y) - 0.02) for y in ys]
    for x in [1.0 - 1.14 * k for k in range(int((1.0 - X_REAR - 0.4) / 1.14) + 1)]:
        add_extruded_yz(bm, outer + inner, x - 0.025, x + 0.025, ALU, bev=0.004)
    return finish_mesh(bm, "SM_Sklapac_strecha")


def build_post():
    # stlpik plachty: pivot dole v strede, vyska 2.50 m
    bm = bmesh.new()
    h = ROOF_RAIL_BOT - FLOOR_TOP
    add_box(bm, (0.06, 0.05, h), (0.0, 0.0, h * 0.5), ALU, bev=0.006)
    add_box(bm, (0.08, 0.08, 0.06), (0.0, 0.0, 0.03), STEEL, bev=0.006)
    add_box(bm, (0.07, 0.07, 0.05), (0.0, 0.0, h + 0.025), STEEL, bev=0.006)
    add_box(bm, (0.04, 0.012, 0.30), (0.0, 0.03, 1.30), DARK)
    return finish_mesh(bm, "SM_Sklapac_stlpik")


def build_curtain_panel():
    # jeden dielik plachty: pivot na prednej hrane dole, tiahne sa do -X, na harmoniku sa ohybaju zavesy medzi dielikmi
    bm = bmesh.new()
    w, h = CURTAIN_W, CURTAIN_TOP - CURTAIN_BOT
    add_box(bm, (w - 0.012, 0.012, h), (-w * 0.5, 0.0, h * 0.5), CURTAIN, bev=0.004)
    add_box(bm, (w - 0.012, 0.016, 0.14), (-w * 0.5, 0.0, 0.07), DARK, bev=0.002)
    add_box(bm, (w - 0.012, 0.016, 0.20), (-w * 0.5, 0.0, h - 0.34), WHITE, bev=0.002)
    add_box(bm, (0.014, 0.022, h), (-0.007, 0.0, h * 0.5), ALU, bev=0.002)
    add_box(bm, (0.05, 0.03, 0.04), (-w * 0.5, 0.0, h - 0.02), STEEL, bev=0.004)
    return finish_mesh(bm, "SM_Sklapac_plachta_dielik")


# ---------------------------------------------------------------------------
# Podpery (elektricke nohy), svetla, zabrany, skrinka, rezerva
# ---------------------------------------------------------------------------

def build_leg_outer():
    # vonkajsia (pevna) cast nohy: pivot na zemi pod nohou, lava; zrkadlom vznikne prava
    bm = bmesh.new()
    zt = FLOOR_BOT
    add_box(bm, (0.14, 0.14, zt - 0.62), (0.0, 0.0, (zt + 0.62) * 0.5), FRAME, bev=0.01)
    add_box(bm, (0.30, 0.03, 0.58), (0.0, -(LEG_Y - BEAM_Y - 0.06 + 0.015), 1.06), STEEL, bev=0.004)
    add_box(bm, (0.12, 0.10, 0.14), (0.0, 0.12, 0.95), STEEL, bev=0.012)
    return bm


def build_leg_inner():
    # vnutorna (vysuvacia) cast nohy: pivot = spodok pate, pri zdvihnutych podperach je 0.34 m nad zemou
    bm = bmesh.new()
    add_box(bm, (0.10, 0.10, 0.86), (0.0, 0.0, 0.45), STEEL, bev=0.006)
    add_box(bm, (0.30, 0.30, 0.02), (0.0, 0.0, 0.01), FRAME, bev=0.006)
    add_cylinder(bm, 0.055, 0.05, along_z((0.0, 0.0, 0.045)), DARK, segments=10, bev=0.006)
    return finish_mesh(bm, "SM_Sklapac_noha_vnutorna")


def build_leg_cross():
    # spojovaci hriadel medzi nohami a vzpery k nosnikom: pivot v strede medzi nohami
    bm = bmesh.new()
    add_cylinder(bm, 0.02, 2.0 * LEG_Y - 0.12, along_y((0.0, 0.0, 0.95)), STEEL, segments=8)
    for s in SIDES_LR:
        add_rod(bm, (0.0, s * (LEG_Y - 0.07), 0.70), (0.0, s * (BEAM_Y - 0.04), 1.10), 0.025, STEEL, segments=6)
        add_rod(bm, (0.0, s * (LEG_Y - 0.07), 0.70), (-0.40, s * (BEAM_Y - 0.04), 1.10), 0.02, STEEL, segments=6)
    return finish_mesh(bm, "SM_Sklapac_podpery_traverza")


def build_side_lights():
    # bocne obrysove svetla na vonkajsej strane nosnikov (naves nema bocne listy, iba stredovy ram)
    bm = bmesh.new()
    y = BEAM_Y + 0.012
    for x in SIDE_LIGHT_X:
        add_box(bm, (0.17, 0.012, 0.07), (x, y + 0.006, 1.345), DARK)
        add_box(bm, (0.14, 0.025, 0.05), (x, y + 0.0145, 1.345), LAMP_OR, bev=0.006)
    return bm


def build_side_guard():
    bm = bmesh.new()
    y = HALF_W - 0.075
    xs = GUARD_XS
    if not xs:
        return bm
    for x in xs:
        add_box(bm, (0.05, 0.05, 0.74), (x, y, 0.92), ALU, bev=0.006)
        add_box(bm, (0.09, 0.09, 0.03), (x, y, 1.305), STEEL)
    for z in (0.62, 0.84, 1.06):
        add_box(bm, (xs[0] - xs[-1] + 0.10, 0.04, 0.10), ((xs[0] + xs[-1]) * 0.5, y, z), ALU, bev=0.006)
    return bm


def build_toolbox():
    # skrina na naradie pod ramom vlavo z cierneho plastu s dvoma rukovatami (pivot v strede x, vyska je absolutna)
    bm = bmesh.new()
    add_box(bm, (0.70, 0.42, 0.40), (0.0, 0.82, 0.90), PLAST, bev=0.04)
    add_box(bm, (0.62, 0.012, 0.32), (0.0, 1.03, 0.90), DARK, bev=0.012)
    for x in (-0.17, 0.17):
        add_cylinder(bm, 0.035, 0.03, along_y((x, 1.045, 0.95)), DARK, segments=10, bev=0.006)
        add_box(bm, (0.085, 0.022, 0.026), (x, 1.068, 0.95), DARK, bev=0.006)
    add_box(bm, (0.12, 0.004, 0.03), (0.17, 1.038, 0.80), WHITE)
    for x in (-0.22, 0.22):
        add_box(bm, (0.06, 0.18, 0.04), (x, 0.60, 1.08), FRAME, bev=0.004)
    return finish_mesh(bm, "SM_Sklapac_naradi_skrinka")


def build_trailer_axle():
    # naprava bez diferencialu s bubnovymi brzdami: pivot v osi kolies
    bm = bmesh.new()
    add_cylinder(bm, 0.075, 2.0 * SPINDLE - 0.04, along_y((0.0, 0.0, 0.0)), FRAME, segments=12)
    add_box(bm, (0.16, 0.30, 0.15), (0.0, 0.0, 0.0), FRAME, bev=0.03)
    for s in SIDES_LR:
        add_cylinder(bm, 0.095, 0.03, along_y((0.0, s * (SPINDLE - 0.035), 0.0)), STEEL, segments=12)
        add_u_bolts(bm, s * RAIL_Y, 0.08, ARM_CLAMP_Z - 0.045, 0.07)
        add_shock_bracket(bm, SHOCK_LOW, s)
        add_cylinder(bm, 0.09, 0.12, along_y((0.20, s * 0.65, 0.0)), DARK, segments=10, bev=0.012)
        add_rod(bm, (0.20, s * 0.59, 0.0), (0.04, s * 0.56, 0.0), 0.012, STEEL)
    return finish_mesh(bm, "SM_Sklapac_naprava")


def build_wheel():
    bm = bmesh.new()
    add_hub_drum(bm)
    add_truck_tire(bm, 0.08)
    add_wheel_disc(bm, HUB_LEN, HUB_LEN + 0.02, 1.0)
    add_truck_hub(bm, HUB_LEN + 0.02)
    return finish_mesh(bm, "SM_Sklapac_koleso")


# ---------------------------------------------------------------------------
# Len pre plato: predna stena (nizka s mriezkou) a zadna hrana
# ---------------------------------------------------------------------------

def build_headboard():
    bm = bmesh.new()
    xf = X_FRONT
    h = 1.20
    low = 0.60
    add_box(bm, (0.04, 2.0 * (HALF_W - 0.04), low), (xf - 0.02, 0.0, FLOOR_TOP + low * 0.5), WHITE, bev=0.004)
    for k in range(-4, 5):
        add_box(bm, (0.03, 0.04, low - 0.10), (xf + 0.015, k * 0.25, FLOOR_TOP + low * 0.5), ALU, bev=0.004)
    for k in range(-5, 6):
        add_box(bm, (0.03, 0.035, h - low - 0.05), (xf - 0.02, k * 0.215, FLOOR_TOP + low + (h - low) * 0.5 - 0.02), ALU, bev=0.004)
    for z in (FLOOR_TOP + low + 0.04, FLOOR_TOP + low + 0.30):
        add_box(bm, (0.04, 2.0 * (HALF_W - 0.04), 0.05), (xf - 0.02, 0.0, z), ALU, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.12, 0.10, h), (xf - 0.06, s * (HALF_W - 0.05), FLOOR_TOP + h * 0.5), ALU, bev=0.008)
        add_box(bm, (0.02, 0.14, 0.05), (xf + 0.01, s * 1.13, FLOOR_TOP + h - 0.08), LAMP_WHITE, bev=0.004)
        add_box(bm, (0.012, 0.14, 0.04), (xf + 0.006, s * 0.90, FLOOR_TOP + 0.14), RED, bev=0.002)
    add_box(bm, (0.14, 2.0 * HALF_W - 0.004, 0.10), (xf - 0.07, 0.0, FLOOR_TOP + h + 0.05), ALU, bev=0.008)
    add_box(bm, (0.08, 0.34, 0.24), (xf + 0.04, 0.55, 1.80), DARK, bev=0.012)
    for y, mat in ((0.45, REDPAINT), (0.56, YELLOW)):
        add_cylinder(bm, 0.025, 0.08, along_x((xf + 0.10, y, 1.80)), mat, segments=8, bev=0.004)
    add_cylinder(bm, 0.045, 0.08, along_x((xf + 0.10, 0.68, 1.80)), DARK, segments=10, bev=0.006)
    add_cylinder(bm, 0.025, 0.02, along_x((xf + 0.15, 0.68, 1.80)), STEEL, segments=8)
    add_front_apron(bm)
    return finish_mesh(bm, "SM_Sklapac_celo")


def build_rear_edge():
    # zadna hrana plata: hlinikova priecka s rohovymi uchytmi
    bm = bmesh.new()
    xp = X_REAR + 0.06
    add_box(bm, (0.12, 2.0 * HALF_W - 0.004, 0.13), (xp, 0.0, 1.345), ALU, bev=0.008)
    for s in SIDES_LR:
        add_box(bm, (0.14, 0.10, 0.16), (xp, s * (HALF_W - 0.05), 1.34), ALU, bev=0.01)
    for k in range(-3, 4):
        add_box(bm, (0.05, 0.03, 0.03), (xp - 0.065, k * 0.30, 1.35), STEEL, bev=0.004)
    add_rear_apron(bm)
    return finish_mesh(bm, "SM_Sklapac_zadny_lem")


def add_rear_apron(bm):
    # zadna zastera: od zadnej priecky plata sa stiahne dole az k nosnikom a skryva konce nosnikov a zadny priecnik
    z0, z1 = 1.12, 1.31
    zm = (z0 + z1) * 0.5
    add_box(bm, (0.03, 2.0 * (HALF_W - 0.03), z1 - z0), (X_REAR + 0.015, 0.0, zm), ALU, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.05, 0.07, z1 - z0 + 0.02), (X_REAR + 0.025, s * (HALF_W - 0.05), zm - 0.01), ALU, bev=0.008)
    for k in range(-3, 4):
        add_box(bm, (0.012, 0.04, z1 - z0 - 0.05), (X_REAR - 0.003, k * 0.33, zm), ALU, bev=0.003)


def build_bumper():
    # mohutny zadny podjazdovy naraznik: hlboky hlinikovy profil, hrube nosne rury, velke koncovky, cervenobiely pas
    bm = bmesh.new()
    xb = X_REAR + 0.20
    zb = 0.62
    add_box(bm, (0.16, 2.42, 0.20), (xb, 0.0, zb), ALU, bev=0.03)
    add_box(bm, (0.04, 2.30, 0.05), (xb + 0.095, 0.0, zb - 0.075), DARK, bev=0.006)
    add_box(bm, (0.02, 2.30, 0.012), (xb - 0.083, 0.0, zb + 0.082), DARK)
    add_box(bm, (0.02, 2.30, 0.012), (xb - 0.083, 0.0, zb - 0.082), DARK)
    for s in SIDES_LR:
        add_box(bm, (0.22, 0.10, 0.27), (xb, s * 1.21, zb), DARK, bev=0.025)
        for y in (0.95, 0.40):
            add_box(bm, (0.09, 0.09, 1.26 - (zb + 0.10)), (xb, s * y, (1.26 + zb + 0.10) * 0.5), ALU, bev=0.012)
            add_box(bm, (0.14, 0.16, 0.04), (xb, s * y, 1.27), FRAME, bev=0.005)
        add_box_between(bm, (xb + 0.30, s * 0.95, 1.16), (xb, s * 0.95, zb + 0.14), 0.06, 0.10, FRAME, bev=0.006)
        add_box_between(bm, (xb + 0.30, s * 0.95, 1.20), (xb + 0.08, s * 0.95, 1.20), 0.06, 0.06, FRAME, bev=0.004)
    for k in range(-4, 5):
        add_box(bm, (0.012, 0.15, 0.115), (xb - 0.087, k * 0.155, zb), RED if k % 2 == 0 else WHITE, bev=0.002)
    add_box(bm, (0.012, 0.52, 0.12), (X_REAR - 0.007, 0.0, 1.22), WHITE, bev=0.003)
    add_box(bm, (0.03, 0.14, 0.03), (X_REAR - 0.012, 0.0, 1.295), DARK, bev=0.012)
    return finish_mesh(bm, "SM_Sklapac_zadny_naraznik")


def build_rear_light():
    # zadne svetlo na nariazniku (lava strana): siroky obdlznik na zadnej strane pri konci, zvonka oranzova smerovka,
    # cervene ryhovane sklo, vnutri biele cuvanie
    bm = bmesh.new()
    xb = X_REAR + 0.20
    ly, lz = HALF_W - 0.30, 0.62
    xh = xb - 0.08 - 0.035
    xl = xh - 0.0405
    add_box(bm, (0.07, 0.37, 0.13), (xh, ly, lz), DARK, bev=0.012)
    add_box(bm, (0.012, 0.085, 0.095), (xl, ly + 0.1325, lz), LAMP_OR, bev=0.003)
    add_box(bm, (0.012, 0.17, 0.095), (xl, ly - 0.005, lz), LAMP_RED, bev=0.003)
    for dy in (-0.05, 0.0, 0.05):
        add_box(bm, (0.016, 0.006, 0.095), (xl - 0.002, ly - 0.005 + dy, lz), DARK)
    add_box(bm, (0.012, 0.07, 0.095), (xl, ly - 0.135, lz), LAMP_WHITE, bev=0.003)
    add_box(bm, (0.045, 0.012, 0.05), (xh, ly + 0.19, lz), RED, bev=0.003)
    return bm


def build_side_skirt():
    # bocna zastera (lava): od bocnej listy dole az k nosnikom (z = 1.12); pred tahacovymi kolesami sa zdvihne nahor,
    # aby nezasahovala do blatnikov tahaca; v mieste ovladaca ma otvor
    bm = bmesh.new()
    y0, y1 = HALF_W - 0.022, HALF_W - 0.002
    zt, zb = 1.29, 1.12
    ramp0, ramp1 = -1.75, -1.35
    gap0, gap1 = CTRL_X - 0.17, CTRL_X + 0.17
    for xa, xb_ in ((FLOOR_X0, gap0), (gap1, ramp0)):
        if xa < xb_ - 0.01:
            add_extruded(bm, [(xa, zt), (xa, zb), (xb_, zb), (xb_, zt)], y0, y1, "XZ", ALU)
            add_box(bm, (xb_ - xa, 0.004, 0.012), ((xa + xb_) * 0.5, y1 + 0.001, 1.205), DARK)
    add_extruded(bm, [(ramp0, zt), (ramp0, zb), (ramp1, zt)], y0, y1, "XZ", ALU)
    return bm


def add_front_apron(bm):
    # predna zastera: od prednej hrany plata dole k nosnikom
    add_box(bm, (0.03, 2.0 * (HALF_W - 0.03), 0.10), (X_FRONT - 0.065, 0.0, 1.36), ALU, bev=0.004)



# ---------------------------------------------------------------------------
# Lepsie kolesa: pneumatika s dezenom (5 radov blokov v tvare V), napisy na boku, disk s otvormi a maticami
# (prepisuje jednoduche verzie z dielov tahacov)
# ---------------------------------------------------------------------------

TREAD_N = 36
TREAD_STEP = 2.0 * math.pi / TREAD_N
TREAD_ROWS = (-0.135, -0.068, 0.0, 0.068, 0.135)
TREAD_ROW_W = 0.056


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


def add_truck_tire(bm, y, width=TIRE_W):
    carc_r = WHEEL_R - 0.022
    add_ring(bm, carc_r, RIM_R + 0.02, width, y, DARK, 28, bev=width * 0.14)
    for row, yc in enumerate(TREAD_ROWS):
        lean = TREAD_STEP * 0.45 * (1.0 if yc < 0.0 else -1.0 if yc > 0.0 else 0.0)
        shift = 0.5 * (row % 2)
        for i in range(TREAD_N):
            a0 = TREAD_STEP * (i + shift) + TREAD_STEP * 0.11
            add_arc_block(bm, a0, a0 + TREAD_STEP * 0.78, y + yc - TREAD_ROW_W * 0.5, y + yc + TREAD_ROW_W * 0.5,
                          carc_r - 0.004, WHEEL_R, TIRE, lean)
    for s in SIDES_LR:
        # napis a ryhy na boku pneumatiky
        face = y + s * width * 0.5
        y0, y1 = (face - 0.001, face + 0.003) if s > 0 else (face - 0.003, face + 0.001)
        for k in range(24):
            a0 = 2.0 * math.pi * k / 24
            add_arc_block(bm, a0, a0 + 0.07, y0, y1, 0.395, 0.435 if k % 3 == 0 else 0.425, DARK, 0.0, 0.0005)
        add_ring(bm, 0.37, 0.362, 0.006, y + s * (width * 0.5 - 0.001), DARK, 28)
        add_ring(bm, RIM_R + 0.032, RIM_R - 0.012, 0.018, y + s * (width * 0.5 - 0.004), RIM, 20)
    add_ring(bm, RIM_R, RIM_R - 0.012, width - 0.03, y, RIM, 20)


def add_wheel_disc(bm, y0, y1, holes):
    side = 1.0 if holes > 0 else -1.0
    face = y1 if holes > 0 else y0
    add_cylinder(bm, RIM_R - 0.01, y1 - y0, along_y((0.0, (y0 + y1) * 0.5, 0.0)), RIM, segments=24)
    add_ring(bm, RIM_R - 0.012, RIM_R - 0.045, 0.012, face + side * 0.004, RIM, 24)
    ring_of(bm, 10, 0.19, face, 0.042, 0.008, DARK, segments=10)
    ring_of(bm, 10, 0.118, face + side * 0.006, 0.016, 0.014, CHROME, segments=6)


# ---------------------------------------------------------------------------
# Ovladac zdvihu napravy (s nakreslenymi sipkami hore a dole), kos na rezervu
# ---------------------------------------------------------------------------

def arrow_points(up, cx, cz):
    pts = [(0.0, 0.030), (-0.026, 0.004), (-0.010, 0.004), (-0.010, -0.028), (0.010, -0.028), (0.010, 0.004), (0.026, 0.004)]
    if not up:
        pts = [(x, -z) for x, z in reversed(pts)]
    return [(cx + x, cz + z) for x, z in pts]


def build_controller():
    # pult zdvihu napravy: pivot na vonkajsej strane (y = 0), zadna doska sa opiera o zadnu stranu zastery (v scene je otoceny dozadu); vonkajsia strana +Y
    bm = bmesh.new()
    add_box(bm, (0.17, 0.07, 0.28), (0.0, -0.035, 0.0), DARK, bev=0.012)
    add_box(bm, (0.15, 0.006, 0.26), (0.0, 0.003, 0.0), DARK, bev=0.002)
    for up, z in ((True, 0.075), (False, -0.075)):
        add_box(bm, (0.095, 0.012, 0.095), (0.0, 0.012, z), WHITE, bev=0.008)
        add_extruded(bm, arrow_points(up, 0.0, z), 0.018, 0.022, "XZ", DARK)
    add_cylinder(bm, 0.012, 0.01, along_y((0.0, 0.008, 0.0)), LAMP_OR, segments=8)
    add_box(bm, (0.20, 0.012, 0.32), (0.0, -0.076, 0.0), FRAME, bev=0.004)
    add_rod(bm, (0.05, -0.035, -0.14), (0.05, -0.035, -0.26), 0.008, DARK, segments=5)
    return finish_mesh(bm, "SM_Sklapac_ovladac_napravy")


def build_spare():
    # rezervne koleso: pivot v strede kolesa, vonkajsia strana +Y (vpravo sa otaca o 180 st.)
    bm = bmesh.new()
    add_truck_tire(bm, 0.0)
    add_wheel_disc(bm, 0.15, 0.17, 1.0)
    add_truck_hub(bm, 0.17)
    return finish_mesh(bm, "SM_Sklapac_rezerva")


def build_spare_basket():
    # kos na rezervu pre lavu stranu (stred kolesa v y = SPARE_Y): dva U-profily z rurok pod kolesom a konzoly k nosnikom;
    # pivot v strede kolesa (x), y a z su absolutne
    bm = bmesh.new()
    yc, zc = SPARE_Y, SPARE_Z
    bottom = zc - TIRE_W * 0.5
    half = WHEEL_R + 0.065
    z_top, z_low = 1.10, bottom - 0.02
    path = [(-half, z_top), (-half, z_low + 0.04), (-half + 0.04, z_low), (half - 0.04, z_low), (half, z_low + 0.04), (half, z_top)]
    for y in (yc - 0.30, yc + 0.30):
        for a, b in zip(path, path[1:]):
            add_rod(bm, (a[0], y, a[1]), (b[0], y, b[1]), 0.016, FRAME, segments=8)
        yb = BEAM_Y + (0.06 if y > BEAM_Y else -0.06)
        for x in (-half, half):
            add_box(bm, (0.06, abs(y - yb) + 0.06, 0.04), (x, (y + yb) * 0.5, z_top + 0.005), FRAME, bev=0.004)
    for x in (-half, half):
        add_rod(bm, (x, yc - 0.30, 0.92), (x, yc + 0.30, 0.92), 0.013, FRAME, segments=8)
    add_cylinder(bm, 0.05, 0.035, along_z((0.0, yc, 1.14)), STEEL, segments=8, bev=0.005)
    return bm



# ---------------------------------------------------------------------------
# Rozmery podla dlzky, diely, zostava navesov, animacia, katalog, export
# ---------------------------------------------------------------------------

MIN_LENGTH = 8.0
PANEL_TARGET_W = 0.2036
SHARED_PARTS = {}
# diely, ktorych rozmer zavisi od velkosti navesu (mesh dostane v nazve dlzku)
LENGTH_PARTS = ("Sklapac_ram", "Sklapac_korba", "Sklapac_zadne_celo", "Sklapac_zadny_naraznik", "Sklapac_zadne_svetlo_L", "Sklapac_zadne_svetlo_P",
                "Sklapac_bocne_svetla_L", "Sklapac_bocne_svetla_P", "Sklapac_zabrana_L", "Sklapac_zabrana_P") + tuple("Sklapac_valec_%d" % k for k in range(9))


# ---------------------------------------------------------------------------
# Sklapaci naves: korba (pivot v zavese vzadu), zadne celo (pivot hore na zadnej hrane), teleskopicky valec vpredu
# ---------------------------------------------------------------------------

def build_tip_box():
    # korba v tvare U (skosene rohy), pivot v osi zavesu vzadu, x dopredu; vrch podlahy v z = BOX_FLOOR
    bm = bmesh.new()
    hw, m = TIP_HW, BOX_MAT
    top = BOX_FLOOR + hw
    u0, u1 = -0.10, U_FRONT
    ln, uc = u1 - u0, (u1 + u0) * 0.5
    zc = 0.52
    add_box(bm, (ln, 1.46, 0.02), (uc, 0.0, BOX_FLOOR - 0.01), m, bev=0.004)
    ang = math.degrees(math.atan2(zc - BOX_FLOOR, 0.51))
    clen = math.hypot(0.51, zc - BOX_FLOOR)
    for s in SIDES_LR:
        add_box(bm, (ln, clen, 0.02), (uc, s * 0.985, (zc + BOX_FLOOR) * 0.5), m, bev=0.004, rotation=(s * ang, 0.0, 0.0))
        add_box(bm, (ln, 0.02, top - zc), (uc, s * 1.24, (top + zc) * 0.5), m, bev=0.004)
        add_box(bm, (ln, 0.11, 0.09), (uc, s * 1.205, top - 0.03), m, bev=0.012)
        add_box(bm, (ln - 0.30, 0.04, 0.07), (uc, s * 1.265, zc + (top - zc) * 0.42), m, bev=0.006)
        n_rib = max(3, int(ln / 0.85))
        for i in range(n_rib + 1):
            u = u0 + 0.20 + i * (ln - 0.40) / n_rib
            add_box(bm, (0.08, 0.045, top - zc - 0.04), (u, s * 1.2675, (top + zc) * 0.5 - 0.02), m, bev=0.006)
            add_box(bm, (0.08, 0.045, 0.30), (u, s * 1.215, zc - 0.10), m, bev=0.006, rotation=(s * ang, 0.0, 0.0))
        add_box(bm, (ln - 0.10, 0.14, 0.12), (uc, s * 0.52, 0.0), FRAME, bev=0.008)
    for i in range(int(ln / 0.9) + 1):
        add_box(bm, (0.07, 1.50, 0.09), (u0 + 0.25 + i * 0.9, 0.0, 0.015), FRAME, bev=0.006)
    # predna stena s rebrami a hornym nosnikom, rebra su zvonka (pred stenou)
    add_box(bm, (0.03, 2.48, hw + 0.02), (u1 - 0.015, 0.0, BOX_FLOOR + hw * 0.5), m, bev=0.004)
    for y in (-0.90, -0.45, 0.0, 0.45, 0.90):
        add_box(bm, (0.07, 0.08, hw - 0.20), (u1 + 0.035, y, BOX_FLOOR + hw * 0.5 - 0.05), m, bev=0.006)
    add_box(bm, (0.15, 2.52, 0.12), (u1 - 0.035, 0.0, top), m, bev=0.012)
    add_box(bm, (0.10, 2.50, 0.08), (u1 + 0.03, 0.0, BOX_FLOOR + 0.30), m, bev=0.008)
    # ucha valca sklapania: dve platne na prednej stene a cap vo vyske A_V
    for s in SIDES_LR:
        add_box(bm, (A_U - U_FRONT + 0.14, 0.04, 0.30), ((A_U + U_FRONT) * 0.5 + 0.02, s * 0.11, A_V), STEEL, bev=0.006)
        add_box(bm, (0.12, 0.05, 0.40), (U_FRONT + 0.06, s * 0.11, A_V - 0.12), STEEL, bev=0.006)
    add_cylinder(bm, 0.035, 0.34, along_y((A_U, 0.0, A_V)), CHROME, segments=10)
    # zadna hrana: horne cepy zadneho cela, zadne stlpiky, zavesove ucha dole
    add_box(bm, (0.12, 2.50, 0.10), (u0 + 0.05, 0.0, BOX_FLOOR + 0.05), m, bev=0.008)
    for s in SIDES_LR:
        add_box(bm, (0.14, 0.10, hw), (u0 + 0.05, s * 1.215, BOX_FLOOR + hw * 0.5), m, bev=0.01)
        add_box(bm, (0.10, 0.06, 0.12), (-0.04, s * 1.15, top - 0.04), STEEL, bev=0.008)
        add_box(bm, (0.18, 0.05, 0.22), (0.0, s * 0.60, 0.0), STEEL, bev=0.008)
        add_box(bm, (0.06, 0.12, 0.20), (u0 + 0.02, s * 1.20, BOX_FLOOR + 0.20), STEEL, bev=0.006)
    add_cylinder(bm, 0.025, 2.50, along_y((-0.06, 0.0, top - 0.03)), CHROME, segments=8)
    add_cylinder(bm, 0.045, 1.46, along_y((0.0, 0.0, 0.0)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Sklapac_korba")


def build_tip_gate():
    # zadne celo: pivot hore (os klbu vodorovne v Y), panel visi dole (-Z)
    bm = bmesh.new()
    gh = TIP_HW - 0.06
    m = BOX_MAT
    add_box(bm, (0.035, 2.40, gh), (0.0, 0.0, -gh * 0.5 - 0.02), m, bev=0.004)
    for y in (-1.0, -0.5, 0.0, 0.5, 1.0):
        add_box(bm, (0.055, 0.07, gh - 0.14), (-0.045, y, -gh * 0.5 - 0.02), m, bev=0.006)
    add_box(bm, (0.07, 0.07, 0.10), (-0.03, 0.0, -gh * 0.5 + 0.0), DARK, bev=0.004)
    add_box(bm, (0.06, 2.44, 0.08), (-0.02, 0.0, -gh - 0.02), m, bev=0.008)
    add_cylinder(bm, 0.04, 2.46, along_y((0.0, 0.0, 0.0)), STEEL, segments=10)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.07, gh), (-0.02, s * 1.215, -gh * 0.5 - 0.02), m, bev=0.008)
        add_box(bm, (0.07, 0.10, 0.12), (-0.04, s * 1.18, -gh + 0.06), STEEL, bev=0.008)
        add_rod(bm, (-0.07, s * 1.18, -gh + 0.06), (-0.12, s * 1.18, -gh + 0.28), 0.014, CHROME)
    add_box(bm, (0.012, 2.30, 0.02), (0.021, 0.0, -gh - 0.06), DARK)
    return finish_mesh(bm, "SM_Sklapac_zadne_celo")


def build_tip_cyl_stage(k, n, ell, radii):
    bm = bmesh.new()
    r = radii[k]
    add_cylinder(bm, r, ell, along_z((0.0, 0.0, ell * 0.5)), STEEL if k == 0 else CHROME, segments=10, bev=0.004)
    if k == 0:
        add_cylinder(bm, r * 1.10, 0.06, along_z((0.0, 0.0, 0.03)), DARK, segments=10)
        add_cylinder(bm, r * 0.55, r * 3.0, along_y((0.0, 0.0, -0.03)), DARK, segments=8)
        add_box(bm, (r * 1.4, r * 2.2, 0.12), (0.0, 0.0, 0.06), DARK, bev=0.005)
    else:
        add_cylinder(bm, r * 1.12, 0.04, along_z((0.0, 0.0, 0.02)), STEEL, segments=10)
    if k < n - 1:
        add_cylinder(bm, r * 1.06, 0.05, along_z((0.0, 0.0, ell - 0.025)), DARK, segments=10)
    if k == n - 1:
        add_cylinder(bm, r * 1.25, 0.05, along_z((0.0, 0.0, ell - 0.01)), STEEL, segments=10)
        add_cylinder(bm, r * 0.85, r * 3.2, along_y((0.0, 0.0, ell + 0.03)), DARK, segments=8)
    return finish_mesh(bm, "SM_Sklapac_valec_%d" % k)


def tip_cylinder_family(put):
    radii = [0.115 * (1.0 - 0.12 * k) for k in range(CYL_N)]
    for k in range(CYL_N):
        put(build_tip_cyl_stage(k, CYL_N, CYL_ELL, radii))


def tip_telescope(coll, name, parts, base_parent, base_pt, aim_parent, aim_pt):
    # teleskopicky valec: zaklad mieri osou +Z na ciel, stupne sa vysuvaju o (d - dlzka stupna) x k / (n - 1)
    base = new_object(coll, name + "_1", parts["Sklapac_valec_0"], base_pt, base_parent)
    aim = empty(coll, name + "_ciel", aim_pt, aim_parent)
    track(base, aim, "TRACK_Z")
    for k in range(1, CYL_N):
        stage = new_object(coll, "%s_%d" % (name, k + 1), parts["Sklapac_valec_%d" % k], (0.0, 0.0, 0.0), base)
        driver(stage, "location", 2, "(d - %.4f) * %.4f" % (CYL_ELL, k / (CYL_N - 1.0)), [("d", "DIST", (base, aim))])
    return base, aim


def build_side_lights():
    # bocne obrysove svetla na vonkajsej strane nosnikov (naves nema bocne listy, iba stredovy ram)
    bm = bmesh.new()
    y = BEAM_Y + 0.012
    for x in SIDE_LIGHT_X:
        add_box(bm, (0.17, 0.012, 0.07), (x, y + 0.006, 1.345), DARK)
        add_box(bm, (0.14, 0.025, 0.05), (x, y + 0.0145, 1.345), LAMP_OR, bev=0.006)
    return bm


def configure(length):
    # nastavi vsetky rozmery, ktore zavisia od dlzky (napravy, ram, bocne svetla, korba, valec sklapania...)
    length = max(length, MIN_LENGTH)
    x_rear = X_FRONT - length
    n_ax = 2 if length < 8.5 else 3
    last = x_rear + 1.40
    axles = tuple(last + AXLE_GAP * (n_ax - 1 - i) for i in range(n_ax))
    ramp_end = axles[0] + ARM_PIVOT.x + 0.35
    beam_bottom = [(1.52, COUPLING_Z), (-0.75, COUPLING_Z), (-1.60, 1.10), (ramp_end + 0.60, 1.10), (ramp_end, FRAME_BOT),
                   (axles[-1] - 0.60, FRAME_BOT), (axles[-1] - 0.95, 1.12), (x_rear + 0.10, 1.12)]
    deep = [-0.95]
    k = 0
    while -1.90 - 0.95 * k > x_rear + 0.35:
        deep.append(-1.90 - 0.95 * k)
        k += 1
    guard = ()
    lights = [0.85]
    while lights[-1] - 3.5 > x_rear + 1.0:
        lights.append(lights[-1] - 3.5)
    lights.append(x_rear + 0.40)
    hw, tilt, col = TIP_SIZES.get(length, (1.35 + 0.15 * round(length - 8.0), 44.0, 0))
    hinge_x = x_rear + 0.32
    u_front = BOX_FRONT - hinge_x
    a_u, a_v = u_front + 0.20, BOX_FLOOR + 0.92 * hw
    ds = []
    for i in range(61):
        th = math.radians(tilt) * i / 60.0
        ax = hinge_x + a_u * math.cos(th) - a_v * math.sin(th)
        az = HZ + a_u * math.sin(th) + a_v * math.cos(th)
        ds.append(math.hypot(ax - CYL_BX, az - CYL_BZ))
    ell = min(ds) * 0.985
    n = max(3, int(math.ceil(max(ds) * 1.03 / ell)))
    globals().update(dict(
        LENGTH=length, X_REAR=x_rear, AXLES=axles, BEAM_BOTTOM=beam_bottom, XBEAMS_DEEP=deep,
        FLOOR_X0=x_rear + 0.12, FLOOR_X1=X_FRONT - 0.05, FLOOR_LEN=X_FRONT - 0.05 - x_rear - 0.12,
        FLOOR_MID=(x_rear + 0.12 + X_FRONT - 0.05) * 0.5, GUARD_XS=guard, SIDE_LIGHT_X=lights, POSTS_X=(),
        DOOR_HINGE_X=x_rear - 0.045, SPARE_X=axles[-1] - 1.50, TOOLBOX_X=LEG_X - 0.60, CTRL_X=axles[-1] - 1.50 - 0.725,
        TIP_HW=hw, TIP_ANGLE=math.radians(tilt), BOX_MAT=BOX0 + col, HINGE_X=hinge_x, U_FRONT=u_front, A_U=a_u, A_V=a_v,
        CYL_N=n, CYL_ELL=ell, CYL_DMIN=min(ds), CYL_DMAX=max(ds)))


def length_tag(length):
    return ("%.1f" % length).replace(".", "_")


def clear_collection(coll):
    for obj in list(coll.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.get("sklapac"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_"):
            bpy.data.curves.remove(curve)


def build_parts(mats, tag):
    built = {}

    def put(mesh):
        built[mesh.name[3:].split(".")[0]] = mesh

    def put_lr(bm, name):
        mirrored = mirror_y(bm)
        put(finish_mesh(bm, name + "_L"))
        put(finish_mesh(mirrored, name + "_P"))

    common = [build_frame, build_kingpin_plate, build_bumper, build_toolbox, build_spare, build_controller,
              build_trailer_axle, build_wheel, build_shock_body, build_shock_rod, build_trailing_arm, build_air_bag,
              build_leg_inner, build_leg_cross, build_tip_box, build_tip_gate]
    for fn in common:
        put(fn())
    tip_cylinder_family(put)
    put_lr(build_leg_outer(), "SM_Sklapac_noha_vonkajsia")
    put_lr(build_side_guard(), "SM_Sklapac_zabrana")
    put_lr(build_rear_light(), "SM_Sklapac_zadne_svetlo")
    put_lr(build_side_lights(), "SM_Sklapac_bocne_svetla")
    put_lr(build_mudguard(0.72, 1.19, "frame"), "SM_Sklapac_blatnik")
    put_lr(build_spare_basket(), "SM_Sklapac_rezerva_kos")

    parts = {}
    for key, mesh in built.items():
        if key in LENGTH_PARTS:
            mesh.name = "SM_%s_%s" % (key, tag)
        elif key in SHARED_PARTS:
            bpy.data.meshes.remove(mesh)
            parts[key] = SHARED_PARTS[key]
            continue
        else:
            SHARED_PARTS[key] = mesh
        mesh["sklapac"] = 1
        for mat in mats:
            mesh.materials.append(mat)
        parts[key] = mesh
    return parts


# ---------------------------------------------------------------------------
# Zostava jedneho navesu
# ---------------------------------------------------------------------------

def build_trailer(coll, parts, rn, y_pos):
    def nm(text):
        return "%s_%s" % (rn, text)

    n_ax = len(AXLES)
    curtain = TRAILER_TYPE == "plachta"
    root = new_object(coll, rn, None, (0.0, y_pos, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.0
    set_prop(root, "Vyska_podvozku", 0.0, -0.06, 0.10, "Dofuknutie / vypustenie vankusov v metroch (zadok hore / dole)")
    set_prop(root, "Zdvih_napravy", 0.0, 0.0, 1.0, "0 = prva naprava dole, 1 = zdvihnuta (ovladac na boku)")
    set_prop(root, "Podpery", 0.0, 0.0, 1.0, "0 = podpery hore (na tahaci), 1 = spustene na zem")
    set_prop(root, "Rezerva_L", 1, 0, 1, "1 = lave rezervne koleso lezi v kosi pod ramom, 0 = prazdny kos")
    set_prop(root, "Rezerva_P", 1, 0, 1, "1 = prave rezervne koleso lezi v kosi pod ramom, 0 = prazdny kos")
    set_prop(root, "Sklopenie", 0.0, 0.0, 1.0, "0 = korba lezi, 1 = vyklopena (45 st.)")
    set_prop(root, "Zadne_celo", 0.0, 0.0, 1.0, "0 = zadne celo zatvorene, 1 = otvorene o 72 st.")
    if curtain:
        set_prop(root, "Plachta_L", 0.0, 0.0, 1.0, "0 = lava plachta zatiahnuta, 1 = odsunuta dopredu")
        set_prop(root, "Plachta_P", 0.0, 0.0, 1.0, "0 = prava plachta zatiahnuta, 1 = odsunuta dopredu")
        set_prop(root, "Zadne_dvere", 0.0, 0.0, 1.0, "0 = zatvorene, 1 = otvorene o 270 stupnov")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    # --- teren pod kazdou napravou (animacia) a napravy ---
    terrain = []
    for i, ax in enumerate(AXLES):
        t = empty(coll, nm("teren_%d" % (i + 1)), (ax, 0.0, WHEEL_R), root)
        t.empty_display_type = "PLAIN_AXES"
        t.empty_display_size = 0.3
        terrain.append(t)
    tvars = [("t%d" % (i + 1), "TRANSFORM", (terrain[i], "LOC_Z")) for i in range(n_ax)]
    rvars = [("r%d" % (i + 1), "TRANSFORM", (terrain[i], "ROT_X")) for i in range(n_ax)]
    body_vars = tvars + rvars + [prop("v", "Vyska_podvozku"), prop("l", "Zdvih_napravy")]
    span = -sum(AXLES) / n_ax
    zm = "((1 - l) * t1 + %s) / (%d - l)" % (" + ".join("t%d" % (i + 1) for i in range(1, n_ax)), n_ax)
    h = "(%.3f * (%s - %.3f) + v)" % (BODY_FOLLOW, zm, WHEEL_R)
    roll = "%.3f * ((1 - l) * r1 + %s) / (%d - l)" % (BODY_FOLLOW * 0.7, " + ".join("r%d" % (i + 1) for i in range(1, n_ax)), n_ax)
    axle_objs = []
    for i, ax in enumerate(AXLES):
        axle = new_object(coll, nm("naprava_%d" % (i + 1)), parts["Sklapac_naprava"], (ax, 0.0, WHEEL_R), root)
        if i == 0:
            # zdvihnuta naprava ide k ramu (o LIFT_HEIGHT nad kludovu polohu voci ramu) a nakloni sa s nim
            lifted = "%.3f + %.3f + %.4f * %s / %.3f" % (WHEEL_R, LIFT_HEIGHT, -ax, h, span)
            driver(axle, "location", 2, "(1 - l) * t1 + l * (%s)" % lifted, body_vars)
            driver(axle, "rotation_euler", 0, "(1 - l) * r1 + l * (%s)" % roll, body_vars)
        else:
            vars_i = [tvars[i], rvars[i]]
            driver(axle, "location", 2, "t%d" % (i + 1), vars_i)
            driver(axle, "rotation_euler", 0, "r%d" % (i + 1), vars_i)
        axle_objs.append(axle)

    # --- odpruzena skrina: otaca sa okolo capu (predok je na tahaci), zadok ide hore / dole s vankusmi ---
    body = new_object(coll, nm("ram"), parts["Sklapac_ram"], (0.0, 0.0, 0.0), root)
    pitch_expr = "atan(%s / %.3f)" % (h, span)
    driver(body, "rotation_euler", 1, pitch_expr, body_vars)
    driver(body, "rotation_euler", 0, roll, body_vars)
    # cap v tocni ostava na mieste: skrina sa otaca okolo bodu capu (0, 0, COUPLING_Z), nie okolo zeme
    driver(body, "location", 0, "-%.3f * cos(%s) * sin(%s)" % (COUPLING_Z, roll, pitch_expr), body_vars)
    driver(body, "location", 1, "%.3f * sin(%s)" % (COUPLING_Z, roll), body_vars)
    driver(body, "location", 2, "%.3f * (1 - cos(%s) * cos(%s))" % (COUPLING_Z, roll, pitch_expr), body_vars)
    body_parts = ["Sklapac_cap_deska", "Sklapac_zadny_naraznik"]
    for name in body_parts:
        new_object(coll, nm(name[PFX_LEN:]), parts[name], (0.0, 0.0, 0.0), body)
    new_object(coll, nm("naradi_skrinka"), parts["Sklapac_naradi_skrinka"], (TOOLBOX_X, 0.0, 0.0), body)
    new_object(coll, nm("ovladac_napravy"), parts["Sklapac_ovladac_napravy"], (CTRL_X, BEAM_Y + 0.13, 1.12), body)
    for side in ("L", "P"):
        names = ["Sklapac_zadne_svetlo_", "Sklapac_bocne_svetla_"]
        if len(parts["Sklapac_zabrana_" + side].vertices):
            names.append("Sklapac_zabrana_")
        for name in names:
            new_object(coll, nm(name[PFX_LEN:] + side), parts[name + side], (0.0, 0.0, 0.0), body)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        new_object(coll, nm("rezerva_kos_" + side), parts["Sklapac_rezerva_kos_" + side], (SPARE_X, 0.0, 0.0), body)
        spare = new_object(coll, nm("rezerva_" + side), parts["Sklapac_rezerva"], (SPARE_X, s * SPARE_Y, SPARE_Z), body, (90.0, 0.0, 0.0))
        for path_name in ("hide_viewport", "hide_render"):
            driver(spare, path_name, -1, "r < 0.5", [prop("r", "Rezerva_" + side)])

    # --- kolesa, ramena, vankuse, tlmice, blatniky ---
    path, seat_local, bag_bottom, _ = arm_geometry()
    bag_rest = FRAME_BOT - bag_bottom.z
    for i, ax in enumerate(AXLES):
        axle, n = axle_objs[i], i + 1
        for s, side in ((1.0, "L"), (-1.0, "P")):
            new_object(coll, nm("koleso_%d_%s" % (n, side)), parts["Sklapac_koleso"], (0.0, s * SPINDLE, 0.0), axle,
                       (0.0, 0.0, 0.0 if s > 0 else 180.0))
            aim = empty(coll, nm("rameno_ciel_%d_%s" % (n, side)), (0.0, s * RAIL_Y, ARM_CLAMP_Z), axle)
            arm = new_object(coll, nm("rameno_%d_%s" % (n, side)), parts["Sklapac_rameno"],
                             (ax + ARM_PIVOT.x, s * RAIL_Y, ARM_PIVOT.z), body)
            track(arm, aim, "TRACK_NEGATIVE_X")
            seat_aim = empty(coll, nm("vankus_ciel_%d_%s" % (n, side)), tuple(seat_local), arm)
            bag_top = (ax + bag_bottom.x, s * RAIL_Y, FRAME_BOT)
            bag = new_object(coll, nm("vankus_%d_%s" % (n, side)), parts["Sklapac_vankus"], bag_top, body)
            track(bag, seat_aim, "TRACK_NEGATIVE_Z")
            # vyska vankusa = vzdialenost bodu na rame a sedla na ramene (samostatny bod, aby sa necital sam)
            top_aim = empty(coll, nm("vankus_hore_%d_%s" % (n, side)), bag_top, body)
            driver(bag, "scale", 2, "d / %.4f" % bag_rest, [("d", "DIST", (top_aim, seat_aim))])
            link_pair(coll, nm("tlmic_%d_%s" % (n, side)), parts["Sklapac_tlmic_valec"], parts["Sklapac_tlmic_piestnica"],
                      axle, Vector((SHOCK_LOW.x, s * SHOCK_LOW.y, SHOCK_LOW.z)), body,
                      Vector((ax + SHOCK_UP.x, s * SHOCK_UP.y, SHOCK_UP.z)), "TRACK_Z", "TRACK_NEGATIVE_Z")
            new_object(coll, nm("blatnik_%d_%s" % (n, side)), parts["Sklapac_blatnik_" + side], (ax, 0.0, WHEEL_R), body)

    # --- elektricke podpery: vonkajsie nohy, vysuvacie nohy (idu na zem), spojovaci hriadel ---
    for s, side in ((1.0, "L"), (-1.0, "P")):
        new_object(coll, nm("noha_vonkajsia_" + side), parts["Sklapac_noha_vonkajsia_" + side], (LEG_X, s * LEG_Y, 0.0), body)
        inner = new_object(coll, nm("noha_vnutorna_" + side), parts["Sklapac_noha_vnutorna"], (LEG_X, s * LEG_Y, LEG_TRAVEL), body)
        driver(inner, "location", 2, "%.3f * (1 - p)" % LEG_TRAVEL, [prop("p", "Podpery")])
    new_object(coll, nm("podpery_traverza"), parts["Sklapac_podpery_traverza"], (LEG_X, 0.0, 0.0), body)
    # rovnaky ovladac (sipky hore a dole) aj pri nohach: na vonkajsej strane laveho stlpu nohy nad motorom nohy
    new_object(coll, nm("ovladac_podper"), parts["Sklapac_ovladac_napravy"], (LEG_X, LEG_Y + 0.07 + 0.082, 1.17), body)

    tip_rig(coll, parts, nm, body, prop)
    animate(root, terrain, curtain)
    return root


def build_curtain_parts(coll, parts, nm, body, prop):
    # --- stlpiky (schovaju sa pri odsunuti plachty) ---
    for s, side in ((1.0, "L"), (-1.0, "P")):
        for k, x in enumerate(POSTS_X):
            post = new_object(coll, nm("stlpik_%s_%d" % (side, k + 1)), parts["Sklapac_stlpik"],
                              (x, s * (HALF_W - 0.05), FLOOR_TOP), body)
            for path_name in ("hide_viewport", "hide_render"):
                driver(post, path_name, -1, "p > 0.02", [prop("p", "Plachta_" + side)])

    # --- plachty z dielikov: retaz klbov, kazdy dielik je dieta svojho klbu, odsuva sa ako harmonika ---
    for s, side in ((1.0, "L"), (-1.0, "P")):
        pv = prop("p", "Plachta_" + side)
        link = empty(coll, nm("plachta_%s_klb_0" % side), (CURTAIN_FRONT, s * CURTAIN_Y, CURTAIN_BOT), body)
        link.empty_display_size = 0.05
        driver(link, "location", 1, "%.4f * (%.4f + 0.5 * %.5f * sin(p * %.3f))" % (s, CURTAIN_Y, CURTAIN_W, CURTAIN_FOLD), [pv])
        driver(link, "rotation_euler", 2, "%.0f * p * %.3f" % (-s, CURTAIN_FOLD), [pv])
        new_object(coll, nm("plachta_%s_dielik_0" % side), parts["Sklapac_plachta_dielik"], (0.0, 0.0, 0.0), link)
        for i in range(1, CURTAIN_PANELS):
            link = empty(coll, nm("plachta_%s_klb_%d" % (side, i)), (-CURTAIN_W, 0.0, 0.0), link)
            link.empty_display_size = 0.05
            sign = s * (1.0 if i % 2 == 1 else -1.0)
            driver(link, "rotation_euler", 2, "%.0f * 2 * p * %.3f" % (sign, CURTAIN_FOLD), [pv])
            new_object(coll, nm("plachta_%s_dielik_%d" % (side, i)), parts["Sklapac_plachta_dielik"], (0.0, 0.0, 0.0), link)

    # --- zadne dvere (otvaraju sa o 270 stupnov az na bok navesu) ---
    for s, side in ((1.0, "L"), (-1.0, "P")):
        door = new_object(coll, nm("dvere_" + side), parts["Sklapac_dvere_" + side], (DOOR_HINGE_X, s * DOOR_HINGE_Y, 0.0), body)
        driver(door, "rotation_euler", 2, "%.0f * d * %.4f" % (-s, DOOR_OPEN), [prop("d", "Zadne_dvere")])


def tip_rig(coll, parts, nm, body, prop):
    # korba sa otaca okolo zavesu vzadu (predok ide hore), zadne celo okolo horneho cepu, valec vpredu mieri na ucho na prednej stene
    box = new_object(coll, nm("korba"), parts["Sklapac_korba"], (HINGE_X, 0.0, HZ), body)
    driver(box, "rotation_euler", 1, "%.5f * s" % -TIP_ANGLE, [prop("s", "Sklopenie")])
    gate = new_object(coll, nm("zadne_celo"), parts["Sklapac_zadne_celo"], (-0.06, 0.0, BOX_FLOOR + TIP_HW - 0.03), box)
    driver(gate, "rotation_euler", 1, "g * %.4f" % GATE_OPEN, [prop("g", "Zadne_celo")])
    tip_telescope(coll, nm("valec_sklapania"), parts, body, (CYL_BX, 0.0, CYL_BZ), box, (A_U, 0.0, A_V))


def animate(root, terrain, curtain):
    # jazda cez nerovnosti (zadne napravy ich prejdu neskor), potom ukazka ovladacov
    bumps = [(1, 0.0, 0.0), (12, 0.05, 4.0), (24, -0.03, -3.0), (36, 0.06, -5.0), (48, -0.02, 3.0), (60, 0.0, 0.0)]
    for i, ax in enumerate(AXLES):
        delay = int(round((-ax - 4.0) * 4.0))
        amp = 1.0 - 0.1 * i
        key(terrain[i], "location", 2, [(f + delay, WHEEL_R + z * amp) for f, z, _ in bumps])
        key(terrain[i], "rotation_euler", 0, [(f + delay, math.radians(r * amp)) for f, _, r in bumps])

    def keys(prop_name, frames):
        for frame, value in frames:
            root[prop_name] = value
            root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)

    keys("Vyska_podvozku", [(1, 0.0), (95, 0.0), (115, 0.10), (135, 0.10), (155, -0.06), (170, -0.06), (185, 0.0)])
    keys("Zdvih_napravy", [(1, 0.0), (195, 0.0), (215, 1.0), (240, 1.0), (258, 0.0)])
    keys("Podpery", [(1, 0.0), (270, 0.0), (300, 1.0), (340, 1.0), (370, 0.0)])
    keys("Sklopenie", [(1, 0.0), (400, 0.0), (500, 1.0), (550, 1.0), (640, 0.0)])
    keys("Zadne_celo", [(1, 0.0), (415, 0.0), (445, 1.0), (590, 1.0), (625, 0.0)])


COMMON_SECTIONS = [
    ("PODPERY, REZERVA, SKRINKA, OVLADAC", ["Sklapac_noha_vonkajsia_L", "Sklapac_noha_vonkajsia_P", "Sklapac_noha_vnutorna",
                                            "Sklapac_podpery_traverza", "Sklapac_naradi_skrinka", "Sklapac_ovladac_napravy",
                                            "Sklapac_rezerva", "Sklapac_rezerva_kos_L", "Sklapac_rezerva_kos_P"]),
    ("BLATNIKY", ["Sklapac_blatnik_L", "Sklapac_blatnik_P"]),
    ("NAPRAVY A PEROVANIE", ["Sklapac_naprava", "Sklapac_koleso", "Sklapac_rameno", "Sklapac_vankus", "Sklapac_tlmic_valec",
                             "Sklapac_tlmic_piestnica"]),
]
SHARED_TYPE_SECTION = {
    "sklapac": ("SKLAPAC - SPOLOCNE", ["Sklapac_cap_deska"]),
    "plachta": ("SKRINA - SPOLOCNE", ["Sklapac_cap_deska", "Sklapac_celo", "Sklapac_dvere_L", "Sklapac_dvere_P", "Sklapac_stlpik"]),
    "plato": ("PLATO - SPOLOCNE", ["Sklapac_cap_deska", "Sklapac_celo"]),
}
LENGTH_SECTION = {
    "sklapac": ["Sklapac_ram", "Sklapac_korba", "Sklapac_zadne_celo", "Sklapac_zadny_naraznik", "Sklapac_zadne_svetlo_L", "Sklapac_zadne_svetlo_P",
                "Sklapac_bocne_svetla_L", "Sklapac_bocne_svetla_P", "Sklapac_zabrana_L", "Sklapac_zabrana_P"],
    "plachta": ["Sklapac_ram", "Sklapac_podlaha", "Sklapac_strecha", "Sklapac_zadny_portal", "Sklapac_plachta_dielik", "Sklapac_zadny_naraznik",
                "Sklapac_zadne_svetlo_L", "Sklapac_zadne_svetlo_P", "Sklapac_bocne_svetla_L", "Sklapac_bocne_svetla_P", "Sklapac_zabrana_L",
                "Sklapac_zabrana_P", "Sklapac_zastera_bok_L", "Sklapac_zastera_bok_P"],
    "plato": ["Sklapac_ram", "Sklapac_podlaha", "Sklapac_zadny_lem", "Sklapac_zadny_naraznik", "Sklapac_zadne_svetlo_L", "Sklapac_zadne_svetlo_P",
              "Sklapac_bocne_svetla_L", "Sklapac_bocne_svetla_P", "Sklapac_zabrana_L", "Sklapac_zabrana_P", "Sklapac_zastera_bok_L", "Sklapac_zastera_bok_P"],
}


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)
    SHARED_PARTS.clear()
    mats = [get_material(*m) for m in MATERIALS]

    roots, variants = [], []
    for index, length in enumerate(VARIANTS):
        configure(length)
        tag = length_tag(LENGTH)
        parts = build_parts(mats, tag)
        rn = "%s_%s" % (NAME_PREFIX, tag)
        roots.append(build_trailer(child_collection(coll, rn), parts, rn, Y_POS - index * 4.0))
        variants.append(dict(length=LENGTH, tag=tag, parts=parts, axles=AXLES, rear=X_REAR, root=rn, spare=SPARE_X, tool=TOOLBOX_X,
                             guard=GUARD_XS, ctrl=CTRL_X, posts=POSTS_X, panels=CURTAIN_PANELS, panel_w=CURTAIN_W,
                             hinge=DOOR_HINGE_X, box_len=U_FRONT + 0.10, hw=TIP_HW, tilt=math.degrees(TIP_ANGLE), cyl_n=CYL_N, cyl_ell=CYL_ELL,
                             dmin=CYL_DMIN, dmax=CYL_DMAX, hinge_x=HINGE_X))
    scene.frame_start, scene.frame_end = 1, 660
    scene.frame_set(1)

    # --- katalog dielov: spolocne diely jedenkrat, potom diely podla dlzky ---
    kit = child_collection(coll, "Sklapac_diely")
    lines = ["Naves (sklapaci) - diely (rozmery X x Y x Z v metroch). Predok = +X, lava = +Y, pociatok = zem pod capom.", ""]
    sections = [SHARED_TYPE_SECTION[TRAILER_TYPE]] + COMMON_SECTIONS
    for v in variants:
        sections.append(("DIELY PRE DLZKU %.1f m" % v["length"], [(k, v["parts"]) for k in LENGTH_SECTION[TRAILER_TYPE] +
                                                                sorted(x for x in v["parts"] if x.startswith("Sklapac_valec_"))]))
    y_cursor = 4.0
    for title, keys in sections:
        items = []
        for k in keys:
            if isinstance(k, tuple):
                items.append((k[0], k[1][k[0]]))
            else:
                items.append((k, variants[0]["parts"][k]))
        items = [(k, m) for k, m in items if len(m.vertices)]
        depth = max(bounds(m)[1][1] - bounds(m)[1][0] for _, m in items)
        row_y = y_cursor + depth * 0.5
        add_label(kit, title, (-16.0, row_y, 0.001), mats[DARK])
        x = -14.0
        lines.append("== %s ==" % title)
        for k, mesh in items:
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            slot = max(x1 - x0, 1.2)
            label = mesh.name[3:]
            new_object(kit, "Diel_" + label[PFX_LEN:], mesh, (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0))
            add_label(kit, "%s\n%.2f x %.2f x %.2f" % (label, x1 - x0, y1 - y0, z1 - z0), (x + slot * 0.5, row_y - depth * 0.5 - 0.2, 0.001),
                      mats[DARK])
            lines.append("%-34s %.2f x %.2f x %.2f" % (label, x1 - x0, y1 - y0, z1 - z0))
            x += slot + 0.35
        lines.append("")
        y_cursor += depth + 0.9

    def vec(v):
        return "(%.3f, %.3f, %.3f)" % tuple(v)

    _, seat_local, bag_bottom, _ = arm_geometry()
    lines += ["DLZKY: " + ", ".join("%.1f m (%d napravy)" % (v["length"], len(v["axles"])) for v in variants), ""]
    for v in variants:
        lines.append("%s: napravy x = %s; koniec skrine x = %.2f; stred rezervy x = %.2f; skrinka x = %.2f; ovladac x = %.2f; zabrany x = %s" % (
            v["root"], ", ".join("%.2f" % a for a in v["axles"]), v["rear"], v["spare"], v["tool"], v["ctrl"],
            ", ".join("%.2f" % x for x in v["guard"]) or "bez"))
        if TRAILER_TYPE == "plachta":
            lines.append("    stlpiky x = %s; plachta %d dielikov po %.3f m; zavesy dveri x = %.3f" % (
                ", ".join("%.2f" % x for x in v["posts"]), v["panels"], v["panel_w"], v["hinge"]))
    lines += [
        "",
        "AKO JE TO POSKLADANE (hierarchia v kolekciach podla dlzky), suradnice od pociatku navesu (zem pod capom):",
        "  Hlavny objekt navesu (prazdny) - posuvaj nim cely naves, vlastnosti = ovladanie (popis na zaciatku skriptu).",
        "  Zapriahnutie: cap navesu da na stred tocne tahaca (x tocne + Posun_tocne); spodok dosky s capom je vo vyske %.2f m = vrch tocne." % COUPLING_Z,
        "  Skrina (ram): otaca sa okolo capu, zadok ide hore o Vyska_podvozku + %.1f x pohyb naprav." % BODY_FOLLOW,
        "  Napravy: pivot v osi kolies (z = %.3f); kolesa su ich deti (pravu stranu otoc o 180 st.). Prva naprava sa da zdvihnut." % WHEEL_R,
        "  Ramena: cap na rame v x napravy + %.2f, z %.2f; mieria osou -X na bod %s pod napravou." % (
            ARM_PIVOT.x, ARM_PIVOT.z, vec((0, RAIL_Y, ARM_CLAMP_Z))),
        "  Vankuse: hore na rame (x napravy %.2f, z %.2f), mieria osou -Z na sedlo na ramene %s; vysku natiahni mierkou Z = vzdialenost / %.3f." % (
            bag_bottom.x, FRAME_BOT, vec(seat_local), FRAME_BOT - bag_bottom.z),
        "  Tlmice: valec na naprave mieri osou +Z na horne oko na rame, piestnica z horneho oka mieri osou -Z dole.",
        "    dole %s (od napravy), hore x napravy + %.2f, y %.2f, z %.2f." % (vec(SHOCK_LOW), SHOCK_UP.x, SHOCK_UP.y, SHOCK_UP.z),
        "  Podpery: vonkajsie nohy v x %.2f, y +-%.2f; vnutorne nohy idu o %.2f m dole (Podpery 0 -> 1). Podpery su elektricke, bez kliky." % (
            LEG_X, LEG_Y, LEG_TRAVEL),
        "  Rezerva: dve kolesa vedla seba (lave a prave, stredy v y = +-%.2f, z = %.3f), lezia vodorovne pod ramom (otocene o 90 st. okolo X, plocha disku hore); kazde ma kos z dvoch U-rurok; vlastnosti Rezerva_L a Rezerva_P." % (SPARE_Y, SPARE_Z),
        "  Ovladac napravy: na vonkajsej strane laveho nosnika hned za lavou rezervou (pivot na vonkajsej strane v y = %.2f, z = 1.12, x = x rezervy - 0.725), smeruje do +Y; sipky hore a dole su nakreslene na tlacidlach." % (BEAM_Y + 0.13),
        "  Rovnaky ovladac je aj pri podperach (objekt ovladac_podper): na vonkajsej strane laveho stlpu nohy, pivot v (%.2f, %.2f, 1.17), smeruje do +Y." % (LEG_X, LEG_Y + 0.07 + 0.082),
        "  Prave diely _P su zrkadlove. Blatniky, svetla a zabrany maju pivot v pociatku navesu alebo v osi kolesa.",
        "V Unreali: kazdy par 'mieri na' urob cez Find Look at Rotation (alebo Look At v Control Rig / Animation Blueprinte).",
    ]
    if TRAILER_TYPE == "plachta":
        lines += [
            "  Plachta: kazdy dielik je dieta klbu na svojom prednom okraji; klb i je dieta predchadzajuceho dielika a je o -sirku dielika (X) od neho.",
            "    Klby sa striedavo otacaju o +-2 x %.2f rad (harmonika). Prvy klb je na rame v %s (lava), pre pravu stranu zrkadlovo." % (
                CURTAIN_FOLD, vec((CURTAIN_FRONT, CURTAIN_Y, CURTAIN_BOT))),
            "  Stlpiky (pivot dole, z = %.2f) sa pri odsunuti plachty schovaju. Dvere: otacaju sa okolo Z o 270 st. (lave zaporne, prave kladne)." % FLOOR_TOP,
        ]

    lines += [
        "",
        "SKLAPACI NAVES: korba (pivot v zavese vzadu: x = zadok + 0.32, z = %.2f, os Y) sa otaca o -Sklopenie x sklon (45 st. a menej podla velkosti) okolo Y," % HZ,
        "  zadne celo je jej dieta (pivot hore na zadnej hrane, os Y), otvara sa o Zadne_celo x 72 st. dozadu a hore.",
        "  Valec sklapania: zaklad na rame vpredu (x = %.2f, z = %.2f), ciel na ucho na prednej stene korby (objekt valec_sklapania_ciel je dieta korby)," % (CYL_BX, CYL_BZ),
        "    teleskopicky s 6 stupnami (dlzka stupna podla velkosti, pozri nizsie); zaklad mieri osou +Z na ciel, stupen k sa vysuva o (d - dlzka stupna) x k / (n - 1).",
        "  Vlastnosti: Sklopenie (0 = korba lezi, 1 = vyklopena), Zadne_celo (0 = zatvorene, 1 = otvorene); ostatne ako pri plate (Vyska_podvozku, Zdvih_napravy, Podpery, Rezerva_L/P).",
        "  Animacia (snimky 1 az 660): jazda, vyska, zdvih napravy, podpery, potom sklopenie korby s otvorenim zadneho cela a spat.",
    ]
    for v in variants:
        lines.append("  %s: korba %.2f m, vyska bokov %.2f m, sklon %.0f st., valec %d stupnov po %.2f m (vzdialenost %.2f az %.2f m), zavesy x = %.2f" % (
            v["root"], v["box_len"], v["hw"], v["tilt"], v["cyl_n"], v["cyl_ell"], v["dmin"], v["dmax"], v["hinge_x"]))

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        done = set()
        for v in variants:
            for mesh in v["parts"].values():
                if mesh.name not in done and len(mesh.vertices):
                    done.add(mesh.name)
                    export_mesh(coll, mesh, mesh.name)
        with open(os.path.join(EXPORT_DIR, COLLECTION + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    select_only(roots[0])
    print("\n".join(lines))


main()

