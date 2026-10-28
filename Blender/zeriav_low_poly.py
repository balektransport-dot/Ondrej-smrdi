# Stylizovane low poly autozeriav pre Blender 3.0 a novsi: dve velkosti (Zeriav_40t: 3 napravy, 4-dielne teleskopicke rameno; Zeriav_80t: 4 napravy, 5-dielne rameno),
# podvozok s kabinou, riadenymi nahradami, kolesami a styrmi vysuvnymi podperami, otocna nadstavba s kabinou zerava, protizavazim, teleskopickym ramenom na valci zdvihu,
# hlavou s kladkou a lanom s hakovym blokom. Vsetko je demontovatelne po dieloch (uchyty), animacia je na uchytoch.
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Zeriav": podkolekcie pre kazdy zeriav (Zeriav_40t, Zeriav_80t) a Zeriav_diely (kazdy diel samostatne s menovkou).
# Ovladanie vlastnostami na hlavnom objekte (panel N -> Item alebo Object -> Custom Properties), popis v subore Zeriav.txt.
# Predok = +X, lava strana = +Y. Pociatok = zem pod osou otocnej nadstavby. Do priecinka Zeriav v domovskom priecinku ulozi FBX kazdeho dielu a textovy subor.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Zeriav"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Zeriav")
DOC_FILE = "Zeriav.txt"
DOC_TITLE = "Autozeriav"
FRAME_END = 1000
KIT_Y0 = 10.0


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
# Materialy
# ---------------------------------------------------------------------------

