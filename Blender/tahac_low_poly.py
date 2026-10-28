# Stylizovany low poly tahac (americky, kabina nad motorom) pre Blender 3.0 a novsi.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
# Vytvori kolekciu "Tahac": karoseriu "SM_Tahac" a kolesa (predne jednoduche, zadne dvojmontaz).
# Do domovskeho priecinka ulozi 3 FBX pre Unreal:
#   SM_Tahac.fbx               - karoseria bez kolies (pivot na zemi)
#   SM_Tahac_KolesoPredne.fbx  - predne koleso (pivot v strede osi), 2x
#   SM_Tahac_KolesoZadne.fbx   - zadna dvojmontaz (pivot v strede osi), 4x
# Pozicie kolies sa vypisu v konzole (Window -> Toggle System Console).
# Skript sa da spustit znova: stary tahac sa nahradi novym.

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

NAME = "SM_Tahac"
FRONT_WHEEL = "SM_Tahac_KolesoPredne"
REAR_WHEEL = "SM_Tahac_KolesoZadne"
COLLECTION = "Tahac"
EXPORT_FBX = True
EXPORT_DIR = os.path.expanduser("~")

# Rozmery v metroch (zem je z = 0, predok je na +X)
WHEEL_R = 0.52
WHEEL_W = 0.30
WHEEL_SIDES = 14            # hrany pneumatiky - menej = hranatejsie
TRACK_FRONT = 1.03          # stred predneho kolesa od stredu auta
TRACK_REAR = 0.90           # stred zadnej dvojmontaze od stredu auta
DUAL_GAP = 0.33             # vzdialenost dvoch pneumatik vo dvojmontazi
AXLES_X = [1.85, -1.35, -2.70]

# Farby (zmen podla chuti)
PAINT_LOW = (0.30, 0.24, 0.16, 1.0)   # bezova
PAINT_TOP = (0.22, 0.015, 0.03, 1.0)  # vinova

