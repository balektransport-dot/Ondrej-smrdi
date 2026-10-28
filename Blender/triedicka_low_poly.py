# Stylizovana low poly pasova triedicka materialov (mobilne dvojsitove triedenie) pre Blender 3.0 a novsi: nasypka so zalozenym podavacim pasom, vibracne dvojsito (horne a dolne sito, pruziny,
# vibracne motory), tri vystupne pasove dopravniky (hrube = nadsitne na osi, stredne = vlavo, jemne = vpravo) s kamenmi, motorovy diel s dvierkami, vodny rozstrek, plosina s rebrikom a styri hromady
# (vstup, nasypka, hrube, stredne, jemne). Vsetko je demontovatelne po dieloch (uchyty), animacia je na uchytoch a riadi ju niekolko vlastnosti na hlavnom objekte.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Triedicka" (podkolekcia Triedicka_pasova) a Triedicka_diely (kazdy diel samostatne s menovkou). Ovladanie vlastnostami na hlavnom objekte (panel N -> Item alebo
# Object -> Custom Properties), popis v subore Triedicka.txt. Predok = +X (hrube dopravnik), nasypka vzadu (-X), lava strana = +Y. Pociatok = zem pod stredom podvozku.
# Do priecinka Triedicka v domovskom priecinku ulozi FBX kazdeho dielu a textovy subor s popisom skladania. Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Triedicka"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Triedicka")
DOC_FILE = "Triedicka.txt"
DOC_TITLE = "Pasova triedicka materialov"
FRAME_END = 1000
KIT_Y0 = 16.0


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
# Materialy (spolocne pre drvic a triedicku)
# ---------------------------------------------------------------------------

