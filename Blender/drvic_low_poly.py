# Stylizovany low poly pasovy celustovy drvic kamena na strk pre Blender 3.0 a novsi (mobilny drvic na pasovom podvozku): nasypka s bocnicami a rostom, vibracny podavac,
# celustovy drvic (pevna a pohybliva celust, excentricky hriadel so zotrvacnikmi, kolena), vystupny pasovy dopravnik so zhlukmi kamenov, motorovy diel s dvierkami, vodny rozstrek, plosina s rebrikom
# a hromady (kamen v nasypke, kamen na zemi, vydrveny strk). Vsetko je demontovatelne po dieloch (uchyty), animacia je na uchytoch a riadi ju niekolko vlastnosti na hlavnom objekte.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Drvic" (podkolekcia Drvic_celustovy) a Drvic_diely (kazdy diel samostatne s menovkou). Ovladanie vlastnostami na hlavnom objekte (panel N -> Item alebo
# Object -> Custom Properties), popis v subore Drvic.txt. Predok = +X (vystup dopravnika), nasypka vzadu (-X), lava strana = +Y. Pociatok = zem pod stredom podvozku.
# Do priecinka Drvic v domovskom priecinku ulozi FBX kazdeho dielu a textovy subor s popisom skladania. Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Drvic"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Drvic")
DOC_FILE = "Drvic.txt"
DOC_TITLE = "Celustovy drvic kamena"
FRAME_END = 1000
KIT_Y0 = 14.0


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
    bsdf = mats[TIRE].node_tree.nodes.get("Principled BSDF") if mats[TIRE].node_tree else None
    if bsdf:
        for sock in ("Specular IOR Level", "Specular"):
            if sock in bsdf.inputs:
                bsdf.inputs[sock].default_value = 0.08          # matna guma bez kovoveho lesku
                break
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


def rrect4(y0, y1, z0, z1, r_t, r_b, n=3, r_l=None, r_r=None):
    # obdlznik v YZ s ROZNYMI polomermi hornych (r_t) a spodnych (r_b) rohov; pri r <= 0.004 je roh prakticky ostry (rovna plocha pre dosadnutie)
    pts = []
    for cy_s, cz_s, a0, rr in ((1, 1, 0.0, r_t), (-1, 1, 90.0, r_t), (-1, -1, 180.0, r_b), (1, -1, 270.0, r_b)):
        rr = max(min(rr, (y1 - y0) * 0.5, (z1 - z0) * 0.5), 0.004)
        cy = (y1 - rr) if cy_s > 0 else (y0 + rr)
        cz = (z1 - rr) if cz_s > 0 else (z0 + rr)
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cy + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


def loft_rr(bm, stations, mat, n=3, flat=""):
    # hladke teleso z priecnych rezov (zaoblenych obdlznikov): stations = [(x, y0, y1, z0, z1, r), ...] od zadu dopredu; konce sa uzavru;
    # flat: "b" = spodne hrany ostre (spodna plocha lezi na inom diele), "t" = horne hrany ostre
    secs = []
    for st in stations:
        r = max(st[5], 0.004)
        secs.append((st[0], rrect4(st[1], st[2], st[3], st[4], 0.004 if "t" in flat else r, 0.004 if "b" in flat else r, n)))
    return loft_yz(bm, secs, mat)


def pillow(bm, x0, x1, y0, y1, z0, z1, r, mat, n=3, steps=3, flat=""):
    # zaoblene teleso (kvader so zaoblenymi hranami polomeru r, hladke tienovanie); flat = plochy, ktore ostanu ROVNE a ostre (dosadaju na iny diel):
    # "b" spodok, "t" vrch, "l" strana -Y, "r" strana +Y, "a" zadok (-X), "f" predok (+X); zaoblia sa len hrany medzi ostatnymi plochami
    r = min(r, (x1 - x0) * 0.5 - 0.001, (y1 - y0) * 0.5 - 0.001, (z1 - z0) * 0.5 - 0.001)
    ph = [math.pi * 0.5 * k / steps for k in range(steps + 1)]
    ends = [(r * (1.0 - math.cos(p)), r * (1.0 - math.sin(p))) for p in ph]       # (vzdialenost od steny, zmensenie)
    back = [(0.0, 0.0)] if "a" in flat else ends
    front = [(0.0, 0.0)] if "f" in flat else ends
    stations = []
    for t, d in back:
        stations.append((x0 + t, d))
    for t, d in front[::-1]:
        stations.append((x1 - t, d))
    out = []
    for x, d in stations:
        yy0 = y0 if "l" in flat else y0 + d
        yy1 = y1 if "r" in flat else y1 - d
        zz0 = z0 if "b" in flat else z0 + d
        zz1 = z1 if "t" in flat else z1 - d
        rr = max(r - d, 0.004)
        r_t = 0.004 if ("t" in flat or "l" in flat or "r" in flat) else rr
        r_b = 0.004 if ("b" in flat or "l" in flat or "r" in flat) else rr
        out.append((x, rrect4(yy0, yy1, zz0, zz1, r_t, r_b, n)))
    return loft_yz(bm, out, mat)