MATERIALS = [
    ("ZR_Ram", (0.022, 0.023, 0.028, 1.0), 0.15, 0.55, 0.0, 1.0),
    ("ZR_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0, 1.0),
    ("ZR_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0, 1.0),
    ("ZR_Pneu", (0.010, 0.010, 0.010, 1.0), 0.0, 0.95, 0.0, 1.0),
    ("ZR_Disk", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("ZR_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("ZR_Sklo", (0.015, 0.03, 0.045, 1.0), 0.0, 0.04, 0.0, 1.0),
    ("ZR_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("ZR_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("ZR_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0, 1.0),
    ("ZR_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("ZR_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0, 1.0),
    ("ZR_Pozink", (0.55, 0.57, 0.58, 1.0), 0.6, 0.45, 0.0, 1.0),
    ("ZR_Plast", (0.13, 0.135, 0.145, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("ZR_Siva", (0.40, 0.42, 0.45, 1.0), 0.5, 0.50, 0.0, 1.0),
    ("ZR_Interier", (0.10, 0.10, 0.11, 1.0), 0.0, 0.70, 0.0, 1.0),
    ("ZR_Sedadlo", (0.20, 0.19, 0.17, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("ZR_Lak_zlty", (0.96, 0.62, 0.02, 1.0), 0.2, 0.32, 0.0, 1.0),
    ("ZR_Lak_cierny", (0.030, 0.031, 0.035, 1.0), 0.1, 0.55, 0.0, 1.0),
    ("ZR_Betonove_zavazie", (0.36, 0.37, 0.38, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("ZR_Vystraha", (0.90, 0.30, 0.02, 1.0), 0.0, 0.50, 0.0, 1.0),
    ("ZR_Lano", (0.10, 0.10, 0.11, 1.0), 0.6, 0.55, 0.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, GLASS, LAMP_OR, LAMP_RED, LAMP_WHITE, RED, WHITE, GALV, PLAST, GRAY, INT, SEAT,
 PAINT_YEL, PAINT_BLK, CWT, WARN, ROPE) = range(22)


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


def loft_rr(bm, stations, mat, n=3):
    # hladke teleso z priecnych rezov (zaoblenych obdlznikov): stations = [(x, y0, y1, z0, z1, r), ...] od zadu dopredu; konce sa uzavru
    secs = [(st[0], rounded_rect(st[1], st[2], st[3], st[4], max(st[5], 0.004), n)) for st in stations]
    return loft_yz(bm, secs, mat)


def pillow(bm, x0, x1, y0, y1, z0, z1, r, mat, n=3, steps=3):
    # zaoblene teleso (kvader so zaoblenymi hranami polomeru r, hladke tienovanie): kazda hrana je kruhovy obluk
    r = min(r, (x1 - x0) * 0.5 - 0.001, (y1 - y0) * 0.5 - 0.001, (z1 - z0) * 0.5 - 0.001)
    ph = [math.pi * 0.5 * k / steps for k in range(steps + 1)]
    ends = [(r * (1.0 - math.cos(p)), r * (1.0 - math.sin(p))) for p in ph]       # (vzdialenost od steny, zmensenie)
    st = [(x0 + t, y0 + d, y1 - d, z0 + d, z1 - d, r - d) for t, d in ends]
    st += [(x1 - t, y0 + d, y1 - d, z0 + d, z1 - d, r - d) for t, d in ends[::-1]]
    return loft_rr(bm, st, mat, n)


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
# Pneumatiky: telo pneumatiky je OTOCENY PRIEREZ (zaoblene rameno, vypukla bocnica s rebrom, korunovy dezen, drazky) a dezenove bloky
# (bahno: sikme stredove bloky + ramenne bloky zalomene na bocnicu; cesta: pozdlzne rebra + male ramenne bloky). Pneumatika sedi na hrane disku, ventilok je na disku.
# sc = mierka dezenu a drobnych detailov (1.0 pre osobne auto, vacsia pre nakladne kolesa).
# ---------------------------------------------------------------------------

TIRE_SEGS = 24


def tire_revolve(bm, loop, segs, mat):
    # prierez (y, polomer) otoceny okolo osi Y; uhol t smeruje ako otocenie okolo Y (rovnako ako ramy dezenovych blokov)
    ts = [2.0 * math.pi * k / segs for k in range(segs)]
    rings = [[bm.verts.new((rho * math.sin(t), y, rho * math.cos(t))) for t in ts] for y, rho in loop]
    faces = []
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        for k in range(segs):
            m = (k + 1) % segs
            faces.append(bm.faces.new((rings[i][k], rings[i][m], rings[j][m], rings[j][k])))
    set_material(faces, mat)
    return faces


def tire_profile(r, w, rim, th, grooves=(), bead=None, sc=1.0):
    # polovica prierezu pre y > 0 od uchytu na disku po stred dezenu; grooves = [(y stred, sirka)] pozdlzne drazky hlbky th * 0.75
    hw = w * 0.5
    H = r - rim
    by = hw - 0.05 * sc if bead is None else bead
    rt = r - th
    e = 0.003 * sc
    half = [(by, rim * 0.965), (by + e, rim * 1.012),
            (by + 0.012 * sc, rim + 0.075 * H), (by + 0.018 * sc, rim + 0.095 * H),          # ochranne rebro pri disku
            (hw * 0.91, rim + 0.24 * H), (hw * 0.985, rim + 0.43 * H), (hw * 1.0 + e, rim + 0.465 * H), (hw * 1.0 + e, rim + 0.535 * H), (hw * 0.985, rim + 0.57 * H), (hw * 0.975, rim + 0.74 * H),
            (hw * 0.90, rt - 0.012 * sc), (hw * 0.76, rt - 0.001 * sc), (hw * 0.70, rt)]
    for gy, gw in sorted(grooves, reverse=True):
        d = th * 0.75
        half += [(gy + gw * 0.5 + 0.006 * sc, rt), (gy + gw * 0.5, rt - d), (gy - gw * 0.5, rt - d), (gy - gw * 0.5 - 0.006 * sc, rt)]
    half.append((0.0, rt + e))
    return half


def tire_lug(bm, t, rho, y, size, yaw, tilt, mat, bev):
    # dezenovy blok so zaoblenymi hranami (jeden segment zrazenia): guma, nie plech
    frame = Matrix.Rotation(t, 4, "Y") @ Matrix.Translation((0.0, 0.0, rho))
    matrix = frame @ place((0.0, y, 0.0), (tilt, 0.0, yaw)) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    verts = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)["verts"]
    faces = faces_of(verts)
    set_material(faces, mat)
    r = 0.12 * min(size)
    if r > 0.0:
        res = bmesh.ops.bevel(bm, geom=list({e for f in faces for e in f.edges}), offset=r, segments=1, profile=0.5, affect="EDGES", clamp_overlap=True)
        set_material(res["faces"], mat)


def add_tire(bm, r, w, rim, style="road", segs=TIRE_SEGS, sc=1.0):
    # pneumatika okolo osi Y (stred v pociatku, symetricka); style: "bahno" (hruby dezen) alebo "cesta" (rebra + ramenne bloky)
    hw = w * 0.5
    th = (0.026 if style == "bahno" else 0.014) * sc
    grooves = () if style == "bahno" else ((w * 0.20, 0.018 * sc), (-w * 0.20, 0.018 * sc))
    half = tire_profile(r, w, rim, th, [g for g in grooves if g[0] > 0.0], None, sc)
    loop = [(-y, rho) for y, rho in half[:-1]] + [(0.0, half[-1][1])] + half[:-1][::-1]
    tire_revolve(bm, loop, segs, TIRE)
    step = 2.0 * math.pi / segs
    rt = r - th
    if style == "bahno":
        for k in range(segs):
            t = step * k
            tire_lug(bm, t, rt + th * 0.5, w * 0.17, (0.052 * sc, 0.085 * sc, th), 24.0, 0.0, TIRE, 0.0)
            tire_lug(bm, t + step * 0.5, rt + th * 0.5, -w * 0.17, (0.052 * sc, 0.085 * sc, th), -24.0, 0.0, TIRE, 0.0)
            for s in (1.0, -1.0):
                tire_lug(bm, t + step * (0.25 if s > 0 else 0.75), r - 0.044 * sc, s * hw * 0.84, (0.050 * sc, 0.080 * sc, 0.046 * sc), s * 8.0, -s * 38.0, TIRE, 0.0)
    else:
        for k in range(segs):
            t = step * k
            for s in (1.0, -1.0):
                tire_lug(bm, t + (0.0 if s > 0 else step * 0.5), r - 0.021 * sc, s * hw * 0.85, (0.030 * sc, 0.036 * sc, 0.020 * sc), s * 10.0, -s * 34.0, TIRE, 0.0)


def tire_valve(bm, rim, y_out, sc=1.0):
    # ventilok na vonkajsej strane disku: gumova stopka s malou chromovou ciapockou, tesne nad plochou disku
    t = 0.75
    x, z = rim * 0.78 * math.sin(t), rim * 0.78 * math.cos(t)
    add_cylinder(bm, 0.0075 * sc, 0.020 * sc, along_y((x, y_out - 0.010 * sc, z)), DARK, segments=8)
    add_cylinder(bm, 0.0058 * sc, 0.010 * sc, along_y((x, y_out + 0.006 * sc, z)), CHROME, segments=8)


# ---------------------------------------------------------------------------
# Parametre zerava a podvozok (nosic): ram, kabina, nahrady s kolesami, vysuvne podpery
# Suradnice podvozku: pociatok = zem pod osou otocnej nadstavby, predok +X, lava +Y. Vyska: ram z0 az z1, venec otocnej nadstavby v ring_top.
# ---------------------------------------------------------------------------

CRANES = {
    "40t": dict(key="40t", name="Zeriav_40t", R=0.58, TW=0.40, rim=0.36, track=1.05, axles=[3.55, 2.25, -1.95], steer=2, front=5.45, f_rear=-3.60,
                z0=0.85, z1=1.20, cab=(3.30, 5.45), cab_roof=2.95, ring=1.05, ring_top=1.45, oxs=[1.0, -3.1], stroke=2.0,
                boom_L=[7.2, 6.6, 6.1, 5.6], boom_b=[0.84, 0.74, 0.64, 0.54], boom_h=[0.90, 0.80, 0.70, 0.60], piv=(-0.9, -0.35, 2.10),
                cw_front=-2.45, cw_h=1.30, hs_h=1.15, deck_f=1.5, cw_n=3, ucab=(-0.15, 1.55), ucab_h=1.85, hw=1.35, lift=0.12, hose=0.14, steer_max=35.0, boom_max=78.0, hook_len=0.95),
    "80t": dict(key="80t", name="Zeriav_80t", R=0.70, TW=0.48, rim=0.43, track=1.24, axles=[4.60, 3.25, -1.75, -3.10], steer=2, front=6.70, f_rear=-4.60,
                z0=1.00, z1=1.40, cab=(4.25, 6.70), cab_roof=3.30, ring=1.25, ring_top=1.65, oxs=[1.25, -4.25], stroke=2.4,
                boom_L=[8.3, 7.6, 7.0, 6.5, 6.0], boom_b=[1.00, 0.88, 0.76, 0.64, 0.52], boom_h=[1.05, 0.93, 0.81, 0.69, 0.57], piv=(-1.1, -0.40, 2.40),
                cw_front=-3.00, cw_h=1.55, hs_h=1.40, deck_f=1.8, cw_n=4, ucab=(-0.15, 1.85), ucab_h=2.0, hw=1.55, lift=0.14, hose=0.17, steer_max=33.0, boom_max=78.0, hook_len=0.95),
}


def zr_deck0(C):
    return C["cw_front"] - C["cw_n"] * 0.34 + 0.02


def zr_hh(C):
    # polsirka puzdra podpery (vonkajsi okraj podvozku)
    return C["track"] + 0.23


def zr_beam_len(C):
    return C["stroke"] + 0.55


def zr_pneu_scale(C):
    return C["R"] / 0.41


def zr_sy(s, a, b):
    # pas (a az b) na strane s: pre s > 0 (a, b), pre s < 0 (-b, -a)
    return (a, b) if s > 0 else (-b, -a)


def build_zr_ram(C):
    # podvozok (cierny): dva zaoblene podlzniky, rurove priecniky s koncovymi platnami, hadice a konzoly
    bm = bmesh.new()
    x_f, x_r = C["front"] - 0.25, C["f_rear"]
    z0, z1 = C["z0"], C["z1"]
    for s in SIDES_LR:
        ya, yb = zr_sy(s, 0.46, 0.64)
        pillow(bm, x_r, x_f, ya, yb, z0, z1, 0.05, FRAME)
        for dz in (0.10, 0.24):
            add_rod(bm, (x_r + 0.35, s * 0.40, z0 + dz), (x_f - 0.40, s * 0.40, z0 + dz), 0.018, PLAST, segments=6)
    n = int((x_f - x_r) / 0.9)
    for k in range(n + 1):
        x = x_r + 0.1 + (x_f - x_r - 0.2) * k / n
        add_cylinder(bm, 0.06, 1.00, along_y((x, 0.0, z0 + 0.13)), FRAME, segments=10, bev=0.004)
        for s in SIDES_LR:
            ya, yb = zr_sy(s, 0.44, 0.50)
            bx(bm, x - 0.09, x + 0.09, ya, yb, z0 + 0.02, z0 + 0.26, FRAME, 0.02)
            for dz in (0.06, 0.20):
                add_cylinder(bm, 0.018, 0.02, along_y((x, s * 0.65, z0 + dz)), STEEL, segments=6)
    bx(bm, x_f - 0.1, x_f + 0.1, -0.66, 0.66, z0, z1, FRAME, 0.04)
    return finish_mesh(bm, "SM_Zr_ram_" + C["key"])


def build_zr_zakladna(C):
    # zakladna vencoveho loziska: spodny prstenec na ramu, tmavy tesniaci pas, horny prstenec so skrutkami (stoji, otacaju sa diely nad nim)
    bm = bmesh.new()
    r, z0, z1 = C["ring"], C["z1"], C["ring_top"]
    pillow(bm, -r - 0.05, r + 0.05, -0.66, 0.66, z0, z0 + 0.07, 0.03, FRAME)
    add_cylinder(bm, r + 0.03, z1 - z0 - 0.10, along_z((0.0, 0.0, z0 + (z1 - z0 - 0.10) * 0.5 + 0.05)), FRAME, segments=32, bev=0.025)
    add_cylinder(bm, r + 0.04, 0.025, along_z((0.0, 0.0, z0 + (z1 - z0) * 0.55)), PLAST, segments=32)
    add_cylinder(bm, r - 0.05, 0.07, along_z((0.0, 0.0, z1 - 0.035)), STEEL, segments=32, bev=0.01)
    for k in range(28):
        a = 2.0 * math.pi * k / 28
        add_cylinder(bm, 0.027, 0.032, along_z(((r - 0.02) * math.cos(a), (r - 0.02) * math.sin(a), z1 + 0.014)), CHROME, segments=6, bev=0.004)
    return finish_mesh(bm, "SM_Zr_zakladna_" + C["key"])


def cab_stations(C, ls=False):
    x0, xf = C["cab"]
    zf, zr, hw = C["z1"], C["cab_roof"], 1.20
    zb = zf - 0.06
    pts = [(x0, hw - 0.10, zr - 0.30, 0.10), (x0 + 0.04, hw - 0.04, zr - 0.12, 0.18), (x0 + 0.14, hw - 0.01, zr - 0.03, 0.24), (x0 + 0.40, hw, zr, 0.27),
           (xf - 0.75, hw, zr, 0.27), (xf - 0.40, hw - 0.005, zr - 0.02, 0.27), (xf - 0.18, hw - 0.02, zr - 0.07, 0.26), (xf - 0.06, hw - 0.05, zr - 0.13, 0.22),
           (xf, hw - 0.12, zr - 0.23, 0.16)]
    return [(x, -h, h, zb, top, r) for x, h, top, r in pts]


def build_zr_kabina(C):
    # kabina nosica (zlta): hladke zaoblene telo z rezov, velke celne sklo s ramom, zadne bocne okna, otvory dveri, strecha so svetlami, stierace, clona, klimatizacia
    bm = bmesh.new()
    x0, xf = C["cab"]
    zf, zr, hw = C["z1"], C["cab_roof"], 1.20
    loft_rr(bm, cab_stations(C), PAINT_YEL, 4)
    zc = (zf + 0.85 + zr - 0.34) * 0.5
    h = zr - 0.34 - zf - 0.85
    add_box(bm, (0.03, 1.80, h), (xf + 0.002, 0.0, zc), GLASS)
    win_frame(bm, "X", 0.0, xf, zc, 1.80, h, 0.05, 0.05, 0.004, PAINT_BLK, 0.012)
    add_box(bm, (0.03, 0.03, h), (xf + 0.012, 0.0, zc), PAINT_BLK)                                    # stredny stlpik
    for s in SIDES_LR:
        add_box(bm, (1.40, 0.014, zr - zf - 0.35), (xf - 0.90, s * (hw + 0.004), zf + 0.22 + (zr - zf - 0.35) * 0.5), INT)          # otvor dveri
        win_frame(bm, "Y", x0 + 0.62, s * hw, zr - 0.62, 0.74, 0.62, 0.035, 0.03, s * 0.004, PAINT_BLK)
        add_box(bm, (0.74, 0.012, 0.62), (x0 + 0.62, s * (hw + 0.004), zr - 0.62), GLASS)
        add_rod(bm, (xf - 0.10, s * (hw + 0.03), zf + 0.35), (xf - 0.10, s * (hw + 0.03), zr - 0.45), 0.014, STEEL, segments=6)     # drziak
        for dz in (0.35, zr - zf - 0.45):
            add_rod(bm, (xf - 0.10, s * hw, zf + dz), (xf - 0.10, s * (hw + 0.03), zf + dz), 0.012, STEEL, segments=6)
        bx(bm, x0 + 0.20, xf - 0.80, s * (hw + 0.001), s * (hw + 0.012), zf - 0.04, zf + 0.20, PAINT_BLK, 0.008)       # cierny prah
        for k in range(2):
            bx(bm, x0 + 0.35 + 0.35 * k, x0 + 0.62 + 0.35 * k, s * (hw + 0.001), s * (hw + 0.010), zf + 0.55, zf + 0.60, DARK, 0.004)
    pillow(bm, xf - 0.10, xf + 0.16, -1.04, 1.04, zr - 0.30, zr - 0.20, 0.04, PAINT_BLK)               # clona nad celnym sklom
    for k in range(5):
        add_box(bm, (0.05, 0.13, 0.045), (xf - 0.30, -0.72 + 0.36 * k, zr + 0.02), LAMP_OR, bev=0.008)    # obrysove svetla na streche
    pillow(bm, x0 + 0.12, x0 + 0.92, -0.62, 0.62, zr - 0.01, zr + 0.14, 0.06, PAINT_BLK)               # klimatizacia
    for k in range(5):
        bx(bm, x0 + 0.20 + 0.13 * k, x0 + 0.24 + 0.13 * k, -0.50, 0.50, zr + 0.14, zr + 0.155, STEEL, 0.003)
    for s in (-0.45, 0.35):
        add_rod(bm, (xf + 0.02, s, zf + 0.88), (xf + 0.02, s + 0.55, zf + 1.12), 0.011, DARK, segments=5)        # stierace
        add_rod(bm, (xf + 0.02, s, zf + 0.88), (xf + 0.02, s + 0.05, zf + 0.88), 0.016, DARK, segments=5)
    add_box(bm, (0.03, 2.0, 0.40), (x0 - 0.012, 0.0, zr - 0.62), PAINT_BLK, bev=0.01)
    return finish_mesh(bm, "SM_Zr_kabina_" + C["key"])


def build_zr_dvere(C):
    # dvere nosica (lave; prave je zrkadlo), pivot na zavese pri prednej hrane (y = 1.20, z = podlaha kabiny); dvere siahaju do -X
    bm = bmesh.new()
    top = C["cab_roof"] - C["z1"] - 0.16
    pillow(bm, -1.42, -0.02, 0.0, 0.07, 0.22, top, 0.035, PAINT_YEL, 3, 2)
    h = top - 0.22 - 0.50
    zc = 0.22 + 0.50 + h * 0.5 + 0.02
    add_box(bm, (1.06, 0.02, h), (-0.70, 0.072, zc), GLASS)
    win_frame(bm, "Y", -0.70, 0.07, zc, 1.06, h, 0.045, 0.03, 0.004, PAINT_BLK)
    add_rod(bm, (-1.28, 0.08, 0.98), (-1.12, 0.08, 0.98), 0.014, CHROME, segments=6)
    bx(bm, -1.30, -1.10, 0.07, 0.088, 0.94, 1.02, STEEL, 0.008)
    bx(bm, -1.30, -0.15, 0.07, 0.080, 0.30, 0.34, PAINT_BLK, 0.006)
    for k in range(3):
        bx(bm, -0.50 - 0.18 * k, -0.40 - 0.18 * k, 0.07, 0.078, 0.55, 0.57, PAINT_BLK, 0.002)
    return bm


def build_zr_maska(C):
    # predna maska kabiny (cierna): panel s chromovymi lamelami a znackou, spodny dych a drziak znacky
    bm = bmesh.new()
    xf, zf = C["cab"][1], C["z1"]
    pillow(bm, xf - 0.10, xf + 0.06, -1.06, 1.06, zf - 0.42, zf + 0.34, 0.06, PAINT_BLK)
    for k in range(9):
        add_rod(bm, (xf + 0.065, -0.60, zf - 0.30 + 0.065 * k), (xf + 0.065, 0.60, zf - 0.30 + 0.065 * k), 0.012, CHROME, segments=6)
    pillow(bm, xf + 0.04, xf + 0.075, -0.20, 0.20, zf + 0.20, zf + 0.30, 0.012, CHROME)
    pillow(bm, xf + 0.03, xf + 0.07, -0.55, 0.55, zf - 0.40, zf - 0.30, 0.012, DARK)
    for s in SIDES_LR:
        bx(bm, xf + 0.04, xf + 0.068, s * 0.64, s * 0.68, zf - 0.30, zf + 0.24, CHROME, 0.006)
    return finish_mesh(bm, "SM_Zr_maska_" + C["key"])


def build_zr_svetlomet():
    # predne svetlo (lave; prave je zrkadlo): zaoblene puzdro, hlavne svetlo s chromovym prstencom, smerovka, denne svetlo
    bm = bmesh.new()
    pillow(bm, 0.0, 0.09, -0.26, 0.26, -0.13, 0.13, 0.035, DARK)
    add_cylinder(bm, 0.095, 0.03, along_x((0.095, -0.05, 0.0)), CHROME, segments=18)
    add_cylinder(bm, 0.082, 0.035, along_x((0.10, -0.05, 0.0)), LAMP_WHITE, segments=18, bev=0.006)
    pillow(bm, 0.07, 0.105, 0.10, 0.23, -0.10, -0.01, 0.012, LAMP_OR)
    pillow(bm, 0.07, 0.105, 0.10, 0.23, 0.02, 0.10, 0.012, LAMP_WHITE)
    return bm


def build_zr_naraznik_predny(C):
    # predny naraznik: zaoblene ocelove teleso s nastupnym rostom, vlecne oka, hmlovky, smerovky a drziak znacky
    bm = bmesh.new()
    xf = C["front"]
    pillow(bm, xf - 0.24, xf + 0.08, -1.26, 1.26, 0.52, 0.88, 0.09, PAINT_BLK)
    bx(bm, xf - 0.32, xf + 0.10, -1.05, 1.05, 0.40, 0.52, STEEL, 0.015)
    for k in range(14):
        bx(bm, xf - 0.30, xf + 0.08, -1.0 + 0.15 * k, -0.95 + 0.15 * k, 0.52, 0.535, DARK, 0.003)
    for s in SIDES_LR:
        add_cylinder(bm, 0.04, 0.10, along_x((xf + 0.12, s * 0.60, 0.60)), STEEL, segments=10, bev=0.006)
        add_cylinder(bm, 0.025, 0.12, along_x((xf + 0.12, s * 0.60, 0.60)), DARK, segments=8)
        add_cylinder(bm, 0.065, 0.03, along_x((xf + 0.095, s * 0.95, 0.70)), CHROME, segments=14)
        add_cylinder(bm, 0.055, 0.035, along_x((xf + 0.10, s * 0.95, 0.70)), LAMP_WHITE, segments=14)
        pillow(bm, xf + 0.06, xf + 0.10, *zr_sy(s, 0.70, 1.00), 0.78, 0.84, 0.015, LAMP_OR)
    pillow(bm, xf + 0.06, xf + 0.09, -0.26, 0.26, 0.60, 0.74, 0.012, WHITE)
    return finish_mesh(bm, "SM_Zr_naraznik_predny_" + C["key"])


def build_zr_zrkadlo():
    # vonkajsie zrkadlo (lave; prave je zrkadlo): dve ramena, hlavne a siroke zrkadlo v zaoblenych puzdrach
    bm = bmesh.new()
    add_rod(bm, (0.0, 0.0, 0.10), (0.0, 0.36, 0.16), 0.016, STEEL, segments=6)
    add_rod(bm, (0.0, 0.0, -0.20), (0.0, 0.36, -0.10), 0.016, STEEL, segments=6)
    pillow(bm, -0.055, 0.055, 0.34, 0.47, -0.04, 0.34, 0.035, PAINT_BLK)
    pillow(bm, -0.058, -0.045, 0.355, 0.455, -0.02, 0.32, 0.005, CHROME)
    pillow(bm, -0.05, 0.05, 0.34, 0.45, -0.30, -0.08, 0.03, PAINT_BLK)
    pillow(bm, -0.053, -0.042, 0.355, 0.435, -0.28, -0.10, 0.005, CHROME)
    return bm


def build_zr_schodik():
    # nastupne schodiky pri dveriach (lave; prave je zrkadlo): dva stupne s ryhovanim v rame, konzola; pivot v rovine dveri pri kabine
    bm = bmesh.new()
    for z in (-0.40, -0.78):
        pillow(bm, -0.32, 0.22, 0.0, 0.32, z - 0.03, z + 0.02, 0.012, PAINT_BLK)
        for k in range(8):
            bx(bm, -0.30 + 0.065 * k, -0.26 + 0.065 * k, 0.02, 0.30, z + 0.02, z + 0.030, STEEL, 0.002)
        bx(bm, -0.32, 0.22, 0.30, 0.325, z - 0.04, z + 0.06, PAINT_BLK, 0.006)
    for x in (-0.28, 0.18):
        bx(bm, x - 0.02, x + 0.02, 0.0, 0.30, -0.82, -0.20, PAINT_BLK, 0.01)
    return bm


def build_zr_nadrz(C):
    # nadrz paliva (lava strana): hlinikovy valec s pasmi, plnicim hrdlom a mierkou
    bm = bmesh.new()
    add_cylinder(bm, 0.30, 1.30, along_x((0.0, 0.0, 0.0)), GALV, segments=20, bev=0.04)
    for dx in (-0.45, 0.45):
        add_cylinder(bm, 0.312, 0.05, along_x((dx, 0.0, 0.0)), STEEL, segments=20)
        bx(bm, dx - 0.03, dx + 0.03, -0.05, 0.05, -0.42, -0.27, STEEL, 0.006)
    add_cylinder(bm, 0.06, 0.08, along_z((0.35, 0.0, 0.31)), CHROME, segments=12, bev=0.008)
    add_cylinder(bm, 0.05, 0.03, along_z((0.35, 0.0, 0.36)), PAINT_BLK, segments=12)
    bx(bm, -0.10, 0.10, 0.28, 0.33, -0.12, 0.12, PAINT_BLK, 0.01)
    return finish_mesh(bm, "SM_Zr_nadrz_" + C["key"])


def build_zr_skrinka(C):
    # naradova skrinka (prava strana): zaoblene teleso s vekom, dvierkami a zamkami
    bm = bmesh.new()
    pillow(bm, -0.65, 0.65, -0.24, 0.24, -0.26, 0.26, 0.04, PAINT_BLK)
    for k in range(2):
        pillow(bm, -0.60 + 0.62 * k, -0.04 + 0.62 * k, -0.252, -0.236, -0.22, 0.20, 0.006, GALV)
        bx(bm, -0.18 + 0.62 * k, -0.12 + 0.62 * k, -0.262, -0.250, -0.04, 0.04, STEEL, 0.004)
    bx(bm, -0.62, 0.62, -0.25, -0.235, 0.20, 0.23, PAINT_BLK, 0.006)
    return finish_mesh(bm, "SM_Zr_skrinka_" + C["key"])


def build_zr_vyfuk():
    # vyfuk (zvisla trubka za kabinou): trubka s tepelnym stitom, dazdovou klapkou a konzolami
    bm = bmesh.new()
    add_cylinder(bm, 0.065, 1.20, along_z((0.0, 0.0, 0.60)), STEEL, segments=12, bev=0.004)
    add_cylinder(bm, 0.095, 0.55, along_z((0.0, 0.0, 0.40)), GALV, segments=12, bev=0.006)
    for z in (0.18, 0.62):
        add_cylinder(bm, 0.10, 0.025, along_z((0.0, 0.0, z)), STEEL, segments=12)
    add_cylinder(bm, 0.09, 0.03, along_z((0.0, 0.0, 1.20)), DARK, segments=12)
    add_box(bm, (0.14, 0.14, 0.012), (0.04, 0.0, 1.235), STEEL, rotation=(0.0, -20.0, 0.0))
    add_rod(bm, (0.0, 0.0, 0.0), (0.20, 0.0, -0.13), 0.06, STEEL, segments=10)
    for z in (0.35, 0.95):
        bx(bm, -0.09, 0.0, -0.09, 0.09, z - 0.025, z + 0.025, FRAME, 0.006)
    return finish_mesh(bm, "SM_Zr_vyfuk")


def build_zr_naprava(C):
    # naprava (pivot v osi kolies): trubka, diferencial, redukcne telesa, brzdove valce, vzduchove vaky, tahla
    bm = bmesh.new()
    t, R = C["track"], C["R"]
    add_cylinder(bm, 0.11, 2.0 * t - 0.7, along_y((0.0, 0.0, 0.0)), FRAME, segments=14, bev=0.01)
    add_cylinder(bm, 0.25, 0.44, along_y((0.0, 0.0, 0.0)), FRAME, segments=18, bev=0.05)
    pillow(bm, 0.05, 0.40, -0.17, 0.17, -0.12, 0.12, 0.05, DARK)
    for s in SIDES_LR:
        add_cylinder(bm, 0.18, 0.14, along_y((0.0, s * (t - 0.42), 0.0)), FRAME, segments=16, bev=0.02)
        add_cylinder(bm, 0.075, 0.13, along_y((-0.15, s * (t - 0.62), 0.18)), STEEL, segments=10, bev=0.008)
        add_rod(bm, (-0.15, s * (t - 0.55), 0.18), (-0.15, s * (t - 0.42), 0.16), 0.022, STEEL, segments=8)
        for dx in (-0.36, 0.36):
            add_cylinder(bm, 0.09, 0.26, along_z((dx, s * (t - 0.62), R * 0.55 + 0.10)), PLAST, segments=14, bev=0.015)        # vzduchovy vak
            add_cylinder(bm, 0.11, 0.025, along_z((dx, s * (t - 0.62), R * 0.55 + 0.235)), FRAME, segments=14)
            add_cylinder(bm, 0.11, 0.025, along_z((dx, s * (t - 0.62), R * 0.55 - 0.03)), FRAME, segments=14)
    return finish_mesh(bm, "SM_Zr_naprava_" + C["key"])


def build_zr_zakladka(C):
    # zakladka kolesa (lava; prava je zrkadlo): puzdro riadenia s osou kolesa, kralikovy cap a ryhaca tyc, pivot v stredni zatacania
    bm = bmesh.new()
    add_cylinder(bm, 0.155, 0.22, along_y((0.0, 0.11, 0.0)), FRAME, segments=16, bev=0.012)
    add_cylinder(bm, 0.075, 0.34, along_z((0.0, 0.0, 0.0)), STEEL, segments=10, bev=0.006)
    add_cylinder(bm, 0.09, 0.05, along_z((0.0, 0.0, 0.18)), PAINT_BLK, segments=10)
    add_box_between(bm, (0.06, 0.0, -0.12), (0.34, -0.10, -0.12), 0.05, 0.05, STEEL, bev=0.006)
    return bm


def build_zr_pneu(C):
    # pneumatika zerava (pivot v osi, symetricka): nakladna terenna s hrubym dezenom
    bm = bmesh.new()
    add_tire(bm, C["R"], C["TW"], C["rim"], "bahno", 28, zr_pneu_scale(C))
    return finish_mesh(bm, "SM_Zr_pneu_" + C["key"])


def build_zr_disk(C):
    # disk (lavy, vonkajsia strana +Y; pravy je zrkadlo): ocelovy s prelisom, prirubou, vencom 10 matic, otvormi a stredovym krytom
    w, rim = C["TW"], C["rim"]
    k = zr_pneu_scale(C)
    bm = bmesh.new()
    add_ring(bm, rim, rim * 0.88, 0.05 * k, w * 0.5 - 0.03 * k, RIM, 32, bev=0.01)
    add_cylinder(bm, rim * 0.90, 0.025, along_y((0.0, w * 0.5 - 0.05 * k, 0.0)), GRAY, segments=32)
    add_ring(bm, rim * 0.66, rim * 0.56, 0.03 * k, w * 0.5 - 0.035 * k, STEEL, 24, bev=0.006)
    for j in range(10):
        a = 2.0 * math.pi * j / 10
        add_cylinder(bm, 0.045 * k, 0.04, along_y((rim * 0.40 * math.cos(a), w * 0.5 - 0.02 * k, rim * 0.40 * math.sin(a))), CHROME, segments=6, bev=0.004)
        add_cylinder(bm, 0.07 * k, 0.03, along_y((rim * 0.76 * math.cos(a + 0.3), w * 0.5 - 0.05 * k, rim * 0.76 * math.sin(a + 0.3))), DARK, segments=10)
    add_cylinder(bm, rim * 0.22, 0.09, along_y((0.0, w * 0.5 - 0.015 * k, 0.0)), STEEL, segments=16, bev=0.012)
    add_cylinder(bm, rim * 0.14, 0.12, along_y((0.0, w * 0.5 + 0.03 * k, 0.0)), CHROME, segments=16, bev=0.012)
    tire_valve(bm, rim, w * 0.5, k)
    return bm


def build_zr_blatnik(C):
    # blatnik (lavy; pravy je zrkadlo), pivot v osi kolesa: hrubsi oblukovy kryt nad kolesom (160 az 20 st.) so zaoblenou hranou, bocnou clonou a gumenou zastierkou za kolesom
    R, w = C["R"], C["TW"] + 0.12
    bm = bmesh.new()
    ro, ri = R + 0.11, R + 0.06
    angles = [160.0 - 140.0 * k / 16.0 for k in range(17)]
    outer = [(ro * math.cos(math.radians(a)), ro * math.sin(math.radians(a))) for a in angles]
    inner = [(ri * math.cos(math.radians(a)), ri * math.sin(math.radians(a))) for a in angles]
    add_extruded(bm, outer + inner[::-1], -w * 0.5, w * 0.5, "XZ", PAINT_BLK, bev=0.022)
    skirt = [((ro - 0.14) * math.cos(math.radians(a)), (ro - 0.14) * math.sin(math.radians(a))) for a in angles]
    add_extruded(bm, outer + skirt[::-1], w * 0.5 - 0.035, w * 0.5, "XZ", PAINT_BLK, bev=0.012)
    xr = ro * math.cos(math.radians(160.0))
    zr_ = ro * math.sin(math.radians(160.0))
    add_box(bm, (0.035, w - 0.06, 0.44), (xr - 0.02, 0.0, zr_ - 0.26), PLAST, bev=0.01)                  # gumova zastierka
    for k in range(3):
        add_box(bm, (0.05, w - 0.16, 0.03), (xr - 0.04, 0.0, zr_ - 0.12 - 0.12 * k), PLAST, bev=0.006)
    bx(bm, xr - 0.06, xr + 0.05, -w * 0.5 + 0.05, w * 0.5 - 0.05, zr_ - 0.03, zr_ + 0.03, STEEL, 0.006)
    return bm


def build_zr_podpera_nosnik(C):
    # puzdro vysuvnej podpery (priecny nosnik pod ramom, cierny; pivot v strede ramu v ose podpery): zaoblene teleso, koncove platne so skrutkami
    bm = bmesh.new()
    zc = C["z0"] - 0.10
    hh = zr_hh(C)
    pillow(bm, -0.24, 0.24, -hh, hh, zc - 0.18, zc + 0.18, 0.05, FRAME)
    for s in SIDES_LR:
        bx(bm, -0.26, 0.26, *zr_sy(s, hh - 0.04, hh + 0.02), zc - 0.20, zc + 0.20, STEEL, 0.012)
        for dx in (-0.15, 0.15):
            for dz in (-0.12, 0.12):
                add_cylinder(bm, 0.022, 0.02, along_y((dx, s * (hh + 0.03), zc + dz)), CHROME, segments=6, bev=0.004)
    bx(bm, -0.12, 0.12, -0.30, 0.30, zc + 0.18, zc + 0.24, FRAME, 0.01)
    return finish_mesh(bm, "SM_Zr_podpera_nosnik_" + C["key"])


def build_zr_podpera_vysuv(C):
    # vysuvny nosnik podpery (lavy; pravy je zrkadlo), pivot na vnutornom konci, siaha do +Y; koncovy blok pre valec, vystrazne pasy, tmavy pas
    bm = bmesh.new()
    L = zr_beam_len(C)
    pillow(bm, -0.20, 0.20, 0.0, L, -0.16, 0.16, 0.05, PAINT_YEL)
    pillow(bm, -0.25, 0.25, L - 0.52, L, -0.21, 0.21, 0.06, PAINT_YEL)
    bx(bm, -0.215, 0.215, 0.0, 0.12, -0.17, 0.17, STEEL, 0.012)
    for k in range(4):
        add_box(bm, (0.12, 0.22, 0.012), (0.0, 0.40 + 0.40 * k, 0.163), WARN, bev=0.002, rotation=(0.0, 0.0, 40.0))
    bx(bm, -0.202, 0.202, 0.3, L - 0.6, -0.02, 0.03, PAINT_BLK, 0.004)
    add_cylinder(bm, 0.04, 0.14, along_z((0.0, L - 0.25, 0.0)), STEEL, segments=8)
    return bm


def build_zr_podpera_valec(C):
    # puzdro valca podpery (zvisla trubka na konci nosnika; pivot v osi valca na spodku trubky): zlte teleso, hornna priruba, hadicove pripojky, spodne tesnenie
    bm = bmesh.new()
    add_cylinder(bm, 0.145, 0.70, along_z((0.0, 0.0, 0.35)), PAINT_YEL, segments=16, bev=0.012)
    add_cylinder(bm, 0.165, 0.05, along_z((0.0, 0.0, 0.70)), STEEL, segments=16, bev=0.006)
    add_cylinder(bm, 0.165, 0.05, along_z((0.0, 0.0, 0.03)), DARK, segments=16)
    for dz in (0.20, 0.52):
        add_cylinder(bm, 0.03, 0.10, along_x((0.16, 0.0, dz)), STEEL, segments=8)
    add_rod(bm, (0.20, 0.0, 0.20), (0.26, 0.0, 0.42), 0.014, PLAST, segments=6)
    add_rod(bm, (0.20, 0.0, 0.52), (0.26, 0.0, 0.42), 0.014, PLAST, segments=6)
    return finish_mesh(bm, "SM_Zr_podpera_valec_" + C["key"])


def build_zr_podpera_tyc(C):
    # piest podpery s podlozkou (pivot na spodku podlozky, tyc stupa nahor): chromovy piest, klbova hlava, zaoblena podlozka s rebrami
    bm = bmesh.new()
    pillow(bm, -0.34, 0.34, -0.34, 0.34, 0.0, 0.055, 0.02, PAINT_BLK)
    for k in range(5):
        bx(bm, -0.30 + 0.15 * k, -0.27 + 0.15 * k, -0.30, 0.30, 0.0, 0.065, PAINT_BLK, 0.004)
    lr = C["z0"] + C["lift"] - 0.28
    add_cylinder(bm, 0.09, lr, along_z((0.0, 0.0, 0.10 + lr * 0.5)), CHROME, segments=16, bev=0.004)
    add_cylinder(bm, 0.115, 0.08, along_z((0.0, 0.0, 0.095)), STEEL, segments=14, bev=0.01)
    return finish_mesh(bm, "SM_Zr_podpera_tyc_" + C["key"])


def build_zr_opierka(C):
    # opierka ramena na streche kabiny (dve konzoly s gumovym sedlom)
    bm = bmesh.new()
    x0, xf = C["cab"]
    zr = C["cab_roof"]
    top = C["ring_top"] + C["piv"][2] - C["boom_h"][0] * 0.5          # spodok ramena v polohe 0 st.
    for x in (xf - 0.60, x0 + 0.50):
        pillow(bm, x - 0.20, x + 0.20, C["piv"][1] - 0.52, C["piv"][1] + 0.52, zr, top - 0.03, 0.04, PAINT_BLK)
        pillow(bm, x - 0.17, x + 0.17, C["piv"][1] - 0.44, C["piv"][1] + 0.44, top - 0.035, top, 0.012, PLAST)
    return finish_mesh(bm, "SM_Zr_opierka_" + C["key"])


def build_zr_naraznik_zadny(C):
    # zadny naraznik s ochranou proti podbehnutiu, nastupnym plechom a odrazkami
    bm = bmesh.new()
    xr = C["f_rear"]
    pillow(bm, xr - 0.30, xr + 0.02, -1.16, 1.16, C["z0"] - 0.10, C["z0"] + 0.28, 0.07, PAINT_BLK)
    bx(bm, xr - 0.34, xr - 0.28, -0.60, 0.60, C["z0"] + 0.22, C["z0"] + 0.30, STEEL, 0.01)
    for s in SIDES_LR:
        bx(bm, xr - 0.315, xr - 0.285, *zr_sy(s, 0.85, 1.10), C["z0"] + 0.00, C["z0"] + 0.12, RED, 0.004)
    bx(bm, xr - 0.315, xr - 0.28, -0.26, 0.26, C["z0"] + 0.02, C["z0"] + 0.16, WHITE, 0.004)                   # drziak znacky
    return finish_mesh(bm, "SM_Zr_naraznik_zadny_" + C["key"])


def build_zr_svetlo_zadne():
    # zadne svetlo (lave; prave je zrkadlo): vodorovne zaoblene puzdro so styrmi okruhlymi sklami
    bm = bmesh.new()
    pillow(bm, -0.03, 0.03, -0.24, 0.24, -0.07, 0.07, 0.025, DARK)
    for dy, mat in ((0.17, LAMP_RED), (0.057, LAMP_OR), (-0.057, LAMP_WHITE), (-0.17, LAMP_RED)):
        add_cylinder(bm, 0.045, 0.014, along_x((-0.03, dy, 0.0)), mat, segments=16, bev=0.004)
    return bm


def cr_carrier_parts(put, put_lr, C):
    put(build_zr_ram(C))
    put(build_zr_zakladna(C))
    put(build_zr_kabina(C))
    put_lr(build_zr_dvere(C), "SM_Zr_dvere_" + C["key"])
    put(build_zr_maska(C))
    put(build_zr_naraznik_predny(C))
    put(build_zr_nadrz(C))
    put(build_zr_skrinka(C))
    put(build_zr_naprava(C))
    put(build_zr_pneu(C))
    put_lr(build_zr_disk(C), "SM_Zr_disk_" + C["key"])
    put_lr(build_zr_blatnik(C), "SM_Zr_blatnik_" + C["key"])
    put(build_zr_podpera_nosnik(C))
    put_lr(build_zr_podpera_vysuv(C), "SM_Zr_podpera_vysuv_" + C["key"])
    put(build_zr_podpera_valec(C))
    put(build_zr_podpera_tyc(C))
    put(build_zr_opierka(C))
    put(build_zr_naraznik_zadny(C))
    put_lr(build_zr_zakladka(C), "SM_Zr_zakladka_" + C["key"])


def zr_common_parts(put, put_lr):
    put_lr(build_zr_svetlomet(), "SM_Zr_svetlomet")
    put_lr(build_zr_zrkadlo(), "SM_Zr_zrkadlo")
    put_lr(build_zr_schodik(), "SM_Zr_schodik")
    put(build_zr_vyfuk())
    put_lr(build_zr_svetlo_zadne(), "SM_Zr_svetlo_zadne")


def zr_parts(put, put_lr):
    zr_common_parts(put, put_lr)
    for C in CRANES.values():
        cr_carrier_parts(put, put_lr, C)
        cr_upper_parts(put, put_lr, C)


PART_MAKERS.append(zr_parts)


# ---------------------------------------------------------------------------
# Otocna nadstavba (plosina, kryt motora, protizavazie, kabina zerava, konzoly ramena), teleskopicke rameno, hlava s kladkou, hakovy blok, lano
# Suradnice nadstavby: pociatok = os otocenia na vrchu vencoveho loziska, predok +X, lava +Y.
# Suradnice ramena: pociatok = otocny cap ramena, os ramena = +X (rameno stupa rotaciou okolo Y o -uhol), stupne sa vysuvaju po +X.
# ---------------------------------------------------------------------------

def zr_cab_y(C):
    b1 = C["boom_b"][0]
    return C["piv"][1] + b1 * 0.5 + 0.28, C["hw"] + 0.05


def zr_stage_rear(C, k):
    # poloha zadneho konca stupna k (0 = zakladny) v suradniciach otocneho capu pri zasunutom ramene; kazdy dalsi stupen vystupuje o 0.05 pred predchadzajuci
    L = C["boom_L"]
    if k == 0:
        return -0.45
    return zr_stage_rear(C, k - 1) + L[k - 1] - L[k] + 0.05


def zr_stage_stroke(C, k):
    return C["boom_L"][k] - 1.25


def build_zr_plosina(C):
    # plosina nadstavby: zaoblena doska, spodna sukna k vencu, protisklzove listy, zabradlie z rur (stlpiky, horna a stredna trubka, ohyby) s lemom
    bm = bmesh.new()
    d0, d1, hw = zr_deck0(C), C["deck_f"], C["hw"]
    pillow(bm, d0, d1, -hw, hw, 0.0, 0.14, 0.05, PAINT_BLK)
    add_cylinder(bm, C["ring"] - 0.05, 0.10, along_z((0.0, 0.0, -0.03)), STEEL, segments=32)
    for k in range(int((d1 - 0.8 - C["cw_front"]) / 0.16)):
        x = C["cw_front"] + 0.9 + 0.16 * k
        if x > d1 - 0.15:
            break
        for s in SIDES_LR:
            bx(bm, x, x + 0.08, *zr_sy(s, hw - 0.22, hw - 0.04), 0.14, 0.152, STEEL, 0.003)
    zt = 0.14
    xs = [C["cw_front"] + 0.2, C["cw_front"] * 0.5 - 0.2, -0.45]
    for s in SIDES_LR:
        y = s * (hw - 0.06)
        for x in xs:
            add_cylinder(bm, 0.022, 0.95, along_z((x, y, zt + 0.475)), STEEL, segments=8, bev=0.003)
            add_cylinder(bm, 0.04, 0.02, along_z((x, y, zt + 0.01)), STEEL, segments=8)
        for dz in (0.95, 0.50):
            add_rod(bm, (xs[0], y, zt + dz), (xs[-1], y, zt + dz), 0.021 if dz > 0.9 else 0.017, STEEL, segments=8)
        bx(bm, xs[0] - 0.1, xs[-1] + 0.1, *zr_sy(s, hw - 0.075, hw - 0.04), zt, zt + 0.10, PAINT_BLK, 0.008)
        add_rod(bm, (xs[-1], y, zt + 0.95), (xs[-1], s * (hw - 0.60), zt + 0.95), 0.019, STEEL, segments=8)
        add_rod(bm, (xs[0], y, zt + 0.95), (xs[0], s * (hw - 0.60), zt + 0.95), 0.019, STEEL, segments=8)
    return finish_mesh(bm, "SM_Zr_plosina_" + C["key"])


def build_zr_kryt(C):
    # kryt motora a hydrauliky (zlty): hladke zaoblene telo so sklonenou strechou, bocne mriezky v ramikoch, servisne dvierka s klukami, chladic, nasavanie, vyfuk
    bm = bmesh.new()
    x0, x1, hw, h = C["cw_front"], -0.30, C["hw"] - 0.03, C["hs_h"]
    z0 = 0.14
    ztop = z0 + h
    st = [(x0, hw - 0.10, ztop - 0.40, 0.12), (x0 + 0.05, hw - 0.04, ztop - 0.22, 0.18), (x0 + 0.30, hw - 0.01, ztop - 0.05, 0.22), (x0 + 0.70, hw, ztop, 0.24),
          (x1 - 0.30, hw, ztop, 0.24), (x1 - 0.08, hw - 0.02, ztop - 0.05, 0.20), (x1, hw - 0.07, ztop - 0.16, 0.12)]
    loft_rr(bm, [(x, -w, w, z0, top, r) for x, w, top, r in st], PAINT_YEL, 4)
    for s in SIDES_LR:
        npan = 2 if (x1 - x0) < 2.5 else 3
        pitch = (x1 - x0 - 0.80) / npan
        for k in range(npan):
            xm = x0 + 0.40 + pitch * (k + 0.5)
            pw = pitch * 0.5 - 0.05
            pillow(bm, xm - pw, xm + pw, *zr_sy(s, hw - 0.002, hw + 0.035), z0 + h * 0.27, z0 + h * 0.80, 0.02, PAINT_BLK)
            for j in range(6):
                zz = z0 + h * 0.31 + j * 0.075 * h
                bx(bm, xm - pw + 0.03, xm + pw - 0.03, *zr_sy(s, hw + 0.03, hw + 0.05), zz, zz + 0.022, STEEL, 0.004)
            bx(bm, xm - pitch * 0.5, xm - pitch * 0.5 + 0.012, *zr_sy(s, hw - 0.003, hw + 0.004), z0 + 0.10, ztop - 0.14, DARK, 0.002)        # sparovka dvierok
        add_cylinder(bm, 0.025, 0.05, along_y((x0 + 0.55, s * (hw + 0.025), z0 + h * 0.18)), STEEL, segments=8)
        add_cylinder(bm, 0.025, 0.05, along_y((x1 - 0.55, s * (hw + 0.025), z0 + h * 0.18)), STEEL, segments=8)
    pillow(bm, x0 + 0.55, x0 + 1.15, -hw + 0.55, -hw + 1.15, ztop - 0.02, ztop + 0.16, 0.05, PAINT_BLK)       # nasavanie vzduchu
    add_cylinder(bm, 0.11, 0.30, along_z((x0 + 0.85, -hw + 0.85, ztop + 0.28)), GALV, segments=14, bev=0.01)
    add_cylinder(bm, 0.07, 0.75, along_z((x0 + 0.55, hw - 0.28, ztop + 0.30)), STEEL, segments=12, bev=0.005)
    add_cylinder(bm, 0.10, 0.45, along_z((x0 + 0.55, hw - 0.28, ztop + 0.22)), GALV, segments=12, bev=0.008)
    add_cylinder(bm, 0.095, 0.04, along_z((x0 + 0.55, hw - 0.28, ztop + 0.69)), DARK, segments=12)
    pillow(bm, x1 - 0.85, x1 - 0.15, -hw + 0.25, hw - 0.25, ztop - 0.01, ztop + 0.10, 0.04, PAINT_BLK)       # chladic nad kabinou
    for k in range(6):
        bx(bm, x1 - 0.80 + 0.1 * k, x1 - 0.76 + 0.1 * k, -hw + 0.35, hw - 0.35, ztop + 0.10, ztop + 0.12, STEEL, 0.003)
    return finish_mesh(bm, "SM_Zr_kryt_" + C["key"])


def build_zr_zavazie(C, k):
    # doska protizavazia k (k = 0 je predna): zaoblena betonova doska, kovove rohy, zdvihacie oka, vystrazne pasy na zadnej hrane
    bm = bmesh.new()
    xa = C["cw_front"] - 0.34 * k
    hw = C["hw"] - 0.05
    zt = 0.14 + C["cw_h"]
    pillow(bm, xa - 0.33, xa - 0.01, -hw, hw, 0.14, zt, 0.05, CWT)
    for s in SIDES_LR:
        for z in (0.14, zt - 0.10):
            bx(bm, xa - 0.325, xa - 0.015, *zr_sy(s, hw - 0.01, hw + 0.012), z, z + 0.10, PAINT_BLK, 0.008)
    for yy in (-0.7, 0.7):
        add_cylinder(bm, 0.075, 0.035, along_y((xa - 0.17, yy, zt + 0.10)), STEEL, segments=14, bev=0.006)
        add_cylinder(bm, 0.045, 0.045, along_y((xa - 0.17, yy, zt + 0.10)), DARK, segments=12)
        bx(bm, xa - 0.20, xa - 0.14, yy - 0.02, yy + 0.02, zt, zt + 0.07, STEEL, 0.006)
    if k == C["cw_n"] - 1:
        for j in range(7):
            add_box(bm, (0.012, 0.16, 0.14), (xa - 0.335, -0.9 + 0.30 * j, 0.14 + 0.20), WARN if j % 2 == 0 else PAINT_BLK, bev=0.002, rotation=(0.0, 0.0, 0.0))
    return finish_mesh(bm, "SM_Zr_zavazie_%d_%s" % (k + 1, C["key"]))


def build_zr_kabina_zerava(C):
    # kabina zerava (zlta, velke okna): hladke zaoblene telo, vysoke celne sklo s ramom, bocne okna, stresne okno, clona, stierace, cierny prah, madla
    bm = bmesh.new()
    x0, x1 = C["ucab"]
    y0, y1 = zr_cab_y(C)
    h = C["ucab_h"]
    z0 = 0.14
    zt = z0 + h
    yc = (y0 + y1) * 0.5
    hwc = (y1 - y0) * 0.5
    st = [(x0, hwc - 0.08, zt - 0.24, 0.10), (x0 + 0.05, hwc - 0.02, zt - 0.08, 0.14), (x0 + 0.22, hwc, zt - 0.01, 0.16), (x0 + 0.55, hwc, zt, 0.18),
          (x1 - 0.55, hwc, zt, 0.18), (x1 - 0.25, hwc, zt - 0.02, 0.18), (x1 - 0.08, hwc - 0.02, zt - 0.08, 0.15), (x1, hwc - 0.06, zt - 0.20, 0.10)]
    loft_rr(bm, [(x, yc - w, yc + w, z0, top, r) for x, w, top, r in st], PAINT_YEL, 4)
    # celne sklo
    gz0, gz1 = z0 + 0.52, zt - 0.28
    gw = hwc * 2.0 - 0.36
    add_box(bm, (0.03, gw, gz1 - gz0), (x1 + 0.002, yc, (gz0 + gz1) * 0.5), GLASS)
    win_frame(bm, "X", yc, x1, (gz0 + gz1) * 0.5, gw, gz1 - gz0, 0.05, 0.05, 0.004, PAINT_BLK, 0.012)
    # bocne okna (vonkajsie s dvermi sa kryje dverami, vnutorne smerom k ramenu)
    for ya, sgn in ((y0, -1.0), (y1, 1.0)):
        add_box(bm, (x1 - x0 - 0.62, 0.02, gz1 - gz0 + 0.08), ((x0 + x1) * 0.5 - 0.22, ya + sgn * 0.004, (gz0 + gz1) * 0.5 + 0.04), GLASS)
        win_frame(bm, "Y", (x0 + x1) * 0.5 - 0.22, ya, (gz0 + gz1) * 0.5 + 0.04, x1 - x0 - 0.62, gz1 - gz0 + 0.08, 0.045, 0.03, sgn * 0.004, PAINT_BLK)
        bx(bm, x0 + 0.15, x1 - 0.30, *((ya + 0.0, ya + sgn * 0.012) if sgn > 0 else (ya - 0.012, ya)), z0, z0 + 0.34, PAINT_BLK, 0.008)
    add_box(bm, (0.78, gw - 0.20, 0.025), ((x0 + x1) * 0.5 - 0.15, yc, zt + 0.004), GLASS)
    pillow(bm, x1 - 0.18, x1 + 0.12, yc - hwc - 0.04, yc + hwc + 0.04, zt - 0.25, zt - 0.17, 0.035, PAINT_BLK)       # clona
    pillow(bm, x0 + 0.20, x0 + 0.80, yc - 0.40, yc + 0.40, zt - 0.005, zt + 0.10, 0.04, PAINT_BLK)
    for sgn in (-1.0, 1.0):
        add_rod(bm, (x1 + 0.02, yc + sgn * 0.12, gz0 + 0.05), (x1 + 0.02, yc + sgn * 0.12 + 0.45, gz0 + 0.30), 0.010, DARK, segments=5)       # stierace
        add_rod(bm, (x1 - 0.12, yc + sgn * (hwc + 0.025), z0 + 0.3), (x1 - 0.12, yc + sgn * (hwc + 0.025), zt - 0.5), 0.014, STEEL, segments=6)    # madla
    return finish_mesh(bm, "SM_Zr_kabina_zerava_" + C["key"])


def build_zr_dvere_zerava(C):
    # dvere kabiny zerava (lava strana, y = vonkajsia hrana); pivot na zavese pri prednej hrane, dvere siahaju do -X
    bm = bmesh.new()
    x0, x1 = C["ucab"]
    h = C["ucab_h"]
    wd = (x1 - x0) * 0.58
    pillow(bm, -wd, -0.02, 0.0, 0.05, 0.42, h - 0.12, 0.025, PAINT_YEL, 3, 2)
    h2 = h - 0.12 - 0.42 - 0.26
    add_box(bm, (wd - 0.22, 0.02, h2), (-wd * 0.5, 0.055, 0.42 + 0.14 + h2 * 0.5), GLASS)
    win_frame(bm, "Y", -wd * 0.5, 0.05, 0.42 + 0.14 + h2 * 0.5, wd - 0.22, h2, 0.04, 0.03, 0.004, PAINT_BLK)
    add_rod(bm, (-wd + 0.18, 0.07, 0.75), (-wd + 0.04, 0.07, 0.75), 0.013, CHROME, segments=6)
    return finish_mesh(bm, "SM_Zr_dvere_zerava_" + C["key"])


def build_zr_pult(C):
    # sedadlo operatora so zaoblenymi polstrami a podlokietnikmi s joystickmi, pult s displejom, volant pedalov
    bm = bmesh.new()
    x0, x1 = C["ucab"]
    y0, y1 = zr_cab_y(C)
    xm, ym = (x0 + x1) * 0.5 - 0.15, (y0 + y1) * 0.5
    z0 = 0.14
    pillow(bm, xm - 0.28, xm + 0.18, ym - 0.24, ym + 0.24, z0 + 0.36, z0 + 0.46, 0.04, SEAT)
    pillow(bm, xm - 0.31, xm - 0.19, ym - 0.24, ym + 0.24, z0 + 0.42, z0 + 1.00, 0.05, SEAT)
    pillow(bm, xm - 0.30, xm - 0.20, ym - 0.14, ym + 0.14, z0 + 1.00, z0 + 1.18, 0.04, SEAT)
    bx(bm, xm - 0.06, xm + 0.04, ym - 0.06, ym + 0.06, z0, z0 + 0.36, DARK, 0.01)
    bx(bm, xm - 0.20, xm + 0.14, ym - 0.19, ym + 0.19, z0 + 0.20, z0 + 0.24, DARK, 0.01)
    for s in SIDES_LR:
        pillow(bm, xm - 0.20, xm + 0.28, ym + s * 0.30 - 0.05, ym + s * 0.30 + 0.05, z0 + 0.46, z0 + 0.58, 0.03, DARK)
        add_cylinder(bm, 0.012, 0.18, along_z((xm + 0.18, ym + s * 0.30, z0 + 0.67)), STEEL, segments=6)
        add_cylinder(bm, 0.025, 0.06, along_z((xm + 0.18, ym + s * 0.30, z0 + 0.78)), DARK, segments=8, bev=0.008)
    pillow(bm, x1 - 0.42, x1 - 0.12, y0 + 0.20, y1 - 0.20, z0, z0 + 0.62, 0.04, INT)
    pillow(bm, x1 - 0.36, x1 - 0.28, ym - 0.30, ym + 0.30, z0 + 0.62, z0 + 0.84, 0.02, INT)
    bx(bm, x1 - 0.285, x1 - 0.275, ym - 0.18, ym + 0.18, z0 + 0.66, z0 + 0.80, LAMP_WHITE)
    return finish_mesh(bm, "SM_Zr_pult_" + C["key"])


def build_zr_konzoly(C):
    # konzoly otocneho capu ramena: dve zaoblene cheeky, cap s hlavami skrutiek a maznicou, drziaky valca zdvihu
    bm = bmesh.new()
    px, py, pz = C["piv"]
    b1 = C["boom_b"][0]
    for s in SIDES_LR:
        yy = py + s * (b1 * 0.5 + 0.07)
        add_extruded(bm, [(px - 0.40, 0.14), (px + 0.35, 0.14), (px + 0.20, pz - 0.20), (px + 0.0, pz + 0.30), (px - 0.30, pz + 0.30), (px - 0.45, pz - 0.30)],
                     yy - 0.05, yy + 0.05, "XZ", PAINT_YEL, bev=0.03)
        add_cylinder(bm, 0.12, 0.03, along_y((px, yy + s * 0.055, pz)), STEEL, segments=18, bev=0.006)
        for a in range(6):
            ang = 2.0 * math.pi * a / 6
            add_cylinder(bm, 0.014, 0.015, along_y((px + 0.09 * math.cos(ang), yy + s * 0.075, pz + 0.09 * math.sin(ang))), CHROME, segments=6)
    add_cylinder(bm, 0.07, b1 + 0.34, along_y((px, py, pz)), STEEL, segments=16, bev=0.004)
    cx = px + 1.5
    for s in SIDES_LR:
        pillow(bm, cx - 0.20, cx + 0.20, py + s * 0.17 - 0.045, py + s * 0.17 + 0.045, 0.14, 0.40, 0.025, PAINT_YEL)
    pillow(bm, cx - 0.30, cx + 0.30, py - 0.30, py + 0.30, 0.10, 0.17, 0.02, PAINT_BLK)
    return finish_mesh(bm, "SM_Zr_konzoly_" + C["key"])


def build_zr_majak():
    # oranzovy majak so soklom a prstencom (na streche kabiny zerava)
    bm = bmesh.new()
    add_cylinder(bm, 0.10, 0.04, along_z((0.0, 0.0, 0.02)), DARK, segments=16, bev=0.006)
    add_cylinder(bm, 0.075, 0.11, along_z((0.0, 0.0, 0.095)), LAMP_OR, segments=16, bev=0.012)
    add_cylinder(bm, 0.078, 0.015, along_z((0.0, 0.0, 0.155)), DARK, segments=16)
    return finish_mesh(bm, "SM_Zr_majak")


def build_zr_svetlo_pracovne():
    # pracovne svetlo (biele sklo v zaobleno puzdre s ochrannym ramikom; pivot v strede zadnej steny)
    bm = bmesh.new()
    pillow(bm, 0.0, 0.11, -0.14, 0.14, -0.08, 0.08, 0.03, DARK)
    add_cylinder(bm, 0.062, 0.03, along_x((0.115, 0.0, 0.0)), CHROME, segments=16)
    add_cylinder(bm, 0.052, 0.034, along_x((0.118, 0.0, 0.0)), LAMP_WHITE, segments=16, bev=0.004)
    return finish_mesh(bm, "SM_Zr_svetlo_pracovne")


def build_zr_stupen(C, k):
    # stupen ramena k (pivot na zadnom konci, os +X, dlzka L_k): rura so zaoblenymi rohmi, zvarove pasy, predny cierny obruc, tenke pasy, stitok; zakladny stupen: oka, hadice, drziaky
    L, b, h = C["boom_L"][k], C["boom_b"][k], C["boom_h"][k]
    bm = bmesh.new()
    r = min(b, h) * 0.30
    add_extruded_yz(bm, rounded_rect(-b * 0.5, b * 0.5, -h * 0.5, h * 0.5, r, 4), 0.0, L, PAINT_YEL, bev=0.008)
    for t in (0.22, 0.48, 0.74):
        x = L * t
        add_extruded_yz(bm, rounded_rect(-b * 0.5 - 0.012, b * 0.5 + 0.012, -h * 0.5 - 0.012, h * 0.5 + 0.012, r + 0.012, 4), x - 0.03, x + 0.03, PAINT_YEL, bev=0.006)
    add_extruded_yz(bm, rounded_rect(-b * 0.5 - 0.022, b * 0.5 + 0.022, -h * 0.5 - 0.022, h * 0.5 + 0.022, r + 0.022, 4), L - 0.20, L, PAINT_BLK, bev=0.012)
    for s in SIDES_LR:
        for zz in (-h * 0.20, h * 0.20):
            bx(bm, 0.30, L - 0.40, *zr_sy(s, b * 0.5 - 0.001, b * 0.5 + 0.005), zz - 0.018, zz + 0.018, PAINT_BLK, 0.003)
        bx(bm, L * 0.30, L * 0.30 + 0.80, *zr_sy(s, b * 0.5 - 0.001, b * 0.5 + 0.012), -h * 0.12, h * 0.12, PAINT_BLK, 0.006)
        for j in range(3):
            bx(bm, L * 0.30 + 0.12 + 0.22 * j, L * 0.30 + 0.20 + 0.22 * j, *zr_sy(s, b * 0.5 + 0.011, b * 0.5 + 0.016), -h * 0.08, h * 0.08, WHITE, 0.002)
    bx(bm, 0.25, L - 0.40, -0.05, 0.05, h * 0.5 - 0.001, h * 0.5 + 0.006, PAINT_BLK, 0.003)
    if k == 0:
        for s in SIDES_LR:
            pillow(bm, -0.05, 0.40, *zr_sy(s, b * 0.5 - 0.14, b * 0.5 - 0.06), -h * 0.5 - 0.12, h * 0.5 + 0.10, 0.03, PAINT_YEL)           # oka capu
            pillow(bm, 3.45 - 0.14, 3.45 + 0.14, *zr_sy(s, 0.13, 0.21), -h * 0.5 - 0.18, -h * 0.5 + 0.02, 0.025, PAINT_YEL)               # oka valca zdvihu
            add_cylinder(bm, 0.045, 0.012, along_y((3.45, s * 0.215, -h * 0.5 - 0.12)), STEEL, segments=10)
        bx(bm, 0.0, 0.05, -b * 0.5, b * 0.5, -h * 0.5, h * 0.5, PAINT_BLK, 0.01)
        for j in range(3):
            xx = 0.9 + 1.3 * j
            hose(bm, [(xx - 0.5, b * 0.5 + 0.045, -h * 0.20 + 0.02), (xx + 0.5, b * 0.5 + 0.045, -h * 0.20 + 0.02)], 0.020, PLAST, 8)
            hose(bm, [(xx - 0.5, b * 0.5 + 0.045, -h * 0.30), (xx + 0.5, b * 0.5 + 0.045, -h * 0.30)], 0.020, PLAST, 8)
            bx(bm, xx - 0.03, xx + 0.03, b * 0.5, b * 0.5 + 0.065, -h * 0.34, -h * 0.16, STEEL, 0.006)
    return finish_mesh(bm, "SM_Zr_rameno_%d_%s" % (k + 1, C["key"]))


def build_zr_vitel(C):
    # vitel na zakladnom stupni ramena (pivot v osi bubna na vrchu): bubon s priruba a lanom, ozubenie
    b1, h1 = C["boom_b"][0], C["boom_h"][0]
    bm = bmesh.new()
    add_cylinder(bm, 0.24, b1 - 0.16, along_y((0.0, 0.0, 0.0)), STEEL, segments=20, bev=0.008)
    for s in SIDES_LR:
        add_cylinder(bm, 0.32, 0.03, along_y((0.0, s * (b1 * 0.5 - 0.06), 0.0)), PAINT_BLK, segments=20, bev=0.005)
    for k in range(12):
        a = 2.0 * math.pi * k / 12
        add_cylinder(bm, 0.255, 0.04, along_y((0.0, 0.0, 0.0)), ROPE, segments=3) if False else None
    for k in range(7):
        add_cylinder(bm, 0.255, 0.018, along_y((0.0, -b1 * 0.5 + 0.12 + 0.11 * k, 0.0)), ROPE, segments=20)
    return finish_mesh(bm, "SM_Zr_vitel_" + C["key"])


def build_zr_vitel_podstava(C):
    # podstava vitla (nepohyblivy ram na hornej strane zakladneho stupna): dve konzoly s lozisk, kryt prevodu a podlozka
    b1, h1 = C["boom_b"][0], C["boom_h"][0]
    bm = bmesh.new()
    for s in SIDES_LR:
        add_extruded(bm, [(0.20, h1 * 0.5), (0.95, h1 * 0.5), (0.80, h1 * 0.5 + 0.42), (0.35, h1 * 0.5 + 0.42)],
                     s * (b1 * 0.5 - 0.06) - 0.03, s * (b1 * 0.5 - 0.06) + 0.03, "XZ", PAINT_YEL, bev=0.02)
        add_cylinder(bm, 0.06, 0.14, along_y((0.575, s * (b1 * 0.5 - 0.06), h1 * 0.5 + 0.26)), STEEL, segments=12, bev=0.006)
    pillow(bm, 0.20, 0.95, -b1 * 0.5 + 0.10, b1 * 0.5 - 0.10, h1 * 0.5, h1 * 0.5 + 0.035, 0.012, PAINT_BLK)
    pillow(bm, 0.30, 0.55, b1 * 0.5 - 0.04, b1 * 0.5 + 0.10, h1 * 0.5 + 0.08, h1 * 0.5 + 0.34, 0.04, PAINT_BLK)      # prevodovka vitla
    return finish_mesh(bm, "SM_Zr_vitel_podstava_" + C["key"])


def build_zr_hlava(C):
    # hlava ramena (pivot na prednom konci posledneho stupna): zaoblene cheeky, hlavna kladka s ramenami, horna kladka, vodiace tyce lana a svetlo
    b = C["boom_b"][-1]
    h = C["boom_h"][-1]
    bm = bmesh.new()
    for s in SIDES_LR:
        yy = s * (b * 0.5 + 0.045)
        add_extruded(bm, [(-0.20, -h * 0.5), (0.35, -h * 0.5 - 0.10), (0.56, -0.02), (0.50, 0.22), (0.22, h * 0.5 + 0.10), (-0.20, h * 0.5)],
                     yy - 0.03, yy + 0.03, "XZ", PAINT_YEL, bev=0.022)
        add_cylinder(bm, 0.07, 0.02, along_y((0.30, yy + s * 0.04, -0.06)), STEEL, segments=14)
    add_ring(bm, 0.27, 0.24, b * 0.5, 0.0, STEEL, 24, bev=0.006) if False else None
    add_cylinder(bm, 0.27, b * 0.5, along_y((0.30, 0.0, -0.06)), DARK, segments=24, bev=0.01)
    for a in range(6):
        ang = 2.0 * math.pi * a / 6
        add_box(bm, (0.045, b * 0.5 + 0.02, 0.17), (0.30, 0.0, -0.06), STEEL, bev=0.006, frame=Matrix.Rotation(ang, 4, "Y") @ Matrix.Translation((0.0, 0.0, 0.0)), rotation=(0.0, 0.0, 0.0)) if False else None
    add_cylinder(bm, 0.24, b * 0.5 + 0.02, along_y((0.30, 0.0, -0.06)), STEEL, segments=24)
    add_cylinder(bm, 0.07, b + 0.10, along_y((0.30, 0.0, -0.06)), STEEL, segments=12)
    add_cylinder(bm, 0.12, b * 0.4, along_y((0.12, 0.0, h * 0.5 + 0.05)), DARK, segments=16, bev=0.008)
    add_rod(bm, (0.30, -b * 0.5 - 0.02, -0.40), (0.30, b * 0.5 + 0.02, -0.40), 0.016, STEEL, segments=8)
    pillow(bm, 0.02, 0.12, -0.10, 0.10, h * 0.5 + 0.12, h * 0.5 + 0.22, 0.02, LAMP_RED)                    # svetlo hlavy
    return finish_mesh(bm, "SM_Zr_hlava_" + C["key"])


def build_zr_hak(C):
    # hakovy blok (pivot na hornej strane bloku, hak smeruje dole, otvor haku smeruje +X): zaobleny blok so zltymi platnami a kladkou, vratenom, hak s poistkou
    bm = bmesh.new()
    pillow(bm, -0.16, 0.16, -0.20, 0.20, -0.36, -0.02, 0.05, PAINT_BLK)
    for s in SIDES_LR:
        pillow(bm, -0.19, 0.19, *zr_sy(s, 0.19, 0.225), -0.40, 0.0, 0.05, PAINT_YEL, 3, 2)
    add_cylinder(bm, 0.13, 0.30, along_y((0.0, 0.0, -0.13)), STEEL, segments=18)
    pillow(bm, -0.07, 0.07, -0.13, 0.13, 0.0, 0.06, 0.025, STEEL)
    add_cylinder(bm, 0.08, 0.12, along_z((0.0, 0.0, -0.43)), STEEL, segments=12, bev=0.008)
    add_cylinder(bm, 0.06, 0.14, along_z((0.0, 0.0, -0.53)), PAINT_BLK, segments=12, bev=0.006)
    pts = [(0.0, -0.58)]
    cx, cz, rr = 0.13, -0.74, 0.13
    for a in range(180, 440, 14):
        pts.append((cx + rr * math.cos(math.radians(a)), cz + rr * math.sin(math.radians(a))))
    for i, (p, q) in enumerate(zip(pts, pts[1:])):
        rad = 0.062 - 0.0035 * i
        add_rod(bm, (p[0], 0.0, p[1]), (q[0], 0.0, q[1]), max(rad, 0.03), STEEL, segments=10)
        add_cylinder(bm, max(rad, 0.03), 0.01, along_y((q[0], 0.0, q[1])), STEEL, segments=3) if False else None
    add_rod(bm, (0.26, 0.0, -0.71), (0.12, 0.0, -0.64), 0.012, STEEL, segments=6)      # poistka
    return finish_mesh(bm, "SM_Zr_hak_" + C["key"])


def build_zr_lano():
    # lano (dve vetvy v osi +Z, dlzka 1, pivot na hlave; mierka Z = dlzka)
    bm = bmesh.new()
    for s in SIDES_LR:
        add_cylinder(bm, 0.017, 1.0, along_z((s * 0.14, 0.0, 0.5)), ROPE, segments=8)
    return finish_mesh(bm, "SM_Zr_lano")


def cr_valec(C):
    # teleskopicky valec zdvihu: pocet stupnov, dlzka stupna a polomer podla rozsahu vzdialenosti valca pri uhloch ramena 0 az maximum
    px, py, pz = C["piv"]
    base = Vector((px + 1.5, 0.30))
    att = (3.0, -C["boom_h"][0] * 0.5 - 0.16)
    ds = []
    for th in range(0, int(C["boom_max"]) + 3, 3):
        a = math.radians(th)
        p = Vector((px + att[0] * math.cos(a) - att[1] * math.sin(a), pz + att[0] * math.sin(a) + att[1] * math.cos(a)))
        ds.append((p - base).length)
    return min(ds), max(ds), base, att


def cr_upper_parts(put, put_lr, C):
    put(build_zr_plosina(C))
    put(build_zr_kryt(C))
    for k in range(C["cw_n"]):
        put(build_zr_zavazie(C, k))
    put(build_zr_kabina_zerava(C))
    put(build_zr_dvere_zerava(C))
    put(build_zr_pult(C))
    put(build_zr_konzoly(C))
    put(build_zr_majak())
    put(build_zr_svetlo_pracovne())
    for k in range(len(C["boom_L"])):
        put(build_zr_stupen(C, k))
    put(build_zr_vitel(C))
    put(build_zr_vitel_podstava(C))
    put(build_zr_hlava(C))
    put(build_zr_hak(C))
    put(build_zr_lano())
    dmin, dmax, base, att = cr_valec(C)
    n, ell = tele_stages(dmin * 0.97, dmax * 1.01)
    cylinder_family(put, "Zr_valec_" + C["key"], n, ell, C["hose"])


# ---------------------------------------------------------------------------
# Rig zerava: koren (vlastnosti) -> telo (zdvih na podperach) -> nahrady s riadenim a kolesami, podpery, otocna nadstavba -> rameno (zdvih, vysun) -> hlava;
# hak visi vo svetovej polohe pod hlavou (driver zo svetovej polohy), lano mieri z hlavy na hak.
# ---------------------------------------------------------------------------

ZR_TL = dict(drive0=1, drive1=200, door0=205, door1=225, door2=240, door3=260, out0=210, out1=260, down0=262, down1=330, boom0=340, boom1=420, ext0=420, ext1=520,
             slew0=520, slew1=620, hook0=620, hook1=700, up0=700, up1=760, back0=760, back1=860, ret0=860, ret1=890, low0=890, low1=930, up_out0=930, up_out1=960,
             sout0=960, sout1=990, cdoor0=262, cdoor1=282, cdoor2=300, cdoor3=320)
ZR_DRIVE = 14.0


def zr_rig(coll, C, parts, mats, x_pos, y_pos):
    name, R, t = C["name"], C["R"], C["track"]
    root = new_object(coll, name, None, (x_pos, y_pos, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.5
    set_prop(root, "Koleso_otocenie", 0.0, 0.0, 100000.0, "Otocenie kolies v stupnoch (rastie pri jazde dopredu, neobmedzene)")
    set_prop(root, "Riadenie", 0.0, -C["steer_max"], C["steer_max"], "Uhol riadenych naprav v stupnoch (kladny = dolava)")
    set_prop(root, "Podpery_vysun", 0.0, 0.0, 1.0, "Podpery: 0 = zasunute, 1 = vysunute do boku o %.1f m" % C["stroke"])
    set_prop(root, "Podpery_spust", 0.0, 0.0, 1.0, "Podpery: 0 = hore, 0.7 = podlozky na zemi, 1 = zdvihnuty podvozok o %.2f m" % C["lift"])
    set_prop(root, "Otocenie", 0.0, -360.0, 360.0, "Otocenie nadstavby v stupnoch (kladny = dolava)")
    set_prop(root, "Vyzdvih", 0.0, 0.0, 1.0, "Sklon ramena: 0 = vodorovne (nad kabinou), 1 = %.0f st." % C["boom_max"])
    set_prop(root, "Vysun", 0.0, 0.0, 1.0, "Teleskopicke rameno: 0 = zasunute, 1 = vysunute na plnu dlzku")
    set_prop(root, "Hak", 0.0, 0.0, 1.0, "Hak: 0 = pod hlavou ramena, 1 = na zemi")
    set_prop(root, "Dvere_nosica", 0.0, 0.0, 1.0, "Dvere kabiny nosica (obe): 0 = zatvorene, 1 = otvorene")
    set_prop(root, "Dvere_zerava", 0.0, 0.0, 1.0, "Dvere kabiny zerava: 0 = zatvorene, 1 = otvorene")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    body = empty(coll, name + "_telo", (0.0, 0.0, 0.0), root)
    body.empty_display_type = "ARROWS"
    body.empty_display_size = 0.5
    driver(body, "location", 2, "%.4f * max((s - 0.70) / 0.30, 0.0)" % C["lift"], [prop("s", "Podpery_spust")])
    o0 = (0.0, 0.0, 0.0)
    z0, z1, xf = C["z0"], C["z1"], C["front"]
    cx0, cxf = C["cab"]
    zr_ = C["cab_roof"]
    key_ = C["key"]
    # nosic
    for tag, mk in (("ram", "ram"), ("zakladna", "zakladna"), ("kabina", "kabina"), ("maska", "maska"), ("naraznik_predny", "naraznik_predny"),
                    ("opierka", "opierka"), ("naraznik_zadny", "naraznik_zadny")):
        mount(coll, name, tag, body, o0, [(tag, parts["Zr_%s_%s" % (mk, key_)])])
    mount(coll, name, "nadrz", body, (-0.3 if key_ == "40t" else 0.0, t * 0.9, z0 + 0.07), [("nadrz", parts["Zr_nadrz_" + key_])])
    mount(coll, name, "skrinka", body, (-0.3 if key_ == "40t" else 0.0, -t * 0.9, z0 + 0.07), [("skrinka", parts["Zr_skrinka_" + key_])])
    mount(coll, name, "vyfuk", body, (cx0 - 0.25, -1.08, z1), [("vyfuk", parts["Zr_vyfuk"])])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        hinge, _ = mount(coll, name, "dvere_nosica_" + side, body, (cxf - 0.15, s * 1.20, z1), [("dvere_nosica_" + side, parts["Zr_dvere_%s_%s" % (key_, side)])])
        driver(hinge, "rotation_euler", 2, "%.0f * d * 1.35" % -s, [prop("d", "Dvere_nosica")])
        mount(coll, name, "svetlomet_" + side, body, (cxf + 0.05, s * 0.85, z1 + 0.10), [("svetlomet_" + side, parts["Zr_svetlomet_" + side])])
        mount(coll, name, "zrkadlo_" + side, body, (cxf - 0.30, s * 1.20, zr_ - 0.58), [("zrkadlo_" + side, parts["Zr_zrkadlo_" + side])])
        mount(coll, name, "schodik_" + side, body, (cxf - 0.75, s * 1.20, z1), [("schodik_" + side, parts["Zr_schodik_" + side])])
        mount(coll, name, "svetlo_zadne_" + side, body, (C["f_rear"] - 0.30, s * 0.60, z0 + 0.09), [("svetlo_zadne_" + side, parts["Zr_svetlo_zadne_" + side])])
    # nahrady, riadenie, kolesa
    axles, wheels = [], []
    xc = C["axles"][C["steer"]] if len(C["axles"]) > C["steer"] else C["axles"][-1]
    x1_ = C["axles"][0]
    for i, x in enumerate(C["axles"]):
        sock, _ = mount(coll, name, "naprava_%d" % (i + 1), body, (x, 0.0, R), [("naprava_%d" % (i + 1), parts["Zr_naprava_" + key_])])
        axles.append(sock)
        steer = i < C["steer"]
        f = (x - xc) / (x1_ - xc) if steer else 0.0
        for s, side in ((1.0, "L"), (-1.0, "P")):
            kn, _ = mount(coll, name, "zakladka_%d_%s" % (i + 1, side), sock, (0.0, s * (t - 0.42), 0.0), [("zakladka_%d_%s" % (i + 1, side), parts["Zr_zakladka_%s_%s" % (key_, side)])])
            if steer:
                driver(kn, "rotation_euler", 2, "st * %.6f * %.4f" % (D2R, f), [prop("st", "Riadenie")])
            hub, _ = mount(coll, name, "koleso_%d_%s" % (i + 1, side), kn, (0.0, s * 0.42, 0.0),
                           [("pneu_%d_%s" % (i + 1, side), parts["Zr_pneu_" + key_]), ("disk_%d_%s" % (i + 1, side), parts["Zr_disk_%s_%s" % (key_, side)])])
            driver(hub, "rotation_euler", 1, "r * %.6f" % D2R, [prop("r", "Koleso_otocenie")])
            wheels.append(hub)
            mount(coll, name, "blatnik_%d_%s" % (i + 1, side), body, (x, s * t, R), [("blatnik_%d_%s" % (i + 1, side), parts["Zr_blatnik_%s_%s" % (key_, side)])])
    # vysuvne podpery
    zc = z0 - 0.10
    L = zr_beam_len(C)
    hh = zr_hh(C)
    for g, xg in enumerate(C["oxs"]):
        gn = "predna" if g == 0 else "zadna"
        mount(coll, name, "podpera_nosnik_" + gn, body, (xg, 0.0, 0.0), [("podpera_nosnik_" + gn, parts["Zr_podpera_nosnik_" + key_])])
        for s, side in ((1.0, "L"), (-1.0, "P")):
            beam, _ = mount(coll, name, "podpera_vysuv_%s_%s" % (gn, side), body, (xg, s * (hh + 0.03 - L), zc), [("podpera_vysuv_%s_%s" % (gn, side), parts["Zr_podpera_vysuv_%s_%s" % (key_, side)])])
            driver(beam, "location", 1, "%.0f * (%.4f + e * %.4f)" % (s, hh + 0.03 - L, C["stroke"]), [prop("e", "Podpery_vysun")])
            jack, _ = mount(coll, name, "podpera_valec_%s_%s" % (gn, side), beam, (0.0, s * (L - 0.25), -0.28), [("podpera_valec_%s_%s" % (gn, side), parts["Zr_podpera_valec_" + key_])])
            rod, _ = mount(coll, name, "podpera_tyc_%s_%s" % (gn, side), jack, (0.0, 0.0, 0.0), [("podpera_tyc_%s_%s" % (gn, side), parts["Zr_podpera_tyc_" + key_])])
            driver(rod, "location", 2, "0.40 * (1 - min(s / 0.70, 1.0)) - %.4f * max((s - 0.70) / 0.30, 0.0) - %.4f" % (C["lift"], zc - 0.28), [prop("s", "Podpery_spust")])
    # otocna nadstavba
    turn = empty(coll, name + "_uchyt_otocna", (0.0, 0.0, C["ring_top"]), body)
    turn.empty_display_type = "ARROWS"
    turn.empty_display_size = 0.5
    driver(turn, "rotation_euler", 2, "o * %.6f" % D2R, [prop("o", "Otocenie")])
    px, py, pz = C["piv"]
    ux0, ux1 = C["ucab"]
    uy0, uy1 = zr_cab_y(C)
    for tag in ("plosina", "kryt", "kabina_zerava", "pult", "konzoly"):
        mount(coll, name, tag, turn, o0, [(tag, parts["Zr_%s_%s" % (tag, key_)])])
    for k in range(C["cw_n"]):
        mount(coll, name, "zavazie_%d" % (k + 1), turn, o0, [("zavazie_%d" % (k + 1), parts["Zr_zavazie_%d_%s" % (k + 1, key_)])])
    uh = C["ucab_h"]
    mount(coll, name, "majak", turn, (ux0 + 0.45, (uy0 + uy1) * 0.5, 0.14 + uh + 0.07), [("majak", parts["Zr_majak"])])
    for j, yy in enumerate((uy0 + 0.30, uy1 - 0.30)):
        mount(coll, name, "svetlo_pracovne_%d" % (j + 1), turn, (ux1 - 0.40, yy, 0.14 + uh + 0.07), [("svetlo_pracovne_%d" % (j + 1), parts["Zr_svetlo_pracovne"])])
    udoor, _ = mount(coll, name, "dvere_zerava", turn, (ux1 - 0.32, uy1, 0.14), [("dvere_zerava", parts["Zr_dvere_zerava_" + key_])])
    driver(udoor, "rotation_euler", 2, "-d * 1.35", [prop("d", "Dvere_zerava")])
    # rameno
    piv = empty(coll, name + "_uchyt_rameno_cap", (px, py, pz), turn)
    piv.empty_display_type = "ARROWS"
    piv.empty_display_size = 0.5
    driver(piv, "rotation_euler", 1, "-v * %.4f" % math.radians(C["boom_max"]), [prop("v", "Vyzdvih")])
    n_st = len(C["boom_L"])
    prev, stage_socks = piv, []
    for k in range(n_st):
        if k == 0:
            loc = (zr_stage_rear(C, 0), 0.0, 0.0)
        else:
            loc = (zr_stage_rear(C, k) - zr_stage_rear(C, k - 1), 0.0, 0.0)
        sock, _ = mount(coll, name, "rameno_%d" % (k + 1), prev, loc, [("rameno_%d" % (k + 1), parts["Zr_rameno_%d_%s" % (k + 1, key_)])])
        if k > 0:
            driver(sock, "location", 0, "%.4f + e * %.4f" % (loc[0], zr_stage_stroke(C, k)), [prop("e", "Vysun")])
        stage_socks.append(sock)
        prev = sock
    s1 = stage_socks[0]
    h1 = C["boom_h"][0]
    mount(coll, name, "vitel_podstava", s1, o0, [("vitel_podstava", parts["Zr_vitel_podstava_" + key_])])
    drum, _ = mount(coll, name, "vitel", s1, (0.575, 0.0, h1 * 0.5 + 0.26), [("vitel", parts["Zr_vitel_" + key_])])
    head, _ = mount(coll, name, "hlava", stage_socks[-1], (C["boom_L"][-1], 0.0, 0.0), [("hlava", parts["Zr_hlava_" + key_])])
    anchor = empty(coll, name + "_hlava_lano", (0.30, 0.0, -0.33), head)
    # valec zdvihu
    dmin, dmax, base, att = cr_valec(C)
    n, ell = tele_stages(dmin * 0.97, dmax * 1.01)
    telescope(coll, name + "_valec_zdvihu", parts, "Zr_valec_" + key_, n, ell, turn, (base.x, py, base.y), piv, (att[0], 0.0, att[1]))
    # hak: sokel vo svetovej polohe pod hlavou (nema rodica, lebo visi), lano z hlavy
    hook = empty(coll, name + "_uchyt_hak", (x_pos, y_pos, 1.0), None)
    hook.empty_display_type = "ARROWS"
    hook.empty_display_size = 0.3
    hook.hide_render = True
    hook_obj = new_object(coll, name + "_hak", parts["Zr_hak_" + key_], (0.0, 0.0, 0.0), hook)
    driver_world(hook, "location", 0, "ax", [("ax", anchor, "LOC_X")])
    driver_world(hook, "location", 1, "ay", [("ay", anchor, "LOC_Y")])
    driver_world(hook, "location", 2, "max(%.3f, az - 1.1) * (1 - h) + %.3f * h" % (C["hook_len"], C["hook_len"]), [("az", anchor, "LOC_Z")])
    driver_prop(hook, "location", 2, "h", root, "Hak")
    driver_world(hook, "rotation_euler", 2, "rz", [("rz", head, "ROT_Z")])
    rope, _ = mount(coll, name, "lano", anchor, o0, [("lano", parts["Zr_lano"])])
    track(rope, hook, "TRACK_Z")
    driver(rope, "scale", 2, "d", [("d", "DIST", (anchor, hook))])
    driver(drum, "rotation_euler", 1, "-h * %.4f" % (6.0 * math.pi * 2), [prop("h", "Hak")])
    zr_animate(C, root)
    return dict(root=root, body=body, boom=piv, hook=hook, wheels=wheels, axles=axles, stages=stage_socks, anchor=anchor)


def zr_keys(root, prop_name, frames):
    for frame, value in frames:
        root[prop_name] = value
        root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)


def zr_animate(C, root):
    T = ZR_TL
    x0 = root.location.x
    key(root, "location", 0, [(1, x0), (T["drive1"], x0 + ZR_DRIVE), (1000, x0 + ZR_DRIVE)])
    zr_keys(root, "Koleso_otocenie", [(1, 0.0), (T["drive1"], ZR_DRIVE / C["R"] / D2R)])
    zr_keys(root, "Riadenie", [(1, 0.0), (50, 0.0), (80, 0.6 * C["steer_max"]), (120, -0.6 * C["steer_max"]), (160, 0.0)])
    zr_keys(root, "Dvere_nosica", [(1, 0.0), (T["door0"], 0.0), (T["door1"], 1.0), (T["door2"], 1.0), (T["door3"], 0.0)])
    zr_keys(root, "Podpery_vysun", [(1, 0.0), (T["out0"], 0.0), (T["out1"], 1.0), (T["sout0"], 1.0), (T["sout1"], 0.0)])
    zr_keys(root, "Podpery_spust", [(1, 0.0), (T["down0"], 0.0), (T["down1"], 1.0), (T["up_out0"], 1.0), (T["up_out1"], 0.0)])
    zr_keys(root, "Dvere_zerava", [(1, 0.0), (T["cdoor0"], 0.0), (T["cdoor1"], 1.0), (T["cdoor2"], 1.0), (T["cdoor3"], 0.0)])
    zr_keys(root, "Vyzdvih", [(1, 0.0), (T["boom0"], 0.0), (T["boom1"], 0.85), (T["low0"], 0.85), (T["low1"], 0.0)])
    zr_keys(root, "Vysun", [(1, 0.0), (T["ext0"], 0.0), (T["ext1"], 1.0), (T["back1"], 1.0), (T["ret1"], 0.0)])
    zr_keys(root, "Otocenie", [(1, 0.0), (T["slew0"], 0.0), (T["slew1"], 110.0), (T["back0"], 110.0), (T["back1"], 0.0)])
    zr_keys(root, "Hak", [(1, 0.0), (T["hook0"], 0.0), (T["hook1"], 1.0), (T["up0"], 1.0), (T["up1"], 0.0)])


def zr_scene(coll, parts, mats):
    roots = []
    for i, C in enumerate(CRANES.values()):
        sub = child_collection(coll, C["name"])
        r = zr_rig(sub, C, parts, mats, 0.0, -14.0 * i)
        roots.append(r["root"])
    return roots


SCENE_BUILDERS.append(zr_scene)


def _zr_doc():
    lines = ["", "AUTOZERIAV (Zeriav_40t, Zeriav_80t): podvozok s kabinou, riadenymi nahradami a styrmi vysuvnymi podperami, otocna nadstavba s kabinou zerava a protizavazim,",
             "  teleskopicke rameno na teleskopickom valci zdvihu, hlava s kladkou, lano a hakovy blok. Pociatok = zem pod osou otocnej nadstavby, predok +X, lava +Y.",
             "  Vlastnosti na hlavnom objekte (<Zeriav>): Koleso_otocenie (stupne), Riadenie (+-uhol riadenych naprav), Podpery_vysun, Podpery_spust (0 az 0.7 = podlozky dosadnu, 0.7 az 1 = podvozok sa zdvihne),",
             "    Otocenie (stupne, +-360), Vyzdvih (0 az 1 = 0 az 78 st.), Vysun (0 az 1 = vsetky stupne), Hak (0 = pod hlavou, 1 = na zemi), Dvere_nosica, Dvere_zerava (0 az 1).",
             "  DEMONTAZ: kazdy diel je samostatny objekt <Zeriav>_<diel> a je detom UCHYTU <Zeriav>_uchyt_<diel> (prazdny objekt v pivote dielu), animacia je na uchyte. Vymena: zmaz objekt dielu, novy diel (rovnaky pivot) daj ako dieta uchytu.",
             "  Carrier: ram, zakladna (vencove lozisko), kabina, dvere_nosica_L / _P (zavesa, rotacia Z), maska, naraznik_predny, svetlomet_L / _P, zrkadlo_L / _P, schodik_L / _P, nadrz, skrinka, vyfuk, opierka (rameno na streche),",
             "    naraznik_zadny, svetlo_zadne_L / _P, naprava_N (pohyblivy pivot v osi), zakladka_N_L / _P (riadenie: rotacia Z na prvych dvoch napravach), koleso_N_L / _P (= pneu + disk, os Y), blatnik_N_L / _P,",
             "    podpera_nosnik_predna / zadna (puzdro), podpera_vysuv_<predna|zadna>_L / _P (posun po Y), podpera_valec_*, podpera_tyc_* (piest s podlozkou: stupa podla Podpery_spust).",
             "  Nadstavba (uchyt <Zeriav>_uchyt_otocna, rotacia Z = Otocenie): plosina (so zabradlim), kryt (motor + hydraulika), zavazie_1 az N (dosky protizavazia), kabina_zerava, dvere_zerava (zavesa), pult (sedadlo a ovladace), konzoly (cap ramena + oka valca),",
             "    majak, svetlo_pracovne_1 / _2.",
             "  Rameno (uchyt <Zeriav>_uchyt_rameno_cap, rotacia Y = -Vyzdvih x 78 st.): rameno_1 (zakladny stupen) az rameno_N (kazdy dalsi stupen je dieta predosleho a vysuva sa po X o Vysun x (dlzka - 1.25 m)),",
             "    vitel_podstava + vitel (bubon sa otaca podla Hak), hlava (cheeky, kladka), prazdny objekt <Zeriav>_hlava_lano (miesto, z ktoreho visi lano). Valec zdvihu <Zeriav>_valec_zdvihu_1..n: prvy stupen mieri na ciel (cap na ramene), dalsie sa vysuvaju.",
             "  Hak: uchyt <Zeriav>_uchyt_hak NEMA rodica, jeho poloha je driver zo svetovej polohy hlavy (x, y), vyska = max(%.2f, vyska hlavy - 1.1) pre Hak = 0 az %.2f m (blok na zemi) pre Hak = 1, otocenie Z podla hlavy; lano (<Zeriav>_lano) je dieta hlavy, mieri na hak (Damped Track, mierka Z = vzdialenost)." % (1.0, 1.0),
             "  Animacia: jazda 1 az 200 (kolesa, riadenie), dvere 205 az 260, podpery von 210 az 260 a dole 262 az 330, rameno hore 340 az 420, vysun 420 az 520, otocenie 520 az 620, hak dole 620 az 700 a hore 700 az 760, spat 760 az 860,",
             "    zasunutie 860 az 890, rameno dole 890 az 930, podpery hore 930 az 960 a dnu 960 az 990."]
    for C in CRANES.values():
        lines.append("  %s: %d naprav (x = %s), kolesa R %.2f m, dlzka %.1f m, rameno %d stupnov (zasunute %.1f m, vysunute asi %.1f m od capu), podpery rozpatie %.1f m" % (
            C["name"], len(C["axles"]), ", ".join("%.2f" % x for x in C["axles"]), C["R"], C["front"] - C["f_rear"], len(C["boom_L"]), C["boom_L"][0],
            C["boom_L"][0] + sum(zr_stage_stroke(C, k) for k in range(1, len(C["boom_L"]))), 2.0 * (zr_hh(C) + 0.03 + C["stroke"])))
    return lines


DOC_EXTRA.extend(_zr_doc())
for _C in CRANES.values():
    _k = _C["key"]
    CATALOG_EXTRA.append(("AUTOZERIAV " + _k, ["Zr_%s_%s" % (p, _k) for p in ("ram", "zakladna", "kabina", "maska", "naraznik_predny", "nadrz", "skrinka", "naprava", "pneu", "podpera_nosnik", "podpera_valec", "podpera_tyc",
                                                                           "opierka", "naraznik_zadny", "plosina", "kryt", "kabina_zerava", "dvere_zerava", "pult", "konzoly", "vitel", "vitel_podstava", "hlava", "hak")] +
                         ["Zr_dvere_%s_L" % _k, "Zr_disk_%s_L" % _k, "Zr_blatnik_%s_L" % _k, "Zr_podpera_vysuv_%s_L" % _k, "Zr_zakladka_%s_L" % _k] +
                         ["Zr_zavazie_%d_%s" % (i + 1, _k) for i in range(_C["cw_n"])] + ["Zr_rameno_%d_%s" % (i + 1, _k) for i in range(len(_C["boom_L"]))]))
CATALOG_EXTRA.append(("AUTOZERIAV - SPOLOCNE", ["Zr_svetlomet_L", "Zr_zrkadlo_L", "Zr_schodik_L", "Zr_vyfuk", "Zr_svetlo_zadne_L", "Zr_majak", "Zr_svetlo_pracovne", "Zr_lano"]))


main()