MATERIALS = [
    ("KM_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0, 1.0),
    ("KM_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0, 1.0),
    ("KM_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0, 1.0),
    ("KM_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("KM_Disk", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("KM_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("KM_Sklo", (0.05, 0.10, 0.15, 1.0), 0.0, 0.05, 0.0, 0.88),
    ("KM_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("KM_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("KM_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0, 1.0),
    ("KM_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("KM_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0, 1.0),
    ("KM_Pozink", (0.55, 0.57, 0.58, 1.0), 0.6, 0.45, 0.0, 1.0),
    ("KM_Plast", (0.13, 0.135, 0.145, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("KM_Siva", (0.40, 0.42, 0.45, 1.0), 0.5, 0.50, 0.0, 1.0),
    ("KM_Interier", (0.10, 0.10, 0.11, 1.0), 0.0, 0.70, 0.0, 1.0),
    ("KM_Sedadlo", (0.20, 0.19, 0.17, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("KM_Lak_oranzovy", (0.88, 0.38, 0.04, 1.0), 0.3, 0.40, 0.0, 1.0),
    ("KM_Lak_siedy", (0.20, 0.21, 0.23, 1.0), 0.3, 0.50, 0.0, 1.0),
    ("KM_Lak_modry", (0.07, 0.22, 0.46, 1.0), 0.3, 0.40, 0.0, 1.0),
    ("KM_Pas", (0.04, 0.04, 0.045, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("KM_Pas_lista", (0.11, 0.11, 0.12, 1.0), 0.0, 0.80, 0.0, 1.0),
    ("KM_Oblozenie", (0.17, 0.17, 0.18, 1.0), 0.7, 0.45, 0.0, 1.0),
    ("KM_Kamen", (0.34, 0.32, 0.30, 1.0), 0.0, 0.95, 0.0, 1.0),
    ("KM_Strk", (0.46, 0.43, 0.38, 1.0), 0.0, 0.95, 0.0, 1.0),
    ("KM_Piesok", (0.62, 0.52, 0.34, 1.0), 0.0, 0.95, 0.0, 1.0),
    ("KM_Vystraha", (0.90, 0.30, 0.02, 1.0), 0.0, 0.50, 0.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, GLASS, LAMP_OR, LAMP_RED, LAMP_WHITE, RED, WHITE, GALV, PLAST, GRAY, INT, SEAT,
 PAINT_ORG, PAINT_GRY, PAINT_BLU, PAS, PAS_L, LINER, ROCK, GRAVEL, SAND, WARN) = range(27)


# ---------------------------------------------------------------------------
# Spolocny zaklad: zoznamy dielov a scen, zrazene hrany s dvoma segmentmi, hladke tienovanie s ostrymi hranami nad 50 st., export, zostavenie sceny
# ---------------------------------------------------------------------------

PART_MAKERS = []
SCENE_BUILDERS = []
DOC_EXTRA = []
CATALOG_EXTRA = []
SIDES_LR = (-1.0, 1.0)
D2R = 0.017453
SHARP_ANGLE = math.radians(50.0)


def bevel(bm, edges, offset, mat):
    # zrazene hrany (2 segmenty = zaoblene); nove plochy dostanu farbu dielu
    if offset > 0.0 and edges:
        res = bmesh.ops.bevel(bm, geom=list(edges), offset=offset, segments=2, profile=0.6,
                              affect="EDGES", clamp_overlap=True)
        set_material(res["faces"], mat)


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
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_face_angle(0.0) > SHARP_ANGLE:
            e.smooth = False
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    try:
        mesh.use_auto_smooth = True          # starsie verzie Blendera (do 4.0)
        mesh.auto_smooth_angle = SHARP_ANGLE
    except Exception:
        pass
    return mesh


def export_mesh(coll, mesh, file_name):
    # kazdy diel sa exportuje samostatne v strede sveta, aby mal pivot na svojom mieste
    temp = bpy.data.objects.new(file_name, mesh)
    coll.objects.link(temp)
    select_only(temp)
    path = os.path.join(EXPORT_DIR, file_name + ".fbx")
    try:
        bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                                 apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="EDGE")
    except Exception as error:
        print("FBX sa nepodarilo ulozit:", path, error)
    bpy.data.objects.remove(temp, do_unlink=True)


def clear_collection(coll):
    for sub in [coll] + list(coll.children):
        for obj in list(sub.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.get("mk_part"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_"):
            bpy.data.curves.remove(curve)


def build_parts(mats):
    built = {}

    def put(mesh):
        key_ = mesh.name[3:].split(".")[0]
        if key_ in built:
            bpy.data.meshes.remove(mesh)       # zdielany diel sa postavi len raz
            return
        built[key_] = mesh

    def put_lr(bm, name):
        mirrored = mirror_y(bm)
        put(finish_mesh(bm, name + "_L"))
        put(finish_mesh(mirrored, name + "_P"))

    for maker in PART_MAKERS:
        maker(put, put_lr)
    for mesh in built.values():
        mesh["mk_part"] = 1
        for mat in mats:
            mesh.materials.append(mat)
    return built


def main():
    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)
    clear_collection(coll)
    mats = [get_material(*m) for m in MATERIALS]
    parts = build_parts(mats)
    roots = []
    for builder in SCENE_BUILDERS:
        roots += builder(coll, parts, mats)
    scene.frame_start, scene.frame_end = 1, FRAME_END
    scene.frame_set(1)

    kit = child_collection(coll, COLLECTION + "_diely")
    lines = ["%s - diely (rozmery X x Y x Z v metroch). Predok = +X, lava = +Y." % DOC_TITLE, ""]
    y_cursor = KIT_Y0
    for title, keys in CATALOG_EXTRA:
        keys = [k for k in keys if k in parts and len(parts[k].vertices)]
        if not keys:
            continue
        depth = max(bounds(parts[k])[1][1] - bounds(parts[k])[1][0] for k in keys)
        row_y = y_cursor + depth * 0.5
        add_label(kit, title, (-2.5, row_y, 0.001), mats[DARK])
        x = -1.0
        lines.append("== %s ==" % title)
        for k in keys:
            mesh = parts[k]
            (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
            slot = max(x1 - x0, 1.0)
            new_object(kit, "Diel_" + k[3:], mesh, (x + (slot - (x1 - x0)) * 0.5 - x0, row_y - (y0 + y1) * 0.5, -z0))
            add_label(kit, "%s\n%.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0), (x + slot * 0.5, row_y - depth * 0.5 - 0.2, 0.001), mats[DARK])
            lines.append("%-40s %.2f x %.2f x %.2f" % (k, x1 - x0, y1 - y0, z1 - z0))
            x += slot + 0.35
        lines.append("")
        y_cursor += depth + 0.9
    lines += DOC_EXTRA
    lines += ["V Unreali: kazdy par 'mieri na' urob cez Find Look at Rotation (alebo Look At v Control Rig / Animation Blueprinte)."]

    if EXPORT_FBX:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        for k, mesh in parts.items():
            if len(mesh.vertices):
                export_mesh(coll, mesh, "SM_" + k)
        with open(os.path.join(EXPORT_DIR, DOC_FILE), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    select_only(roots[0])
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Spolocne pomocne funkcie pre rig: driver zo svetovej polohy, uchyty (sockety), teleskopicke valce, zaoblene prierezy
# ---------------------------------------------------------------------------

def driver_world(obj, path, index, expression, variables, local_vars=()):
    # ako driver(), ale premenne (meno, objekt, "LOC_Z") sa citaju vo svetovych suradniciach; local_vars su ten isty zapis v lokalnych suradniciach
    fcurve = obj.driver_add(path, index)
    drv = fcurve.driver
    drv.type = "SCRIPTED"
    for space, items in (("WORLD_SPACE", variables), ("TRANSFORM_SPACE", local_vars)):
        for name, target, ttype in items:
            var = drv.variables.new()
            var.name = name
            var.type = "TRANSFORMS"
            var.targets[0].id = target
            var.targets[0].transform_type = ttype
            var.targets[0].transform_space = space
    drv.expression = expression


def mount(coll, name, tag, parent, loc, specs):
    # uchyt <name>_uchyt_<tag> (prazdny objekt v pivote dielu) a jeho diely: specs = [(pripona objektu, mesh)]; vrati (uchyt, [objekty])
    sock = empty(coll, "%s_uchyt_%s" % (name, tag), loc, parent)
    sock.empty_display_type = "ARROWS"
    sock.empty_display_size = 0.12
    sock.hide_render = True
    objs = [new_object(coll, "%s_%s" % (name, suffix), mesh, (0.0, 0.0, 0.0), sock) for suffix, mesh in specs]
    return sock, objs


def rounded_rect(y0, y1, z0, z1, r, n=4):
    # obdlznik so zaoblenymi rohmi (YZ, proti smeru hodin), n bodov na roh
    r = min(r, (y1 - y0) * 0.5, (z1 - z0) * 0.5)
    pts = []
    for cy, cz, a0 in ((y1 - r, z1 - r, 0.0), (y0 + r, z1 - r, 90.0), (y0 + r, z0 + r, 180.0), (y1 - r, z0 + r, 270.0)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cy + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def loft_yz(bm, sections, mat, mat_fn=None):
    # teleso z prierezov v rovinach YZ: sections = [(x, [(y, z), ...]), ...] s rovnakym poctom bodov; konce sa uzavru; mat_fn(stred plochy) vyberie material
    rings = [[bm.verts.new((x, y, z)) for y, z in pts] for x, pts in sections]
    faces = [bm.faces.new(rings[0][::-1]), bm.faces.new(rings[-1])]
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    for f in faces:
        f.material_index = mat_fn(f.calc_center_median()) if mat_fn else mat
    return faces


def tele_stages(dmin, dmax):
    # dlzka stupna a pocet stupnov teleskopickeho valca pre rozsah vzdialenosti dmin az dmax (stupne sa prekryvaju aspon z 18 %)
    ell = dmin * 0.985
    n = max(2, int(math.ceil((dmax - ell) / (0.82 * ell))) + 1)
    return n, ell


def build_cyl_stage(kind, k, n, ell, radii):
    # stupen teleskopickeho valca (os = +Z, pivot na spodnom konci): 0 = telo s okom, dalsie chromove piesty, posledny s okom
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
    return finish_mesh(bm, "SM_%s_%d" % (kind, k))


def cylinder_family(put, kind, n, ell, r0):
    radii = [r0 * (1.0 - 0.16 * k) for k in range(n)]
    for k in range(n):
        put(build_cyl_stage(kind, k, n, ell, radii))


def telescope(coll, name, parts, kind, n, ell, base_parent, base_pt, aim_parent, aim_pt):
    # teleskopicky valec: prvy stupen na zaklade mieri na ciel, dalsie stupne sa podla vzdialenosti vysuvaju (k-ty o (d - ell) k / (n - 1) po +Z)
    base = new_object(coll, name + "_1", parts["%s_0" % kind], base_pt, base_parent)
    aim = empty(coll, name + "_ciel", aim_pt, aim_parent)
    track(base, aim, "TRACK_Z")
    for k in range(1, n):
        stage = new_object(coll, "%s_%d" % (name, k + 1), parts["%s_%d" % (kind, k)], (0.0, 0.0, 0.0), base)
        driver(stage, "location", 2, "(d - %.4f) * %.4f" % (ell, k / (n - 1.0)), [("d", "DIST", (base, aim))])
    return base, aim


def build_rod_part(name, r, length, mat=STEEL, segments=8):
    # jednoduchy valcovy diel s osou +Z a pivotom v spodnom konci (lano, tyc)
    bm = bmesh.new()
    add_cylinder(bm, r, length, along_z((0.0, 0.0, length * 0.5)), mat, segments=segments)
    return finish_mesh(bm, name)


def bx(bm, x0, x1, y0, y1, z0, z1, mat, bev=0.0):
    # kvader zadany krajnymi hodnotami (x0 az x1, y0 az y1, z0 az z1)
    add_box(bm, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5), mat, bev=bev)


def hose(bm, pts, r, mat, segments=6):
    # lomena hadica / trubka cez body
    for a, b in zip(pts, pts[1:]):
        add_rod(bm, a, b, r, mat, segments=segments)


def driver_prop(obj, path, index, name, target, prop_name):
    # prida k existujucemu driveru premennu z vlastnosti objektu (napr. Hak)
    fc = obj.animation_data.drivers.find(path, index=index)
    var = fc.driver.variables.new()
    var.name = name
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "OBJECT"
    var.targets[0].id = target
    var.targets[0].data_path = '["%s"]' % prop_name


def slab(bm, pts, t, mat, bev=0.0):
    # tenka doska zo styroch bodov (x, y, z) s hrubkou t (smerom proti normale prveho trojuholnika p0 p1 p3)
    p = [Vector(q) for q in pts]
    n = (p[1] - p[0]).cross(p[3] - p[0])
    n.normalize()
    top = [bm.verts.new(q) for q in p]
    bot = [bm.verts.new(q - n * t) for q in p]
    faces = [bm.faces.new(top), bm.faces.new(bot[::-1])]
    for i in range(4):
        j = (i + 1) % 4
        faces.append(bm.faces.new((top[i], top[j], bot[j], bot[i])))
    finish_shape(bm, faces, mat, bev)


# ---------------------------------------------------------------------------
# Kamene, hromady a kusy na pase: nepravidelne low poly kamene (icosfera s posunutymi vrcholmi, spodok oriznuty), hromady (kuzel s nepravidelnym povrchom a kamenmi), zhluky kamenov na pas
# ---------------------------------------------------------------------------

import random


def add_rock(bm, c, rx, ry, rz, seed, mat, cut=0.35, sub=1):
    # nepravidelny kamen so stredom c a polomermi rx, ry, rz; spodok je oriznuty (lezi na podklade)
    rng = random.Random(seed)
    res = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    verts = res["verts"]
    for v in verts:
        k = 0.72 + 0.50 * rng.random()
        v.co = Vector((v.co.x * k * rx, v.co.y * k * ry, max(v.co.z * k, -cut) * rz))
    bmesh.ops.rotate(bm, cent=(0.0, 0.0, 0.0), matrix=Matrix.Rotation(rng.random() * 6.28, 3, "Z"), verts=verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=verts)
    set_material(faces_of(verts), mat)


def build_lumps(name, seed, n, spread, size, mat, height=0.0):
    # zhluk n kamenov v pasme sirky 2 * spread (y) a dlzky 0.5 (x); velkost size = (min, max); pivot na spodku v strede
    rng = random.Random(seed)
    bm = bmesh.new()
    for i in range(n):
        r = size[0] + (size[1] - size[0]) * rng.random()
        add_rock(bm, ((rng.random() - 0.5) * 0.4, (rng.random() * 2 - 1) * (spread - r * 0.6), r * 0.55 + height), r, r * (0.8 + 0.4 * rng.random()), r * 0.75, seed * 31 + i, mat, 0.3, 1)
    return finish_mesh(bm, name)


def pile_profile(f):
    # vyska hromady v podiele polomeru f (1 = okraj, 0 = vrchol), 0 az 1
    return max(0.0, 1.0 - f ** 1.55)


def build_pile(name, radius, height, mat, seed, rocks=0, rock_size=(0.15, 0.35), rock_mat=None, rings=5, segs=16, noise=0.07):
    # hromada (pivot v strede na zemi): kuzel s nepravidelnymi okrajmi a vrstvami, na povrchu volitelne kamene
    rng = random.Random(seed)
    bm = bmesh.new()
    fs = [1.0 - k / float(rings) for k in range(rings)] + [0.0]
    grid = []
    for ri, f in enumerate(fs):
        ring = []
        for s in range(segs if f > 0 else 1):
            a = 2.0 * math.pi * s / segs
            n = 1.0 + noise * (rng.random() * 2 - 1) if 0 < ri < rings else 1.0 + noise * 0.6 * (rng.random() * 2 - 1)
            rr = radius * f * n
            zz = height * pile_profile(f) * (1.0 + noise * 0.6 * (rng.random() * 2 - 1) if f < 1.0 else 1.0) - (0.04 if f >= 1.0 else 0.0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), max(zz, -0.04))))
        grid.append(ring)
    faces = []
    for ri in range(len(grid) - 1):
        a, b = grid[ri], grid[ri + 1]
        for s in range(segs):
            t = (s + 1) % segs
            if len(b) == 1:
                faces.append(bm.faces.new((a[s], a[t], b[0])))
            else:
                faces.append(bm.faces.new((a[s], a[t], b[t], b[s])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    set_material(faces, mat)
    for i in range(rocks):
        f = 0.15 + 0.85 * rng.random()
        a = rng.random() * 6.28
        r = rock_size[0] + (rock_size[1] - rock_size[0]) * rng.random()
        z = height * pile_profile(f) + r * 0.10
        add_rock(bm, (radius * f * math.cos(a), radius * f * math.sin(a), z), r, r * (0.8 + 0.4 * rng.random()), r * 0.8, seed * 17 + i, rock_mat if rock_mat is not None else mat, 0.4, 1)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Pasovy dopravnik: ram s bocnymi nosnikmi a valcekmi, korytovy pas (zatvorena slucka), dva bubny (hlavovy a chvostovy), listy pasu (chevron) a zhluky kamenov, ktore bezia po slucke
# (vlastnost Pas_pohyb v metroch na hlavnom objekte stroja), kryt hlavy so zlabom. Suradnice dopravnika: pociatok = os chvostoveho bubna, os X po pase (smerom k hlave),
# vrch pasu v z = R + hrubka. Dopravnik sa umiestni a nakloni jednym uchytom (rotacia Y o -sklon, otocenie Z).
# ---------------------------------------------------------------------------

def cv_key(c, part):
    return "Cv_%s_%s" % (c["key"], part)


def cv_paint(c):
    return c.get("paint", PAINT_GRY)


def build_cv_ram(c):
    L, W, R, th = c["L"], c["W"], c["R"], c["th"]
    paint = cv_paint(c)
    bm = bmesh.new()
    ys = W * 0.5 + 0.05
    top = R + th + 0.14
    for s in SIDES_LR:
        bx(bm, -0.42, L + 0.42, s * ys, s * (ys + 0.07), -0.34, top, paint, 0.02)
        bx(bm, -0.42, L + 0.42, s * (ys - 0.01), s * (ys + 0.08), top - 0.03, top + 0.03, STEEL, 0.008)
    n = max(2, int(L / 1.5))
    for k in range(n + 1):
        x = -0.30 + (L + 0.60) * k / n
        bx(bm, x - 0.05, x + 0.05, -(ys + 0.07), ys + 0.07, -0.38, -0.31, paint, 0.012)
    rise = 0.2 * W * 0.36
    x = 0.55
    while x < L - 0.40:
        add_rod(bm, (x, -0.30 * W, R - 0.05), (x, 0.30 * W, R - 0.05), 0.05, STEEL, segments=8)
        for s in SIDES_LR:
            add_rod(bm, (x, s * 0.30 * W, R - 0.05), (x, s * 0.50 * W, R - 0.05 + rise), 0.05, STEEL, segments=8)
            bx(bm, x - 0.04, x + 0.04, s * (0.5 * W - 0.02), s * (ys), -0.02, R - 0.02 + rise, GRAY, 0.008)
        x += 0.85
    x = 0.9
    while x < L - 0.5:
        add_rod(bm, (x, -0.46 * W, -R - th - 0.05), (x, 0.46 * W, -R - th - 0.05), 0.045, STEEL, segments=8)
        for s in SIDES_LR:
            bx(bm, x - 0.03, x + 0.03, s * (0.46 * W), s * ys, -R - th - 0.08, -R - th + 0.04, GRAY, 0.006)
        x += 2.2
    if c.get("skirt", True):
        for s in SIDES_LR:
            bx(bm, 0.15, min(1.6, L * 0.4), s * (W * 0.5 - 0.06), s * (W * 0.5 - 0.02), R + th, R + th + 0.20, PLAST, 0.006)
            bx(bm, 0.15, min(1.6, L * 0.4), s * (W * 0.5 - 0.03), s * (W * 0.5 + 0.03), R + th + 0.20, R + th + 0.25, paint, 0.008)
    return finish_mesh(bm, "SM_" + cv_key(c, "ram"))


def cv_trough(c, rise):
    L, W, R, th = c["L"], c["W"], c["R"], c["th"]
    zt = R + th
    return [(-W * 0.5, zt + rise), (-0.30 * W, zt), (0.30 * W, zt), (W * 0.5, zt + rise),
            (W * 0.5, zt - th + rise), (0.30 * W, zt - th), (-0.30 * W, zt - th), (-W * 0.5, zt - th + rise)]


def build_cv_pas(c):
    # pas: korytovy horny chod (na koncoch plochy), oblouky okolo bubnov, spodny chod
    L, W, R, th = c["L"], c["W"], c["R"], c["th"]
    bm = bmesh.new()
    rise = 0.2 * W * 0.36
    ex = min(0.9, L * 0.25)
    loft_yz(bm, [(0.0, cv_trough(c, 0.0)), (ex, cv_trough(c, rise)), (L - ex, cv_trough(c, rise)), (L, cv_trough(c, 0.0))], PAS)
    prof = [(R, -W * 0.5), (R, W * 0.5), (R + th, W * 0.5), (R + th, -W * 0.5)]
    add_at(bm, (L, 0.0, 0.0), sweep_profile, prof, -90.0, 90.0, 10, PAS)
    add_at(bm, (0.0, 0.0, 0.0), sweep_profile, prof, 90.0, 270.0, 10, PAS)
    bx(bm, 0.0, L, -W * 0.5, W * 0.5, -R - th, -R, PAS)
    return finish_mesh(bm, "SM_" + cv_key(c, "pas"))


def build_cv_buben(c):
    # buben (pivot v osi): oblozeny valec s rebrami, prirubami a hriadelou
    W, R = c["W"], c["R"]
    bm = bmesh.new()
    add_cylinder(bm, R, W + 0.02, along_y((0.0, 0.0, 0.0)), DARK, segments=18, bev=0.01)
    for k in range(9):
        a = 2.0 * math.pi * k / 9
        add_box(bm, (0.04, W * 0.92, 0.02), (0.0, 0.0, 0.0), PLAST, frame=Matrix.Translation((0.0, 0.0, 0.0)) @ Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0.0, 0.0, R + 0.005)))
    for s in SIDES_LR:
        add_cylinder(bm, R + 0.015, 0.025, along_y((0.0, s * (W * 0.5 + 0.02), 0.0)), STEEL, segments=18)
        add_cylinder(bm, 0.05, 0.22, along_y((0.0, s * (W * 0.5 + 0.13), 0.0)), STEEL, segments=10)
    return finish_mesh(bm, "SM_" + cv_key(c, "buben"))


def build_cv_lista(c):
    # chevronova lista pasu (pivot v strede na povrchu pasu, V ma hrot k hlave +X)
    W, h = c["W"], c.get("cleat_h", 0.05)
    bm = bmesh.new()
    for s in SIDES_LR:
        add_box(bm, (W * 0.30, 0.045, h), (-W * 0.065, s * W * 0.195, h * 0.5), PAS_L, bev=0.008, rotation=(0.0, 0.0, -s * 38.0))
    return finish_mesh(bm, "SM_" + cv_key(c, "lista"))


def build_cv_kryt(c):
    # hlava: kryt nad hlavovym bubnom a vysypny zlab dolu (otvor zlabu smeruje dolu a dopredu)
    L, W, R, th = c["L"], c["W"], c["R"], c["th"]
    paint = cv_paint(c)
    bm = bmesh.new()
    zt = R + th
    yh = W * 0.5 + 0.08
    pts = [(L - 0.55, zt + 0.02), (L - 0.55, zt + 0.34), (L + 0.30, zt + 0.34), (L + 0.62, -R - 0.34), (L + 0.30, -R - 0.34), (L + 0.12, -0.05), (L + 0.12, zt + 0.02)]
    for s in SIDES_LR:
        add_extruded(bm, pts, s * yh - 0.02, s * yh + 0.02, "XZ", paint, bev=0.008)
    add_box(bm, (0.85, 2 * yh, 0.03), (L - 0.12, 0.0, zt + 0.34), paint, bev=0.008)
    plate = [(L + 0.30, zt + 0.34), (L + 0.62, -R - 0.34), (L + 0.62 - 0.03, -R - 0.34), (L + 0.27, zt + 0.34)]
    add_extruded(bm, plate, -yh, yh, "XZ", LINER, bev=0.004)
    add_box(bm, (0.30, 2 * yh, 0.03), (L + 0.45, 0.0, -R - 0.34), paint, bev=0.008)
    return finish_mesh(bm, "SM_" + cv_key(c, "kryt"))


def build_cv_naklad(c, v):
    # zhluk kamenov na pase (variant v), pivot na povrchu pasu
    lump = c.get("lump", (3, (0.07, 0.13), ROCK))
    return build_lumps("SM_" + cv_key(c, "naklad_%d" % v), c["seed"] * 7 + v, lump[0], c["W"] * 0.40, lump[1], lump[2])


def cv_parts(put, put_lr, c):
    put(build_cv_ram(c))
    put(build_cv_pas(c))
    put(build_cv_buben(c))
    put(build_cv_lista(c))
    if c.get("hood", True):
        put(build_cv_kryt(c))
    for v in range(3):
        put(build_cv_naklad(c, v))


def cv_loop_exprs(L, Rb, c0):
    Lt = 2.0 * L + 2.0 * math.pi * Rb
    S = "fmod(p+%.4f,%.4f)" % (c0, Lt)
    a = "min(max(%s,0),%.4f)" % (S, L)
    f1 = "min(max((%s-%.4f)/%.4f,0),pi)" % (S, L, Rb)
    b = "min(max(%s-%.4f,0),%.4f)" % (S, L + math.pi * Rb, L)
    f2 = "min(max((%s-%.4f)/%.4f,0),pi)" % (S, 2.0 * L + math.pi * Rb, Rb)
    x = "%s+%.4f*sin(%s)-%s-%.4f*sin(%s)" % (a, Rb, f1, b, Rb, f2)
    z = "%.4f*cos(%s)+%.4f*(1-cos(%s))" % (Rb, f1, Rb, f2)
    r = "%s+%s" % (f1, f2)
    return x, z, r


def cv_rig(coll, mname, c, parts, parent, loc, rot, prop_root, prop_name="Pas_pohyb"):
    # dopravnik na uchyte <mname>_uchyt_<id>: ram, pas, dva bubny, kryt, listy a kamene bezia po slucke podla vlastnosti prop_name na prop_root (v metroch)
    cid = c["id"]
    L, W, R, th = c["L"], c["W"], c["R"], c["th"]
    Rb = R + th
    root = empty(coll, "%s_uchyt_%s" % (mname, cid), loc, parent)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 0.3
    root.rotation_euler = rot

    def prop(var):
        return (var, "PROP", (prop_root, '["%s"]' % prop_name))

    mount(coll, mname, cid + "_ram", root, (0.0, 0.0, 0.0), [(cid + "_ram", parts[cv_key(c, "ram")])])
    mount(coll, mname, cid + "_pas", root, (0.0, 0.0, 0.0), [(cid + "_pas", parts[cv_key(c, "pas")])])
    if c.get("hood", True):
        mount(coll, mname, cid + "_kryt", root, (0.0, 0.0, 0.0), [(cid + "_kryt", parts[cv_key(c, "kryt")])])
    for tag, x in (("buben_hlava", L), ("buben_chvost", 0.0)):
        drum, _ = mount(coll, mname, "%s_%s" % (cid, tag), root, (x, 0.0, 0.0), [("%s_%s" % (cid, tag), parts[cv_key(c, "buben")])])
        driver(drum, "rotation_euler", 1, "p / %.4f" % R, [prop("p")])
    Lt = 2.0 * L + 2.0 * math.pi * Rb
    pitch = c.get("pitch", 0.8)
    n = max(4, int(round(Lt / pitch)))
    for i in range(n):
        obj = new_object(coll, "%s_%s_lista_%d" % (mname, cid, i + 1), parts[cv_key(c, "lista")], (0.0, 0.0, 0.0), root)
        x, z, r = cv_loop_exprs(L, Rb, i * Lt / n)
        driver(obj, "location", 0, x, [prop("p")])
        driver(obj, "location", 2, z, [prop("p")])
        driver(obj, "rotation_euler", 1, r, [prop("p")])
    nl = c.get("lumps", 0)
    rng = random.Random(c["seed"])
    for i in range(nl):
        obj = new_object(coll, "%s_%s_naklad_%d" % (mname, cid, i + 1), parts[cv_key(c, "naklad_%d" % (i % 3))], (0.0, 0.0, Rb), root)
        c0 = i * L / nl
        obj.rotation_euler = (0.0, 0.0, (rng.random() - 0.5) * 1.2)
        xs = "fmod(p+%.4f,%.4f)" % (c0, L)
        driver(obj, "location", 0, xs, [prop("p")])
        sc_ = "min(1.0,min(%s,%.4f-%s)/0.7)" % (xs, L, xs)
        for ax in range(3):
            driver(obj, "scale", ax, sc_, [prop("p")])
    head = empty(coll, "%s_%s_hlava" % (mname, cid), (L, 0.0, Rb), root)
    tail = empty(coll, "%s_%s_chvost" % (mname, cid), (0.0, 0.0, Rb), root)
    return dict(root=root, head=head, tail=tail)


def key_linear(obj, prop_name, frames):
    # kluce vlastnosti s linearnou interpolaciou (rovnomerny pohyb pasu): nastavi sa predvolena interpolacia novych klucov
    pref = bpy.context.preferences.edit
    old = pref.keyframe_new_interpolation_type
    pref.keyframe_new_interpolation_type = "LINEAR"
    try:
        for frame, value in frames:
            obj[prop_name] = value
            obj.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)
    finally:
        pref.keyframe_new_interpolation_type = old


# ---------------------------------------------------------------------------
# Pasovy podvozok (lavy pas, pravy je zrkadlo): ram pasu, hnacie koleso so zubami, napinacie koleso, spodne a horne valcceky, retaz s dosticakmi a hrebenmi (stoji)
# Suradnice: pociatok = zem pod stredom podvozku, predok +X; y stredu pasu = spec["y"].
# ---------------------------------------------------------------------------

def tk_path_point(spec, s):
    # bod strednice retaze (x, z, uhol vonkajsej normaly) v dlzke obluka s; slucka: spodny chod dopredu, obluk, horny chod dozadu, obluk
    Lc, Rt, zc = spec["L"], spec["R"] + spec["shoe"] * 0.5, spec["zc"]
    Lt = 2.0 * Lc + 2.0 * math.pi * Rt
    s = s % Lt
    if s < Lc:                                    # spodny chod: z zadu dopredu
        return (-Lc * 0.5 + s, zc - Rt, -math.pi * 0.5)
    s -= Lc
    if s < math.pi * Rt:                          # predny obluk (hore po -90 .. 90)
        a = -math.pi * 0.5 + s / Rt
        return (Lc * 0.5 + Rt * math.cos(a), zc + Rt * math.sin(a), a)
    s -= math.pi * Rt
    if s < Lc:                                    # horny chod dozadu
        return (Lc * 0.5 - s, zc + Rt, math.pi * 0.5)
    s -= Lc
    a = math.pi * 0.5 + s / Rt                    # zadny obluk
    return (-Lc * 0.5 + Rt * math.cos(a), zc + Rt * math.sin(a), a)


def build_tk_unit(spec):
    Lc, R, zc, y, wt = spec["L"], spec["R"], spec["zc"], spec["y"], spec["w"]
    shoe = spec["shoe"]
    bm = bmesh.new()
    Rt = R + shoe * 0.5
    Lt = 2.0 * Lc + 2.0 * math.pi * Rt
    n = int(round(Lt / spec["pitch"]))
    for i in range(n):
        x, z, a = tk_path_point(spec, Lt * i / n)
        frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(-a - math.pi * 0.5, 4, "Y")
        add_box(bm, (Lt / n - 0.012, wt, shoe), (0.0, 0.0, 0.0), DARK, frame=frame)
        add_box(bm, (0.045, wt - 0.04, 0.055), (0.0, 0.0, -shoe * 0.5 - 0.02), STEEL, frame=frame)       # hreben (vonkajsia strana retaze)
    # ram pasu, kolesa, valceky
    bx(bm, -Lc * 0.5 - 0.1, Lc * 0.5 + 0.1, y - wt * 0.5 + 0.05, y - wt * 0.5 + 0.17, zc - 0.22, zc + 0.30, PAINT_GRY, 0.03)
    for xx, nm in ((Lc * 0.5, "hnacie"), (-Lc * 0.5, "napinacie")):
        add_cylinder(bm, R * 0.92, wt - 0.18, along_y((xx, y, zc)), STEEL, segments=18, bev=0.01)
        add_cylinder(bm, R * 0.55, wt - 0.02, along_y((xx, y, zc)), PAINT_GRY, segments=12)
        if nm == "hnacie":
            for k in range(11):
                aa = 2.0 * math.pi * k / 11
                add_box(bm, (0.07, wt - 0.22, 0.09), (xx + (R * 0.92) * math.cos(aa), y, zc + (R * 0.92) * math.sin(aa)), STEEL, rotation=(0.0, -math.degrees(aa), 0.0))
    for k in range(5):
        xx = -Lc * 0.5 + 0.55 + (Lc - 1.1) * k / 4.0
        add_cylinder(bm, 0.13, wt - 0.18, along_y((xx, y, zc - Rt + shoe * 0.5 + 0.13)), STEEL, segments=12)
    for k in range(2):
        xx = -Lc * 0.2 + 0.6 * k * Lc * 0.5
        add_cylinder(bm, 0.075, wt - 0.22, along_y((xx, y, zc + Rt - shoe * 0.5 - 0.075)), STEEL, segments=10)
    bx(bm, Lc * 0.5 + 0.05, Lc * 0.5 + 0.35, y - wt * 0.5 + 0.02, y + wt * 0.5 - 0.02, zc - 0.20, zc + 0.20, PAINT_GRY, 0.03)       # hydromotor
    return bm


# ---------------------------------------------------------------------------
# Spolocne diely prevzate z drvica (motor, dvere, chladic, nadrze, rozstrek, svetlo, majak, rebrik, plosina, bocnice, nasypka); suradnice su ako pri drvici, polohu urcuju uchyty
# ---------------------------------------------------------------------------

def build_tr_nasypka():
    # nasypka: sikme steny (zadna a dve bocne) z dosiek s vystuhami a obrubou, vnutorne oblozenie
    H = HOP
    bm = bmesh.new()
    x0, x1, hw, zt, xb, hb, zb = H["x0"], H["x1"], H["hw"], H["zt"], H["xb"], H["hb"], H["zb"]
    slab(bm, [(x0, hw, zt), (x0, -hw, zt), (xb, -hb, zb), (xb, hb, zb)], 0.05, PAINT_BLU, 0.01)
    slab(bm, [(x1, hw, zt), (x0, hw, zt), (xb, hb, zb), (x1, hb, zb)], 0.05, PAINT_BLU, 0.01)
    slab(bm, [(x0, -hw, zt), (x1, -hw, zt), (x1, -hb, zb), (xb, -hb, zb)], 0.05, PAINT_BLU, 0.01)
    # oblozenie (tmave dosky) pri dne
    slab(bm, [(x0 + 0.20, hw - 0.30, zt - 0.55), (x1 - 0.1, hw - 0.30, zt - 0.55), (x1 - 0.1, hb + 0.02, zb + 0.08), (xb + 0.05, hb + 0.02, zb + 0.08)], 0.02, LINER)
    slab(bm, [(x0 + 0.20, -hw + 0.30, zt - 0.55), (xb + 0.05, -hb - 0.02, zb + 0.08), (x1 - 0.1, -hb - 0.02, zb + 0.08), (x1 - 0.1, -hw + 0.30, zt - 0.55)], 0.02, LINER)
    slab(bm, [(x0 + 0.12, hw - 0.4, zt - 0.5), (x0 + 0.12, -hw + 0.4, zt - 0.5), (xb + 0.05, -hb - 0.02, zb + 0.08), (xb + 0.05, hb + 0.02, zb + 0.08)], 0.02, LINER)
    # obruba hore a vystuhy
    bx(bm, x0 - 0.05, x0 + 0.05, -hw - 0.05, hw + 0.05, zt - 0.05, zt + 0.06, PAINT_GRY, 0.02)
    for s in SIDES_LR:
        bx(bm, x0 - 0.05, x1 + 0.02, s * hw - 0.05, s * hw + 0.05, zt - 0.05, zt + 0.06, PAINT_GRY, 0.02)
        for k in range(4):
            t = (k + 0.5) / 4.0
            xx = x0 + (x1 - x0) * t
            add_rod(bm, (xx, s * (hw + 0.03), zt - 0.02), (xx, s * (hb + 0.03), zb), 0.03, STEEL, segments=6)
    for k in range(3):
        yy = -hw * 0.6 + hw * 0.6 * k
        add_rod(bm, (x0 - 0.03, yy, zt - 0.02), (xb - 0.03, yy * hb / hw, zb), 0.03, STEEL, segments=6)
    return finish_mesh(bm, "SM_Tr_nasypka")


def build_tr_bocnica():
    # bocna klapka nasypky (lava; prava je zrkadlo), pivot na zavese (stred dlzky, horna hrana steny); vyklopena stoji naklonena von o 20 st., zlozena lezi dnu
    H = HOP
    L = H["x1"] - H["x0"]
    bm = bmesh.new()
    add_box(bm, (L - 0.10, 0.05, 0.62), (0.0, 0.0, 0.31), PAINT_BLU, bev=0.015)
    add_box(bm, (L - 0.10, 0.07, 0.06), (0.0, 0.0, 0.64), PAINT_GRY, bev=0.012)
    for k in range(5):
        add_box(bm, (0.06, 0.07, 0.56), (-L * 0.5 + 0.35 + (L - 0.7) * k / 4.0, 0.0, 0.31), PAINT_GRY, bev=0.01)
    return bm


def build_tr_motor():
    # motorovy diel (diesel s krytom, zlava vedla dopravnika): kryt s vetracimi liszami, strecha so sacim kanalom, nosnik, spodne rebra
    bm = bmesh.new()
    x0, x1, y0, y1, z0, z1 = 1.62, 3.42, 0.76, 1.60, 1.13, 2.36
    bx(bm, x0, x1, y0, y1, z0, z1, PAINT_BLU, 0.04)
    bx(bm, x0 + 0.10, x1 - 0.20, y0 + 0.10, y1 - 0.10, z1, z1 + 0.20, PAINT_GRY, 0.03)
    for k in range(4):
        bx(bm, x0 + 0.20 + 0.28 * k, x0 + 0.40 + 0.28 * k, y0 + 0.14, y1 - 0.14, z1 + 0.20, z1 + 0.23, STEEL, 0.004)
    add_cylinder(bm, 0.075, 1.0, along_z((x0 + 0.30, y0 + 0.22, z1 + 0.5)), STEEL, segments=10, bev=0.004)
    add_cylinder(bm, 0.095, 0.05, along_z((x0 + 0.30, y0 + 0.22, z1 + 1.02)), DARK, segments=10)
    for s in (y0 + 0.02, y1 - 0.02):
        bx(bm, x0 - 0.01, x1 + 0.01, s - 0.02, s + 0.02, z0 + 0.02, z0 + 0.10, PAINT_GRY, 0.01)
    return finish_mesh(bm, "SM_Tr_motor")


def build_tr_dvere_motora():
    # dvere motoroveho dielu (pivot na zavese, dvere siahaju do +X; druhe dvere su zrkadlene otocenim v rigu): panel s oknom listov
    bm = bmesh.new()
    add_box(bm, (0.86, 0.04, 1.10), (0.43, 0.02, 0.58), PAINT_BLU, bev=0.015)
    for k in range(6):
        bx(bm, 0.12, 0.74, 0.04, 0.062, 0.18 + 0.12 * k, 0.21 + 0.12 * k, DARK, 0.004)
    bx(bm, 0.70, 0.78, 0.04, 0.07, 0.50, 0.64, STEEL, 0.006)
    return finish_mesh(bm, "SM_Tr_dvere_motora")


def build_tr_chladic():
    # chladic s ventilatorom na predku motora (pivot na spodku v strede plochy): skrinka, ochranna mriezka s listami a nabojom
    bm = bmesh.new()
    bx(bm, 0.0, 0.26, -0.40, 0.40, -0.55, 0.55, PAINT_GRY, 0.03)
    add_ring(bm, 0.36, 0.33, 0.03, 0.0, STEEL, 20)
    for k in range(3):
        add_box(bm, (0.012, 0.66 - 0.2 * k, 0.014), (0.28, 0.0, 0.0), STEEL, rotation=(0.0, 0.0, 0.0), frame=Matrix.Rotation(k * math.pi / 3.0, 4, "X"))
    add_cylinder(bm, 0.07, 0.04, along_x((0.28, 0.0, 0.0)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Tr_chladic")


def build_tr_nadrze():
    # hydraulicka nadrz a nadrz nafty (prava strana ramu): skrine s uzavermi, mierkou hladiny a ciernymi zachytmi
    bm = bmesh.new()
    bx(bm, 1.70, 2.80, -1.62, -0.78, 1.13, 1.95, PAINT_GRY, 0.04)
    bx(bm, 1.70, 2.80, -1.66, -1.62, 1.35, 1.80, DARK, 0.01)
    add_cylinder(bm, 0.07, 0.08, along_z((2.1, -1.2, 1.99)), STEEL, segments=10)
    bx(bm, 2.90, 3.40, -1.62, -0.78, 1.13, 2.30, PAINT_BLU, 0.04)
    for k in range(5):
        bx(bm, 2.95, 3.35, -1.64, -1.62, 1.30 + 0.17 * k, 1.36 + 0.17 * k, DARK, 0.004)
    return finish_mesh(bm, "SM_Tr_nadrze")


def build_tr_rozstrek():
    # vodny rozstrek nad vstupom: rura s piatimi tryskami a priponom
    bm = bmesh.new()
    add_rod(bm, (0.0, -0.9, 0.0), (0.0, 0.9, 0.0), 0.025, PAINT_BLU, segments=8)
    for k in range(5):
        y = -0.7 + 0.35 * k
        add_rod(bm, (0.0, y, 0.0), (0.0, y, -0.12), 0.015, STEEL, segments=6)
        add_cone(bm, 0.0, 0.03, 0.06, along_z((0.0, y, -0.15)), CHROME, segments=8)
    for s in SIDES_LR:
        add_rod(bm, (0.0, s * 0.9, 0.0), (0.0, s * 0.9, -0.55), 0.02, PAINT_BLU, segments=6)
    return finish_mesh(bm, "SM_Tr_rozstrek")


def build_tr_svetlo():
    bm = bmesh.new()
    add_box(bm, (0.10, 0.26, 0.14), (0.05, 0.0, 0.0), DARK, bev=0.02)
    add_box(bm, (0.02, 0.22, 0.10), (0.105, 0.0, 0.0), LAMP_WHITE, bev=0.01)
    return finish_mesh(bm, "SM_Tr_svetlo")


def build_tr_majak():
    bm = bmesh.new()
    add_cylinder(bm, 0.09, 0.05, along_z((0.0, 0.0, 0.025)), DARK, segments=12)
    add_cylinder(bm, 0.07, 0.10, along_z((0.0, 0.0, 0.10)), LAMP_OR, segments=12, bev=0.01)
    return finish_mesh(bm, "SM_Tr_majak")


# ---------------------------------------------------------------------------
# Triedicka: vlastne diely (suradnice: pociatok = zem pod stredom podvozku, predok +X, nasypka vzadu -X)
# ---------------------------------------------------------------------------

TRK_X = 0.90                   # stred pasov (x)
TK = dict(L=3.60, R=0.40, shoe=0.06, zc=0.46, y=1.30, w=0.60, pitch=0.19)
HOP = dict(x0=-4.5, x1=-1.3, hw=1.50, zt=3.00, xb=-3.6, hb=0.64, zb=1.85)
SCR = dict(x=4.0, z=2.90, ang=7.0, L=4.2, hw=0.82, h=0.40)           # stred sita, sklon (stupne, +X dole), dlzka, polsirka, polvyska
SPEC = dict(paint=PAINT_BLU, hood=True, skirt=True)
CV_FEED = dict(key="tr_podavac", id="podavac", L=6.2, W=1.00, R=0.21, th=0.03, pitch=0.9, cleat_h=0.045, lumps=9, seed=7, lump=(5, (0.06, 0.13), ROCK), **SPEC)
CV_FEED_POS, CV_FEED_ANG = (-3.6, 0.0, 1.45), 22.0
CV_HR = dict(key="tr_hrube", id="dopr_hrube", L=7.2, W=0.90, R=0.21, th=0.03, pitch=0.9, cleat_h=0.045, lumps=7, seed=11, lump=(3, (0.09, 0.17), ROCK), **SPEC)
CV_HR_POS, CV_HR_ANG = (6.2, 0.0, 0.95), 20.0
CV_ST = dict(key="tr_stredne", id="dopr_stredne", L=5.2, W=0.90, R=0.21, th=0.03, pitch=0.9, cleat_h=0.045, lumps=6, seed=13, lump=(4, (0.05, 0.10), GRAVEL), **SPEC)
CV_ST_POS, CV_ST_ANG, CV_ST_YAW = (4.9, 0.05, 1.45), 18.0, 90.0
CV_JE = dict(key="tr_jemne", id="dopr_jemne", L=5.2, W=0.90, R=0.21, th=0.03, pitch=0.9, cleat_h=0.045, lumps=6, seed=17, lump=(5, (0.03, 0.06), SAND), **SPEC)
CV_JE_POS, CV_JE_ANG, CV_JE_YAW = (3.1, -0.05, 1.45), 18.0, -90.0
PILES = dict(hrube=((13.9, 0.0), 3.9, 2.8), stredne=((4.9, 6.3), 3.1, 2.3), jemne=((3.1, -6.3), 3.1, 2.3))


def scr_world(xl, zl):
    # bod v suradniciach sita (x po dlzke, z hore od stredu) -> (x, z) vo svete
    a = math.radians(SCR["ang"])
    return (SCR["x"] + xl * math.cos(a) + zl * math.sin(a), SCR["z"] - xl * math.sin(a) + zl * math.cos(a))


def scr_z_at(xw, zl):
    # vyska priamky rovnobeznej so sitom (v z_l) v svetovom x
    a = math.radians(SCR["ang"])
    xl = (xw - SCR["x"] - zl * math.sin(a)) / math.cos(a)
    return scr_world(xl, zl)[1]


def build_tr_podvozok():
    bm = bmesh.new()
    for x in (TRK_X - 1.9, TRK_X + 1.9):
        bx(bm, x - 0.20, x + 0.20, -1.02, 1.02, 0.55, 0.85, PAINT_GRY, 0.03)
    for s in SIDES_LR:
        bx(bm, TRK_X - 2.2, TRK_X + 2.2, s * 0.96, s * 1.10, 0.50, 0.86, PAINT_GRY, 0.03)
        for x in (TRK_X - 1.9, TRK_X, TRK_X + 1.9):
            bx(bm, x - 0.10, x + 0.10, s * 0.98, s * 1.24, 0.85, 0.95, PAINT_GRY, 0.02)
    return finish_mesh(bm, "SM_Tr_podvozok")


def build_tr_ram():
    # horny ram: dva podlzniky, priecniky (mimo dopravnikov), podlahy, stojky nasypky a podstavec sita
    bm = bmesh.new()
    for s in SIDES_LR:
        bx(bm, -4.45, 6.75, s * 0.98, s * 1.24, 0.90, 1.12, PAINT_GRY, 0.03)
    for x in (-4.35, -2.5, -0.6, 1.2, 2.1, 4.0):
        bx(bm, x - 0.10, x + 0.10, -1.14, 1.14, 0.92, 1.08, PAINT_GRY, 0.02)
    for s in SIDES_LR:
        bx(bm, -0.40, 1.80, s * 0.70, s * 1.74, 1.08, 1.13, PAINT_GRY, 0.01)
    # stojky a pozdlzniky nasypky
    for x in (-4.2, -1.5):
        for s in SIDES_LR:
            bx(bm, x - 0.09, x + 0.09, s * 1.12 - 0.09, s * 1.12 + 0.09, 1.12, 2.15, PAINT_GRY, 0.02)
    for s in SIDES_LR:
        bx(bm, -4.30, -1.40, s * 1.12 - 0.09, s * 1.12 + 0.09, 2.05, 2.17, PAINT_GRY, 0.02)
        add_rod(bm, (-4.2, s * 1.12, 1.15), (-2.9, s * 1.12, 2.08), 0.03, STEEL, segments=6)
        add_rod(bm, (-1.5, s * 1.12, 1.15), (-2.8, s * 1.12, 2.08), 0.03, STEEL, segments=6)
    # podstavec sita: styri stojky a dva sikme nosniky
    a = math.radians(SCR["ang"])
    zl = -0.72
    for s in SIDES_LR:
        for xw in (2.3, 6.0):
            zt = scr_z_at(xw, zl - 0.05)
            bx(bm, xw - 0.10, xw + 0.10, s * 1.12 - 0.10, s * 1.12 + 0.10, 1.12, zt, PAINT_GRY, 0.02)
        c = scr_world(0.0, zl - 0.05)
        add_box(bm, (4.9, 0.30, 0.10), (c[0], s * 1.12, c[1]), PAINT_GRY, bev=0.015, rotation=(0.0, SCR["ang"], 0.0))
        for xw0, xw1 in ((2.3, 3.4), (6.0, 4.9)):
            add_rod(bm, (xw0, s * 1.12, scr_z_at(xw0, zl - 0.05) - 0.05), (xw1, s * 1.12, 1.15), 0.03, STEEL, segments=6)
    return finish_mesh(bm, "SM_Tr_ram")


def build_tr_sito():
    # sito (pohyblive; pivot v strede, os X po dlzke): bocnice, dve sita (horne hrubsie, dolne jemnejsie), prekryt stredu, vibracne motory, privodna konzola
    L, hw, h = SCR["L"], SCR["hw"], SCR["h"]
    bm = bmesh.new()
    for s in SIDES_LR:
        bx(bm, -L * 0.5, L * 0.5, s * hw - 0.03, s * hw + 0.03, -h, h, PAINT_BLU, 0.02)
        bx(bm, -L * 0.5 - 0.02, L * 0.5 + 0.02, s * hw - 0.05, s * hw + 0.05, h - 0.03, h + 0.03, PAINT_GRY, 0.015)
        for x in (-1.6, 1.6):
            bx(bm, x - 0.18, x + 0.18, s * hw + 0.02, s * 1.14, -h - 0.04, -h + 0.04, PAINT_GRY, 0.015)         # konzoly pre pruziny
        for k in range(4):
            xx = -1.5 + 1.0 * k
            bx(bm, xx - 0.03, xx + 0.03, s * (hw + 0.03), s * (hw + 0.045), -h + 0.05, h - 0.05, PAINT_GRY, 0.004)
    bx(bm, -L * 0.5, -L * 0.5 + 0.06, -hw, hw, -h, 0.05, PAINT_BLU, 0.01)                                      # predna stena (nahore otvorena)
    for z, step, bars in ((0.14, 0.12, 0), (-0.16, 0.07, 1)):
        n = int(2 * (hw - 0.04) / step)
        for k in range(n + 1):
            y = -hw + 0.04 + 2 * (hw - 0.04) * k / n
            add_box(bm, (L - 0.06, 0.03, 0.03), (0.0, y, z), LINER)
        for k in range(9):
            x = -L * 0.5 + 0.15 + (L - 0.3) * k / 8.0
            add_box(bm, (0.04, 2 * hw - 0.06, 0.035), (x, 0.0, z - 0.025), PAINT_GRY)
    bx(bm, -0.9, 1.7, -hw - 0.01, hw + 0.01, h, h + 0.05, PAINT_GRY, 0.02)                                       # strecha stredu
    for k in range(3):
        bx(bm, -0.7 + 0.8 * k, -0.2 + 0.8 * k, -0.30, 0.30, h + 0.05, h + 0.09, STEEL, 0.01)
        bx(bm, -0.50 + 0.8 * k, -0.40 + 0.8 * k, -0.06, 0.06, h + 0.09, h + 0.12, STEEL, 0.005)
    for s in SIDES_LR:
        add_cylinder(bm, 0.14, 0.40, along_y((-0.2, s * (hw + 0.30), 0.20)), PAINT_GRY, segments=12, bev=0.01)
        bx(bm, -0.45, 0.05, s * (hw + 0.03), s * (hw + 0.50), 0.02, 0.10, PAINT_GRY, 0.012)
    slab(bm, [(L * 0.5, hw, -0.30), (L * 0.5, -hw, -0.30), (L * 0.5 + 0.30, -hw, -0.55), (L * 0.5 + 0.30, hw, -0.55)], 0.04, PAINT_BLU, 0.01)   # koncovy lem
    return finish_mesh(bm, "SM_Tr_sito")


def build_tr_pruziny():
    # styri pruzinove ulozenia sita (v suradniciach sita: pivot v strede sita)
    bm = bmesh.new()
    for x in (-1.6, 1.6):
        for s in SIDES_LR:
            y = s * 1.12
            z0 = -0.72
            bx(bm, x - 0.13, x + 0.13, y - 0.13, y + 0.13, z0 - 0.01, z0 + 0.03, PAINT_GRY, 0.01)
            for k in range(7):
                add_cylinder(bm, 0.085, 0.020, along_z((x, y, z0 + 0.06 + 0.032 * k)), STEEL, segments=10)
            bx(bm, x - 0.13, x + 0.13, y - 0.13, y + 0.13, z0 + 0.28, z0 + 0.31, PAINT_GRY, 0.01)
    return finish_mesh(bm, "SM_Tr_pruziny")


def build_tr_zlaby():
    # zbernne zlaby pod sitom: jemne (pred, nad pravym dopravnikom) a stredne (koniec, nad lavym dopravnikom), plus predny usmernovac pod podavacom
    bm = bmesh.new()
    t = 0.04
    zt = lambda xw: scr_z_at(xw, -SCR["h"] - 0.03)
    # jemne
    slab(bm, [(2.0, 0.85, zt(2.0)), (2.0, -0.85, zt(2.0)), (2.65, -0.55, 1.74), (2.65, 0.15, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(4.25, -0.85, zt(4.25)), (4.25, 0.85, zt(4.25)), (3.55, 0.15, 1.74), (3.55, -0.55, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(2.0, 0.85, zt(2.0)), (4.25, 0.85, zt(4.25)), (3.55, 0.15, 1.74), (2.65, 0.15, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(4.25, -0.85, zt(4.25)), (2.0, -0.85, zt(2.0)), (2.65, -0.55, 1.74), (3.55, -0.55, 1.74)], t, PAINT_GRY, 0.01)
    # stredne
    slab(bm, [(4.35, 0.85, zt(4.35)), (4.35, -0.85, zt(4.35)), (4.45, -0.15, 1.74), (4.45, 0.55, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(6.05, -0.85, zt(6.05)), (6.05, 0.85, zt(6.05)), (5.35, 0.55, 1.74), (5.35, -0.15, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(4.35, 0.85, zt(4.35)), (6.05, 0.85, zt(6.05)), (5.35, 0.55, 1.74), (4.45, 0.55, 1.74)], t, PAINT_GRY, 0.01)
    slab(bm, [(6.05, -0.85, zt(6.05)), (4.35, -0.85, zt(4.35)), (4.45, -0.15, 1.74), (5.35, -0.15, 1.74)], t, PAINT_GRY, 0.01)
    return finish_mesh(bm, "SM_Tr_zlaby")


def build_tr_vstup():
    # vstupny zlab sita: usmernovac pod vysypom podavaca a bocne dosky (pivot v pociatku)
    bm = bmesh.new()
    x0, x1 = 2.35, 3.15
    z0, z1 = scr_world(-1.5, 0.30)[1], scr_world(-0.7, 0.05)[1]
    slab(bm, [(x0 - 0.15, 0.80, z0 + 0.25), (x0 - 0.15, -0.80, z0 + 0.25), (x1, -0.80, z1), (x1, 0.80, z1)], 0.04, LINER, 0.008)
    for s in SIDES_LR:
        slab(bm, [(x0 - 0.15, s * 0.80, z0 + 0.45), (x1 + 0.1, s * 0.80, z1 + 0.20), (x1 + 0.1, s * 0.80, z1), (x0 - 0.15, s * 0.80, z0 + 0.25)], 0.04, PAINT_BLU, 0.008)
    return finish_mesh(bm, "SM_Tr_vstup")


def build_tr_hromada(name, radius, height, mat, seed, rocks, rock_size):
    return build_pile(name, radius, height, mat, seed, rocks, rock_size, mat, 5, 18, 0.05 if mat != ROCK else 0.10)


def tr_parts(put, put_lr):
    put(build_tr_podvozok())
    tk = build_tk_unit(TK)
    shift(tk, (TRK_X, 0.0, 0.0))
    put_lr(tk, "SM_Tr_pas")
    put(build_tr_ram())
    put(build_tr_nasypka())
    put_lr(build_tr_bocnica(), "SM_Tr_bocnica")
    put(build_tr_sito())
    put(build_tr_pruziny())
    put(build_tr_zlaby())
    put(build_tr_vstup())
    put(build_tr_motor())
    put(build_tr_dvere_motora())
    put(build_tr_chladic())
    put(build_tr_nadrze())
    put(build_tr_rozstrek())
    put(build_tr_svetlo())
    put(build_tr_majak())
    put(build_pile("SM_Tr_hromada_nasypka", 1.15, 0.95, ROCK, 11, 26, (0.14, 0.32), ROCK, 4, 14, 0.10))
    put(build_pile("SM_Tr_hromada_vstup", 2.1, 1.25, ROCK, 21, 70, (0.22, 0.48), ROCK, 5, 18, 0.10))
    put(build_tr_hromada("SM_Tr_hromada_hrube", PILES["hrube"][1], PILES["hrube"][2], ROCK, 31, 80, (0.10, 0.22)))
    put(build_tr_hromada("SM_Tr_hromada_stredne", PILES["stredne"][1], PILES["stredne"][2], GRAVEL, 41, 70, (0.05, 0.12)))
    put(build_tr_hromada("SM_Tr_hromada_jemne", PILES["jemne"][1], PILES["jemne"][2], SAND, 51, 20, (0.03, 0.06)))
    for cv in (CV_FEED, CV_HR, CV_ST, CV_JE):
        cv_parts(put, put_lr, cv)


# ---------------------------------------------------------------------------
# Rig triedicky: koren s vlastnostami, uchyty dielov; vibracie sita = Chod x Otacanie (faza v stupnoch), pasy beziacich dopravnikov = Pas_pohyb
# ---------------------------------------------------------------------------

TR_NAME = "Triedicka_pasova"
OFF = -1.82                    # posun motora a nadrzi (diely prevzate z drvica maju suradnice drvica)


def tr_rig(coll, parts, mats):
    name = TR_NAME
    root = new_object(coll, name, None, (0.0, 0.0, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.5
    set_prop(root, "Otacanie", 0.0, 0.0, 1000000.0, "Faza vibracii sita v stupnoch (rastie neobmedzene)")
    set_prop(root, "Chod", 0.0, 0.0, 1.0, "Rozbeh stroja: 0 = stoji, 1 = bezi (vibracie sita)")
    set_prop(root, "Pas_pohyb", 0.0, 0.0, 1000000.0, "Posun pasov vsetkych styroch dopravnikov v metroch (rastie pri behu, neobmedzene)")
    set_prop(root, "Nasypka_bocnice", 0.0, 0.0, 1.0, "Bocne klapky nasypky: 0 = zlozene dnu, 1 = vyklopene von")
    set_prop(root, "Nasypka_naplnenie", 0.0, 0.0, 1.0, "Naplnenie nasypky materialom (0 = prazdna, 1 = plna)")
    set_prop(root, "Hromada_hrube", 0.0, 0.0, 1.0, "Velkost hromady hrubej frakcie (nadsitne, os)")
    set_prop(root, "Hromada_stredne", 0.0, 0.0, 1.0, "Velkost hromady strednej frakcie (vlavo)")
    set_prop(root, "Hromada_jemne", 0.0, 0.0, 1.0, "Velkost hromady jemnej frakcie (vpravo)")
    set_prop(root, "Dvere_motora", 0.0, 0.0, 1.0, "Dvere motoroveho dielu (obe): 0 = zatvorene, 1 = otvorene")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    o0 = (0.0, 0.0, 0.0)
    for tag, key_ in (("podvozok", "Tr_podvozok"), ("ram", "Tr_ram"), ("nasypka", "Tr_nasypka"), ("zlaby", "Tr_zlaby"), ("vstup", "Tr_vstup")):
        mount(coll, name, tag, root, o0, [(tag, parts[key_])])
    for side, s in (("L", 1.0), ("P", -1.0)):
        mount(coll, name, "pas_" + side, root, o0, [("pas_" + side, parts["Tr_pas_" + side])])
        hinge, _ = mount(coll, name, "bocnica_" + side, root, ((HOP["x0"] + HOP["x1"]) * 0.5, s * HOP["hw"], HOP["zt"]), [("bocnica_" + side, parts["Tr_bocnica_" + side])])
        driver(hinge, "rotation_euler", 0, "%.0f * (-0.3491 + (1 - v) * 1.9199)" % s, [prop("v", "Nasypka_bocnice")])
    mount(coll, name, "motor", root, (OFF, 0.0, 0.0), [("motor", parts["Tr_motor"])])
    mount(coll, name, "nadrze", root, (OFF, 0.0, 0.0), [("nadrze", parts["Tr_nadrze"])])
    mount(coll, name, "chladic", root, (3.42 + OFF, 1.18, 1.75), [("chladic", parts["Tr_chladic"])])
    mount(coll, name, "majak", root, (2.0 + OFF, 1.18, 2.56), [("majak", parts["Tr_majak"])])
    mount(coll, name, "rozstrek", root, (3.30, 0.0, 3.95), [("rozstrek", parts["Tr_rozstrek"])])
    for j, (x, y, z) in enumerate(((HOP["x0"] - 0.10, 1.42, 3.12), (HOP["x0"] - 0.10, -1.42, 3.12), (3.0, 0.90, 3.50), (3.0, -0.90, 3.50))):
        lamp, _ = mount(coll, name, "svetlo_%d" % (j + 1), root, (x, y, z), [("svetlo_%d" % (j + 1), parts["Tr_svetlo"])])
        lamp.rotation_euler = (0.0, 0.0, math.pi)
    for j, x in enumerate((1.64, 2.54)):
        door, _ = mount(coll, name, "dvere_motora_%d" % (j + 1), root, (x + OFF, 1.60, 1.18), [("dvere_motora_%d" % (j + 1), parts["Tr_dvere_motora"])])
        driver(door, "rotation_euler", 2, "d * 1.7", [prop("d", "Dvere_motora")])
    # sito: osadenie so sklonom (stoji) -> sito (vibruje po svojej osi X a Z), pruziny
    base = empty(coll, name + "_uchyt_sito_osadenie", (SCR["x"], 0.0, SCR["z"]), root)
    base.empty_display_type = "ARROWS"
    base.empty_display_size = 0.3
    base.rotation_euler = (0.0, math.radians(SCR["ang"]), 0.0)
    mount(coll, name, "pruziny", base, o0, [("pruziny", parts["Tr_pruziny"])])
    screen, _ = mount(coll, name, "sito", base, o0, [("sito", parts["Tr_sito"])])
    driver(screen, "location", 0, "0.012 * c * cos(o * %.6f)" % D2R, [prop("c", "Chod"), prop("o", "Otacanie")])
    driver(screen, "location", 2, "0.010 * c * sin(o * %.6f)" % D2R, [prop("c", "Chod"), prop("o", "Otacanie")])
    # dopravniky
    cvs = {}
    for cv, pos, ang, yaw in ((CV_FEED, CV_FEED_POS, CV_FEED_ANG, 0.0), (CV_HR, CV_HR_POS, CV_HR_ANG, 0.0), (CV_ST, CV_ST_POS, CV_ST_ANG, CV_ST_YAW), (CV_JE, CV_JE_POS, CV_JE_ANG, CV_JE_YAW)):
        cvs[cv["id"]] = cv_rig(coll, name, cv, parts, root, pos, (0.0, -math.radians(ang), math.radians(yaw)), root)
    # hromady
    pile, _ = mount(coll, name, "hromada_nasypka", root, (-2.90, 0.0, 2.00), [("hromada_nasypka", parts["Tr_hromada_nasypka"])])
    driver(pile, "scale", 2, "max(v, 0.001)", [prop("v", "Nasypka_naplnenie")])
    for ax in (0, 1):
        driver(pile, "scale", ax, "sqrt(max(v, 0.001))", [prop("v", "Nasypka_naplnenie")])
    mount(coll, name, "hromada_vstup", root, (-8.2, 0.0, 0.0), [("hromada_vstup", parts["Tr_hromada_vstup"])])
    for tag, pname in (("hrube", "Hromada_hrube"), ("stredne", "Hromada_stredne"), ("jemne", "Hromada_jemne")):
        (px, py), pr, ph = PILES[tag]
        pl, _ = mount(coll, name, "hromada_" + tag, root, (px, py, 0.0), [("hromada_" + tag, parts["Tr_hromada_" + tag])])
        driver(pl, "scale", 2, "max(g, 0.001)", [prop("g", pname)])
        for ax in (0, 1):
            driver(pl, "scale", ax, "sqrt(max(g, 0.001))", [prop("g", pname)])
    tr_animate(root)
    return dict(root=root, conveyors=cvs)


def tr_keys(root, prop_name, frames):
    for frame, value in frames:
        root[prop_name] = value
        root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)


def tr_animate(root):
    tr_keys(root, "Dvere_motora", [(1, 0.0), (20, 0.0), (50, 1.0), (90, 1.0), (120, 0.0)])
    tr_keys(root, "Nasypka_bocnice", [(1, 0.0), (60, 0.0), (100, 1.0)])
    tr_keys(root, "Chod", [(1, 0.0), (130, 0.0), (170, 1.0), (960, 1.0), (1000, 0.0)])
    key_linear(root, "Otacanie", [(1, 0.0), (170, 0.0), (1000, 830 * 25.0)])
    key_linear(root, "Pas_pohyb", [(1, 0.0), (170, 0.0), (1000, 830 * 0.06)])
    tr_keys(root, "Nasypka_naplnenie", [(1, 0.0), (130, 0.0), (210, 1.0), (1000, 0.35)])
    tr_keys(root, "Hromada_hrube", [(1, 0.0), (260, 0.0), (1000, 1.0)])
    tr_keys(root, "Hromada_stredne", [(1, 0.0), (240, 0.0), (1000, 1.0)])
    tr_keys(root, "Hromada_jemne", [(1, 0.0), (220, 0.0), (1000, 1.0)])


def tr_scene(coll, parts, mats):
    sub = child_collection(coll, TR_NAME)
    return [tr_rig(sub, parts, mats)["root"]]


SCENE_BUILDERS.append(tr_scene)
PART_MAKERS.append(tr_parts)


def _tr_doc():
    return ["", "PASOVA TRIEDICKA MATERIALOV (Triedicka_pasova): mobilne dvojsitove triedenie s tromi vystupnymi dopravnikmi. Pociatok = zem pod stredom podvozku, predok +X (hrube dopravnik na osi),",
            "  nasypka vzadu (-X), lava +Y. Tok: nasypka -> podavaci pas -> vibracne dvojsito -> hrube (nadsitne, os), stredne (vlavo, +Y), jemne (vpravo, -Y).",
            "  Vlastnosti na hlavnom objekte: Otacanie (faza vibracii v stupnoch), Chod (0 stoji, 1 bezi: vibracie sita), Pas_pohyb (metre pasov), Nasypka_bocnice, Nasypka_naplnenie, Hromada_hrube / _stredne / _jemne, Dvere_motora.",
            "    Animacia 1 az 1000: dvere motora 20 az 120, bocnice 60 az 100, rozbeh 130 az 170, nasypka sa plni 130 az 210, hromady rastu od 220 / 240 / 260 do 1000.",
            "  DEMONTAZ: kazdy diel je samostatny objekt <Triedicka_pasova>_<diel> a je detom UCHYTU <Triedicka_pasova>_uchyt_<diel> (prazdny objekt v pivote dielu). Vymena: zmaz objekt dielu a novy diel daj ako dieta uchytu.",
            "  Diely: podvozok, pas_L / _P (pasy, stoja), ram (horny ram, stojky, podstavec sita), nasypka, bocnica_L / _P (klapky, rotacia X podla Nasypka_bocnice), sito (pohyblive, vibruje po X a Z) a pruziny (v uchyte sito_osadenie so sklonom %.0f st.)," % SCR["ang"],
            "    zlaby (zbernne zlaby pod sitom), vstup (vstupny zlab sita), motor, dvere_motora_1 / _2, chladic, nadrze, rozstrek, svetlo_1 az 4, majak, hromady: hromada_nasypka, hromada_vstup, hromada_hrube, hromada_stredne, hromada_jemne.",
            "  Dopravniky (kazdy na uchyte <Triedicka_pasova>_uchyt_<id>): podavac (sklon %.0f st., dlzka %.1f m), dopr_hrube (%.0f st., %.1f m), dopr_stredne (%.0f st., %.1f m, otoceny do +Y), dopr_jemne (%.0f st., %.1f m, otoceny do -Y);" % (
                CV_FEED_ANG, CV_FEED["L"], CV_HR_ANG, CV_HR["L"], CV_ST_ANG, CV_ST["L"], CV_JE_ANG, CV_JE["L"]),
            "    kazdy ma diely <id>_ram, _pas (korytovy pas), _kryt (hlava so zlabom), _buben_hlava / _chvost (otacaju sa podla Pas_pohyb); listy pasu (<id>_lista_N) a kamene (<id>_naklad_N) bezia po slucke (poloha je driver z Pas_pohyb).",
            "  Rozmery: dlzka s dopravnikmi a nasypkou asi 20 m, sirka stroja 3.2 m, vyska nasypky 3.0 m, sito %.1f x %.1f m." % (SCR["L"], 2 * SCR["hw"])]


DOC_EXTRA.extend(_tr_doc())
CATALOG_EXTRA.append(("TRIEDICKA", ["Tr_" + p for p in ("podvozok", "pas_L", "ram", "nasypka", "bocnica_L", "sito", "pruziny", "zlaby", "vstup", "motor", "dvere_motora", "chladic", "nadrze", "rozstrek", "svetlo", "majak",
                                                        "hromada_nasypka", "hromada_vstup", "hromada_hrube", "hromada_stredne", "hromada_jemne")]))
for _cv in (CV_FEED, CV_HR, CV_ST, CV_JE):
    CATALOG_EXTRA.append(("DOPRAVNIK " + _cv["id"], [cv_key(_cv, p) for p in ("ram", "pas", "buben", "lista", "kryt", "naklad_0")]))


main()