def win_frame(bm, plane, c0, c1, zc, w, h, t, d, off, mat, bev=0.004):
    # ramik okna (styri listy): plane "Y" = okno v rovine XZ (c0 = stred x, c1 = y polohy), plane "X" = okno v rovine YZ (c0 = stred y, c1 = x polohy);
    # w, h = rozmery otvoru, t = sirka listy, d = hlbka (po normale), off = posun stredu hlbky od c1
    if plane == "Y":
        for z in (zc - h * 0.5 - t * 0.5, zc + h * 0.5 + t * 0.5):
            add_box(bm, (w + 2 * t, d, t), (c0, c1 + off, z), mat, bev=bev)
        for x in (c0 - w * 0.5 - t * 0.5, c0 + w * 0.5 + t * 0.5):
            add_box(bm, (t, d, h), (x, c1 + off, zc), mat, bev=bev)
    else:
        for z in (zc - h * 0.5 - t * 0.5, zc + h * 0.5 + t * 0.5):
            add_box(bm, (d, w + 2 * t, t), (c1 + off, c0, z), mat, bev=bev)
        for y in (c0 - w * 0.5 - t * 0.5, c0 + w * 0.5 + t * 0.5):
            add_box(bm, (d, t, h), (c1 + off, y, zc), mat, bev=bev)


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
# Celustovy drvic: diely (suradnice: pociatok = zem pod stredom podvozku, predok +X, nasypka vzadu -X)
# ---------------------------------------------------------------------------

XC = 0.80                      # stred drvica (x)
ZC = 1.00                      # spodok drvica (vyska)
TK = dict(L=3.10, R=0.40, shoe=0.06, zc=0.46, y=1.28, w=0.58, pitch=0.19)
CONV = dict(key="dr_dopr", id="dopravnik", L=7.6, W=0.90, R=0.21, th=0.03, pitch=0.9, cleat_h=0.045, hood=True, skirt=True, lumps=9, seed=3, paint=PAINT_ORG,
            lump=(4, (0.05, 0.10), GRAVEL))
CONV_POS = (XC - 0.15, 0.0, 0.58)
CONV_ANG = 21.0
SWING_P = (0.36, 1.35)         # excentricky hriadel v suradniciach drvica (x, z nad spodkom)
HOP = dict(x0=-3.9, x1=-0.7, hw=1.40, zt=3.80, xb=-2.8, hb=0.78, zb=2.75)


def build_dr_podvozok():
    # stredny podvozok medzi pasmi: priecniky, vnutorne nosniky, stojky horneho ramu
    bm = bmesh.new()
    for x in (-1.75, 1.75):
        bx(bm, x - 0.20, x + 0.20, -1.02, 1.02, 0.55, 0.85, PAINT_GRY, 0.03)
    for s in SIDES_LR:
        bx(bm, -2.0, 2.0, s * 0.96, s * 1.10, 0.50, 0.86, PAINT_GRY, 0.03)
        for x in (-1.8, 0.0, 1.8):
            bx(bm, x - 0.10, x + 0.10, s * 0.98, s * 1.24, 0.85, 0.95, PAINT_GRY, 0.02)
    return finish_mesh(bm, "SM_Dr_podvozok")


def build_dr_ram():
    # horny ram: dva podlzniky, priecniky (mimo dopravnika), podlahy, stojky nasypky a podavaca s vystuhami
    bm = bmesh.new()
    for s in SIDES_LR:
        bx(bm, -3.45, 3.65, s * 0.98, s * 1.24, 0.90, 1.12, PAINT_GRY, 0.03)
    for x in (-3.35, -2.0, -0.55):
        bx(bm, x - 0.10, x + 0.10, -1.14, 1.14, 0.92, 1.08, PAINT_GRY, 0.02)
    bx(bm, 3.50, 3.70, -1.14, 1.14, 0.92, 1.08, PAINT_GRY, 0.02)
    for s in SIDES_LR:
        bx(bm, 1.50, 3.65, s * 0.70, s * 1.72, 1.08, 1.13, PAINT_GRY, 0.01)            # plechova podlaha pod motorom a nadrzami
    for x in (-3.2, -1.0):
        for s in SIDES_LR:
            bx(bm, x - 0.09, x + 0.09, s * 1.03 - 0.09, s * 1.03 + 0.09, 1.12, 2.62, PAINT_GRY, 0.02)          # stojky
            add_rod(bm, (x - 0.09, s * 1.03, 1.15), (x + 0.9 if x < -2.0 else x - 0.9, s * 1.03, 2.55), 0.03, STEEL, segments=6)
        bx(bm, x - 0.12, x + 0.12, -1.12, 1.12, 2.50, 2.62, PAINT_GRY, 0.02)
    for s in SIDES_LR:
        bx(bm, -3.40, -0.6, s * 0.94, s * 1.12, 2.55, 2.66, PAINT_GRY, 0.02)
    return finish_mesh(bm, "SM_Dr_ram")


def build_dr_nasypka():
    # nasypka: sikme steny (zadna a dve bocne) z dosiek s vystuhami a obrubou, vnutorne oblozenie
    H = HOP
    bm = bmesh.new()
    x0, x1, hw, zt, xb, hb, zb = H["x0"], H["x1"], H["hw"], H["zt"], H["xb"], H["hb"], H["zb"]
    slab(bm, [(x0, hw, zt), (x0, -hw, zt), (xb, -hb, zb), (xb, hb, zb)], 0.05, PAINT_ORG, 0.01)
    slab(bm, [(x1, hw, zt), (x0, hw, zt), (xb, hb, zb), (x1, hb, zb)], 0.05, PAINT_ORG, 0.01)
    slab(bm, [(x0, -hw, zt), (x1, -hw, zt), (x1, -hb, zb), (xb, -hb, zb)], 0.05, PAINT_ORG, 0.01)
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
    return finish_mesh(bm, "SM_Dr_nasypka")