# (nazov, farba, kovovost, drsnost)
MATERIALS = [
    ("Tahac_LakSpodny", PAINT_LOW, 0.0, 0.45),
    ("Tahac_LakHorny", PAINT_TOP, 0.0, 0.40),
    ("Tahac_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.18),
    ("Tahac_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.60),
    ("Tahac_Sklo", (0.02, 0.03, 0.04, 1.0), 0.0, 0.05),
    ("Tahac_Svetla", (0.95, 0.95, 0.90, 1.0), 0.0, 0.20),
    ("Tahac_Oranzova", (1.00, 0.32, 0.02, 1.0), 0.0, 0.30),
    ("Tahac_Cervena", (0.70, 0.01, 0.01, 1.0), 0.0, 0.30),
    ("Tahac_Pneu", (0.015, 0.015, 0.015, 1.0), 0.0, 0.90),
    ("Tahac_Disk", (0.60, 0.60, 0.62, 1.0), 0.9, 0.30),
]
LOW, TOP, CHROME, DARK, GLASS, LIGHT, AMBER, RED, TIRE, RIM = range(10)
SIDES_LR = (-1.0, 1.0)


# ---------------------------------------------------------------------------
# Skladanie z tvarov so zrazenymi hranami
# ---------------------------------------------------------------------------

def set_material(faces, index):
    for f in faces:
        f.material_index = index


def faces_of(verts):
    return {f for v in verts for f in v.link_faces}


def bevel(bm, edges, offset):
    if offset > 0.0 and edges:
        bmesh.ops.bevel(bm, geom=list(edges), offset=offset, segments=1, profile=0.5,
                        affect="EDGES", clamp_overlap=True)


def add_box(bm, size, location, mat, bev=0.0):
    matrix = Matrix.Translation(Vector(location)) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    verts = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)["verts"]
    set_material(faces_of(verts), mat)
    bevel(bm, {e for v in verts for e in v.link_edges}, min(bev, min(size) * 0.45))


def add_cylinder(bm, radius, depth, matrix, mat, segments=8, bev=0.0):
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                  radius1=radius, radius2=radius, depth=depth, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    caps = [f for f in faces if len(f.verts) == segments]
    bevel(bm, {e for f in caps for e in f.edges}, min(bev, radius * 0.4, depth * 0.45))


def add_prism(bm, bottom, top, mat, bev=0.0):
    # 4 body dole + 4 body hore v rovnakom poradi -> uzavrete teleso (klin, skosena plocha)
    b = [bm.verts.new(p) for p in bottom]
    t = [bm.verts.new(p) for p in top]
    faces = [bm.faces.new(b[::-1]), bm.faces.new(t)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(bm.faces.new((b[i], b[j], t[j], t[i])))
    set_material(faces, mat)
    bevel(bm, {e for f in faces for e in f.edges}, bev)


def along_x(location):
    return Matrix.Translation(Vector(location)) @ Matrix.Rotation(math.radians(90.0), 4, "Y")


def along_y(location=(0.0, 0.0, 0.0)):
    return Matrix.Translation(Vector(location)) @ Matrix.Rotation(math.radians(90.0), 4, "X")


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
# Karoseria
# ---------------------------------------------------------------------------

def build_cab(bm):
    # kabina: bezova spodna cast, vinovy pas so strechou, vinovy spojler
    add_box(bm, (2.20, 2.45, 1.90), (1.65, 0.0, 2.10), LOW, bev=0.08)
    add_box(bm, (2.20, 2.45, 0.30), (1.65, 0.0, 3.20), TOP, bev=0.08)
    add_prism(bm,
              [(0.60, -1.20, 3.35), (2.30, -1.20, 3.35), (2.30, 1.20, 3.35), (0.60, 1.20, 3.35)],
              [(0.60, -1.00, 4.00), (1.40, -1.00, 4.00), (1.40, 1.00, 4.00), (0.60, 1.00, 4.00)],
              TOP, bev=0.07)

    # predne sklo z dvoch casti, stierace
    for y in SIDES_LR:
        add_box(bm, (0.04, 1.02, 0.78), (2.76, y * 0.53, 2.62), GLASS, bev=0.015)
        add_box(bm, (0.02, 0.60, 0.03), (2.785, y * 0.50, 2.27), DARK)
    add_box(bm, (0.05, 0.05, 0.80), (2.765, 0.0, 2.62), CHROME)

    # dvere (obrys), bocne okna, kluky, schodiky za prednym kolesom
    for y in SIDES_LR:
        for x in (1.55, 2.65):
            add_box(bm, (0.015, 0.01, 1.75), (x, y * 1.228, 2.125), DARK)
        add_box(bm, (1.10, 0.01, 0.015), (2.10, y * 1.228, 1.25), DARK)
        add_box(bm, (1.10, 0.01, 0.015), (2.10, y * 1.228, 3.00), DARK)
        add_box(bm, (0.85, 0.04, 0.62), (2.15, y * 1.235, 2.62), GLASS, bev=0.015)
        add_box(bm, (0.15, 0.03, 0.04), (1.70, y * 1.24, 2.15), CHROME)
        add_box(bm, (0.40, 0.25, 0.05), (1.05, y * 1.12, 0.95), CHROME)
        add_box(bm, (0.40, 0.25, 0.05), (1.05, y * 1.12, 0.62), CHROME)

    # oranzove svetielka na prednej hrane strechy
    for y in (-0.30, -0.15, 0.0, 0.15, 0.30, -1.05, 1.05):
        add_box(bm, (0.06, 0.10, 0.06), (2.77, y, 3.22), AMBER, bev=0.01)

    # trubky na streche
    for y in SIDES_LR:
        for i, length in enumerate((0.30, 0.40, 0.50)):
            add_cylinder(bm, 0.045, length, along_x((2.75 - length * 0.5, y * (0.70 + i * 0.10), 3.45)),
                         CHROME, segments=6)

    # velke zrkadla na ramenach
    for y in SIDES_LR:
        add_box(bm, (0.04, 0.38, 0.04), (2.60, y * 1.40, 3.00), CHROME)
        add_box(bm, (0.04, 0.38, 0.04), (2.60, y * 1.40, 2.35), CHROME)
        add_box(bm, (0.08, 0.20, 0.75), (2.60, y * 1.62, 2.67), CHROME, bev=0.02)
        add_box(bm, (0.01, 0.16, 0.68), (2.555, y * 1.62, 2.67), GLASS)


def build_front(bm):
    # maska: chromovy ram, tmave pozadie, vodorovne rebra
    add_box(bm, (0.06, 1.25, 0.95), (2.77, 0.0, 1.75), CHROME, bev=0.02)
    add_box(bm, (0.03, 1.10, 0.80), (2.80, 0.0, 1.75), DARK)
    for i in range(8):
        add_box(bm, (0.03, 1.08, 0.025), (2.815, 0.0, 1.42 + i * 0.095), CHROME)

    # svetla: chromovy ramik s dvoma okruhlymi svetlami, nad nim smerovka
    for y in SIDES_LR:
        add_box(bm, (0.05, 0.30, 0.52), (2.78, y * 0.88, 1.62), CHROME, bev=0.02)
        add_box(bm, (0.02, 0.25, 0.46), (2.80, y * 0.88, 1.62), DARK)
        for z in (1.50, 1.74):
            add_cylinder(bm, 0.10, 0.04, along_x((2.815, y * 0.88, z)), LIGHT, segments=10)
        add_box(bm, (0.05, 0.26, 0.09), (2.78, y * 0.88, 2.00), AMBER, bev=0.01)

    # chromovy naraznik so zrazenymi rohmi, otvory a tabulka
    add_box(bm, (0.35, 2.55, 0.40), (2.86, 0.0, 0.95), CHROME, bev=0.09)
    for y in (-0.75, -0.55, 0.55, 0.75):
        add_box(bm, (0.02, 0.10, 0.14), (3.04, y, 0.98), DARK)
    add_box(bm, (0.02, 0.32, 0.15), (3.04, 0.0, 0.98), LIGHT)


def build_chassis(bm):
    rear_mid = (AXLES_X[1] + AXLES_X[2]) * 0.5

    # ram
    for y in (-0.48, 0.48):
        add_box(bm, (6.10, 0.18, 0.30), (-0.30, y, 0.85), DARK)

    # chromove nadrze s tmavymi pasmi
    for y in SIDES_LR:
        add_cylinder(bm, 0.30, 1.10, along_x((0.15, y * 0.83, 0.95)), CHROME, segments=12, bev=0.04)
        for x in (-0.20, 0.50):
            add_cylinder(bm, 0.315, 0.06, along_x((x, y * 0.83, 0.95)), DARK, segments=12)

    # vyfuk za kabinou s krytom
    add_cylinder(bm, 0.075, 2.60, Matrix.Translation((0.42, 1.00, 2.60)), CHROME, segments=8)
    add_cylinder(bm, 0.095, 0.90, Matrix.Translation((0.42, 1.00, 2.45)), RIM, segments=8)

    # plosina nad zadnymi kolesami a tocnica
    add_box(bm, (2.60, 2.30, 0.06), (rear_mid, 0.0, 1.15), DARK, bev=0.02)
    add_box(bm, (0.90, 0.90, 0.10), (rear_mid + 0.30, 0.0, 1.22), DARK)
    add_cylinder(bm, 0.45, 0.10, Matrix.Translation((rear_mid + 0.30, 0.0, 1.31)), RIM, segments=12, bev=0.02)

    # zasterky za kolesami
    for y in SIDES_LR:
        add_box(bm, (0.03, 0.60, 0.55), (AXLES_X[2] - 0.65, y * TRACK_REAR, 0.55), DARK)

    # zadna lista so svetlami
    add_box(bm, (0.12, 2.30, 0.14), (-3.30, 0.0, 0.80), DARK)
    for y in SIDES_LR:
        add_box(bm, (0.03, 0.22, 0.10), (-3.37, y * 0.95, 0.80), RED)
        add_box(bm, (0.03, 0.12, 0.10), (-3.37, y * 0.72, 0.80), AMBER)


def build_body():
    bm = bmesh.new()
    build_cab(bm)
    build_front(bm)
    build_chassis(bm)
    return finish_mesh(bm, NAME)


# ---------------------------------------------------------------------------
# Kolesa (os pozdlz Y, pivot v strede)
# ---------------------------------------------------------------------------

def add_tire(bm, y):
    m = along_y((0.0, y, 0.0))
    add_cylinder(bm, WHEEL_R, WHEEL_W, m, TIRE, segments=WHEEL_SIDES, bev=0.06)
    add_cylinder(bm, WHEEL_R * 0.62, WHEEL_W + 0.012, m, RIM, segments=12, bev=0.02)
    add_cylinder(bm, WHEEL_R * 0.28, WHEEL_W + 0.06, m, CHROME, segments=10, bev=0.02)
    add_cylinder(bm, 0.06, WHEEL_W + 0.12, m, DARK, segments=6)


def build_wheel(name, dual):
    bm = bmesh.new()
    if dual:
        add_tire(bm, -DUAL_GAP * 0.5)
        add_tire(bm, DUAL_GAP * 0.5)
    else:
        add_tire(bm, 0.0)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Materialy, scena, export
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


def add_materials(mesh):
    for name, color, metallic, roughness in MATERIALS:
        mesh.materials.append(get_material(name, color, metallic, roughness))


def clear_collection(coll):
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for name in (NAME, FRONT_WHEEL, REAR_WHEEL):
        mesh = bpy.data.meshes.get(name)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def select_only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def export_fbx(obj, path):
    select_only(obj)
    try:
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                                 apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE")
        print("Ulozene:", path)
    except Exception as error:
        print("FBX sa nepodarilo ulozit:", error)


def export_wheel(coll, mesh):
    # koleso sa exportuje samostatne v strede sveta, aby malo pivot v osi
    temp = bpy.data.objects.new(mesh.name, mesh)
    coll.objects.link(temp)
    export_fbx(temp, os.path.join(EXPORT_DIR, mesh.name + ".fbx"))
    bpy.data.objects.remove(temp, do_unlink=True)


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)

    body_mesh = build_body()
    front_mesh = build_wheel(FRONT_WHEEL, dual=False)
    rear_mesh = build_wheel(REAR_WHEEL, dual=True)
    for mesh in (body_mesh, front_mesh, rear_mesh):
        add_materials(mesh)

    body = bpy.data.objects.new(NAME, body_mesh)
    coll.objects.link(body)

    print("Pozicie kolies (m, voci pivotu karoserie):")
    for i, x in enumerate(AXLES_X):
        mesh, track = (front_mesh, TRACK_FRONT) if i == 0 else (rear_mesh, TRACK_REAR)
        for side, y in (("L", track), ("P", -track)):
            wheel = bpy.data.objects.new("Koleso_%d%s" % (i + 1, side), mesh)
            wheel.location = (x, y, WHEEL_R)
            wheel.parent = body
            coll.objects.link(wheel)
            print("  %s (%s): x=%.2f y=%.2f z=%.2f" % (wheel.name, mesh.name, x, y, WHEEL_R))

    if EXPORT_FBX:
        export_fbx(body, os.path.join(EXPORT_DIR, NAME + ".fbx"))
        export_wheel(coll, front_mesh)
        export_wheel(coll, rear_mesh)

    select_only(body)
    print("Hotovo: %s (%d vrcholov), kolesa %d / %d vrcholov"
          % (NAME, len(body_mesh.vertices), len(front_mesh.vertices), len(rear_mesh.vertices)))


main()