def build_dr_bocnica():
    # bocna klapka nasypky (lava; prava je zrkadlo), pivot na zavese (stred dlzky, horna hrana steny); vyklopena stoji naklonena von o 20 st., zlozena lezi dnu
    H = HOP
    L = H["x1"] - H["x0"]
    bm = bmesh.new()
    add_box(bm, (L - 0.10, 0.05, 0.62), (0.0, 0.0, 0.31), PAINT_ORG, bev=0.015)
    add_box(bm, (L - 0.10, 0.07, 0.06), (0.0, 0.0, 0.64), PAINT_GRY, bev=0.012)
    for k in range(5):
        add_box(bm, (0.06, 0.07, 0.56), (-L * 0.5 + 0.35 + (L - 0.7) * k / 4.0, 0.0, 0.31), PAINT_GRY, bev=0.01)
    return bm


def build_dr_rost():
    # rost (rosty) na dne nasypky: pozdlzne tyce a tri priecky z oblozenia
    bm = bmesh.new()
    for k in range(13):
        y = -0.72 + 1.44 * k / 12.0
        add_box(bm, (2.05, 0.05, 0.09), (-1.75, y, 0.0), LINER, bev=0.006, rotation=(0.0, -3.0, 0.0))
    for x in (-2.6, -1.8, -0.9):
        bx(bm, x - 0.04, x + 0.04, -0.80, 0.80, -0.10, -0.03, PAINT_GRY, 0.01)
    return finish_mesh(bm, "SM_Dr_rost")


def build_dr_podavac():
    # vibracny podavac (pohyblivy; pivot v strede dna): koryto s bocnicami, dno z oblozenia, dva vibracne motory, pruzne ulozenie
    bm = bmesh.new()
    bx(bm, -1.45, 1.50, -0.78, 0.78, -0.05, 0.02, PAINT_ORG, 0.015)
    bx(bm, -1.40, 1.45, -0.74, 0.74, 0.02, 0.05, LINER)
    for s in SIDES_LR:
        bx(bm, -1.45, 1.50, s * 0.76, s * 0.82, -0.05, 0.40, PAINT_ORG, 0.02)
        add_cylinder(bm, 0.12, 0.34, along_y((-0.2, s * 0.98, 0.20)), PAINT_GRY, segments=12, bev=0.01)
        bx(bm, -0.5, 0.1, s * 0.80, s * 0.92, 0.10, 0.30, PAINT_GRY, 0.015)
    bx(bm, 1.40, 1.55, -0.78, 0.78, -0.05, 0.12, PAINT_ORG, 0.015)
    return finish_mesh(bm, "SM_Dr_podavac")


def build_dr_pruziny():
    # pruziny podavaca (styri ulozenia na stojkach: valcove pruziny z kruzkov)
    bm = bmesh.new()
    for x in (-1.3, 0.9):
        for s in SIDES_LR:
            bx(bm, x - 0.12, x + 0.12, s * 0.92 - 0.12, s * 0.92 + 0.12, 0.0, 0.05, PAINT_GRY, 0.01)
            for k in range(6):
                add_cylinder(bm, 0.085, 0.022, along_z((x, s * 0.92, 0.07 + 0.035 * k)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Dr_pruziny")


def build_dr_drvic():
    # celustovy drvic (pevna cast; pivot na spodku v strede): telo z bocnic, pevna celust s oblozenim, vstupny zlab, vystupny zlab, kolenove spojenie s pruzinou
    bm = bmesh.new()
    cheek = [(-0.66, 0.00), (0.66, 0.00), (0.70, 1.20), (0.54, 1.55), (-0.46, 1.55), (-0.70, 1.26)]
    for s in SIDES_LR:
        add_extruded(bm, cheek, s * 0.50 - 0.07, s * 0.50 + 0.07, "XZ", PAINT_ORG, bev=0.025)
        add_cylinder(bm, 0.18, 0.12, along_y((SWING_P[0], s * 0.70, SWING_P[1])), PAINT_GRY, segments=14, bev=0.01)
        add_cylinder(bm, 0.10, 0.05, along_y((SWING_P[0], s * 0.78, SWING_P[1])), STEEL, segments=10)
    # zadna oporna stena a pevna celust
    slab(bm, [(-0.66, 0.5, 0.05), (-0.66, -0.5, 0.05), (-0.46, -0.5, 1.55), (-0.46, 0.5, 1.55)], 0.20, PAINT_ORG, 0.02)
    add_extruded(bm, [(-0.14, 0.10), (-0.04, 0.10), (-0.30, 1.50), (-0.42, 1.50)], -0.50, 0.50, "XZ", LINER, bev=0.006)
    for k in range(9):
        t = (k + 0.5) / 9.0
        z = 0.10 + 1.40 * t
        x = -0.14 - 0.28 * t + 0.045
        add_box(bm, (0.05, 0.96, 0.07), (x, 0.0, z), LINER, rotation=(0.0, 12.0, 0.0))
    # vstupny zlab
    slab(bm, [(-0.46, 0.56, 1.55), (-0.46, -0.56, 1.55), (-0.62, -0.74, 1.90), (-0.62, 0.74, 1.90)], 0.04, PAINT_ORG, 0.01)
    slab(bm, [(0.54, 0.56, 1.55), (0.54, -0.56, 1.55), (0.70, -0.74, 1.90), (0.70, 0.74, 1.90)], 0.04, PAINT_ORG, 0.01)
    for s in SIDES_LR:
        slab(bm, [(-0.46, s * 0.56, 1.55), (0.54, s * 0.56, 1.55), (0.70, s * 0.74, 1.90), (-0.62, s * 0.74, 1.90)], 0.04, PAINT_ORG, 0.01)
    # vystupny zlab pod drvicom
    for s in SIDES_LR:
        add_extruded(bm, [(-0.40, 0.04), (0.45, 0.04), (0.40, -0.16), (-0.20, -0.16)], s * 0.53 - 0.03, s * 0.53 + 0.03, "XZ", PAINT_ORG, bev=0.01)
    bx(bm, 0.36, 0.44, -0.54, 0.54, -0.16, 0.04, PAINT_ORG, 0.01)
    # koleno (zalomena tyc medzi spodkom pohyblivej celuste a zadnym operatkom) a pruzina
    bx(bm, 0.40, 0.70, -0.26, 0.26, 0.04, 0.34, PAINT_GRY, 0.02)
    add_rod(bm, (0.70, 0.0, 0.20), (1.12, 0.0, 0.20), 0.03, STEEL, segments=8)
    for k in range(8):
        add_cylinder(bm, 0.07, 0.03, along_x((0.80 + 0.04 * k, 0.0, 0.20)), STEEL, segments=10)
    bx(bm, 1.10, 1.16, -0.12, 0.12, 0.08, 0.32, PAINT_GRY, 0.01)
    bx(bm, -0.66, 0.66, -0.64, 0.64, -0.02, 0.04, PAINT_GRY, 0.015)                  # podlozka pod drvicom
    return finish_mesh(bm, "SM_Dr_drvic")


def build_dr_celust():
    # pohybliva celust (pivot v osi excentrickeho hriadela): doska s oblozenim a zubami, hlava s loziskom, spodok s kolenom
    bm = bmesh.new()
    add_extruded(bm, [(0.12, 0.16), (-0.08, 0.16), (-0.52, -1.14), (-0.30, -1.14)], -0.49, 0.49, "XZ", PAINT_ORG, bev=0.02)
    add_extruded(bm, [(-0.06, 0.10), (-0.14, 0.10), (-0.50, -1.12), (-0.58, -1.12)][::-1], -0.48, 0.48, "XZ", LINER, bev=0.006)
    for k in range(9):
        t = (k + 0.5) / 9.0
        z = 0.06 - 1.18 * t
        x = -0.12 - 0.40 * t - 0.03
        add_box(bm, (0.05, 0.94, 0.07), (x, 0.0, z), LINER, rotation=(0.0, -20.0, 0.0))
    add_cylinder(bm, 0.14, 0.98, along_y((0.0, 0.0, 0.0)), PAINT_GRY, segments=14, bev=0.01)
    bx(bm, -0.34, -0.08, -0.40, 0.40, -1.22, -1.08, PAINT_GRY, 0.015)
    return finish_mesh(bm, "SM_Dr_celust")


def build_dr_hriadel():
    # excentricky hriadel so zotrvacnikmi (pivot v osi, otaca sa): hriadel, dva zotrvacniky s vencom, nabojom, ramenami a protizavazim
    bm = bmesh.new()
    add_cylinder(bm, 0.09, 1.95, along_y((0.0, 0.0, 0.0)), STEEL, segments=14, bev=0.005)
    for s in SIDES_LR:
        y = s * 0.92
        add_ring(bm, 0.44, 0.34, 0.10, y, PAINT_GRY, 22, bev=0.008)
        add_cylinder(bm, 0.14, 0.14, along_y((0.0, y, 0.0)), STEEL, segments=12, bev=0.008)
        for k in range(6):
            a = 2.0 * math.pi * k / 6
            add_box(bm, (0.09, 0.07, 0.22), (0.0, y, 0.0), PAINT_GRY, bev=0.01,
                    frame=Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0.0, 0.0, 0.26)))
        add_box(bm, (0.20, 0.12, 0.12), (0.0, y, 0.0), PAINT_ORG, bev=0.02, frame=Matrix.Rotation(0.5, 4, "Y") @ Matrix.Translation((0.0, 0.0, 0.40)))
        add_ring(bm, 0.45, 0.43, 0.04, y + s * 0.07, STEEL, 22)
    return finish_mesh(bm, "SM_Dr_hriadel")


def build_dr_motor():
    # motorovy diel (diesel s krytom, zlava vedla dopravnika): kryt s vetracimi liszami, strecha so sacim kanalom, nosnik, spodne rebra
    bm = bmesh.new()
    x0, x1, y0, y1, z0, z1 = 1.62, 3.42, 0.76, 1.60, 1.13, 2.36
    bx(bm, x0, x1, y0, y1, z0, z1, PAINT_ORG, 0.04)
    bx(bm, x0 + 0.10, x1 - 0.20, y0 + 0.10, y1 - 0.10, z1, z1 + 0.20, PAINT_GRY, 0.03)
    for k in range(4):
        bx(bm, x0 + 0.20 + 0.28 * k, x0 + 0.40 + 0.28 * k, y0 + 0.14, y1 - 0.14, z1 + 0.20, z1 + 0.23, STEEL, 0.004)
    add_cylinder(bm, 0.075, 1.0, along_z((x0 + 0.30, y0 + 0.22, z1 + 0.5)), STEEL, segments=10, bev=0.004)
    add_cylinder(bm, 0.095, 0.05, along_z((x0 + 0.30, y0 + 0.22, z1 + 1.02)), DARK, segments=10)
    for s in (y0 + 0.02, y1 - 0.02):
        bx(bm, x0 - 0.01, x1 + 0.01, s - 0.02, s + 0.02, z0 + 0.02, z0 + 0.10, PAINT_GRY, 0.01)
    return finish_mesh(bm, "SM_Dr_motor")


def build_dr_dvere_motora():
    # dvere motoroveho dielu (pivot na zavese, dvere siahaju do +X; druhe dvere su zrkadlene otocenim v rigu): panel s oknom listov
    bm = bmesh.new()
    add_box(bm, (0.86, 0.04, 1.10), (0.43, 0.02, 0.58), PAINT_ORG, bev=0.015)
    for k in range(6):
        bx(bm, 0.12, 0.74, 0.04, 0.062, 0.18 + 0.12 * k, 0.21 + 0.12 * k, DARK, 0.004)
    bx(bm, 0.70, 0.78, 0.04, 0.07, 0.50, 0.64, STEEL, 0.006)
    return finish_mesh(bm, "SM_Dr_dvere_motora")


def build_dr_chladic():
    # chladic s ventilatorom na predku motora (pivot na spodku v strede plochy): skrinka, ochranna mriezka s listami a nabojom
    bm = bmesh.new()
    bx(bm, 0.0, 0.26, -0.40, 0.40, -0.55, 0.55, PAINT_GRY, 0.03)
    add_ring(bm, 0.36, 0.33, 0.03, 0.0, STEEL, 20)
    for k in range(3):
        add_box(bm, (0.012, 0.66 - 0.2 * k, 0.014), (0.28, 0.0, 0.0), STEEL, rotation=(0.0, 0.0, 0.0), frame=Matrix.Rotation(k * math.pi / 3.0, 4, "X"))
    add_cylinder(bm, 0.07, 0.04, along_x((0.28, 0.0, 0.0)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Dr_chladic")


def build_dr_nadrze():
    # hydraulicka nadrz a nadrz nafty (prava strana ramu): skrine s uzavermi, mierkou hladiny a ciernymi zachytmi
    bm = bmesh.new()
    bx(bm, 1.70, 2.80, -1.62, -0.78, 1.13, 1.95, PAINT_GRY, 0.04)
    bx(bm, 1.70, 2.80, -1.66, -1.62, 1.35, 1.80, DARK, 0.01)
    add_cylinder(bm, 0.07, 0.08, along_z((2.1, -1.2, 1.99)), STEEL, segments=10)
    bx(bm, 2.90, 3.40, -1.62, -0.78, 1.13, 2.30, PAINT_ORG, 0.04)
    for k in range(5):
        bx(bm, 2.95, 3.35, -1.64, -1.62, 1.30 + 0.17 * k, 1.36 + 0.17 * k, DARK, 0.004)
    return finish_mesh(bm, "SM_Dr_nadrze")


def build_dr_plosina():
    # obsluzna plosina pozdlz laveho boku drvica s zabradlim a dvoma stlpikmi pre rebrik; pivot v pociatku
    bm = bmesh.new()
    z = 1.38
    bx(bm, -0.60, 1.60, 1.04, 1.58, z - 0.04, z, PAINT_GRY, 0.01)
    for k in range(int(2.2 / 0.1)):
        bx(bm, -0.58 + 0.1 * k, -0.52 + 0.1 * k, 1.06, 1.56, z, z + 0.012, STEEL, 0.003)
    for x in (-0.55, 0.45, 1.55):
        add_rod(bm, (x, 1.55, z), (x, 1.55, z + 1.0), 0.025, STEEL, segments=8)
    add_rod(bm, (-0.55, 1.55, z + 1.0), (1.55, 1.55, z + 1.0), 0.025, STEEL, segments=8)
    add_rod(bm, (-0.55, 1.55, z + 0.5), (1.55, 1.55, z + 0.5), 0.02, STEEL, segments=8)
    for xs in (-0.55, 1.55):
        add_rod(bm, (xs, 1.55, z + 1.0), (xs, 1.08, z + 1.0), 0.02, STEEL, segments=8)
    for x in (-0.55, 0.45, 1.55):
        add_rod(bm, (x, 1.05, z - 0.04), (x, 1.04, 1.12), 0.03, STEEL, segments=6)
    return finish_mesh(bm, "SM_Dr_plosina")


def build_dr_rebrik():
    # rebrik od zeme na plosinu (sikmy, dva bocnice a priecky): pivot na zemi pri spodku
    bm = bmesh.new()
    top = (0.55, 0.0, 1.38)
    for s in (-0.20, 0.20):
        add_rod(bm, (0.0, s, 0.0), (top[0], s, top[2]), 0.02, STEEL, segments=8)
    n = 7
    for k in range(1, n):
        t = k / float(n)
        add_rod(bm, (top[0] * t, -0.20, top[2] * t), (top[0] * t, 0.20, top[2] * t), 0.015, STEEL, segments=6)
    return finish_mesh(bm, "SM_Dr_rebrik")


def build_dr_rozstrek():
    # vodny rozstrek nad vstupom: rura s piatimi tryskami a priponom
    bm = bmesh.new()
    add_rod(bm, (0.0, -0.78, 0.0), (0.0, 0.78, 0.0), 0.025, PAINT_BLU, segments=8)
    for k in range(5):
        y = -0.60 + 0.30 * k
        add_rod(bm, (0.0, y, 0.0), (0.0, y, -0.12), 0.015, STEEL, segments=6)
        add_cone(bm, 0.0, 0.03, 0.06, along_z((0.0, y, -0.15)), CHROME, segments=8)
    for s in SIDES_LR:
        add_rod(bm, (0.0, s * 0.70, 0.0), (0.0, s * 0.70, -0.36), 0.02, PAINT_BLU, segments=6)
    return finish_mesh(bm, "SM_Dr_rozstrek")


def build_dr_svetlo():
    bm = bmesh.new()
    add_box(bm, (0.10, 0.26, 0.14), (0.05, 0.0, 0.0), DARK, bev=0.02)
    add_box(bm, (0.02, 0.22, 0.10), (0.105, 0.0, 0.0), LAMP_WHITE, bev=0.01)
    return finish_mesh(bm, "SM_Dr_svetlo")


def build_dr_majak():
    bm = bmesh.new()
    add_cylinder(bm, 0.09, 0.05, along_z((0.0, 0.0, 0.025)), DARK, segments=12)
    add_cylinder(bm, 0.07, 0.10, along_z((0.0, 0.0, 0.10)), LAMP_OR, segments=12, bev=0.01)
    return finish_mesh(bm, "SM_Dr_majak")


def build_dr_hromada_kamen():
    # kamen v nasypke (hromada v nasypke, pivot na dne v strede)
    return build_pile("SM_Dr_hromada_nasypka", 1.15, 0.95, ROCK, 11, 26, (0.14, 0.32), ROCK, 4, 14, 0.10)


def build_dr_hromada_zem():
    # kamen na zemi (hromada vstupneho materialu pred nasypkou, pivot na zemi v strede)
    return build_pile("SM_Dr_hromada_vstup", 2.1, 1.25, ROCK, 21, 70, (0.22, 0.48), ROCK, 5, 18, 0.10)


def build_dr_hromada_strk():
    # vydrveny strk (hromada pod koncom dopravnika, pivot na zemi v strede)
    return build_pile("SM_Dr_hromada_strk", 3.5, 2.85, GRAVEL, 5, 90, (0.05, 0.12), GRAVEL, 6, 22, 0.035)


def dr_parts(put, put_lr):
    put(build_dr_podvozok())
    put_lr(build_tk_unit(TK), "SM_Dr_pas")
    put(build_dr_ram())
    put(build_dr_nasypka())
    put_lr(build_dr_bocnica(), "SM_Dr_bocnica")
    put(build_dr_rost())
    put(build_dr_podavac())
    put(build_dr_pruziny())
    put(build_dr_drvic())
    put(build_dr_celust())
    put(build_dr_hriadel())
    put(build_dr_motor())
    put(build_dr_dvere_motora())
    put(build_dr_chladic())
    put(build_dr_nadrze())
    put(build_dr_plosina())
    put(build_dr_rebrik())
    put(build_dr_rozstrek())
    put(build_dr_svetlo())
    put(build_dr_majak())
    put(build_dr_hromada_kamen())
    put(build_dr_hromada_zem())
    put(build_dr_hromada_strk())
    cv_parts(put, put_lr, CONV)
    dmin, dmax = dr_cyl_range()
    n, ell = tele_stages(dmin * 0.97, dmax * 1.03)
    cylinder_family(put, "Dr_valec", n, ell, 0.07)


def dr_cyl_range():
    # rozsah vzdialenosti valca podpery dopravnika (pevny; len urcuje pocet stupnov)
    a, b = dr_cyl_points()
    d = (a - b).length
    return d, d


def dr_cyl_points():
    # zaklad valca na ramu a bod na boku dopravnika (svetove suradnice, pre y > 0)
    base = Vector((3.50, 1.10, 1.00))
    ang = math.radians(CONV_ANG)
    xl, yl, zl = 5.0, 0.62, -0.34
    p = Vector((CONV_POS[0] + xl * math.cos(ang) + zl * math.sin(ang), yl, CONV_POS[2] + xl * math.sin(ang) - zl * math.cos(ang)))
    return base, p


# ---------------------------------------------------------------------------
# Rig drvica: koren s vlastnostami, uchyty dielov; otacanie zotrvacnikov = Otacanie (stupne), vibracie a kyvanie celuste podla Chod a Otacanie
# ---------------------------------------------------------------------------

DR_NAME = "Drvic_celustovy"


def dr_rig(coll, parts, mats):
    name = DR_NAME
    root = new_object(coll, name, None, (0.0, 0.0, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.5
    set_prop(root, "Otacanie", 0.0, 0.0, 1000000.0, "Otacanie zotrvacnikov drvica v stupnoch (rastie neobmedzene)")
    set_prop(root, "Chod", 0.0, 0.0, 1.0, "Rozbeh stroja: 0 = stoji, 1 = bezi (vibracie podavaca a kyvanie celuste)")
    set_prop(root, "Pas_pohyb", 0.0, 0.0, 1000000.0, "Posun pasu dopravnika v metroch (rastie pri behu, neobmedzene)")
    set_prop(root, "Nasypka_bocnice", 0.0, 0.0, 1.0, "Bocne klapky nasypky: 0 = zlozene dnu, 1 = vyklopene von")
    set_prop(root, "Nasypka_naplnenie", 0.0, 0.0, 1.0, "Naplnenie nasypky kamenom (0 = prazdna, 1 = plna)")
    set_prop(root, "Hromada_strk", 0.0, 0.0, 1.0, "Velkost hromady vydrveneho strku pod dopravnikom")
    set_prop(root, "Dvere_motora", 0.0, 0.0, 1.0, "Dvere motoroveho dielu (obe): 0 = zatvorene, 1 = otvorene")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    o0 = (0.0, 0.0, 0.0)
    mount(coll, name, "rost", root, (0.0, 0.0, 2.80), [("rost", parts["Dr_rost"])])
    for tag, key_ in (("podvozok", "Dr_podvozok"), ("ram", "Dr_ram"), ("nasypka", "Dr_nasypka"), ("pruziny", "Dr_pruziny"), ("motor", "Dr_motor"),
                      ("nadrze", "Dr_nadrze"), ("plosina", "Dr_plosina")):
        mount(coll, name, tag, root, o0, [(tag, parts[key_])])
    for side, s in (("L", 1.0), ("P", -1.0)):
        mount(coll, name, "pas_" + side, root, o0, [("pas_" + side, parts["Dr_pas_" + side])])
        hinge, _ = mount(coll, name, "bocnica_" + side, root, (-2.30, s * HOP["hw"], HOP["zt"]), [("bocnica_" + side, parts["Dr_bocnica_" + side])])
        driver(hinge, "rotation_euler", 0, "%.0f * (-0.3491 + (1 - v) * 1.9199)" % s, [prop("v", "Nasypka_bocnice")])
    mount(coll, name, "chladic", root, (3.42, 1.18, 1.75), [("chladic", parts["Dr_chladic"])])
    mount(coll, name, "rebrik", root, (-0.95, 1.30, 0.0), [("rebrik", parts["Dr_rebrik"])])
    mount(coll, name, "rozstrek", root, (XC - 0.10, 0.0, 3.22), [("rozstrek", parts["Dr_rozstrek"])])
    mount(coll, name, "majak", root, (2.0, 1.18, 2.56), [("majak", parts["Dr_majak"])])
    for j, (x, y, z) in enumerate(((-3.95, 1.30, 3.95), (-3.95, -1.30, 3.95), (XC - 0.60, 0.78, 2.88), (XC - 0.60, -0.78, 2.88))):
        lamp, _ = mount(coll, name, "svetlo_%d" % (j + 1), root, (x, y, z), [("svetlo_%d" % (j + 1), parts["Dr_svetlo"])])
        lamp.rotation_euler = (0.0, 0.0, math.pi) if j != 2 and j != 3 else (0.0, 0.0, math.pi)
    for j, x in enumerate((1.64, 2.54)):
        door, _ = mount(coll, name, "dvere_motora_%d" % (j + 1), root, (x, 1.60, 1.18), [("dvere_motora_%d" % (j + 1), parts["Dr_dvere_motora"])])
        driver(door, "rotation_euler", 2, "d * 1.7", [prop("d", "Dvere_motora")])
    # podavac (vibruje), rost, drvic, celust (kyva sa), hriadel (otaca sa)
    feeder, _ = mount(coll, name, "podavac", root, (-1.20, 0.0, 2.62), [("podavac", parts["Dr_podavac"])])
    driver(feeder, "location", 0, "-1.2 + 0.010 * c * cos(o * %.6f)" % D2R, [prop("c", "Chod"), prop("o", "Otacanie")])
    driver(feeder, "location", 2, "2.62 + 0.012 * c * sin(o * %.6f)" % D2R, [prop("c", "Chod"), prop("o", "Otacanie")])
    mount(coll, name, "drvic", root, (XC, 0.0, ZC), [("drvic", parts["Dr_drvic"])])
    jaw, _ = mount(coll, name, "celust", root, (XC + SWING_P[0], 0.0, ZC + SWING_P[1]), [("celust", parts["Dr_celust"])])
    driver(jaw, "rotation_euler", 1, "0.05 * c * sin(o * %.6f)" % D2R, [prop("c", "Chod"), prop("o", "Otacanie")])
    shaft, _ = mount(coll, name, "hriadel", root, (XC + SWING_P[0], 0.0, ZC + SWING_P[1]), [("hriadel", parts["Dr_hriadel"])])
    driver(shaft, "rotation_euler", 1, "o * %.6f" % D2R, [prop("o", "Otacanie")])
    # dopravnik
    cv = cv_rig(coll, name, CONV, parts, root, CONV_POS, (0.0, -math.radians(CONV_ANG), 0.0), root)
    d = (dr_cyl_points()[0] - dr_cyl_points()[1]).length
    n, ell = tele_stages(d * 0.97, d * 1.03)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        telescope(coll, "%s_valec_pasu_%s" % (name, side), parts, "Dr_valec", n, ell, root, (3.50, s * 1.10, 1.00), cv["root"], (5.0, s * 0.62, -0.34))
    # hromady
    pile, _ = mount(coll, name, "hromada_nasypka", root, (-2.30, 0.0, 2.68), [("hromada_nasypka", parts["Dr_hromada_nasypka"])])
    driver(pile, "scale", 2, "max(v, 0.001)", [prop("v", "Nasypka_naplnenie")])
    for ax in (0, 1):
        driver(pile, "scale", ax, "sqrt(max(v, 0.001))", [prop("v", "Nasypka_naplnenie")])
    mount(coll, name, "hromada_vstup", root, (-7.0, 0.0, 0.0), [("hromada_vstup", parts["Dr_hromada_vstup"])])
    gravel, _ = mount(coll, name, "hromada_strk", root, (8.60, 0.0, 0.0), [("hromada_strk", parts["Dr_hromada_strk"])])
    driver(gravel, "scale", 2, "max(g, 0.001)", [prop("g", "Hromada_strk")])
    for ax in (0, 1):
        driver(gravel, "scale", ax, "sqrt(max(g, 0.001))", [prop("g", "Hromada_strk")])
    dr_animate(root)
    return dict(root=root, conveyor=cv)


def dr_keys(root, prop_name, frames):
    for frame, value in frames:
        root[prop_name] = value
        root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)


def dr_animate(root):
    dr_keys(root, "Dvere_motora", [(1, 0.0), (20, 0.0), (50, 1.0), (90, 1.0), (120, 0.0)])
    dr_keys(root, "Nasypka_bocnice", [(1, 0.0), (60, 0.0), (100, 1.0)])
    dr_keys(root, "Chod", [(1, 0.0), (130, 0.0), (170, 1.0), (960, 1.0), (1000, 0.0)])
    key_linear(root, "Otacanie", [(1, 0.0), (170, 0.0), (1000, 830 * 21.6)])
    key_linear(root, "Pas_pohyb", [(1, 0.0), (170, 0.0), (1000, 830 * 0.06)])
    dr_keys(root, "Nasypka_naplnenie", [(1, 0.0), (130, 0.0), (210, 1.0), (1000, 0.35)])
    dr_keys(root, "Hromada_strk", [(1, 0.0), (220, 0.0), (1000, 1.0)])


def dr_scene(coll, parts, mats):
    sub = child_collection(coll, DR_NAME)
    return [dr_rig(sub, parts, mats)["root"]]


SCENE_BUILDERS.append(dr_scene)
PART_MAKERS.append(dr_parts)


def _dr_doc():
    return ["", "CELUSTOVY DRVIC KAMENA (Drvic_celustovy): mobilny pasovy drvic. Pociatok = zem pod stredom podvozku, predok +X (vystup dopravnika), nasypka vzadu (-X), lava +Y.",
            "  Vlastnosti na hlavnom objekte: Otacanie (stupne zotrvacnikov), Chod (0 = stoji, 1 = bezi: vibracie podavaca a kyvanie celuste), Pas_pohyb (metre pasu), Nasypka_bocnice (0 zlozene, 1 vyklopene),",
            "    Nasypka_naplnenie (kamen v nasypke), Hromada_strk (hromada strku), Dvere_motora (0 az 1). Animacia 1 az 1000: dvere motora 20 az 120, bocnice 60 az 100, rozbeh 130 az 170, nasypka sa plni 130 az 210, strk rastie 220 az 1000.",
            "  DEMONTAZ: kazdy diel je samostatny objekt <Drvic_celustovy>_<diel> a je detom UCHYTU <Drvic_celustovy>_uchyt_<diel> (prazdny objekt v pivote dielu). Vymena: zmaz objekt dielu a novy diel daj ako dieta uchytu.",
            "  Diely: podvozok, pas_L / _P (pasy, stoja), ram, nasypka, bocnica_L / _P (klapky, rotacia X podla Nasypka_bocnice), rost (rost), pruziny, podavac (vibruje po X a Z), drvic (telo drvica s pevnou celustou),",
            "    celust (pohybliva celust, pivot v osi hriadela, kyva sa o +-3 st.), hriadel (excentricky hriadel so zotrvacnikmi, otaca sa), motor, dvere_motora_1 / _2 (zavesy, rotacia Z), chladic, nadrze, plosina, rebrik, rozstrek (vodny rozstrek),",
            "    svetlo_1 az 4, majak, hromada_nasypka (kamen v nasypke, mierka podla Nasypka_naplnenie), hromada_vstup (vstupny material na zemi), hromada_strk (vydrveny strk, mierka podla Hromada_strk).",
            "  Dopravnik (uchyt <Drvic_celustovy>_uchyt_dopravnik, sklon %.0f st.): dopravnik_ram, dopravnik_pas (korytovy pas), dopravnik_kryt (hlava so zlabom), dopravnik_buben_hlava / _chvost (otacaju sa podla Pas_pohyb), listy pasu a kamene bezia po slucke" % CONV_ANG,
            "    (objekty <Drvic_celustovy>_dopravnik_lista_N a _naklad_N, poloha je driver z Pas_pohyb). Podpera dopravnika: dva teleskopicke valce <Drvic_celustovy>_valec_pasu_L / _P (prvy stupen mieri na bod na bocnici dopravnika).",
            "  Rozmery: dlzka bez dopravnika asi 8 m, s dopravnikom a nasypkou asi 12.5 m, sirka 3.2 m, vyska nasypky 3.8 m, dopravnik %.1f m, pas %.2f m." % (CONV["L"], CONV["W"])]


DOC_EXTRA.extend(_dr_doc())
CATALOG_EXTRA.append(("DRVIC - CELUSTOVY", ["Dr_" + p for p in ("podvozok", "pas_L", "ram", "nasypka", "bocnica_L", "rost", "podavac", "pruziny", "drvic", "celust", "hriadel", "motor", "dvere_motora", "chladic",
                                                              "nadrze", "plosina", "rebrik", "rozstrek", "svetlo", "majak", "hromada_nasypka", "hromada_vstup", "hromada_strk")] +
                      [cv_key(CONV, p) for p in ("ram", "pas", "buben", "lista", "kryt", "naklad_0")]))


main()
