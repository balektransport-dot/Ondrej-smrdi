# Stylizovane low poly pickupy a privesy (voziky) pre Blender 3.0 a novsi: dva pickupy (dvojkabina a jednokabina, cierny pruh, ochranny rollbar, svetelna lista, rurova ochrana, velke kolesa)
# a privesy so spolocnou spojkou na gulu: maly vozik, podval na auto (sklopna a odsuvna riesetkova plosina s navijakom a autom), vozik na palety (s EUR paletami),
# cisternovy vozik, vozik na drevo (s kmenmi) a skrinovy vozik (zadna rampa, bocne dvere).
#
# Pouzitie: zalozka Scripting (Skriptovani) -> pretiahni subor do textoveho editora -> Alt+P.
#
# Vytvori kolekciu "Pickup_vozik": podkolekcie pre kazdy pickup a privesok (napr. Pickup_dvojkabina, Podval_auto_4_0, Vozik_cisterna_3_0) a Pickup_vozik_diely
# (kazdy diel samostatne s menovkou). Ovladanie vlastnostami na hlavnom objekte (panel N -> Item alebo Object -> Custom Properties), popis v subore Pickup_vozik.txt.
# Predok = +X, lava strana = +Y. Pickup: pociatok = zem pod prednou napravou. Privesok: pociatok = zem pod stredom gule (zapriahnutie).
# Pickup dvojkabina je zapriahnuty s podvalom 4.0, pickup jednokabina s malym vozikom 2.6, ostatne privesy stoja samostatne v dalsich radoch.
# Do priecinka Pickup_vozik v domovskom priecinku ulozi FBX kazdeho dielu a textovy subor s popisom skladania.
# Skript sa da spustit znova: stare diely sa nahradia novymi.

import math
import os

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

COLLECTION = "Pickup_vozik"
EXPORT_FBX = True
EXPORT_DIR = os.path.join(os.path.expanduser("~"), "Pickup_vozik")


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
# Materialy a spolocne diely
# ---------------------------------------------------------------------------

MATERIALS = [
    ("PV_Ram", (0.035, 0.037, 0.045, 1.0), 0.3, 0.50, 0.0, 1.0),
    ("PV_Ocel", (0.50, 0.51, 0.53, 1.0), 0.6, 0.40, 0.0, 1.0),
    ("PV_Chrom", (0.85, 0.85, 0.85, 1.0), 1.0, 0.15, 0.0, 1.0),
    ("PV_Pneu", (0.015, 0.015, 0.017, 1.0), 0.0, 0.90, 0.0, 1.0),
    ("PV_Disk", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("PV_Tmava", (0.03, 0.03, 0.03, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("PV_Sklo", (0.10, 0.18, 0.24, 1.0), 0.0, 0.05, 0.0, 0.45),
    ("PV_Svetlo_oranzove", (1.0, 0.35, 0.0, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("PV_Svetlo_cervene", (1.0, 0.02, 0.01, 1.0), 0.0, 0.30, 4.0, 1.0),
    ("PV_Svetlo_biele", (1.0, 0.95, 0.85, 1.0), 0.0, 0.30, 3.0, 1.0),
    ("PV_Odrazka", (0.60, 0.02, 0.02, 1.0), 0.0, 0.35, 0.0, 1.0),
    ("PV_Biela", (0.85, 0.85, 0.83, 1.0), 0.0, 0.40, 0.0, 1.0),
    ("PV_Pozink", (0.55, 0.57, 0.58, 1.0), 0.6, 0.45, 0.0, 1.0),
    ("PV_Hlinik", (0.62, 0.63, 0.64, 1.0), 0.6, 0.35, 0.0, 1.0),
    ("PV_Preglejka", (0.45, 0.30, 0.16, 1.0), 0.0, 0.80, 0.0, 1.0),
    ("PV_Interier", (0.10, 0.10, 0.11, 1.0), 0.0, 0.70, 0.0, 1.0),
    ("PV_Sedadlo", (0.20, 0.19, 0.17, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("PV_Plast", (0.13, 0.135, 0.145, 1.0), 0.0, 0.55, 0.0, 1.0),
    ("PV_Lak_modry", (0.05, 0.14, 0.38, 1.0), 0.4, 0.35, 0.0, 1.0),
    ("PV_Lak_biely", (0.88, 0.88, 0.86, 1.0), 0.1, 0.35, 0.0, 1.0),
    ("PV_Lak_cerveny", (0.55, 0.04, 0.04, 1.0), 0.4, 0.35, 0.0, 1.0),
    ("PV_Lak_zeleny", (0.12, 0.45, 0.45, 1.0), 0.4, 0.35, 0.0, 1.0),
    ("PV_Lak_oranzovy", (0.85, 0.38, 0.05, 1.0), 0.3, 0.40, 0.0, 1.0),
    ("PV_Karton", (0.58, 0.44, 0.26, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("PV_Folia", (0.80, 0.88, 0.95, 1.0), 0.0, 0.15, 0.0, 0.18),
    ("PV_Paleta", (0.72, 0.55, 0.32, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("PV_Pas", (0.90, 0.45, 0.05, 1.0), 0.0, 0.60, 0.0, 1.0),
    ("PV_Siva", (0.40, 0.42, 0.45, 1.0), 0.5, 0.50, 0.0, 1.0),
    ("PV_Kora", (0.30, 0.19, 0.10, 1.0), 0.0, 0.95, 0.0, 1.0),
    ("PV_Drevo_rez", (0.78, 0.60, 0.38, 1.0), 0.0, 0.85, 0.0, 1.0),
    ("PV_ADR", (1.0, 0.55, 0.02, 1.0), 0.0, 0.50, 0.0, 1.0),
]
(FRAME, STEEL, CHROME, TIRE, RIM, DARK, GLASS, LAMP_OR, LAMP_RED, LAMP_WHITE, RED, WHITE, GALV, ALU, PLY, INT, SEAT, PLAST,
 PAINT_BLUE, PAINT_WHITE, PAINT_RED, PAINT_TEAL, PAINT_ORANGE, CARTON, WRAP, PALLET, STRAP, GRAY, BARK, WOODCUT, ADR_MAT) = range(31)
PART_MAKERS = []
SCENE_BUILDERS = []
DOC_EXTRA = []
CATALOG_EXTRA = []
SIDES_LR = (-1.0, 1.0)
D2R = 0.017453


def clear_collection(coll):
    for sub in [coll] + list(coll.children):
        for obj in list(sub.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0 and mesh.get("pickup_vozik"):
            bpy.data.meshes.remove(mesh)
    for curve in list(bpy.data.curves):
        if curve.users == 0 and curve.name.startswith("Menovka_"):
            bpy.data.curves.remove(curve)


def hub_ring(bm, count, radius, y, r, depth, mat):
    for k in range(count):
        a = 2.0 * math.pi * k / count
        add_cylinder(bm, r, depth, along_y((radius * math.cos(a), y, radius * math.sin(a))), mat, segments=6)


def build_wheel_generic(name, r, width, rim_r, spokes=5, studs=5, tread=24):
    # koleso (pivot v osi, vonkajsia strana +Y, os otacania = Y): pneumatika s dezenom, hlinikovy disk so spicami, matice
    bm = bmesh.new()
    add_ring(bm, r - 0.02, rim_r * 0.92, width, 0.0, TIRE, 16, bev=0.02)
    for k in range(tread):
        a = 2.0 * math.pi * k / tread
        add_box(bm, (0.06, width * 0.78, 0.035), (0.0, 0.0, 0.0), TIRE, bev=0.006,
                frame=Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0.0, 0.0, r - 0.018)))
    add_cylinder(bm, rim_r, 0.02, along_y((0.0, width * 0.5 - 0.03, 0.0)), RIM, segments=16)
    add_cylinder(bm, rim_r * 1.02, width * 0.55, along_y((0.0, width * 0.0, 0.0)), STEEL, segments=16)
    for k in range(spokes):
        a = 2.0 * math.pi * k / spokes
        add_box(bm, (0.05, 0.03, rim_r * 0.82), (0.0, 0.0, 0.0), RIM, bev=0.006,
                frame=Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0.0, width * 0.5 - 0.01, rim_r * 0.46)))
    add_cylinder(bm, rim_r * 0.30, 0.06, along_y((0.0, width * 0.5 - 0.005, 0.0)), STEEL, segments=10)
    hub_ring(bm, studs, rim_r * 0.20, width * 0.5 + 0.02, 0.014, 0.03, CHROME)
    add_cylinder(bm, rim_r * 0.36, 0.14, along_y((0.0, -width * 0.5 + 0.04, 0.0)), DARK, segments=10)
    return finish_mesh(bm, name)


# ---------------------------------------------------------------------------
# Jemnejsie tvary: zrazene hrany s dvoma segmentmi, hladke tienovanie s ostrymi hranami nad 50 st. (pri exporte hrany ako skupiny vyhladenia)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Pneumatiky: telo pneumatiky je OTOCENY PRIEREZ (zaoblene rameno, vypukla bocnica s rebrom pri disku, korunovy dezen, rebra / drazky, rebro na bocnici) a dezenove bloky
# (bahno: sikme stredove bloky + ramenne bloky zalomene na bocnicu; cesta: pozdlzne rebra + ramenne bloky), ochranne rebro pri disku.
# Pneumatika sedi na hrane disku (priruba disku vyciuva von nad bocnicu), ventilok je na disku.
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


def tire_profile(r, w, rim, th, grooves=(), bead=None):
    # polovica prierezu pre y > 0 od uchytu na disku po stred dezenu; grooves = [(y stred, sirka)] pozdlzne drazky hlbky th * 0.7
    hw = w * 0.5
    H = r - rim
    by = hw - 0.05 if bead is None else bead
    rt = r - th
    half = [(by, rim * 0.965), (by + 0.003, rim * 1.012),
            (by + 0.012, rim + 0.075 * H), (by + 0.018, rim + 0.095 * H),          # ochranne rebro pri disku
            (hw * 0.91, rim + 0.24 * H), (hw * 0.985, rim + 0.43 * H), (hw * 1.0 + 0.003, rim + 0.465 * H), (hw * 1.0 + 0.003, rim + 0.535 * H), (hw * 0.985, rim + 0.57 * H), (hw * 0.975, rim + 0.74 * H),
            (hw * 0.90, rt - 0.012), (hw * 0.76, rt - 0.001), (hw * 0.70, rt)]
    for gy, gw in sorted(grooves, reverse=True):
        d = th * 0.75
        half += [(gy + gw * 0.5 + 0.006, rt), (gy + gw * 0.5, rt - d), (gy - gw * 0.5, rt - d), (gy - gw * 0.5 - 0.006, rt)]
    half.append((0.0, rt + 0.003))
    return half


def tire_lug(bm, t, rho, y, size, yaw, tilt, mat, bev):
    frame = Matrix.Rotation(t, 4, "Y") @ Matrix.Translation((0.0, 0.0, rho))
    add_box(bm, size, (0.0, y, 0.0), mat, bev=bev, rotation=(tilt, 0.0, yaw), frame=frame)


def add_tire(bm, r, w, rim, style="road", segs=TIRE_SEGS):
    # pneumatika okolo osi Y (stred v pociatku, symetricka); style: "bahno" (hruby dezen) alebo "cesta" (rebra + ramenne bloky)
    hw = w * 0.5
    th = 0.026 if style == "bahno" else 0.014
    grooves = () if style == "bahno" else ((w * 0.20, 0.018), (-w * 0.20, 0.018))
    half = tire_profile(r, w, rim, th, [g for g in grooves if g[0] > 0.0])
    loop = [(-y, rho) for y, rho in half[:-1]] + [(0.0, half[-1][1])] + half[:-1][::-1]
    tire_revolve(bm, loop, segs, TIRE)
    step = 2.0 * math.pi / segs
    rt = r - th
    if style == "bahno":
        for k in range(segs):
            t = step * k
            tire_lug(bm, t, rt + th * 0.5, w * 0.17, (0.052, 0.085, th), 24.0, 0.0, TIRE, 0.0)
            tire_lug(bm, t + step * 0.5, rt + th * 0.5, -w * 0.17, (0.052, 0.085, th), -24.0, 0.0, TIRE, 0.0)
            for s in (1.0, -1.0):
                tire_lug(bm, t + step * (0.25 if s > 0 else 0.75), r - 0.044, s * hw * 0.84, (0.050, 0.080, 0.046), s * 8.0, -s * 38.0, TIRE, 0.0)
    else:
        for k in range(segs):
            t = step * k
            for s in (1.0, -1.0):
                tire_lug(bm, t + (0.0 if s > 0 else step * 0.5), r - 0.021, s * hw * 0.85, (0.030, 0.036, 0.020), s * 10.0, -s * 34.0, TIRE, 0.0)



def tire_valve(bm, rim, y_out):
    # ventilok na vonkajsej strane disku (kratka trubka s ciapockou), mierne nad prirubou
    t = 0.75
    x, z = rim * 0.80 * math.sin(t), rim * 0.80 * math.cos(t)
    add_cylinder(bm, 0.0085, 0.032, along_y((x, y_out - 0.002, z)), STEEL, segments=8)
    add_cylinder(bm, 0.0065, 0.020, along_y((x, y_out + 0.020, z)), CHROME, segments=8)


DOC_EXTRA.extend(["", "PNEUMATIKY (Pv_pk_pneu pickup, Pv_tr_pneu_<polomer> privesy, Pv_auto_koleso): telo je otoceny prierez (zaoblene rameno, vypukla bocnica, ochranne rebro pri disku a rebro na bocnici),",
                  "  pickup ma hruby terenny dezen (sikme stredove bloky a ramenne bloky zalomene na bocnicu), privesy dezen cesta/teren (pozdlzne rebra a male ramenne bloky), kolesa auta na podvale rebra.",
                  "  Disk (pivot v osi, vonkajsia strana +Y) ma prirubu nad bocnicou a ventilok. Pneumatika aj disk su samostatne diely na uchyte koleso_N_<strana>."])


# ---------------------------------------------------------------------------
# Spolocne pomocne funkcie: teleskopicke valce, rifle, lomena drha auta, driver zo svetovej polohy, maly navijak a odtahovane auto
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


def tele_stages(dmin, dmax):
    # dlzka stupna a pocet stupnov teleskopickeho valca pre rozsah vzdialenosti dmin az dmax (stupne sa prekryvaju aspon z 18 %)
    ell = dmin * 0.985
    n = max(2, int(math.ceil((dmax - ell) / (0.82 * ell))) + 1)
    return n, ell


def build_cyl_stage(prefix, k, n, ell, radii):
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
    return finish_mesh(bm, "SM_Pv_valec_%s_%d" % (prefix, k))


def cylinder_family(put, prefix, n, ell, r0):
    radii = [r0 * (1.0 - 0.16 * k) for k in range(n)]
    for k in range(n):
        put(build_cyl_stage(prefix, k, n, ell, radii))


def telescope(coll, name, parts, prefix, n, ell, base_parent, base_pt, aim_parent, aim_pt):
    # teleskopicky valec: prvy stupen na zaklade mieri na ciel, dalsie stupne sa podla vzdialenosti vysuvaju (k-ty o (d - ell) k / (n - 1) po +Z)
    base = new_object(coll, name + "_1", parts["Pv_valec_%s_0" % prefix], base_pt, base_parent)
    aim = empty(coll, name + "_ciel", aim_pt, aim_parent)
    track(base, aim, "TRACK_Z")
    for k in range(1, n):
        stage = new_object(coll, "%s_%d" % (name, k + 1), parts["Pv_valec_%s_%d" % (prefix, k)], (0.0, 0.0, 0.0), base)
        driver(stage, "location", 2, "(d - %.4f) * %.4f" % (ell, k / (n - 1.0)), [("d", "DIST", (base, aim))])
    return base, aim


def diamond(bm, x0, x1, y0, y1, z, mat=STEEL, step=0.13):
    # imitacia rifladeho plechu: radky malych sikmych listiek v obdlzniku (os X - os Y) vo vyske z
    ix = max(1, int((x1 - x0) / step))
    iy = max(1, int((y1 - y0) / step))
    for i in range(ix):
        for j in range(iy):
            x = x0 + (i + 0.5) * (x1 - x0) / ix
            y = y0 + (j + 0.5) * (y1 - y0) / iy
            add_box(bm, (0.055, 0.012, 0.006), (x, y, z + 0.003), mat, rotation=(0.0, 0.0, 45.0 if (i + j) % 2 else -45.0))


def path_point(path, s):
    # bod na lomenej ciare v dlzke obluka s
    acc = 0.0
    for a, b in zip(path, path[1:]):
        seg = (b - a).length
        if acc + seg >= s or b is path[-1]:
            return a + (b - a) * min(1.0, max(0.0, (s - acc) / seg))
        acc += seg
    return path[-1]


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


# maly navijak (pevna cast na prednej stene, buben, lano, hak) - pre podval na auto
def build_pv_winch():
    # pivot na polici v strede, dozadu je -X; buben je zvlast
    bm = bmesh.new()
    add_box(bm, (0.40, 0.46, 0.03), (0.0, 0.0, -0.015), FRAME, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.20, 0.03, 0.20), (0.0, s * 0.19, 0.115), STEEL, bev=0.006)
        add_cylinder(bm, 0.035, 0.05, along_y((0.0, s * 0.205, 0.14)), STEEL, segments=8)
    add_box(bm, (0.13, 0.10, 0.10), (0.02, 0.28, 0.10), DARK, bev=0.01)
    add_cylinder(bm, 0.045, 0.12, along_y((0.0, 0.31, 0.15)), DARK, segments=8, bev=0.004)
    add_cylinder(bm, 0.032, 0.20, along_y((-0.20, 0.0, 0.05)), STEEL, segments=8, bev=0.003)
    for s in SIDES_LR:
        add_box(bm, (0.05, 0.03, 0.08), (-0.20, s * 0.11, 0.05), DARK, bev=0.004)
    add_box(bm, (0.04, 0.04, 0.22), (-0.17, -0.19, 0.12), STEEL, bev=0.004)
    add_cylinder(bm, 0.012, 0.06, along_x((-0.17, -0.19, 0.24)), CHROME, segments=6)
    return finish_mesh(bm, "SM_Pv_navijak")


def build_pv_drum():
    bm = bmesh.new()
    add_cylinder(bm, 0.07, 0.34, along_y((0.0, 0.0, 0.0)), STEEL, segments=12, bev=0.004)
    add_cylinder(bm, 0.085, 0.26, along_y((0.0, 0.0, 0.0)), DARK, segments=12)
    for s in SIDES_LR:
        add_cylinder(bm, 0.11, 0.025, along_y((0.0, s * 0.17, 0.0)), STEEL, segments=12, bev=0.004)
    return finish_mesh(bm, "SM_Pv_navijak_buben")


def build_pv_hook():
    # hak na lane (pivot v oku hore)
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
    return finish_mesh(bm, "SM_Pv_hak")


def build_pv_cable():
    bm = bmesh.new()
    add_cylinder(bm, 0.014, 1.0, along_z((0.0, 0.0, 0.5)), DARK, segments=6)
    return finish_mesh(bm, "SM_Pv_lano")


# odtahovane auto: dva typy podla velkosti podvalu (pivot v strede medzi napravami vo vyske osi, predok +X), kolesa zvlast
PV_CARS = {"4_0": dict(L=3.45, wb=2.30, fo=0.58, w=1.60, h=1.45, rw=0.26, paint=PAINT_ORANGE),
           "5_2": dict(L=4.45, wb=2.65, fo=0.80, w=1.76, h=1.46, rw=0.30, paint=PAINT_TEAL)}


def build_pv_car(size):
    c = PV_CARS[size]
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
    return finish_mesh(bm, "SM_Pv_auto_" + size)


def build_pv_car_wheel(size):
    rw = PV_CARS[size]["rw"]
    bm = bmesh.new()
    add_tire(bm, rw, 0.20, rw * 0.60, "cesta", 20)
    add_cylinder(bm, rw * 0.60, 0.19, along_y((0.0, 0.0, 0.0)), RIM, segments=14)
    add_cylinder(bm, rw * 0.20, 0.22, along_y((0.0, 0.0, 0.0)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Pv_auto_koleso_" + size)


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


def tl(p):
    # bod v suradniciach privesu -> poloha v suradniciach tela (pocitane od vysky gule)
    return (p[0], p[1], p[2] - PK_BALL_Z)


def mount(coll, name, tag, parent, loc, specs):
    # uchyt <name>_uchyt_<tag> (prazdny objekt v pivote dielu) a jeho diely: specs = [(pripona objektu, mesh)]; vrati (uchyt, [objekty])
    sock = empty(coll, "%s_uchyt_%s" % (name, tag), loc, parent)
    sock.empty_display_type = "ARROWS"
    sock.empty_display_size = 0.06
    sock.hide_render = True
    objs = [new_object(coll, "%s_%s" % (name, suffix), mesh, (0.0, 0.0, 0.0), sock) for suffix, mesh in specs]
    return sock, objs


# ---------------------------------------------------------------------------
# Pickup: dvojkabina (4 dvere, kratka korba) a jednokabina (2 dvere, dlha korba). Pociatok = zem pod prednou napravou, predok +X.
# Diely s pivotom v klbe: kapota, dvere, zadne celo korby, volant, nahodne kolesa na napravach (riadenie), tlmice.
# ---------------------------------------------------------------------------

PK_R, PK_TW, PK_TRACK, PK_W = 0.41, 0.30, 0.76, 0.93      # polomer kolesa, sirka pneumatiky, y stredu kolesa, polsirka karoserie
PK_ARCH, PK_FLARE = 0.50, 0.55   # polomer vystrihu blatnika, vonkajsi polomer lemu
BED_Z, BED_TOP = 0.72, 1.16      # podlaha a vrch bokov korby
BAND_Z0, BAND_Z1 = 0.60, 0.99    # cierny pruh na boku (spodok, vrch)
PK_FT = 0.62                    # vrch ramu
PK_BELT, PK_ROOF = 1.12, 1.80   # spodok okien, strecha
PK_WS = -0.20                   # zaklad celneho skla (x)
PK_ROOF_X = -0.62               # predna hrana strechy
PK_HOOD_Z = 1.06                # vrch kapoty pri okne
PK_BALL_Z = 0.45                # vyska gule tazneho zariadenia
PK_FOLLOW = 0.6
PK_RIGS = {}                    # kluc pickupu -> dict(root, body, ball) pre zapriahnutie privesov
PICKUPS = {
    "dvojkabina": dict(name="Pickup_dvojkabina", key="dvojkabina", wb=3.22, cab_back=-2.42, doors=4, paint=PAINT_BLUE, y=0.0),
    "jednokabina": dict(name="Pickup_jednokabina", key="jednokabina", wb=3.10, cab_back=-1.55, doors=2, paint=PAINT_WHITE, y=-6.0),
}


def key_pk(pk):
    return pk["key"]


def pk_rear(pk):
    return -pk["wb"] - 1.06           # os pantov zadneho cela korby (x)


def pk_door_len(pk, kind):
    # dlzka dveri: predne od zavesu -0.30 po stlpik B (-1.26), zadne od -1.30 po zadny stlpik, jednokabina jedny dlhe dvere
    cb = pk["cab_back"]
    if pk["doors"] == 4:
        return 0.96 if kind == "pred" else -1.34 - cb
    return -0.34 - cb


def pk_ball_x(pk):
    return -pk["wb"] - 1.60


def arch_polygon(x0, x1, zb, zt, cx, r=PK_ARCH, n=12):
    # obrys blatnika / boku korby (XZ) s vyrezom kolesa (stred (cx, PK_R), polomer r): x0 = zadok, x1 = predok, spodna hrana zb, horna zt
    zc = PK_R
    half = math.sqrt(max(r * r - (zb - zc) ** 2, 0.0))
    xa, xb = max(cx - half, x0), min(cx + half, x1)
    pts = [(x1, zb), (x1, zt), (x0, zt)]
    if x0 < cx - half:
        pts.append((x0, zb))
    for k in range(n + 1):
        x = xa + (xb - xa) * k / n
        pts.append((x, zc + math.sqrt(max(r * r - (x - cx) ** 2, 0.0))))
    return pts






def build_pk_hood(pk):
    # kapota: pivot na zadnej hrane (x = -0.18, z = vrch pri skle), dopredu +X; stupnovita vypuklina, pod nou tmava izolacia
    p = pk["paint"]
    bm = bmesh.new()
    add_extruded(bm, [(0.0, 0.0), (0.50, -0.02), (1.00, -0.045), (1.12, -0.065), (1.12, -0.14), (0.0, -0.09)], -0.80, 0.80, "XZ", p, bev=0.02)
    add_box(bm, (0.86, 0.50, 0.04), (0.62, 0.0, 0.012), p, bev=0.02, rotation=(0.0, 2.5, 0.0))
    add_box(bm, (0.55, 0.30, 0.03), (0.66, 0.0, 0.038), p, bev=0.014, rotation=(0.0, 2.5, 0.0))
    add_box(bm, (1.04, 1.48, 0.02), (0.58, 0.0, -0.10), DARK, bev=0.004)
    for s in SIDES_LR:
        add_cylinder(bm, 0.02, 0.10, along_y((0.02, s * 0.60, -0.04)), STEEL, segments=8)
    add_box(bm, (0.02, 0.16, 0.05), (1.11, 0.0, -0.10), CHROME, bev=0.003)
    return finish_mesh(bm, "SM_Pv_pk_kapota_" + pk["key"])






def build_pk_wheel_steer():
    # volant: kruh s tromi ramenami a stredom; os otacania = Y (pivot v osi stlpika riadenia)
    bm = bmesh.new()
    add_ring(bm, 0.19, 0.165, 0.035, 0.0, INT, 14, bev=0.006)
    for k in range(3):
        a = 2.0 * math.pi * k / 3.0 + math.pi * 0.5
        add_box(bm, (0.15, 0.025, 0.03), (0.0, 0.0, 0.0), INT, bev=0.004, frame=Matrix.Rotation(a, 4, "Y") @ Matrix.Translation((0.085, 0.0, 0.0)))
    add_cylinder(bm, 0.045, 0.05, along_y((0.0, 0.0, 0.0)), DARK, segments=10, bev=0.006)
    return finish_mesh(bm, "SM_Pv_pk_volant")


def build_pk_door(pk, kind):
    # dvere (lava strana; prava je zrkadlo): pivot na zavese (predna hrana), dvere siahaju do -X; plech, vnutorny panel, cierny pruh, lem blatnika (predne), okno s ramom, kluka; zrkadlo je zvlast
    p = pk["paint"]
    length = pk_door_len(pk, kind)
    pred = kind == "pred"
    cx = 0.30 if pred else None
    bm = bmesh.new()
    zb, zbelt = 0.46, PK_BELT
    add_extruded(bm, door_poly(0.0, -length, zb, zbelt, cx, PK_ARCH), 0.85, 0.93, "XZ", p, bev=0.014)
    add_extruded(bm, door_poly(-0.02, -length + 0.02, zb + 0.03, zbelt - 0.03, cx, PK_ARCH), 0.835, 0.855, "XZ", INT)
    add_extruded(bm, door_poly(0.0, -length, BAND_Z0, BAND_Z1, cx, PK_FLARE), 0.93, 0.944, "XZ", DARK)
    if pred:
        add_extruded(bm, flare_poly(0.30, PK_ARCH, PK_FLARE, xmax=0.0), 0.93, 0.964, "XZ", p, bev=0.01)
    l2 = length - (0.24 if pred else 0.0)
    add_box(bm, (l2, 0.012, 0.12), (-(length - l2) - l2 * 0.5, 0.936, zb + 0.07), PLAST, bev=0.004)
    top = PK_ROOF - 0.08
    front_top = -0.40 if pred else -0.06
    win = [(-0.05, zbelt), (front_top, top), (-length + 0.05, top), (-length + 0.02, zbelt)]
    add_extruded(bm, win, 0.874, 0.886, "XZ", GLASS)
    for a, b in zip(win, win[1:] + win[:1]):
        add_box_between(bm, (a[0], 0.88, a[1]), (b[0], 0.88, b[1]), 0.06, 0.05, DARK, bev=0.012)
    add_box(bm, (0.16, 0.03, 0.04), (-length + 0.20, 0.945, zbelt - 0.07), CHROME, bev=0.01)
    add_cylinder(bm, 0.015, 0.1, along_z((0.0, 0.92, zb + 0.10)), STEEL, segments=8)
    add_cylinder(bm, 0.015, 0.1, along_z((0.0, 0.92, zbelt - 0.10)), STEEL, segments=8)
    return bm




def build_pk_tailgate(pk):
    # zadne celo korby: pivot na spodnom pante (x = pk_rear, z = podlaha), stena stoji nahor; pri otvoreni sa sklopi dozadu o 90 st.
    p = pk["paint"]
    h = BED_TOP - BED_Z - 0.02
    bm = bmesh.new()
    add_box(bm, (0.05, 1.62, h), (-0.03, 0.0, h * 0.5), p, bev=0.018)
    add_box(bm, (0.012, 1.40, h * 0.62), (-0.062, 0.0, h * 0.46), p, bev=0.006)
    add_box(bm, (0.02, 1.30, 0.025), (-0.07, 0.0, 0.10), p, bev=0.004)
    add_box(bm, (0.02, 0.22, 0.06), (-0.068, 0.0, h * 0.70), DARK, bev=0.012)
    add_box(bm, (0.06, 1.62, 0.04), (-0.03, 0.0, h - 0.01), DARK, bev=0.012)
    for s in SIDES_LR:
        add_cylinder(bm, 0.02, 0.10, along_y((0.0, s * 0.76, 0.0)), STEEL, segments=8)
        add_rod(bm, (0.0, s * 0.78, 0.18), (0.0, s * 0.78, 0.36), 0.006, DARK, segments=4)
    return finish_mesh(bm, "SM_Pv_pk_zadne_celo_" + pk["key"])




def build_pk_schodiky(pk):
    # bocny schodik (chrom, od predneho blatnika po koniec kabiny; lavy, pravy je zrkadlo)
    cb = pk["cab_back"]
    bm = bmesh.new()
    x0, x1 = -0.64, cb + 0.20
    add_cylinder(bm, 0.036, x0 - x1, along_x(((x0 + x1) * 0.5, 0.99, 0.40)), CHROME, segments=12)
    add_box(bm, (x0 - x1 - 0.20, 0.10, 0.025), ((x0 + x1) * 0.5, 0.99, 0.38), DARK, bev=0.01)
    for x in (x0 - 0.12, x1 + 0.12, (x0 + x1) * 0.5):
        add_rod(bm, (x, 0.99, 0.40), (x, 0.85, 0.50), 0.018, CHROME, segments=8)
    return bm


def build_pk_axle_front():
    # predna naprava (pivot v osi kolies, z = PK_R): trubka, diferencial, ramena, koncove telesa riadenia
    bm = bmesh.new()
    add_cylinder(bm, 0.05, 1.16, along_y((0.0, 0.0, 0.0)), STEEL, segments=10)
    add_box(bm, (0.30, 0.28, 0.26), (0.0, 0.14, 0.0), DARK, bev=0.04)
    for s in SIDES_LR:
        add_box(bm, (0.12, 0.12, 0.22), (0.0, s * 0.62, 0.0), STEEL, bev=0.01)
        add_box_between(bm, (0.10, s * 0.20, 0.10), (0.10, s * 0.60, -0.02), 0.06, 0.05, STEEL, bev=0.004)
        add_box_between(bm, (-0.28, s * 0.26, 0.24), (-0.06, s * 0.60, 0.06), 0.06, 0.05, STEEL, bev=0.004)
        add_cylinder(bm, 0.015, 0.20, along_z((0.0, s * 0.60, 0.15)), CHROME, segments=6)
    add_rod(bm, (-0.16, -0.60, 0.06), (-0.16, 0.60, 0.06), 0.018, STEEL, segments=6)
    return finish_mesh(bm, "SM_Pv_pk_naprava_predna")


def build_pk_axle_rear():
    # zadna naprava: trubka, diferencial, brzdove bubny; listove pera su zvlast
    bm = bmesh.new()
    add_cylinder(bm, 0.055, 1.50, along_y((0.0, 0.0, 0.0)), STEEL, segments=12)
    add_cylinder(bm, 0.16, 0.26, along_x((0.0, 0.0, 0.0)), DARK, segments=14, bev=0.01)
    for s in SIDES_LR:
        add_cylinder(bm, 0.13, 0.08, along_y((0.0, s * 0.68, 0.0)), DARK, segments=14)
    return finish_mesh(bm, "SM_Pv_pk_naprava_zadna")


def build_pk_shock():
    # tlmic: valec (pivot dole, mieri +Z) a piestnica (pivot hore, mieri -Z)
    bm = bmesh.new()
    add_cylinder(bm, 0.026, 0.24, along_z((0.0, 0.0, 0.12)), DARK, segments=8)
    add_cylinder(bm, 0.032, 0.03, along_z((0.0, 0.0, 0.02)), STEEL, segments=8)
    bm2 = bmesh.new()
    add_cylinder(bm2, 0.014, 0.24, along_z((0.0, 0.0, -0.12)), CHROME, segments=8)
    add_cylinder(bm2, 0.034, 0.03, along_z((0.0, 0.0, -0.02)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Pv_pk_tlmic_valec"), finish_mesh(bm2, "SM_Pv_pk_tlmic_piestnica")


def flare_poly(cx, r_in, r_out, xmin=None, xmax=None, n=12):
    # lem okolo vystrihu kolesa (horny oblukovy od vpredu po vzadu), volitelne orezany v x (xmin: nechaj x >= xmin, xmax: nechaj x <= xmax)
    def span(r):
        t0, t1 = 0.0, math.pi
        if xmax is not None:
            t0 = math.acos(max(-1.0, min(1.0, (xmax - cx) / r)))
        if xmin is not None:
            t1 = math.acos(max(-1.0, min(1.0, (xmin - cx) / r)))
        return t0, t1

    def arc(r, t0, t1):
        return [(cx + r * math.cos(t0 + (t1 - t0) * k / n), PK_R + r * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]

    a0, a1 = span(r_out)
    b0, b1 = span(r_in)
    return arc(r_out, a0, a1) + arc(r_in, b1, b0)


def door_poly(x_front, x_rear, zb, zt, cx, r, n=10):
    # obrys dveri / pruhu (XZ, lokalne od zavesu): predny dolny roh vyrezany podla oblukovya kolesa (stred cx lokalne), ak cx None bez vyrezu
    pts = [(x_rear, zb), (x_rear, zt), (x_front, zt)]
    zc = PK_R
    if cx is not None:
        dx = x_front - cx
        if r * r > dx * dx:
            za = zc + math.sqrt(r * r - dx * dx)
            if za > zb:
                xs = cx - math.sqrt(max(r * r - (zb - zc) ** 2, 0.0))
                pts.append((x_front, min(za, zt)))
                for k in range(1, n + 1):
                    x = x_front + (xs - x_front) * k / n
                    pts.append((x, zc + math.sqrt(max(r * r - (x - cx) ** 2, 0.0))))
                return pts
    pts.append((x_front, zb))
    return pts


def side_y(s, a, b):
    # rozsah y na strane s (a < b v kladnej polovici)
    return (a, b) if s > 0 else (-b, -a)


def build_pk_rollbar(pk):
    # ochranny rollbar za kabinou (ako pri uzitkovych pickupoch): dva stlpy, horna priecka, sikme vzpery k bokom korby, ochranna mriezka pred zadnym oknom
    cb = pk["cab_back"]
    xc = cb - 0.28
    zt = 1.92
    bm = bmesh.new()
    for s in SIDES_LR:
        y = s * 0.86
        add_rod(bm, (xc, y, BED_TOP + 0.02), (xc, y, zt - 0.08), 0.034, ALU, segments=10)
        add_rod(bm, (xc, y, zt - 0.08), (xc, s * 0.78, zt), 0.034, ALU, segments=10)
        add_rod(bm, (xc, y, zt - 0.10), (xc - 1.10, s * 0.88, BED_TOP + 0.02), 0.030, ALU, segments=8)
        add_box(bm, (0.16, 0.12, 0.03), (xc, y, BED_TOP + 0.045), STEEL, bev=0.008)
        add_box(bm, (0.16, 0.12, 0.03), (xc - 1.10, s * 0.88, BED_TOP + 0.045), STEEL, bev=0.008)
        add_rod(bm, (xc, s * 0.20, BED_Z + 0.04), (xc, s * 0.20, 1.55), 0.024, ALU, segments=8)
    add_rod(bm, (xc, -0.78, zt), (xc, 0.78, zt), 0.034, ALU, segments=10)
    add_rod(bm, (xc, -0.86, 1.55), (xc, 0.86, 1.55), 0.026, ALU, segments=8)
    return finish_mesh(bm, "SM_Pv_pk_rollbar_" + pk["key"])








def build_pk_ram(pk):
    # ram: dva podlzniky, priecniky a veze tlmicov
    wb = pk["wb"]
    bm = bmesh.new()
    x0, x1 = 0.85, -wb - 1.00
    xc, ln = (x0 + x1) * 0.5, x0 - x1
    for s in SIDES_LR:
        add_box(bm, (ln, 0.09, 0.14), (xc, s * 0.40, 0.56), FRAME, bev=0.02)
        add_box(bm, (0.10, 0.10, 0.22), (0.55, s * 0.42, 0.70), STEEL, bev=0.012)       # veze tlmicov vpredu
        add_box(bm, (0.06, 0.10, 0.18), (-wb - 0.60, s * 0.42, 0.66), STEEL, bev=0.01)
    for k in range(int(ln / 0.62) + 1):
        add_box(bm, (0.07, 0.80, 0.07), (x0 - 0.15 - 0.62 * k, 0.0, 0.58), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_pk_ram_" + pk["key"])


def build_pk_pohon(pk):
    # pohon: prevodovka, rozdelovacka, kardany
    wb = pk["wb"]
    bm = bmesh.new()
    add_box(bm, (0.70, 0.46, 0.34), (-0.50, 0.0, 0.44), DARK, bev=0.04)
    add_box(bm, (0.40, 0.34, 0.26), (-1.05, 0.0, 0.42), DARK, bev=0.04)
    add_rod(bm, (-1.20, 0.0, 0.42), (-wb, 0.0, 0.42), 0.04, STEEL, segments=10)
    add_rod(bm, (-0.60, 0.0, 0.40), (0.0, 0.0, 0.40), 0.035, STEEL, segments=10)
    return finish_mesh(bm, "SM_Pv_pk_pohon_" + pk["key"])


def build_pk_nadrz(pk):
    bm = bmesh.new()
    add_box(bm, (0.80, 0.52, 0.24), (-pk["wb"] * 0.62, -0.05, 0.40), PLAST, bev=0.05)
    return finish_mesh(bm, "SM_Pv_pk_nadrz_" + pk["key"])


def build_pk_vyfuk(pk):
    wb = pk["wb"]
    bm = bmesh.new()
    add_rod(bm, (-0.50, 0.30, 0.34), (-wb - 0.80, 0.30, 0.32), 0.035, STEEL, segments=10)
    add_cylinder(bm, 0.07, 0.62, along_x((-wb - 0.55, 0.30, 0.30)), STEEL, segments=14)
    add_cylinder(bm, 0.035, 0.12, along_x((-wb - 1.03, 0.30, 0.30)), CHROME, segments=10)
    return finish_mesh(bm, "SM_Pv_pk_vyfuk_" + pk["key"])


def build_pk_kryt(pk):
    bm = bmesh.new()
    add_box(bm, (0.40, 0.84, 0.05), (0.70, 0.0, 0.34), STEEL, bev=0.01)
    return finish_mesh(bm, "SM_Pv_pk_kryt_" + pk["key"])


def build_pk_blatnik(pk):
    # predny blatnik (lava strana; prava je zrkadlo): plech s vyrezom kolesa, cierny pruh, lem, kryt kolesnej skrine, veza tlmica, bocna smerovka
    p = pk["paint"]
    bm = bmesh.new()
    poly = arch_polygon(-0.28, 0.90, 0.46, 1.00, 0.0, PK_ARCH)
    band = arch_polygon(-0.28, 0.90, BAND_Z0, BAND_Z1, 0.0, PK_FLARE)
    flare = flare_poly(0.0, PK_ARCH, PK_FLARE, xmin=-0.28)
    add_extruded(bm, poly, 0.62, 0.93, "XZ", p, bev=0.014)
    add_extruded(bm, band, 0.93, 0.944, "XZ", DARK)
    add_extruded(bm, flare, 0.93, 0.964, "XZ", p, bev=0.01)
    add_box(bm, (0.50, 0.30, 0.04), (0.0, 0.62, 0.99), p, bev=0.012)
    add_box(bm, (0.30, 0.06, 0.20), (-0.11, 0.66, 0.90), DARK, bev=0.01)
    add_box(bm, (0.10, 0.014, 0.04), (0.45, 0.934, 0.80), LAMP_OR, bev=0.004)
    return bm


def build_pk_celny_panel(pk):
    bm = bmesh.new()
    add_box(bm, (0.06, 1.24, 0.54), (0.87, 0.0, 0.73), pk["paint"], bev=0.016)
    return finish_mesh(bm, "SM_Pv_pk_celny_panel_" + pk["key"])


def build_pk_mriezka(pk):
    # mriezka: ram, tmavy vlozok, dve vodorovne a dve zvisle priecky, znak
    p = pk["paint"]
    bm = bmesh.new()
    add_box(bm, (0.05, 1.06, 0.40), (0.925, 0.0, 0.80), p, bev=0.022)
    add_box(bm, (0.03, 0.94, 0.30), (0.945, 0.0, 0.80), DARK, bev=0.01)
    for z in (0.755, 0.845):
        add_box(bm, (0.026, 0.94, 0.03), (0.955, 0.0, z), p, bev=0.006)
    for y in (-0.23, 0.23):
        add_box(bm, (0.026, 0.03, 0.30), (0.955, y, 0.80), p, bev=0.006)
    add_box(bm, (0.026, 0.11, 0.11), (0.965, 0.0, 0.80), CHROME, bev=0.008, rotation=(45.0, 0.0, 0.0))
    return finish_mesh(bm, "SM_Pv_pk_mriezka_" + pk["key"])


def build_pk_svetlomet(pk):
    # predny svetlomet so smerovkou (lava strana; prava je zrkadlo)
    bm = bmesh.new()
    add_box(bm, (0.05, 0.38, 0.38), (0.925, 0.75, 0.80), pk["paint"], bev=0.024)
    add_box(bm, (0.03, 0.31, 0.31), (0.945, 0.75, 0.80), DARK, bev=0.012)
    add_box(bm, (0.016, 0.25, 0.15), (0.962, 0.75, 0.885), LAMP_WHITE, bev=0.01)
    add_box(bm, (0.016, 0.25, 0.07), (0.962, 0.75, 0.715), LAMP_OR, bev=0.008)
    return bm


def build_pk_naraznik_predny(pk):
    # predny naraznik: hlinikovy nosnik, tmavy pas, spodna doska a kryt, SPZ, hmlovky, tazne oka
    bm = bmesh.new()
    add_box(bm, (0.26, 1.92, 0.22), (0.92, 0.0, 0.56), ALU, bev=0.05)
    add_box(bm, (0.04, 1.40, 0.10), (1.05, 0.0, 0.56), DARK, bev=0.015)
    add_box(bm, (0.22, 1.60, 0.10), (0.90, 0.0, 0.41), DARK, bev=0.03)
    add_box(bm, (0.36, 0.90, 0.05), (0.78, 0.0, 0.46), STEEL, bev=0.006)
    add_box(bm, (0.012, 0.52, 0.12), (1.058, 0.0, 0.56), WHITE, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.02, 0.16, 0.08), (1.052, s * 0.72, 0.56), LAMP_WHITE, bev=0.006)
        add_box(bm, (0.08, 0.04, 0.06), (1.06, s * 0.38, 0.42), RED, bev=0.006)
    return finish_mesh(bm, "SM_Pv_pk_naraznik_predny_" + pk["key"])


def build_pk_bullbar(pk):
    # rurova ochrana (bull bar): dva stlpy, horna a stredna priecka, uchytenia k naraznikovi a mriezke
    bm = bmesh.new()
    for s in SIDES_LR:
        add_rod(bm, (1.10, s * 0.50, 0.40), (1.10, s * 0.50, 0.98), 0.034, DARK, segments=12)
        add_rod(bm, (1.10, s * 0.50, 0.50), (1.00, s * 0.50, 0.50), 0.030, DARK, segments=10)
        add_rod(bm, (1.10, s * 0.50, 0.94), (0.96, s * 0.50, 0.90), 0.030, DARK, segments=10)
        add_cylinder(bm, 0.040, 0.05, along_z((1.10, s * 0.50, 0.98)), DARK, segments=12)
    add_rod(bm, (1.10, -0.50, 0.98), (1.10, 0.50, 0.98), 0.034, DARK, segments=12)
    add_rod(bm, (1.10, -0.50, 0.64), (1.10, 0.50, 0.64), 0.028, DARK, segments=10)
    add_box(bm, (0.012, 0.40, 0.12), (1.118, 0.0, 0.56), WHITE, bev=0.004)
    return finish_mesh(bm, "SM_Pv_pk_bullbar_" + pk["key"])


def build_pk_motor(pk):
    # motor, chladic, baterka a nadoby v motorovom priestore
    bm = bmesh.new()
    add_box(bm, (0.60, 0.50, 0.44), (0.30, 0.0, 0.74), FRAME, bev=0.04)
    add_box(bm, (0.30, 0.46, 0.14), (0.30, 0.0, 1.00), DARK, bev=0.02)
    add_box(bm, (0.05, 0.84, 0.50), (0.72, 0.0, 0.76), DARK, bev=0.006)
    add_cylinder(bm, 0.20, 0.06, along_x((0.66, 0.0, 0.76)), STEEL, segments=14)
    add_box(bm, (0.28, 0.20, 0.20), (0.30, 0.46, 0.80), PLAST, bev=0.015)
    add_box(bm, (0.26, 0.17, 0.19), (0.30, -0.47, 0.70), DARK, bev=0.012)
    add_box(bm, (0.04, 0.03, 0.03), (0.38, -0.47, 0.82), RED, bev=0.003)
    return finish_mesh(bm, "SM_Pv_pk_motor_" + pk["key"])


def build_pk_stierace(pk):
    # vodny zlab pod sklom a stieraca
    bm = bmesh.new()
    add_box(bm, (0.18, 1.66, 0.07), (-0.14, 0.0, 1.03), PLAST, bev=0.015)
    for s in SIDES_LR:
        add_rod(bm, (-0.16, s * 0.12, 1.07), (-0.20, s * 0.62, 1.09), 0.008, DARK, segments=4)
    return finish_mesh(bm, "SM_Pv_pk_stierace_" + pk["key"])


def build_pk_kabina(pk):
    # kabina (pevna schranka): podlaha, prahy, vnutorne bocnice, stlpiky A / B / C, palubna doska hore, zadna stena
    p = pk["paint"]
    cb = pk["cab_back"]
    dc = pk["doors"] == 4
    bm = bmesh.new()
    ln = PK_WS - cb
    xc = (PK_WS + cb) * 0.5
    add_box(bm, (ln, 1.70, 0.04), (xc, 0.0, 0.62), INT, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (ln - 0.10, 0.10, 0.14), (xc, s * 0.865, 0.52), p, bev=0.025)
        add_box(bm, (ln - 0.05, 0.02, 0.50), (xc - 0.02, s * 0.825, 0.88), INT, bev=0.004)
        add_box_between(bm, (-0.22, s * 0.855, 1.06), (PK_ROOF_X, s * 0.83, PK_ROOF - 0.04), 0.075, 0.07, p, bev=0.025)
        if dc:
            add_box(bm, (0.075, 0.075, PK_ROOF - 1.06), (-1.28, s * 0.855, (PK_ROOF + 1.06) * 0.5 - 0.02), p, bev=0.02)
        add_box_between(bm, (cb + 0.02, s * 0.85, 1.12), (cb + 0.14 if dc else cb + 0.12, s * 0.83, PK_ROOF - 0.04), 0.09, 0.07, p, bev=0.025)
    add_box(bm, (0.30, 1.70, 0.06), (-0.40, 0.0, 1.04), p, bev=0.02)
    add_box(bm, (0.06, 1.70, 0.62), (cb - 0.02, 0.0, 1.43), p, bev=0.02)
    return finish_mesh(bm, "SM_Pv_pk_kabina_" + pk["key"])


def build_pk_strecha(pk):
    # strecha: priecny rez s mierne klenutym vrchom a zaoblenymi hranami, vnutorny strop
    p = pk["paint"]
    cb = pk["cab_back"]
    bm = bmesh.new()
    roof = [(-0.88, 1.74), (-0.88, 1.775), (-0.82, 1.797), (-0.40, 1.808), (0.40, 1.808), (0.82, 1.797), (0.88, 1.775), (0.88, 1.74)]
    add_extruded_yz(bm, roof, cb - 0.04, PK_ROOF_X + 0.03, p, bev=0.012)
    add_box(bm, (PK_ROOF_X - cb, 1.62, 0.02), ((PK_ROOF_X + cb) * 0.5, 0.0, PK_ROOF - 0.07), INT)
    return finish_mesh(bm, "SM_Pv_pk_strecha_" + pk["key"])


def build_pk_sklo_predne(pk):
    bm = bmesh.new()
    add_box_between(bm, (-0.23, 0.0, 1.07), (PK_ROOF_X + 0.02, 0.0, PK_ROOF - 0.05), 1.52, 0.014, GLASS)
    return finish_mesh(bm, "SM_Pv_pk_sklo_predne_" + pk["key"])


def build_pk_sklo_zadne(pk):
    cb = pk["cab_back"]
    bm = bmesh.new()
    add_box(bm, (0.012, 1.20, 0.32), (cb + 0.012, 0.0, 1.56), GLASS)
    add_box(bm, (0.02, 1.26, 0.38), (cb + 0.005, 0.0, 1.56), DARK, bev=0.01)
    return finish_mesh(bm, "SM_Pv_pk_sklo_zadne_" + pk["key"])


def build_pk_lista(pk):
    # svetelna lista na streche (4 svetlomety na ramciku s nohami)
    xb = PK_ROOF_X - 0.14
    bm = bmesh.new()
    add_box(bm, (0.18, 1.12, 0.04), (xb, 0.0, PK_ROOF + 0.05), ALU, bev=0.014)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.06, 0.07), (xb, s * 0.52, PK_ROOF + 0.015), STEEL, bev=0.01)
    for k in range(4):
        y = -0.42 + 0.28 * k
        add_box(bm, (0.12, 0.22, 0.16), (xb, y, PK_ROOF + 0.15), DARK, bev=0.035)
        add_box(bm, (0.014, 0.17, 0.11), (xb + 0.066, y, PK_ROOF + 0.15), LAMP_WHITE, bev=0.01)
    return finish_mesh(bm, "SM_Pv_pk_lista_" + pk["key"])


def build_pk_palubka(pk):
    # palubna doska: horna a spodna cast, sapy vetrania, displej, pristroje
    bm = bmesh.new()
    add_box(bm, (0.34, 1.62, 0.26), (-0.36, 0.0, 0.88), INT, bev=0.03)
    add_box(bm, (0.22, 1.40, 0.10), (-0.30, 0.0, 1.02), INT, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.20, 0.30, 0.20), (-0.27, s * 0.62, 1.04), DARK, bev=0.015)
    add_box(bm, (0.04, 0.30, 0.18), (-0.20, 0.0, 1.00), DARK, bev=0.008)
    add_box(bm, (0.04, 0.34, 0.14), (-0.50, 0.38, 1.02), DARK, bev=0.008)
    return finish_mesh(bm, "SM_Pv_pk_palubka_" + pk["key"])


def build_pk_sedadla(pk):
    # sedadla, stredova konzola, radiaca paka, pedale
    cb = pk["cab_back"]
    dc = pk["doors"] == 4
    bm = bmesh.new()
    for s in SIDES_LR:
        add_box(bm, (0.50, 0.46, 0.12), (-0.88, s * 0.40, 0.68), SEAT, bev=0.03)
        add_box_between(bm, (-1.10, s * 0.40, 0.72), (-1.22, s * 0.40, 1.28), 0.46, 0.12, SEAT, bev=0.03)
        add_box(bm, (0.08, 0.28, 0.16), (-1.26, s * 0.40, 1.40), SEAT, bev=0.02)
    add_box(bm, (0.80, 0.22, 0.26), (-0.88, 0.0, 0.76), INT, bev=0.03)
    add_rod(bm, (-0.62, 0.0, 0.90), (-0.60, 0.0, 1.10), 0.014, STEEL, segments=6)
    add_cylinder(bm, 0.03, 0.05, along_z((-0.60, 0.0, 1.12)), DARK, segments=10)
    if dc:
        add_box(bm, (0.50, 1.50, 0.12), (-1.88, 0.0, 0.68), SEAT, bev=0.03)
        add_box_between(bm, (-2.10, 0.0, 0.72), (-2.22, 0.0, 1.22), 1.50, 0.12, SEAT, bev=0.03)
        for k in (-0.46, 0.0, 0.46):
            add_box(bm, (0.08, 0.28, 0.16), (-2.26, k, 1.34), SEAT, bev=0.02)
    else:
        add_box_between(bm, (cb + 0.10, 0.0, 0.70), (cb + 0.10, 0.0, 1.10), 1.50, 0.10, SEAT, bev=0.02)
    for s in SIDES_LR:
        add_box(bm, (0.30, 0.20, 0.03), (-0.62, s * 0.30, 0.64), DARK, bev=0.004)
    return finish_mesh(bm, "SM_Pv_pk_sedadla_" + pk["key"])


def build_pk_mirror(pk):
    # vonkajsie zrkadlo na dverach (lava strana; prava je zrkadlo): pivot v zavese dveri, rameno, telo zrkadla a sklo
    bm = bmesh.new()
    zbelt = PK_BELT
    add_box(bm, (0.10, 0.16, 0.03), (-0.14, 0.99, zbelt + 0.06), DARK, bev=0.008)
    add_box(bm, (0.08, 0.20, 0.22), (-0.18, 1.09, zbelt + 0.15), pk["paint"], bev=0.03)
    add_box(bm, (0.012, 0.17, 0.19), (-0.224, 1.09, zbelt + 0.15), GLASS)
    return bm


def build_pk_podlaha(pk):
    # podlaha korby: plast, vlozka, listy a priecniky pod podlahou
    x1 = pk["cab_back"] - 0.05
    x0 = pk_rear(pk)
    ln, xc = x1 - x0, (x1 + x0) * 0.5
    bm = bmesh.new()
    add_box(bm, (ln, 1.62, 0.04), (xc, 0.0, BED_Z), PLAST, bev=0.008)
    add_box(bm, (ln - 0.02, 1.54, 0.012), (xc, 0.0, BED_Z + 0.026), DARK)
    for k in range(int(ln / 0.14)):
        add_box(bm, (0.035, 1.54, 0.012), (x1 - 0.12 - 0.14 * k, 0.0, BED_Z + 0.033), DARK)
    for k in range(int(ln / 0.55) + 1):
        add_box(bm, (0.08, 1.50, 0.06), (x1 - 0.20 - 0.55 * k, 0.0, BED_Z - 0.05), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_pk_podlaha_" + pk["key"])


def build_pk_bok(pk):
    # bok korby (lavy; pravy je zrkadlo): plech s vyrezom kolesa, cierny pruh, lem, horna lista, zalisky, kotviace oka
    p = pk["paint"]
    wb = pk["wb"]
    x1 = pk["cab_back"] - 0.05
    x0 = pk_rear(pk)
    ln, xc = x1 - x0, (x1 + x0) * 0.5
    bm = bmesh.new()
    add_extruded(bm, arch_polygon(x0, x1, 0.46, BED_TOP, -wb, PK_ARCH), 0.81, 0.93, "XZ", p, bev=0.012)
    add_extruded(bm, arch_polygon(x0, x1, BAND_Z0, BAND_Z1, -wb, PK_FLARE), 0.93, 0.944, "XZ", DARK)
    add_extruded(bm, flare_poly(-wb, PK_ARCH, PK_FLARE), 0.93, 0.964, "XZ", p, bev=0.01)
    add_box(bm, (ln, 0.15, 0.05), (xc, 0.87, BED_TOP + 0.012), p, bev=0.022)
    for k in range(3):
        add_box(bm, (0.14, 0.012, 0.05), (x1 - 0.30 - 0.50 * k, 0.944, BED_TOP - 0.10), DARK, bev=0.005)
    for z in (x1 - 0.20, x0 + 0.20):
        add_box(bm, (0.05, 0.03, 0.06), (z, 0.80, BED_Z + 0.12), STEEL, bev=0.006)
    return bm


def build_pk_naboj(pk):
    # vnutorny naboj kolesa v korbe (lavy; pravy je zrkadlo)
    bm = bmesh.new()
    add_box(bm, (0.86, 0.26, 0.26), (-pk["wb"], 0.68, BED_Z + 0.13), PLAST, bev=0.05)
    return bm


def build_pk_celo(pk):
    # celna stena korby s hornou listou
    x1 = pk["cab_back"] - 0.05
    bm = bmesh.new()
    add_box(bm, (0.06, 1.70, BED_TOP - BED_Z + 0.02), (x1, 0.0, (BED_TOP + BED_Z) * 0.5 + 0.01), pk["paint"], bev=0.014)
    add_box(bm, (0.05, 1.64, 0.05), (x1 - 0.03, 0.0, BED_TOP + 0.012), DARK, bev=0.012)
    return finish_mesh(bm, "SM_Pv_pk_celo_" + pk["key"])


def build_pk_naraznik_zadny(pk):
    # zadny naraznik: hlinikovy nosnik, stupacka s protismykovymi listami, SPZ, odrazky
    xr = pk_rear(pk)
    bm = bmesh.new()
    add_box(bm, (0.26, 1.88, 0.20), (xr - 0.19, 0.0, 0.60), ALU, bev=0.045)
    add_box(bm, (0.24, 0.80, 0.03), (xr - 0.20, 0.0, 0.715), DARK, bev=0.008)
    for k in range(6):
        add_box(bm, (0.02, 0.70, 0.01), (xr - 0.20 - 0.07 + 0.04 * k, 0.0, 0.73), STEEL)
    add_box(bm, (0.012, 0.52, 0.12), (xr - 0.325, 0.0, 0.60), WHITE, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.04, 0.05), (xr - 0.32, s * 0.88, 0.45), RED, bev=0.005)
        add_box(bm, (0.012, 0.12, 0.05), (xr - 0.322, s * 0.80, 0.64), RED, bev=0.003)
    return finish_mesh(bm, "SM_Pv_pk_naraznik_zadny_" + pk["key"])


def build_pk_svetlo_zadne(pk):
    # vysoke koncove svetlo na rohu korby (lave; prave je zrkadlo): puzdro, cervene, oranzove a biele sklo
    xr = pk_rear(pk)
    bm = bmesh.new()
    add_box(bm, (0.04, 0.13, 0.36), (xr - 0.02, 0.865, 0.94), DARK, bev=0.02)
    add_box(bm, (0.012, 0.10, 0.22), (xr - 0.045, 0.865, 0.99), LAMP_RED, bev=0.006)
    add_box(bm, (0.012, 0.10, 0.06), (xr - 0.045, 0.865, 0.83), LAMP_OR, bev=0.004)
    add_box(bm, (0.012, 0.10, 0.05), (xr - 0.045, 0.865, 0.77), LAMP_WHITE, bev=0.004)
    return bm


def build_pk_tazne(pk):
    # tazne zariadenie: nosnik pod ramom, drziak gule, gula, 7-polova zasuvka, oka retaze
    xr = pk_rear(pk)
    bx = pk_ball_x(pk)
    bm = bmesh.new()
    add_box(bm, (0.92, 0.10, 0.10), (xr - 0.17, 0.0, 0.50), STEEL, bev=0.014)
    add_box(bm, (0.12, 0.10, 0.14), (bx + 0.02, 0.0, 0.43), STEEL, bev=0.014)
    add_cylinder(bm, 0.028, 0.06, along_z((bx, 0.0, PK_BALL_Z - 0.04)), CHROME, segments=14)
    add_cone(bm, 0.028, 0.020, 0.03, along_z((bx, 0.0, PK_BALL_Z + 0.015)), CHROME, segments=14)
    add_cylinder(bm, 0.045, 0.012, along_z((bx, 0.0, PK_BALL_Z - 0.075)), STEEL, segments=14)
    add_cylinder(bm, 0.035, 0.06, along_x((bx + 0.12, 0.22, 0.62)), DARK, segments=12)
    add_cylinder(bm, 0.028, 0.02, along_x((bx + 0.15, 0.22, 0.62)), STEEL, segments=10)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.04, 0.05), (bx + 0.15, s * 0.14, 0.55), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Pv_pk_tazne_" + pk["key"])


def build_pk_zachytavac(pk):
    # zachytavac blata za zadnym kolesom (lavy; pravy je zrkadlo)
    bm = bmesh.new()
    add_box(bm, (0.03, 0.26, 0.30), (-pk["wb"] - 0.47, 0.86, 0.40), PLAST, bev=0.008)
    return bm


def build_pk_pero():
    # listove pero zadnej napravy (pivot v strede peria v osi napravy): styri listy, trmen, strmene
    bm = bmesh.new()
    for k in range(4):
        add_box(bm, (1.10 - 0.12 * k, 0.07, 0.016), (0.0, 0.0, 0.075 + 0.02 * k), STEEL, bev=0.003)
    add_box(bm, (0.10, 0.10, 0.08), (0.0, 0.0, 0.04), STEEL, bev=0.008)
    for dx in (-0.06, 0.06):
        add_rod(bm, (dx, -0.035, 0.10), (dx, -0.035, -0.05), 0.010, STEEL, segments=6)
        add_rod(bm, (dx, 0.035, 0.10), (dx, 0.035, -0.05), 0.010, STEEL, segments=6)
    return finish_mesh(bm, "SM_Pv_pk_pero")


def build_pk_pneu():
    # pneumatika pickupu (pivot v osi, symetricka): vysoka terenna s hrubym bahnom dezenom, vypukla bocnica a ramenne bloky
    bm = bmesh.new()
    add_tire(bm, PK_R, PK_TW, 0.285, "bahno", 24)
    return finish_mesh(bm, "SM_Pv_pk_pneu")


def build_pk_disk():
    # disk pickupu (lavy, vonkajsia strana +Y; pravy je zrkadlo): svetly disk s piatimi masivnymi licami, stred s maticami
    w, rim = PK_TW, 0.285
    bm = bmesh.new()
    add_ring(bm, rim, rim * 0.86, 0.045, w * 0.5 - 0.03, RIM, 22, bev=0.01)
    add_cylinder(bm, rim * 0.88, 0.02, along_y((0.0, w * 0.5 - 0.045, 0.0)), DARK, segments=22)
    for k in range(5):
        a = 2.0 * math.pi * k / 5.0
        ca, sa = math.cos(a), math.sin(a)
        raw = [(-0.040, 0.06), (0.040, 0.06), (0.072, rim * 0.93), (-0.072, rim * 0.93)]
        pts = [(x * ca + z * sa, -x * sa + z * ca) for x, z in raw]
        add_extruded(bm, pts, w * 0.5 - 0.085, w * 0.5 - 0.025, "XZ", RIM, bev=0.008)
    add_cylinder(bm, 0.095, 0.075, along_y((0.0, w * 0.5 - 0.025, 0.0)), RIM, segments=14, bev=0.01)
    for k in range(5):
        a = 2.0 * math.pi * k / 5.0 + math.pi / 5.0
        add_cylinder(bm, 0.014, 0.03, along_y((0.062 * math.cos(a), w * 0.5 + 0.015, 0.062 * math.sin(a))), CHROME, segments=6)
    add_cylinder(bm, 0.11, 0.14, along_y((0.0, -w * 0.5 + 0.04, 0.0)), DARK, segments=12)
    tire_valve(bm, rim, w * 0.5)
    return bm


PK_SINGLE = ("ram", "pohon", "nadrz", "vyfuk", "kryt", "celny_panel", "mriezka", "naraznik_predny", "bullbar", "motor", "stierace", "kabina", "strecha", "sklo_predne",
             "sklo_zadne", "lista", "palubka", "sedadla", "podlaha", "celo", "naraznik_zadny", "tazne", "rollbar")
PK_SIDED = ("blatnik", "svetlomet", "bok", "naboj", "svetlo_zadne", "zachytavac", "schodiky")


def pk_parts(put, put_lr):
    put(build_pk_wheel_steer())
    put(build_pk_axle_front())
    put(build_pk_axle_rear())
    put(build_pk_pero())
    put(build_pk_pneu())
    put_lr(build_pk_disk(), "SM_Pv_pk_disk")
    for m in build_pk_shock():
        put(m)
    for pk in PICKUPS.values():
        for tag in PK_SINGLE:
            put(globals()["build_pk_" + tag](pk))
        for tag in PK_SIDED:
            put_lr(globals()["build_pk_" + tag](pk), "SM_Pv_pk_%s_%s" % (tag, pk["key"]))
        put_lr(build_pk_mirror(pk), "SM_Pv_pk_zrkadlo_" + key_pk(pk))
        put(build_pk_hood(pk))
        put(build_pk_tailgate(pk))
        kinds = ("pred", "zad") if pk["doors"] == 4 else ("pred",)
        for kind in kinds:
            put_lr(build_pk_door(pk, kind), "SM_Pv_pk_dvere_%s_%s" % (kind, pk["key"]))


def pk_rig(coll, pk, parts, mats, y_pos):
    name, key, wb = pk["name"], pk["key"], pk["wb"]
    dc = pk["doors"] == 4
    root = new_object(coll, name, None, (0.0, y_pos, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.0
    set_prop(root, "Riadenie", 0.0, -35.0, 35.0, "Natocenie prednych kolies v stupnoch (+ = dolava)")
    set_prop(root, "Koleso_otocenie", 0.0, 0.0, 100000.0, "Otocenie kolies v stupnoch (rastie pri jazde dopredu, neobmedzene)")
    set_prop(root, "Kapota", 0.0, 0.0, 1.0, "0 = zatvorena, 1 = otvorena (55 st.)")
    set_prop(root, "Zadne_celo", 0.0, 0.0, 1.0, "0 = zatvorene, 1 = sklopene dozadu (90 st.)")
    door_props = [("Dvere_pred_L", "pred", 1.0), ("Dvere_pred_P", "pred", -1.0)] + ([("Dvere_zad_L", "zad", 1.0), ("Dvere_zad_P", "zad", -1.0)] if dc else [])
    for pn, kind, s in door_props:
        set_prop(root, pn, 0.0, 0.0, 1.0, "Dvere: 0 = zatvorene, 1 = otvorene (72 st.)")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    tf = empty(coll, name + "_teren_predna", (0.0, 0.0, PK_R), root)
    tr = empty(coll, name + "_teren_zadna", (-wb, 0.0, PK_R), root)
    for t in (tf, tr):
        t.empty_display_type = "PLAIN_AXES"
        t.empty_display_size = 0.3
    body_vars = [("fz", "TRANSFORM", (tf, "LOC_Z")), ("rz", "TRANSFORM", (tr, "LOC_Z")), ("fr", "TRANSFORM", (tf, "ROT_X")), ("rr", "TRANSFORM", (tr, "ROT_X"))]
    axle_f, _ = mount(coll, name, "naprava_predna", root, (0.0, 0.0, PK_R), [("naprava_predna", parts["Pv_pk_naprava_predna"])])
    axle_r, _ = mount(coll, name, "naprava_zadna", root, (-wb, 0.0, PK_R), [("naprava_zadna", parts["Pv_pk_naprava_zadna"])])
    for axle, t in ((axle_f, tf), (axle_r, tr)):
        tv = [("t", "TRANSFORM", (t, "LOC_Z")), ("tr", "TRANSFORM", (t, "ROT_X"))]
        driver(axle, "location", 2, "t", tv)
        driver(axle, "rotation_euler", 0, "tr", tv)
    body = new_object(coll, name + "_karoseria", None, (0.0, 0.0, 0.0), root)
    body.empty_display_size = 0.2
    driver(body, "location", 2, "%.2f * (fz - %.3f)" % (PK_FOLLOW, PK_R), body_vars)
    driver(body, "rotation_euler", 1, "atan(%.2f * (rz - fz) / %.3f)" % (PK_FOLLOW, wb), body_vars)
    driver(body, "rotation_euler", 0, "%.3f * (fr + rr)" % (PK_FOLLOW * 0.35), body_vars)
    o0 = (0.0, 0.0, 0.0)
    for tag in PK_SINGLE:
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_pk_%s_%s" % (tag, key)])])
    for tag in PK_SIDED:
        for side in ("L", "P"):
            mount(coll, name, "%s_%s" % (tag, side), body, o0, [("%s_%s" % (tag, side), parts["Pv_pk_%s_%s_%s" % (tag, key, side)])])
    hood, _ = mount(coll, name, "kapota", body, (-0.18, 0.0, PK_HOOD_Z), [("kapota", parts["Pv_pk_kapota_" + key])])
    driver(hood, "rotation_euler", 1, "-h * 0.96", [prop("h", "Kapota")])
    gate, _ = mount(coll, name, "zadne_celo", body, (pk_rear(pk), 0.0, BED_Z + 0.02), [("zadne_celo", parts["Pv_pk_zadne_celo_" + key])])
    driver(gate, "rotation_euler", 1, "-g * 1.5708", [prop("g", "Zadne_celo")])
    for pn, kind, s in door_props:
        side = "L" if s > 0 else "P"
        hinge_x = -0.30 if kind == "pred" else -1.30
        door, _ = mount(coll, name, "dvere_%s_%s" % (kind, side), body, (hinge_x, 0.0, 0.0), [("dvere_%s_%s" % (kind, side), parts["Pv_pk_dvere_%s_%s_%s" % (kind, key, side)])])
        driver(door, "rotation_euler", 2, "%.0f * d * 1.26" % -s, [prop("d", pn)])
        if kind == "pred":
            mount(coll, name, "zrkadlo_" + side, door, (0.0, 0.0, 0.0), [("zrkadlo_" + side, parts["Pv_pk_zrkadlo_%s_%s" % (key, side)])])
    # volant: stlpik riadenia (prazdny objekt natocen osou Y na vodica), volant sa otaca o trojnasobok natocenia kolies
    axis = Vector((-0.90, 0.0, 0.44)).normalized()
    column = empty(coll, name + "_stlpik_riadenia", (-0.64, 0.38, 0.98), body)
    column.rotation_euler = Vector((0.0, 1.0, 0.0)).rotation_difference(axis).to_euler()
    wheel_s, _ = mount(coll, name, "volant", column, (0.0, 0.0, 0.0), [("volant", parts["Pv_pk_volant"])])
    driver(wheel_s, "rotation_euler", 1, "-3.0 * r * %.6f" % D2R, [prop("r", "Riadenie")])
    # pera zadnej napravy, kolesa (pneu + disk na uchyte kolesa) a tlmice
    for s, side in ((1.0, "L"), (-1.0, "P")):
        mount(coll, name, "pero_zadne_" + side, axle_r, (0.0, s * 0.42, 0.0), [("pero_zadne_" + side, parts["Pv_pk_pero"])])
        knuckle = empty(coll, "%s_cap_riadenia_%s" % (name, side), (0.0, s * 0.60, 0.0), axle_f)
        driver(knuckle, "rotation_euler", 2, "r * %.6f" % D2R, [prop("r", "Riadenie")])
        for axle_, tag, loc, parent in (("predne", "koleso_predne_" + side, (0.0, s * (PK_TRACK - 0.60), 0.0), knuckle), ("zadne", "koleso_zadne_" + side, (0.0, s * PK_TRACK, 0.0), axle_r)):
            hub, _ = mount(coll, name, tag, parent, loc, [("pneu_" + tag, parts["Pv_pk_pneu"]), ("disk_" + tag, parts["Pv_pk_disk_" + side])])
            driver(hub, "rotation_euler", 1, "r * %.6f" % D2R, [prop("r", "Koleso_otocenie")])
        link_pair(coll, "%s_tlmic_predny_%s" % (name, side), parts["Pv_pk_tlmic_valec"], parts["Pv_pk_tlmic_piestnica"],
                  axle_f, Vector((0.08, s * 0.50, 0.04)), body, Vector((0.08, s * 0.50, 0.50)), "TRACK_Z", "TRACK_NEGATIVE_Z")
        link_pair(coll, "%s_tlmic_zadny_%s" % (name, side), parts["Pv_pk_tlmic_valec"], parts["Pv_pk_tlmic_piestnica"],
                  axle_r, Vector((-0.10, s * 0.55, 0.04)), body, Vector((-0.10, s * 0.55, 0.50)), "TRACK_Z", "TRACK_NEGATIVE_Z")
    ball = empty(coll, name + "_gula", (pk_ball_x(pk), 0.0, PK_BALL_Z), body)
    ball.empty_display_type = "SPHERE"
    ball.empty_display_size = 0.05
    ball.hide_render = False
    PK_RIGS[key] = dict(root=root, body=body, ball=ball, pk=pk)
    return root, dict(tf=tf, tr=tr)


def animate_pk(pk, root, ter):
    bumps = [(1, 0.0, 0.0), (14, 0.05, 4.0), (28, -0.03, -3.0), (42, 0.06, -5.0), (56, -0.02, 3.0), (70, 0.0, 0.0)]
    for i, t in enumerate((ter["tf"], ter["tr"])):
        delay = 0 if i == 0 else int(round(pk["wb"] * 4.0))
        key(t, "location", 2, [(f + delay, PK_R + z) for f, z, _ in bumps])
        key(t, "rotation_euler", 0, [(f + delay, math.radians(r)) for f, _, r in bumps])

    def keys(prop_name, frames):
        for frame, value in frames:
            root[prop_name] = value
            root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)

    keys("Koleso_otocenie", [(1, 0.0), (300, 3600.0)])
    keys("Riadenie", [(1, 0.0), (90, 0.0), (130, 30.0), (170, -30.0), (210, 0.0)])
    keys("Kapota", [(1, 0.0), (230, 0.0), (260, 1.0), (300, 1.0), (330, 0.0)])
    keys("Dvere_pred_L", [(1, 0.0), (340, 0.0), (370, 1.0), (440, 1.0), (470, 0.0)])
    keys("Dvere_pred_P", [(1, 0.0), (350, 0.0), (380, 1.0), (450, 1.0), (480, 0.0)])
    if pk["doors"] == 4:
        keys("Dvere_zad_L", [(1, 0.0), (390, 0.0), (420, 1.0), (460, 1.0), (490, 0.0)])
        keys("Dvere_zad_P", [(1, 0.0), (400, 0.0), (430, 1.0), (470, 1.0), (500, 0.0)])
    keys("Zadne_celo", [(1, 0.0), (500, 0.0), (530, 1.0), (580, 1.0), (610, 0.0)])


def pk_scene(coll, parts, mats):
    roots = []
    for pk in PICKUPS.values():
        root, ter = pk_rig(child_collection(coll, pk["name"]), pk, parts, mats, pk["y"])
        animate_pk(pk, root, ter)
        roots.append(root)
    return roots


def _pk_doc():
    lines = ["", "PICKUP (Pickup_dvojkabina: 4 dvere, kratka korba; Pickup_jednokabina: 2 dvere, dlha korba; pociatok = zem pod prednou napravou, predok +X, lava strana +Y):"]
    for pk in PICKUPS.values():
        lines.append("  %s: rozvor %.2f m, dlzka od predneho narazniku (x = 0.96) po zadny naraznik (x = %.2f) %.2f m, sirka %.2f m, vyska strechy %.2f m, kabina po x = %.2f, korba %.2f m, gula tazneho zariadenia v (%.2f, 0, %.2f), rozchod %.2f m, kolesa R %.2f" % (
            pk["name"], pk["wb"], pk_rear(pk) - 0.32, 0.96 - (pk_rear(pk) - 0.32), 2.0 * PK_W + 0.12, PK_ROOF, pk["cab_back"], pk_rear(pk) - pk["cab_back"] + 0.05,
            pk_ball_x(pk), PK_BALL_Z, 2.0 * PK_TRACK, PK_R))
    lines += [
        "  Kostra: root (<Pickup>) -> prazdny objekt <Pickup>_karoseria (nasleduje teren: nakloni sa podla predneho a zadneho terenneho objektu a podla ich vysky, PK_FOLLOW 0.6) -> uchyty dielov.",
        "  DEMONTAZ: kazdy diel je samostatny objekt <Pickup>_<diel> na UCHYTE <Pickup>_uchyt_<diel> (prazdny objekt v pivote dielu); animacia je na uchyte. Vymena / oprava: zmaz objekt dielu a novy diel (rovnaky pivot) daj ako dieta uchytu s nulovou polohou.",
        "    Pevne diely karoserie (pivot v pociatku pickupu): ram, pohon (prevodovka, kardany), nadrz, vyfuk, kryt (spodny kryt motora), celny_panel, mriezka, naraznik_predny, bullbar, motor, stierace, kabina (schranka s podlahou a stlpikmi), strecha, sklo_predne, sklo_zadne, lista (svetelna),",
        "    palubka, sedadla, podlaha (korby), celo (celna stena korby), naraznik_zadny, tazne (gula, drziak, zasuvka), rollbar; po stranach (_L / _P): blatnik, svetlomet, bok (bok korby), naboj (naboj kolesa v korbe), svetlo_zadne, zachytavac (blata), schodiky.",
        "  Pohyblive diely: kapota (pivot na zadnej hrane (-0.18, 0, 1.06), rotacia Y o -Kapota x 55 st.), zadne_celo (pivot na spodnom pante, rotacia Y o -Zadne_celo x 90 st.), dvere_pred_L / _P a dvere_zad_L / _P (pivot na zavese, predne -0.30, zadne -1.30, rotacia Z o -/+ Dvere_xxx x 72 st.),",
        "    zrkadlo_L / _P (dieta uchytu dveri, pohybuje sa s nimi), volant (uchyt na stlpiku riadenia, toci sa o trojnasobok Riadenia).",
        "  Naprava predna / zadna (uchyt <Pickup>_uchyt_naprava_predna / _zadna) sa hybe podla terennych prazdnych objektov <Pickup>_teren_predna / _zadna; zadne pera (pero_zadne_L / _P) su deti zadnej napravy; tlmice (valec + piestnica) mieria na seba medzi naprava a karoseriou.",
        "  Kolesa: uchyt koleso_predne_L / _P je dieta prazdneho objektu <Pickup>_cap_riadenia_L / _P (otacanie o Riadenie, os Z), uchyt koleso_zadne_L / _P je dieta zadnej napravy; kazdy nesie pneu (pneumatika) a disk (L / _P je zrkadlo) a toci sa okolo Y podla Koleso_otocenie.",
        "  Prazdny objekt <Pickup>_gula (na karoserii, vo vyske gule tazneho zariadenia): privesy ho citaju vo svetovych suradniciach (driver) a naklonaju sa okolo gule.",
        "  Vlastnosti na koreni: Riadenie (-35 az 35), Koleso_otocenie (kumulativne stupne), Kapota, Zadne_celo, Dvere_pred_L, Dvere_pred_P, Dvere_zad_L, Dvere_zad_P (0 az 1). Animacia 1 az 610: jazda s nerovnostami, riadenie, kapota, dvere, zadne celo.",
    ]
    return lines


DOC_EXTRA.extend(_pk_doc())
PART_MAKERS.append(pk_parts)
SCENE_BUILDERS.append(pk_scene)
CATALOG_EXTRA.append(("PICKUP - SPOLOCNE", ["Pv_pk_volant", "Pv_pk_naprava_predna", "Pv_pk_naprava_zadna", "Pv_pk_pero", "Pv_pk_pneu", "Pv_pk_disk_L", "Pv_pk_tlmic_valec", "Pv_pk_tlmic_piestnica"]))
for _pk in PICKUPS.values():
    _k = _pk["key"]
    CATALOG_EXTRA.append(("PICKUP %s - KAROSERIA" % _k.upper(), ["Pv_pk_%s_%s" % (p, _k) for p in PK_SINGLE] + ["Pv_pk_kapota_" + _k, "Pv_pk_zadne_celo_" + _k]))
    CATALOG_EXTRA.append(("PICKUP %s - STRANY A DVERE" % _k.upper(), ["Pv_pk_%s_%s_L" % (p, _k) for p in PK_SIDED] + ["Pv_pk_zrkadlo_%s_L" % _k] +
                          ["Pv_pk_dvere_%s_%s_L" % (kd, _k) for kd in (("pred", "zad") if _pk["doors"] == 4 else ("pred",))]))


# ---------------------------------------------------------------------------
# Spolocne diely a zaklad riggu pre privesy (vozik, podval na auto, vozik na palety, cisterna, drevo, skrina).
# Pociatok privesu = zem pod stredom gule, predok +X, privesok ide do -X. Telo privesu sa otaca okolo gule (prazdny objekt vo vyske gule),
# naprava sa pohybuje podla terenu a telo sa nakloni medzi gulou a naprava. Koleso otacanie = vlastnost Koleso_otocenie.
# VSETKO JE DEMONTOVATELNE: kazdy diel je samostatny objekt na svojom UCHYTE (prazdny objekt <Privesok>_uchyt_<diel>), animacia je na uchyte, nie na dieli.
# Diel vymenis tak, ze zmazes objekt <Privesok>_<diel> a novy objekt (rovnaky pivot) das za dieta uchytu - animacia ostane.
# ---------------------------------------------------------------------------

def tr_wheel_code(r, alloy=False, narrow=False):
    return "%d%s%s" % (round(r * 100), "a" if alloy else "", "d" if narrow else "")


def build_tr_pneu(r, alloy=False, narrow=False):
    # pneumatika (pivot v osi kolesa, symetricka): otoceny prierez s vypuklou bocnicou, pozdlzne rebra a ramenne bloky; narrow = uzsia pre dvojmontaz
    w = 0.16 if narrow else (0.20 if alloy else (0.19 if r < 0.34 else 0.21))
    rim = r * (0.70 if alloy else 0.62)
    bm = bmesh.new()
    add_tire(bm, r, w, rim, "cesta", 28)
    return finish_mesh(bm, "SM_Pv_tr_pneu_" + tr_wheel_code(r, alloy, narrow))


def build_tr_disk(r, alloy=False, narrow=False):
    # disk kolesa (lava strana, vonkajsia strana +Y; prava je zrkadlo): ocelovy s prelisom a maticami, alebo hlinikovy s 15 licami
    w = 0.16 if narrow else (0.20 if alloy else (0.19 if r < 0.34 else 0.21))
    rim = r * (0.70 if alloy else 0.62)
    bm = bmesh.new()
    add_ring(bm, rim, rim * 0.90, 0.04, w * 0.5 - 0.03, RIM, 24, bev=0.008)
    add_cylinder(bm, rim * 0.92, 0.02, along_y((0.0, w * 0.5 - 0.045, 0.0)), DARK if alloy else RIM, segments=24)
    if alloy:
        for k in range(15):
            a = 2.0 * math.pi * k / 15
            ca, sa = math.cos(a), math.sin(a)
            raw = [(-0.014, 0.05), (0.014, 0.05), (0.022, rim * 0.93), (-0.022, rim * 0.93)]
            pts = [(x * ca + z * sa, -x * sa + z * ca) for x, z in raw]
            add_extruded(bm, pts, w * 0.5 - 0.075, w * 0.5 - 0.035, "XZ", RIM, bev=0.004)
        add_cylinder(bm, 0.06, 0.07, along_y((0.0, w * 0.5 - 0.03, 0.0)), RIM, segments=14, bev=0.008)
        for k in range(5):
            a = 2.0 * math.pi * k / 5
            add_cylinder(bm, 0.011, 0.03, along_y((0.036 * math.cos(a), w * 0.5, 0.036 * math.sin(a))), CHROME, segments=6)
        tire_valve(bm, rim, w * 0.5)
    else:
        add_ring(bm, rim * 0.70, rim * 0.60, 0.02, w * 0.5 - 0.025, STEEL, 16, bev=0.004)
        add_cylinder(bm, rim * 0.34, 0.05, along_y((0.0, w * 0.5 - 0.03, 0.0)), STEEL, segments=14, bev=0.008)
        for k in range(5):
            a = 2.0 * math.pi * k / 5
            add_cylinder(bm, 0.017, 0.03, along_y((rim * 0.46 * math.cos(a), w * 0.5 - 0.02, rim * 0.46 * math.sin(a))), CHROME, segments=6)
        tire_valve(bm, rim, w * 0.5)
    return bm


def build_tr_naprava(track, name, dual=0.0):
    # naprava (pivot v osi kolies): trubka, dva bubny ulozenia, cepy (pri dvojmontazi dlhsie cez obe kolesa); pera a kolesa su zvlast
    bm = bmesh.new()
    add_cylinder(bm, 0.045, 2.0 * track - 0.20, along_y((0.0, 0.0, 0.0)), STEEL, segments=12)
    for s in SIDES_LR:
        if dual:
            add_cylinder(bm, 0.085, 0.08, along_y((0.0, s * (track - dual - 0.13), 0.0)), DARK, segments=12)
            add_cylinder(bm, 0.055, 2.0 * dual + 0.18, along_y((0.0, s * track, 0.0)), STEEL, segments=10)
        else:
            add_cylinder(bm, 0.085, 0.10, along_y((0.0, s * (track - 0.17), 0.0)), DARK, segments=12)
            add_cylinder(bm, 0.055, 0.08, along_y((0.0, s * (track - 0.095), 0.0)), STEEL, segments=10)
        add_box(bm, (0.09, 0.07, 0.04), (0.0, s * (track - 0.30), 0.045), STEEL, bev=0.008)
    return finish_mesh(bm, name)


def build_tr_pero():
    # listove pero (pivot v osi naprav, v strede peria): tri listy, strmeny, svorka, oka; pripevnuje sa k naprave
    bm = bmesh.new()
    for k in range(3):
        add_box(bm, (0.80 - 0.12 * k, 0.05, 0.014), (0.0, 0.0, 0.058 + 0.018 * k), STEEL, bev=0.003)
    add_box(bm, (0.08, 0.08, 0.05), (0.0, 0.0, 0.030), STEEL, bev=0.006)
    for dx in (-0.05, 0.05):
        add_rod(bm, (dx, -0.04, 0.095), (dx, -0.04, -0.03), 0.009, STEEL, segments=6)
        add_rod(bm, (dx, 0.04, 0.095), (dx, 0.04, -0.03), 0.009, STEEL, segments=6)
    for sx in (-0.41, 0.41):
        add_box(bm, (0.05, 0.05, 0.05), (sx, 0.0, 0.075), DARK, bev=0.006)
    return finish_mesh(bm, "SM_Pv_tr_pero")


def build_tr_fender(r, width):
    # blatnik (lava strana; prava je zrkadlo), pivot v osi kolesa: maly oblukovy kryt len nad horom kolesa (150 az 30 st. nad osou), vonkajsi okraj, priruba na strane -Y
    bm = bmesh.new()
    ro, ri = r + 0.085, r + 0.045
    angles = [150.0 - 120.0 * k / 12.0 for k in range(13)]
    outer = [(ro * math.cos(math.radians(a)), ro * math.sin(math.radians(a))) for a in angles]
    inner = [(ri * math.cos(math.radians(a)), ri * math.sin(math.radians(a))) for a in angles]
    add_extruded(bm, outer + inner[::-1], -width * 0.5, width * 0.5, "XZ", GALV, bev=0.008)
    skirt_i = [((ro - 0.05) * math.cos(math.radians(a)), (ro - 0.05) * math.sin(math.radians(a))) for a in angles]
    add_extruded(bm, outer + skirt_i[::-1], width * 0.5 - 0.02, width * 0.5 + 0.012, "XZ", GALV, bev=0.005)
    for a in (150.0, 30.0):
        add_box(bm, (0.06, width + 0.02, 0.03), (ro * math.cos(math.radians(a)), 0.0, ro * math.sin(math.radians(a))), STEEL, bev=0.008, rotation=(0.0, 90.0 - a, 0.0))
    add_box(bm, (0.26, 0.05, 0.03), (0.0, -width * 0.5 + 0.005, ro - 0.012), STEEL, bev=0.006)      # priruba na strane k telu (vnutorna = -Y)
    return bm


def build_tr_wing(r, length, width):
    # krdlovy blatnik (lava strana; prava je zrkadlo), pivot v osi kolesa: rovna horna plocha so skosenymi koncami, okraj (nad polovicou kolesa)
    bm = bmesh.new()
    top, low = r + 0.055, r - 0.05
    prof = [(-length * 0.5, low - 0.03), (-length * 0.5, low), (-length * 0.5 + 0.16, top), (length * 0.5 - 0.16, top), (length * 0.5, low),
            (length * 0.5, low - 0.03), (length * 0.5 - 0.16, top - 0.03), (-length * 0.5 + 0.16, top - 0.03)]
    add_extruded(bm, prof, -width * 0.5, width * 0.5, "XZ", PAINT_BLUE, bev=0.01)
    lip = [(-length * 0.5 + 0.05, low - 0.02), (-length * 0.5 + 0.16, top - 0.02), (length * 0.5 - 0.16, top - 0.02), (length * 0.5 - 0.05, low - 0.02),
           (length * 0.5 - 0.10, low - 0.06), (-length * 0.5 + 0.10, low - 0.06)]
    add_extruded(bm, lip, width * 0.5 - 0.025, width * 0.5, "XZ", PAINT_BLUE, bev=0.006)
    for k in range(3):
        x = -length * 0.5 + 0.40 + (length - 0.80) * k / 2.0
        add_box(bm, (0.06, 0.05, 0.04), (x, -width * 0.5 + 0.03, top - 0.045), STEEL, bev=0.008)
    add_box(bm, (0.10, 0.012, 0.045), (0.0, width * 0.5 + 0.006, top - 0.07), LAMP_OR, bev=0.004)
    return bm


def build_tr_coupler():
    # spojka privesu (pevna cast, siva): zosikmena hlava s puzdrom pre gulu (stred gule v povodni), vyztuz, zachytna poistka; pakou zvlast
    bm = bmesh.new()
    prof = [(-0.20, -0.055), (0.06, -0.075), (0.17, -0.04), (0.17, 0.035), (0.08, 0.075), (-0.20, 0.06)]
    add_extruded(bm, prof, -0.075, 0.075, "XZ", GRAY, bev=0.018)
    add_cylinder(bm, 0.066, 0.10, along_z((0.0, 0.0, -0.045)), DARK, segments=16, bev=0.006)
    add_box(bm, (0.12, 0.11, 0.05), (-0.10, 0.0, 0.085), GRAY, bev=0.012)
    add_box(bm, (0.05, 0.05, 0.05), (0.15, 0.0, 0.07), STEEL, bev=0.008)
    add_box(bm, (0.03, 0.04, 0.05), (0.14, 0.10, 0.0), DARK, bev=0.006)
    add_cylinder(bm, 0.015, 0.05, along_z((-0.02, 0.0, 0.09)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Pv_tr_spojka")


def build_tr_coupler_lever():
    # paka spojky: pivot na zadnom konci (os Y), paka mieri do +X; pri otvoreni sa zdvihne
    bm = bmesh.new()
    add_box(bm, (0.24, 0.035, 0.022), (0.12, 0.0, 0.0), DARK, bev=0.008)
    add_box(bm, (0.045, 0.075, 0.045), (0.245, 0.0, 0.012), RED, bev=0.014)
    add_cylinder(bm, 0.02, 0.06, along_y((0.0, 0.0, 0.0)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Pv_tr_spojka_paka")


def build_tr_jockey():
    # opierne koleso (pohyblive): pivot v osi kolesa v hornej polohe, trubka ide nahor, vidlica a koleso dole; po zasunuti sa trubka posuva v objimke
    bm = bmesh.new()
    add_cylinder(bm, 0.028, 0.46, along_z((0.0, 0.0, 0.25)), GRAY, segments=12, bev=0.004)
    add_box(bm, (0.05, 0.05, 0.03), (0.0, 0.0, 0.485), GRAY, bev=0.008)
    add_cylinder(bm, 0.036, 0.12, along_z((0.0, 0.0, 0.03)), DARK, segments=12)
    for s in SIDES_LR:
        add_box(bm, (0.03, 0.012, 0.12), (0.0, s * 0.046, -0.01), STEEL, bev=0.004)
    add_cylinder(bm, 0.100, 0.07, along_y((0.0, 0.0, 0.0)), TIRE, segments=16, bev=0.014)
    add_cylinder(bm, 0.060, 0.075, along_y((0.0, 0.0, 0.0)), RIM, segments=10)
    return finish_mesh(bm, "SM_Pv_tr_opierne_koleso")


def build_tr_oje(t):
    # oje (A-rama, siva): dve sikme nosniky z predneho rohu ramu do jedneho jazyka, jazyk, priecna vzpera; pociatok = pociatok privesu
    o = t["oje"]
    z, z0 = o["z"], o.get("z0")
    bm = bmesh.new()
    xt = -0.46
    for s in SIDES_LR:
        add_box_between(bm, (o["xf"] + 0.04, s * o["hw"], z if z0 is None else z0), (xt, s * 0.045, z - 0.04), 0.06, 0.09, GRAY, bev=0.02)
    add_box(bm, (-xt + 0.04, 0.10, 0.09), ((xt + 0.04) * 0.5, 0.0, z - 0.04), GRAY, bev=0.02)
    add_box(bm, (0.14, 0.10, 0.11), (-0.30, 0.0, z - 0.04), GRAY, bev=0.02)
    add_box_between(bm, (o["xf"] + 0.30, -o["hw"] * 0.62, z - 0.01), (o["xf"] + 0.30, o["hw"] * 0.62, z - 0.01), 0.045, 0.055, GRAY, bev=0.012)
    return finish_mesh(bm, "SM_Pv_tr_oje_" + t["key"])


def build_tr_objimka():
    # objimka opierneho kolesa na jazyku (vlavo od jazyka, x = -0.30) s kurbliou; opierne koleso sa v nej posuva
    z = 0.515
    bm = bmesh.new()
    add_box(bm, (0.12, 0.10, 0.16), (-0.30, 0.10, z + 0.02), GRAY, bev=0.015)
    add_box(bm, (0.08, 0.16, 0.04), (-0.30, 0.05, z - 0.02), GRAY, bev=0.01)
    add_rod(bm, (-0.24, 0.16, z + 0.06), (-0.12, 0.16, z + 0.06), 0.010, CHROME, segments=8)
    add_box(bm, (0.04, 0.05, 0.05), (-0.11, 0.16, z + 0.06), DARK, bev=0.008)
    return finish_mesh(bm, "SM_Pv_tr_objimka")


def build_tr_retaze():
    # bezpecnostne retaze (V) s hakmi na jazyku
    z = 0.515
    bm = bmesh.new()
    for s in SIDES_LR:
        add_rod(bm, (-0.38, s * 0.03, z - 0.07), (-0.20, s * 0.13, z - 0.12), 0.007, DARK, segments=5)
        add_rod(bm, (-0.20, s * 0.13, z - 0.12), (0.04, s * 0.11, z - 0.10), 0.007, DARK, segments=5)
        add_box(bm, (0.03, 0.025, 0.04), (0.06, s * 0.11, z - 0.10), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Pv_tr_retaze")


def build_tr_zastrcka():
    # zastrcka svetiel (7-polova) s kabelom k oju
    z = 0.515
    bm = bmesh.new()
    add_box(bm, (0.05, 0.05, 0.07), (-0.16, -0.10, z), DARK, bev=0.01)
    add_rod(bm, (-0.16, -0.10, z - 0.03), (-0.42, -0.04, z - 0.08), 0.008, DARK, segments=5)
    return finish_mesh(bm, "SM_Pv_tr_zastrcka")


def build_tr_zaves(t):
    # uchytenia per na ramu (zaves pred a za naprav pre kazde pero)
    h = t["hang"]
    bm = bmesh.new()
    for x in t["axles"]:
        for s in SIDES_LR:
            for dx in (-0.41, 0.41):
                add_box(bm, (0.10, 0.09, h["h"]), (x + dx, s * t["sy"], h["z"]), STEEL, bev=0.01)
    return finish_mesh(bm, "SM_Pv_tr_zaves_" + t["key"])


def build_tr_konzola(t):
    # konzola blatnika (lava strana; prava je zrkadlo): nosnik od ramu k prirube blatnika, pri nosnikoch aj vzpery nahor; pre kazdu nahradu
    k = t["kons"]
    bm = bmesh.new()
    for x in t["axles"]:
        add_box(bm, (0.20, k["y1"] - k["y0"], 0.05), (x, (k["y0"] + k["y1"]) * 0.5, k["zb"]), t.get("kons_mat", FRAME), bev=0.012)
        if k.get("zt"):
            for dx in (-0.28, 0.28):
                add_rod(bm, (x + dx, k["yr"], k["zb"]), (x + dx, k["yr"], k["zt"]), 0.022, STEEL, segments=8)
    return bm


def build_tr_svetlo():
    # koncove svetlo (lave; prave je zrkadlo; pivot v strede, sklo smeruje do -X): VODOROVNE puzdro s tromi okruhlymi sklami vedla seba (von brzdove cervene, smerovka oranzova, cuvanie biele) a odrazkou
    bm = bmesh.new()
    add_box(bm, (0.05, 0.34, 0.12), (0.0, 0.0, 0.0), DARK, bev=0.025)
    for dy, mat in ((0.115, LAMP_RED), (0.0, LAMP_OR), (-0.115, LAMP_WHITE)):
        add_cylinder(bm, 0.043, 0.014, along_x((-0.028, dy, 0.0)), mat, segments=16, bev=0.003)
    return bm


def build_tr_spz():
    # drziak a znacka (pivot v strede, znacka smeruje do -X) s osvetlenim
    bm = bmesh.new()
    add_box(bm, (0.012, 0.44, 0.14), (0.0, 0.0, 0.0), STEEL, bev=0.004)
    add_box(bm, (0.014, 0.40, 0.12), (-0.006, 0.0, 0.0), WHITE, bev=0.004)
    add_box(bm, (0.03, 0.10, 0.03), (-0.01, 0.0, 0.105), DARK, bev=0.006)
    return finish_mesh(bm, "SM_Pv_tr_spz")


def build_tr_naraznik(t):
    # zadny naraznik (VACSI: hlboky hlinikovy profil so spodnym pasom, zachytne konzoly k ramu, odrazky); pri medzere (gap) je prerusena v strede (napr. pre najazdy)
    b = t["bump"]
    x, w, z = b["x"], b["w"], b["z"]
    bm = bmesh.new()
    gap = b.get("gap")
    spans = [(-w * 0.5, w * 0.5)] if not gap else [(-w * 0.5, -gap[1]), (-gap[0], gap[0]), (gap[1], w * 0.5)]
    for y0, y1 in spans:
        add_box(bm, (0.16, y1 - y0, 0.18), (x + 0.08, (y0 + y1) * 0.5, z), GRAY, bev=0.035)
        add_box(bm, (0.03, y1 - y0 - 0.06, 0.04), (x - 0.005, (y0 + y1) * 0.5, z - 0.065), DARK, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.012, 0.10, 0.05), (x - 0.006, s * (w * 0.5 - 0.40), z + 0.06), RED, bev=0.003)
        add_box(bm, (0.36, 0.08, 0.10), (x + 0.30, s * t["sy"], z - 0.0), GRAY, bev=0.015)
    return finish_mesh(bm, "SM_Pv_tr_naraznik_" + t["key"])


def build_tr_obrysove(t):
    # obrysove svetla (oranzove po stranach, biele vpredu, cervene vzadu): zoznam t["markers"] = (x, y, z, typ)
    bm = bmesh.new()
    for x, y, z, kind in t["markers"]:
        if kind == "or":
            add_box(bm, (0.10, 0.012, 0.045), (x, y, z), LAMP_OR, bev=0.004)
        elif kind == "white":
            add_box(bm, (0.04, 0.06, 0.04), (x, y, z), LAMP_WHITE, bev=0.006)
        else:
            add_box(bm, (0.04, 0.06, 0.04), (x, y, z), RED, bev=0.006)
    return finish_mesh(bm, "SM_Pv_tr_obrysove_" + t["key"])


def tr_type_parts(put, put_lr, t):
    # diely zavisle od typu privesu (oje, zaves, konzola, naraznik, obrysove svetla, naprava)
    put(build_tr_oje(t))
    put(build_tr_zaves(t))
    put_lr(build_tr_konzola(t), "SM_Pv_tr_konzola_" + t["key"])
    put(build_tr_naraznik(t))
    put(build_tr_obrysove(t))
    put(build_tr_naprava(t["track"], "SM_" + ax_key(t["track"], t.get("dual", 0.0)), t.get("dual", 0.0)))
    if t.get("fender") == "wing":
        put_lr(build_tr_wing(t["R"], t["wing"][0], t["wing"][1]), "SM_Pv_tr_kridlo_" + t["key"])


def tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m):
    # spolocny zaklad privesu; vrati dict(root, body, axles, wheels, terrain, name). Typove diely pripoji volajuci k body (cez mount a tl()).
    # ball_src: objekt vo vyske gule (gula pickupu) alebo None -> vlastna staticka gula
    name, R = tr["name"], tr["R"]
    root = new_object(coll, name, None, (x_pos, y_pos, 0.0))
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 1.0
    set_prop(root, "Koleso_otocenie", 0.0, 0.0, 100000.0, "Otocenie kolies v stupnoch (rastie pri jazde dopredu, neobmedzene)")
    set_prop(root, "Opierne_koleso", 0.0, 0.0, 1.0, "Opierne koleso na oji: 0 = vytiahnute (jazda), 1 = spustene na zem")
    set_prop(root, "Spojka", 0.0, 0.0, 1.0, "Paka spojky: 0 = zatvorena (zaistena na gule), 1 = otvorena")

    def prop(var, prop_name):
        return (var, "PROP", (root, '["%s"]' % prop_name))

    if ball_src is None:
        ball_src = empty(coll, name + "_gula_teren", (0.0, 0.0, PK_BALL_Z), root)
        ball_src.empty_display_type = "SPHERE"
        ball_src.empty_display_size = 0.05
        ball_src.hide_render = False
    xs = tr["axles"]
    alloy = tr.get("wheel") == "alloy"
    dual = tr.get("dual", 0.0)
    rk = tr_wheel_code(R, alloy, bool(dual))
    terrains, axles, wheels = [], [], []
    k = PK_R / R
    for i, x in enumerate(xs):
        t = empty(coll, "%s_teren_%d" % (name, i + 1), (x, 0.0, R), root)
        t.empty_display_type = "PLAIN_AXES"
        t.empty_display_size = 0.2
        terrains.append(t)
        sock, objs = mount(coll, name, "naprava_%d" % (i + 1), root, (x, 0.0, R), [("naprava_%d" % (i + 1), parts[ax_key(tr["track"], dual)])])
        tv = [("t", "TRANSFORM", (t, "LOC_Z")), ("tr", "TRANSFORM", (t, "ROT_X"))]
        driver(sock, "location", 2, "t", tv)
        driver(sock, "rotation_euler", 0, "tr", tv)
        axles.append(sock)
        for s, side in ((1.0, "L"), (-1.0, "P")):
            mount(coll, name, "pero_%d_%s" % (i + 1, side), sock, (0.0, s * tr["sy"], 0.0), [("pero_%d_%s" % (i + 1, side), parts["Pv_tr_pero"])])
            for tag, yy in ((("_vnut", s * (tr["track"] - dual)), ("_von", s * (tr["track"] + dual))) if dual else (("", s * tr["track"]),)):
                hub, hobjs = mount(coll, name, "koleso_%d_%s%s" % (i + 1, side, tag), sock, (0.0, yy, 0.0),
                                   [("pneu_%d_%s%s" % (i + 1, side, tag), parts["Pv_tr_pneu_" + rk]), ("disk_%d_%s%s" % (i + 1, side, tag), parts["Pv_tr_disk_%s_%s" % (rk, side)])])
                driver(hub, "rotation_euler", 1, "r * %.6f * %.4f" % (D2R, k), [prop("r", "Koleso_otocenie")])
                wheels.append(hub)
    body = new_object(coll, name + "_telo", None, (0.0, 0.0, PK_BALL_Z), root)
    body.empty_display_type = "ARROWS"
    body.empty_display_size = 0.3
    mean = "(%s) / %d" % (" + ".join("a%d" % i for i in range(len(xs))), len(xs))
    lm = -sum(xs) / len(xs)
    driver_world(body, "location", 2, "bz", [("bz", ball_src, "LOC_Z")])
    driver_world(body, "rotation_euler", 1, "atan((%s - %.3f - (bz - %.3f)) / %.3f)" % (mean, R, PK_BALL_Z, lm), [("bz", ball_src, "LOC_Z")],
                 [("a%d" % i, t, "LOC_Z") for i, t in enumerate(terrains)])
    o0 = tl((0.0, 0.0, 0.0))
    # spolocne pevne diela (kazdy na svojom uchyte v pocitku privesu)
    for tag, key_ in (("oje", "Pv_tr_oje_" + tr["key"]), ("objimka", "Pv_tr_objimka"), ("retaze", "Pv_tr_retaze"), ("zastrcka", "Pv_tr_zastrcka"), ("zaves", "Pv_tr_zaves_" + tr["key"]),
                      ("naraznik", "Pv_tr_naraznik_" + tr["key"]), ("obrysove", "Pv_tr_obrysove_" + tr["key"])):
        mount(coll, name, tag, body, o0, [(tag, parts[key_])])
    mount(coll, name, "spojka", body, tl((0.0, 0.0, 0.48)), [("spojka", parts["Pv_tr_spojka"])])
    lever, _ = mount(coll, name, "spojka_paka", body, tl((-0.10, 0.0, 0.565)), [("spojka_paka", parts["Pv_tr_spojka_paka"])])
    driver(lever, "rotation_euler", 1, "-s * 0.96", [prop("s", "Spojka")])
    jock, _ = mount(coll, name, "opierne_koleso", body, tl((-0.30, 0.16, 0.33)), [("opierne_koleso", parts["Pv_tr_opierne_koleso"])])
    driver(jock, "location", 2, "%.3f - 0.23 * j" % (0.33 - PK_BALL_Z), [prop("j", "Opierne_koleso")])
    # zadne svetla na naraznik, znacka v strede
    b = tr["bump"]
    for s, side in ((1.0, "L"), (-1.0, "P")):
        mount(coll, name, "svetlo_" + side, body, tl((b["x"] - 0.025, s * (b["w"] * 0.5 - 0.20), b["z"])), [("svetlo_" + side, parts["Pv_tr_svetlo_" + side])])
    mount(coll, name, "spz", body, tl((b["x"] - 0.012, 0.0, b["z"] + 0.0)), [("spz", parts["Pv_tr_spz"])])
    # blatniky a ich konzoly
    kind = tr.get("fender", "arc")
    xw = sum(xs) / len(xs)
    for s, side in ((1.0, "L"), (-1.0, "P")):
        mount(coll, name, "konzola_" + side, body, o0, [("konzola_" + side, parts["Pv_tr_konzola_%s_%s" % (tr["key"], side)])])
        if kind == "wing":
            mount(coll, name, "kridlo_" + side, body, tl((xw, s * tr["track"], R)), [("kridlo_" + side, parts["Pv_tr_kridlo_%s_%s" % (tr["key"], side)])])
        else:
            for i, x in enumerate(xs):
                mount(coll, name, "blatnik_%d_%s" % (i + 1, side), body, tl((x, s * tr["track"], R)),
                      [("blatnik_%d_%s" % (i + 1, side), parts["Pv_tr_blatnik_%d_%s" % (round(R * 100), side)])])
    return dict(root=root, body=body, axles=axles, wheels=wheels, terrains=terrains, prop=prop, ball=ball_src, name=name)


def tr_keys(root, prop_name, frames):
    # klucovanie vlastnosti na koreni po snimkach
    for frame, value in frames:
        root[prop_name] = value
        root.keyframe_insert(data_path='["%s"]' % prop_name, frame=frame)


def tr_animate(tr, r, delay_m, jock=None, lever=None):
    # terenne nerovnosti pre naprave, otacanie kolies, opierne koleso (zdvihnute pocas jazdy) a spojka; jock / lever = vlastne kluce
    root, k = r["root"], PK_R / tr["R"]
    bumps = [(1, 0.0, 0.0), (14, 0.05, 4.0), (28, -0.03, -3.0), (42, 0.06, -5.0), (56, -0.02, 3.0), (70, 0.0, 0.0)]
    for t, x in zip(r["terrains"], tr["axles"]):
        delay = int(round((delay_m - x) * 4.0))
        key(t, "location", 2, [(f + delay, tr["R"] + 0.7 * z) for f, z, _ in bumps])
        key(t, "rotation_euler", 0, [(f + delay, math.radians(0.7 * a)) for f, _, a in bumps])
    tr_keys(root, "Koleso_otocenie", [(1, 0.0), (300, 3600.0 * k)])
    tr_keys(root, "Opierne_koleso", jock or [(1, 0.0), (730, 0.0), (760, 1.0), (790, 1.0), (820, 0.0)])
    tr_keys(root, "Spojka", lever or [(1, 0.0), (700, 0.0), (725, 1.0), (850, 1.0), (870, 0.0)])


TR_FENDER_W = 0.24
TRAILERS = {}              # typ -> (slovnik variantov, funkcia riggu); registruju moduly vozik / podval / ...


def ax_key(track, dual=0.0):
    return "Pv_tr_naprava_%d%s" % (int(round(track * 100 + 1e-6)), "d" if dual else "")


def tr_parts(put, put_lr):
    put(build_tr_coupler())
    put(build_tr_coupler_lever())
    put(build_tr_jockey())
    put(build_tr_objimka())
    put(build_tr_retaze())
    put(build_tr_zastrcka())
    put(build_tr_pero())
    put_lr(build_tr_svetlo(), "SM_Pv_tr_svetlo")
    put(build_tr_spz())
    for r in (0.28, 0.30, 0.31):
        put(build_tr_pneu(r))
        put_lr(build_tr_disk(r), "SM_Pv_tr_disk_%d" % round(r * 100))
        put_lr(build_tr_fender(r, TR_FENDER_W), "SM_Pv_tr_blatnik_%d" % round(r * 100))
    put(build_tr_pneu(0.30, True))
    put_lr(build_tr_disk(0.30, True), "SM_Pv_tr_disk_30a")
    put(build_tr_pneu(0.30, True, True))
    put_lr(build_tr_disk(0.30, True, True), "SM_Pv_tr_disk_30ad")


def _tr_doc():
    return ["", "PRIVESY - SPOLOCNY ZAKLAD A DEMONTAZ (vozik, podval na auto, vozik na palety, cisterna, drevo, skrina):",
            "  Pociatok privesu = zem pod stredom gule (x = 0), predok +X, privesok ide do -X, gula je vo vyske %.2f m. Koren (<Privesok>) nesie vlastnosti Koleso_otocenie, Opierne_koleso, Spojka (+ vlastnosti typu)." % PK_BALL_Z,
            "  Telo (<Privesok>_telo, prazdny objekt vo vyske gule) sa otaca okolo gule (os Y): jeho vyska = svetova vyska gule (pri zapriahnuti objekt <Pickup>_gula, inak staticka gula) a sklon = atan((priemerna vyska naprav - polomer - (vyska gule - %.2f)) / vzdialenost naprav od gule)." % PK_BALL_Z,
            "  DEMONTAZ: kazdy diel je samostatny objekt <Privesok>_<diel> a je detom UCHYTU <Privesok>_uchyt_<diel> (prazdny objekt v pivote dielu). Animacia (otacanie, posun, sklapanie) je na UCHYTE, nie na dieli.",
            "    Vymena / oprava: zmaz objekt dielu (uchyt nechaj), novy diel (mesh s rovnakym pivotom) daj ako dieta uchytu s nulovou polohou - animacia a poloha ostanu. Pevne diela maju pivot v pociatku privesu (zem pod gulou), pohyblive v klbe / osi.",
            "    Spolocne diela kazdeho privesu: oje, objimka, retaze, zastrcka, spojka, spojka_paka, opierne_koleso, zaves (uchytenia per), naprava_N, pero_N_L / _P, koleso_N_L / _P (= pneu + disk), blatnik_N_L / _P (alebo kridlo_L / _P),",
            "    konzola_L / _P (nosnik blatnika), naraznik, svetlo_L / _P (zadne svetla su na naraznik), spz, obrysove. Typove diela (ram, podlaha, bocnice, ...) su popisane pri kazdom privesu.",
            "  Naprava (uchyt <Privesok>_uchyt_naprava_N) sa hybe podla terenneho prazdneho objektu <Privesok>_teren_N (kluce nerovnosti, oneskorene podla vzdialenosti od gule); pera a kolesa su deti naprav.",
            "  Koleso: uchyt koleso_N_L / _P (os Y, otacanie podla Koleso_otocenie x pomer polomerov pickupu a privesu) nesie dva diely: pneu (pneumatika) a disk (disk L / _P je zrkadlo). Blatniky kryju kolesa len nad osou (najviac po polovicu kolesa).",
            "  Spojka: pevna hlava (Pv_tr_spojka, puzdro pre gulu v povodni) a paka (pivot na zadnom konci, rotacia Y o -Spojka x 55 st.). Opierne koleso: trubka s kolesom sa posuva o -0.23 x Opierne_koleso po Z v objimke na oji."]


DOC_EXTRA.extend(_tr_doc())
PART_MAKERS.append(tr_parts)
CATALOG_EXTRA.append(("PRIVESY - SPOLOCNE", ["Pv_tr_spojka", "Pv_tr_spojka_paka", "Pv_tr_opierne_koleso", "Pv_tr_objimka", "Pv_tr_retaze", "Pv_tr_zastrcka", "Pv_tr_pero", "Pv_tr_svetlo_L", "Pv_tr_spz",
                                              "Pv_tr_pneu_28", "Pv_tr_pneu_30", "Pv_tr_pneu_30a", "Pv_tr_pneu_31",
                                              "Pv_tr_disk_28_L", "Pv_tr_disk_30_L", "Pv_tr_disk_30a_L", "Pv_tr_disk_31_L",
                                              "Pv_tr_blatnik_28_L", "Pv_tr_blatnik_30_L", "Pv_tr_blatnik_31_L"]))


# ---------------------------------------------------------------------------
# Maly vozik (privesny vozik na naradie, zahradu, odpad): jedna naprava, nizke bocnice, sklapacie zadne celo, oje s opiernym kolesom a spojkou, svetla na zadnom naraznik.
# Dve velkosti: Vozik_2_0 (podlaha 2.0 x 1.2 m) a Vozik_2_6 (2.6 x 1.4 m).
# Demontovatelne diely (uchyty <Vozik>_uchyt_<diel>): ram, podlaha, celna_stena, bocnica_L / _P, zadne_celo + spolocne (oje, naprava, pera, kolesa, blatniky, naraznik, svetla ...).
# ---------------------------------------------------------------------------

VOZIKY = {
    "2_0": dict(key="2_0", name="Vozik_2_0", Ld=2.00, Wd=1.20, h=0.40, R=0.28),
    "2_6": dict(key="2_6", name="Vozik_2_6", Ld=2.60, Wd=1.40, h=0.45, R=0.28),
}
VZ_XF = -1.02          # predna hrana podlahy
VZ_ZF = 0.60           # horny povrch podlahy


def vz_geo(v):
    xr = VZ_XF - v["Ld"]
    xax = VZ_XF - v["Ld"] * 0.52
    track = v["Wd"] * 0.5 + 0.045 + TR_FENDER_W * 0.5
    sy = v["Wd"] * 0.5 - 0.06
    return dict(xr=xr, xax=xax, track=track, sy=sy)


def vz_tr(v):
    g = vz_geo(v)
    Wd, h = v["Wd"], v["h"]
    return dict(name=v["name"], key="vz_" + v["key"], R=v["R"], axles=[g["xax"]], track=g["track"], sy=g["sy"],
                oje=dict(xf=VZ_XF, hw=g["sy"], z=0.515), hang=dict(z=0.46, h=0.07),
                kons=dict(y0=Wd * 0.5 + 0.03, y1=g["track"] - 0.10, zb=0.62), kons_mat=STEEL,
                bump=dict(x=g["xr"] - 0.07, w=Wd + 0.50, z=0.50),
                markers=[(VZ_XF - v["Ld"] * 0.5, k * (Wd * 0.5 + 0.038), VZ_ZF + h * 0.80, "or") for k in SIDES_LR] +
                        [(VZ_XF + 0.015, k * (Wd * 0.5 + 0.02), VZ_ZF + h + 0.05, "white") for k in SIDES_LR] +
                        [(VZ_XF + 0.015, k * (Wd * 0.5 + 0.02), VZ_ZF + 0.06, "red") for k in SIDES_LR])


def build_vz_frame(v):
    # ram: dva podlzniky a priecniky (nosne), bez oje, naprav a svetiel
    g = vz_geo(v)
    Wd, Ld, xr = v["Wd"], v["Ld"], g["xr"]
    bm = bmesh.new()
    xc = (VZ_XF + xr) * 0.5
    for s in SIDES_LR:
        add_box(bm, (Ld + 0.08, 0.07, 0.11), (xc, s * g["sy"], 0.515), FRAME, bev=0.02)
    for k in range(int(Ld / 0.55) + 1):
        add_box(bm, (0.06, Wd - 0.04, 0.07), (VZ_XF - 0.10 - 0.55 * k, 0.0, 0.50), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_vz_ram_" + v["key"])


def build_vz_floor(v):
    # podlaha: preglejka s priecnymi listami
    g = vz_geo(v)
    Wd, Ld = v["Wd"], v["Ld"]
    bm = bmesh.new()
    add_box(bm, (Ld, Wd, 0.03), ((VZ_XF + g["xr"]) * 0.5, 0.0, VZ_ZF - 0.015), PLY, bev=0.008)
    for k in range(int(Ld / 0.20)):
        add_box(bm, (0.018, Wd - 0.02, 0.008), (VZ_XF - 0.10 - 0.20 * k, 0.0, VZ_ZF + 0.002), DARK)
    return finish_mesh(bm, "SM_Pv_vz_podlaha_" + v["key"])


def build_vz_front(v):
    # celna stena: plech s rebrami, horna lista, zachyty bocnic
    Wd, h = v["Wd"], v["h"]
    bm = bmesh.new()
    add_box(bm, (0.04, Wd + 0.08, h + 0.10), (VZ_XF + 0.02, 0.0, VZ_ZF + (h + 0.10) * 0.5), GALV, bev=0.014)
    for fz in (0.3, 0.6):
        add_box(bm, (0.012, Wd - 0.10, 0.04), (VZ_XF + 0.046, 0.0, VZ_ZF + (h + 0.10) * fz), GALV, bev=0.006)
    add_box(bm, (0.06, Wd + 0.10, 0.04), (VZ_XF + 0.02, 0.0, VZ_ZF + h + 0.11), ALU, bev=0.014)
    return finish_mesh(bm, "SM_Pv_vz_celna_" + v["key"])


def build_vz_side(v):
    # bocnica (lava strana; prava je zrkadlo): plech s rebrami, horna lista, stlpiky, zachyt zadneho cela
    g = vz_geo(v)
    Wd, Ld, h, xr = v["Wd"], v["Ld"], v["h"], g["xr"]
    xc = (VZ_XF + xr) * 0.5
    yb = Wd * 0.5 + 0.015
    bm = bmesh.new()
    add_box(bm, (Ld + 0.04, 0.03, h), (xc, yb, VZ_ZF + h * 0.5), GALV, bev=0.012)
    for fz in (0.30, 0.62):
        add_box(bm, (Ld - 0.16, 0.012, 0.035), (xc, Wd * 0.5 + 0.036, VZ_ZF + h * fz), GALV, bev=0.006)
    add_box(bm, (Ld + 0.06, 0.055, 0.04), (xc, yb, VZ_ZF + h + 0.01), ALU, bev=0.016)
    for k in range(4):
        x = VZ_XF - 0.05 - (Ld - 0.10) * k / 3.0
        add_box(bm, (0.045, 0.05, h + 0.03), (x, yb, VZ_ZF + h * 0.5 + 0.005), STEEL, bev=0.01)
    add_box(bm, (0.04, 0.05, 0.05), (xr + 0.02, yb, VZ_ZF + h * 0.5), STEEL, bev=0.008)
    return bm


def build_vz_gate(v):
    # zadne celo: pivot na spodnom pante (x = zadna hrana podlahy, z = podlaha), stoji nahor, sklapa sa dozadu o 90 st.
    Wd, h = v["Wd"], v["h"]
    bm = bmesh.new()
    add_box(bm, (0.03, Wd - 0.01, h - 0.01), (-0.016, 0.0, h * 0.5 + 0.005), GALV, bev=0.012)
    for fz in (0.30, 0.62):
        add_box(bm, (0.012, Wd - 0.18, 0.035), (-0.036, 0.0, h * fz), GALV, bev=0.006)
    add_box(bm, (0.05, Wd + 0.02, 0.04), (-0.016, 0.0, h - 0.01), ALU, bev=0.016)
    for s in SIDES_LR:
        add_cylinder(bm, 0.018, 0.08, along_y((0.0, s * (Wd * 0.5 - 0.06), 0.0)), STEEL, segments=10)
        add_box(bm, (0.03, 0.05, 0.05), (0.01, s * (Wd * 0.5 + 0.005), h - 0.03), STEEL, bev=0.008)
    return finish_mesh(bm, "SM_Pv_vz_zadne_celo_" + v["key"])


def vz_parts(put, put_lr):
    for v in VOZIKY.values():
        tr_type_parts(put, put_lr, vz_tr(v))
        put(build_vz_frame(v))
        put(build_vz_floor(v))
        put(build_vz_front(v))
        put_lr(build_vz_side(v), "SM_Pv_vz_bocnica_" + v["key"])
        put(build_vz_gate(v))


def vz_rig(coll, v, parts, mats, ball_src, x_pos, y_pos, delay_m):
    g = vz_geo(v)
    tr = vz_tr(v)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, name, prop = r["root"], r["body"], v["name"], r["prop"]
    set_prop(root, "Zadne_celo", 0.0, 0.0, 1.0, "Zadne celo: 0 = zatvorene, 1 = sklopene dozadu (90 st.)")
    o0 = tl((0.0, 0.0, 0.0))
    for tag in ("ram", "podlaha", "celna"):
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_vz_%s_%s" % (tag, v["key"])])])
    for side in ("L", "P"):
        mount(coll, name, "bocnica_" + side, body, o0, [("bocnica_" + side, parts["Pv_vz_bocnica_%s_%s" % (v["key"], side)])])
    gate, _ = mount(coll, name, "zadne_celo", body, tl((g["xr"], 0.0, VZ_ZF)), [("zadne_celo", parts["Pv_vz_zadne_celo_" + v["key"]])])
    driver(gate, "rotation_euler", 1, "-g * 1.5708", [prop("g", "Zadne_celo")])
    tr_animate(tr, r, delay_m)
    tr_keys(root, "Zadne_celo", [(1, 0.0), (600, 0.0), (630, 1.0), (690, 1.0), (720, 0.0)])
    return r


def _vz_doc():
    lines = ["", "MALY VOZIK (Vozik_2_0, Vozik_2_6; privesny vozik s jednou napravou, pociatok = zem pod stredom gule, predok +X, vozik ide do -X):"]
    for v in VOZIKY.values():
        g = vz_geo(v)
        lines.append("  %s: podlaha %.2f x %.2f m, bocnice %.2f m, prednak podlahy x = %.2f, zadna hrana x = %.2f, naprava x = %.2f, rozchod %.2f m (kolesa R %.2f)" % (
            v["name"], v["Ld"], v["Wd"], v["h"], VZ_XF, g["xr"], g["xax"], g["track"] * 2.0, v["R"]))
    lines += [
        "  Typove diely (uchyt <Vozik>_uchyt_<diel>, objekt <Vozik>_<diel>): ram, podlaha, celna (celna stena), bocnica_L / _P, zadne_celo (pivot na spodnom pante, rotacia Y o -Zadne_celo x 90 st.).",
        "  Spolocne diely: oje, objimka, retaze, zastrcka, spojka, spojka_paka, opierne_koleso, zaves, naprava_1, pero_1_L / _P, koleso_1_L / _P (pneu + disk), blatnik_1_L / _P, konzola_L / _P, naraznik, svetlo_L / _P (na naraznik), spz, obrysove.",
    ]
    return lines


TRAILERS["vozik"] = (VOZIKY, vz_rig)
PART_MAKERS.append(vz_parts)
DOC_EXTRA.extend(_vz_doc())
CATALOG_EXTRA.append(("MALY VOZIK", ["Pv_vz_%s_%s" % (p, v) for v in VOZIKY for p in ("ram", "podlaha", "celna", "zadne_celo")] + ["Pv_vz_bocnica_%s_%s" % (v, s) for v in VOZIKY for s in ("L", "P")] +
                      ["Pv_tr_oje_vz_%s" % v for v in VOZIKY] + ["Pv_tr_zaves_vz_%s" % v for v in VOZIKY] + ["Pv_tr_konzola_vz_%s_L" % v for v in VOZIKY] +
                      ["Pv_tr_naraznik_vz_%s" % v for v in VOZIKY] + ["Pv_tr_obrysove_vz_%s" % v for v in VOZIKY] + [ax_key(vz_geo(v)["track"]) for v in VOZIKY.values()]))


# ---------------------------------------------------------------------------
# Podval na auto (privesny podvalnik): PEVNA riesetkova paluba na ramu a dva vysuvne najazdy. Najazdy lezia pod palubou; vysunu sa dozadu a sklopia na zem,
# maly navijak s lanom a hakom na prednej stene vytiahne auto po najazdoch na palubu. Dve velkosti: Podval_auto_4_0 (paluba 4.0 m, jedna naprava)
# a Podval_auto_5_2 (5.2 m, tandem). Zadne svetla su na zadnom naraznik (rozdelenom, aby sa najazdy mali kde sklopit).
# Demontovatelne diely (uchyty <Podval>_uchyt_<diel>): ram, paluba, vedenie, zabradlie_L / _P, najazd_L / _P, celna_stena, drziak_rezervy, rezerva, navijak, buben, hak, lano + spolocne.
# ---------------------------------------------------------------------------

PD_XF = -1.50         # predna hrana paluby
PD_ZB, PD_ZT = 0.59, 0.68        # spodok a vrch paluby
PD_HALF = 0.93        # polsirka paluby (vonkajsi okraj bocneho nosnika)
PD_HR = 0.45          # vyska celnej steny
PD_TRACK, PD_SY = 1.14, 0.28     # y stredu kolies, y podlzniku ramu
PD_RY = 0.63          # y stredu najazdu
PD_RW = 0.46          # sirka najazdu
PD_RT = 0.06          # hrubka najazdu
PODVALY = {
    "4_0": dict(key="4_0", name="Podval_auto_4_0", Lb=4.00, Lr=2.40, R=0.30, axles=[-3.70]),
    "5_2": dict(key="5_2", name="Podval_auto_5_2", Lb=5.20, Lr=2.60, R=0.30, axles=[-4.15, -5.25]),
}


def pd_geo(p):
    # rozmery a uhol sklopenia najazdu: spodna hrana konca najazdu sa dotkne zeme
    Lb, lr = p["Lb"], p["Lr"]
    xf, xr = PD_XF, PD_XF - Lb
    zh = PD_ZB - 0.005
    th = 0.2
    for _ in range(60):
        th = math.asin(min(0.9, (zh - PD_RT * math.cos(th)) / lr))
    return dict(xf=xf, xr=xr, zb=PD_ZB, zt=PD_ZT, zh=zh, lr=lr, theta=th, lip=0.30)


def pd_tr(p):
    xs = p["axles"]
    xw = sum(xs) / len(xs)
    g = pd_geo(p)
    zt = PD_ZT
    return dict(name=p["name"], key="pd_" + p["key"], R=p["R"], axles=xs, track=PD_TRACK, sy=PD_SY, wheel="alloy", dual=0.09, fender="wing", wing=((max(xs) - min(xs)) + 0.70, 0.38),
                oje=dict(xf=PD_XF, hw=PD_SY, z=0.515, z0=0.53), hang=dict(z=0.43, h=0.07),
                kons=dict(y0=PD_SY - 0.01, y1=1.00, zb=0.43, zt=0.64, yr=0.97), kons_mat=PAINT_BLUE,
                bump=dict(x=g["xr"] - 0.08, w=2.62, z=0.50, gap=(0.34, 0.90)),
                markers=[(PD_XF - 0.9, k * (PD_HALF + 0.006), PD_ZB + 0.06, "or") for k in SIDES_LR] + [(g["xr"] + g["lip"] + 0.2, k * (PD_HALF + 0.006), PD_ZB + 0.06, "or") for k in SIDES_LR] +
                        [(g["xr"] + 0.12, k * (PD_HALF + 0.006), PD_ZB + 0.05, "red") for k in SIDES_LR])


def build_pd_chassis(p):
    # pevny podvozok (modry): dva podlzniky a priecniky pod palubou
    g = pd_geo(p)
    bm = bmesh.new()
    x_rear = g["xr"] + 0.10
    xc, ln = (PD_XF + x_rear) * 0.5, PD_XF - x_rear
    for s in SIDES_LR:
        add_box(bm, (ln, 0.07, 0.12), (xc, s * PD_SY, 0.53), PAINT_BLUE, bev=0.02)
    for k in range(int(ln / 0.80) + 1):
        add_box(bm, (0.06, 2 * PD_SY - 0.07, 0.07), (PD_XF - 0.15 - 0.80 * k, 0.0, 0.50), PAINT_BLUE, bev=0.015)
    add_box(bm, (0.06, 2 * PD_SY - 0.07, 0.08), (x_rear, 0.0, 0.50), PAINT_BLUE, bev=0.015)
    return finish_mesh(bm, "SM_Pv_pd_ram_" + p["key"])


def pd_zs(g, x):
    # vrch paluby v mieste x: rovno, na zadnom konci nabeh (lip)
    return g["zh"] + (g["zt"] - g["zh"]) * max(0.0, min(1.0, (x - g["xr"]) / g["lip"]))


def build_pd_deck(p):
    # paluba (modra, riesetkova, pevna): bocne nosniky, dva pasy z priecnych latiek na pozdlznych nosnikoch, stredny plech vpredu, priecniky pod nou, zadny nabeh, upinacie oka
    g = pd_geo(p)
    xr, xf, zb, zt, lip = g["xr"], g["xf"], g["zb"], g["zt"], g["lip"]
    bm = bmesh.new()
    side = [(xr, zb), (xf, zb), (xf, zt + 0.035), (xr + lip, zt + 0.035), (xr, zb + 0.04)]
    inner = [(xr + lip, zb), (xf, zb), (xf, zt - 0.022), (xr + lip, zt - 0.022)]
    for s in SIDES_LR:
        ya, yb = side_y(s, PD_HALF - 0.05, PD_HALF)
        add_extruded(bm, side, ya, yb, "XZ", PAINT_BLUE, bev=0.025)
        yc, yd = side_y(s, 0.38, 0.44)
        add_extruded(bm, inner, yc, yd, "XZ", PAINT_BLUE, bev=0.012)
        ye, yf = side_y(s, 0.64, 0.68)
        add_extruded(bm, inner, ye, yf, "XZ", PAINT_BLUE, bev=0.01)
        yg, yh = side_y(s, 0.40, PD_HALF - 0.05)
        add_extruded(bm, [(xr, zb), (xr + lip, zb), (xr + lip, zt), (xr, g["zh"])], yg, yh, "XZ", PAINT_BLUE, bev=0.01)
    x = xr + lip + 0.06
    while x < xf - 0.08:
        for s in SIDES_LR:
            add_box(bm, (0.05, 0.48, 0.022), (x, s * 0.64, zt - 0.011), PAINT_BLUE, bev=0.008)
        x += 0.088
    add_box(bm, (1.45, 0.76, 0.022), (xf - 0.775, 0.0, zt - 0.011), PAINT_BLUE, bev=0.01)
    xs = xr + 0.55
    while xs < xf - 0.1:
        add_box(bm, (0.06, 2 * PD_HALF - 0.06, 0.05), (xs, 0.0, zb + 0.025), PAINT_BLUE, bev=0.01)
        xs += 0.62
    for s in SIDES_LR:
        for k in range(3):
            add_box(bm, (0.12, 0.03, 0.04), (xr + lip + 0.6 + (xf - xr - lip - 1.4) * k / 2.0, s * (PD_HALF + 0.012), zt), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Pv_pd_paluba_" + p["key"])


def build_pd_guides(p):
    # vedenie najazdov pod palubou: dve koleje na kazdy najazd (zachytne listy) a zarazka vpredu
    g = pd_geo(p)
    xr, zb, lr = g["xr"], g["zb"], g["lr"]
    bm = bmesh.new()
    for s in SIDES_LR:
        for y in (PD_RY - PD_RW * 0.5 - 0.015, PD_RY + PD_RW * 0.5 + 0.015):
            add_box(bm, (lr + 0.05, 0.03, 0.05), (xr + (lr + 0.05) * 0.5, s * y, zb - 0.025), GRAY, bev=0.008)
        add_box(bm, (0.04, PD_RW + 0.06, 0.05), (xr + lr + 0.05, s * PD_RY, zb - 0.025), GRAY, bev=0.008)
    return finish_mesh(bm, "SM_Pv_pd_vedenie_" + p["key"])


def build_pd_rails(p):
    # rurove zabradlie (lava strana; prava je zrkadlo): dva stlpiky a horna trubka s rohmi
    g = pd_geo(p)
    xf, zt = g["xf"], g["zt"]
    bm = bmesh.new()
    ya = PD_HALF - 0.02
    x1, x2 = xf - 0.22, xf - 1.55
    zt0 = zt + 0.035
    for xx in (x1, x2):
        add_rod(bm, (xx, ya, zt0), (xx, ya, zt0 + 0.26), 0.018, STEEL, segments=10)
        add_box(bm, (0.07, 0.07, 0.02), (xx, ya, zt0 + 0.01), STEEL, bev=0.008)
    add_rod(bm, (x1, ya, zt0 + 0.26), (x1 - 0.07, ya, zt0 + 0.33), 0.018, STEEL, segments=10)
    add_rod(bm, (x2, ya, zt0 + 0.26), (x2 + 0.07, ya, zt0 + 0.33), 0.018, STEEL, segments=10)
    add_rod(bm, (x1 - 0.07, ya, zt0 + 0.33), (x2 + 0.07, ya, zt0 + 0.33), 0.018, STEEL, segments=10)
    return bm


def build_pd_ramp(p):
    # najazd (pivot na hornom konci, v osi najazdu, na hornom povrchu; najazd siaha do -X): dva bocne nosniky, stredny nosnik a priecne latky, skoseny koniec na zem, drziak na tahanie
    g = pd_geo(p)
    lr = g["lr"]
    bm = bmesh.new()
    prof = [(0.0, -PD_RT), (0.0, 0.015), (-lr + 0.25, 0.015), (-lr, -0.045), (-lr, -PD_RT)]
    for s in SIDES_LR:
        ya, yb = side_y(s, PD_RW * 0.5 - 0.05, PD_RW * 0.5)
        add_extruded(bm, prof, ya, yb, "XZ", PAINT_BLUE, bev=0.012)
    add_extruded(bm, [(0.0, -PD_RT), (0.0, 0.0), (-lr + 0.25, 0.0), (-lr, -0.045), (-lr, -PD_RT)], -0.025, 0.025, "XZ", PAINT_BLUE, bev=0.008)
    slope = -math.degrees(math.atan2(0.045, 0.25))
    x = -0.06
    while x > -lr + 0.02:
        if x > -lr + 0.25:
            add_box(bm, (0.05, PD_RW - 0.10, 0.022), (x, 0.0, -0.011), PAINT_BLUE, bev=0.008)
        else:
            zz = -0.045 * (-lr + 0.25 - x) / 0.25
            add_box(bm, (0.05, PD_RW - 0.10, 0.022), (x, 0.0, zz - 0.011), PAINT_BLUE, bev=0.008, rotation=(0.0, -slope, 0.0))
        x -= 0.088
    add_box(bm, (0.05, PD_RW, 0.03), (-0.025, 0.0, -0.02), STEEL, bev=0.008)                 # horny zachyt
    add_rod(bm, (-lr + 0.04, -0.14, -0.035), (-lr + 0.04, 0.14, -0.035), 0.013, STEEL, segments=8)   # drziak na vytahovanie
    return finish_mesh(bm, "SM_Pv_pd_najazd_" + p["key"])


def build_pd_rack():
    # celna stena paluby (nizka, modra, s mriezkou): pivot v strede prednej hrany paluby na hornej strane (dozadu je -X); polica pre navijak
    bm = bmesh.new()
    hr = PD_HR
    for s in SIDES_LR:
        add_box(bm, (0.07, 0.07, hr), (-0.035, s * (PD_HALF - 0.05), hr * 0.5), PAINT_BLUE, bev=0.02)
        add_box(bm, (0.16, 0.09, 0.04), (-0.08, s * (PD_HALF - 0.05), 0.02), STEEL, bev=0.008)
    add_box(bm, (0.07, 2 * PD_HALF - 0.04, 0.07), (-0.035, 0.0, hr), PAINT_BLUE, bev=0.02)
    add_box(bm, (0.06, 2 * PD_HALF - 0.12, 0.10), (-0.03, 0.0, 0.06), PAINT_BLUE, bev=0.015)
    add_box(bm, (0.05, 2 * PD_HALF - 0.12, 0.04), (-0.025, 0.0, hr * 0.52), PAINT_BLUE, bev=0.01)
    for k in range(-5, 6):
        add_rod(bm, (-0.03, k * 0.16, 0.10), (-0.03, k * 0.16, hr - 0.03), 0.011, STEEL, segments=6)
    add_box(bm, (0.42, 0.50, 0.03), (-0.22, 0.0, hr + 0.015), GRAY, bev=0.008)
    for s in SIDES_LR:
        add_extruded(bm, [(-0.02, hr), (-0.40, hr), (-0.02, hr - 0.28)], s * 0.22 - 0.015, s * 0.22 + 0.015, "XZ", GRAY, bev=0.004)
        add_box(bm, (0.07, 0.14, 0.05), (-0.03, s * (PD_HALF - 0.30), hr + 0.05), LAMP_OR, bev=0.008)
    return finish_mesh(bm, "SM_Pv_pd_celna_stena")


def build_pd_spare_mount():
    # drziak rezervneho kolesa na prednej strane celnej steny (dve dosky, pivot ako celna stena)
    bm = bmesh.new()
    add_box(bm, (0.04, 0.40, 0.04), (0.02, 0.0, 0.10), GRAY, bev=0.008)
    add_box(bm, (0.04, 0.40, 0.04), (0.02, 0.0, 0.46), GRAY, bev=0.008)
    add_rod(bm, (0.04, 0.0, 0.10), (0.12, 0.0, 0.30), 0.012, STEEL, segments=6)
    add_rod(bm, (0.04, 0.0, 0.46), (0.12, 0.0, 0.30), 0.012, STEEL, segments=6)
    return finish_mesh(bm, "SM_Pv_pd_drziak_rezervy")


def pd_rail_path(g, car):
    # stredy osi kolies auta pri vytahovani: zem -> sklopeny najazd (skosenie, rovna cast) -> nabeh paluby -> paluba (offset povrchu o polomer kolesa); body (x, z) v suradniciach privesu
    th, lr = g["theta"], g["lr"]

    def w(lx, lz):
        return Vector((g["xr"] + lx * math.cos(th) - lz * math.sin(th), g["zh"] + lx * math.sin(th) + lz * math.cos(th)))

    tip = w(-lr, -0.045)
    pts = [Vector((tip.x - 30.0, 0.0)), tip, w(-lr + 0.25, 0.0), w(0.0, 0.0), Vector((g["xr"] + g["lip"], g["zt"])), Vector((g["xf"], g["zt"]))]
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

    path = [lines[0][0]] + [meet(lines[i], lines[i + 1]) for i in range(len(lines) - 1)] + [lines[-1][0] + lines[-1][1] * (pts[-1] - pts[-2]).length]
    return path, pts


def pd_parts(put, put_lr):
    put(build_pv_winch())
    put(build_pv_drum())
    put(build_pv_hook())
    put(build_pv_cable())
    put(build_pd_rack())
    put(build_pd_spare_mount())
    for size in PV_CARS:
        put(build_pv_car(size))
        put(build_pv_car_wheel(size))
    for p in PODVALY.values():
        tr_type_parts(put, put_lr, pd_tr(p))
        put(build_pd_chassis(p))
        put(build_pd_deck(p))
        put(build_pd_guides(p))
        put_lr(build_pd_rails(p), "SM_Pv_pd_zabradlie_" + p["key"])
        put(build_pd_ramp(p))


PD_TL = dict(jock0=420, jock1=445, out0=450, out1=500, tilt0=500, tilt1=550, hook0=560, hook1=590, pull0=590, pull1=720, tback0=740, tback1=790, in0=790, in1=840,
             jock2=880, jock3=910, lever0=920, lever1=945, lever2=970, lever3=990, show=440)
PD_RIGS = {}


def pd_rig(coll, p, parts, mats, ball_src, x_pos, y_pos, delay_m):
    g = pd_geo(p)
    key_, name = p["key"], p["name"]
    car = PV_CARS[key_]
    tr = pd_tr(p)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, prop = r["root"], r["body"], r["prop"]
    set_prop(root, "Najazd_vysun", 0.0, 0.0, 1.0, "Najazdy: 0 = zasunute pod palubou, 1 = vysunute dozadu o %.2f m" % (g["lr"] - 0.05))
    set_prop(root, "Najazd_sklon", 0.0, 0.0, 1.0, "Najazdy: 0 = vodorovne, 1 = sklopene na zem o %.1f st. (koniec sa dotkne zeme)" % math.degrees(g["theta"]))
    set_prop(root, "Hak_k_autu", 0.0, 0.0, 1.0, "Hak: 0 = v drziaku pri navijaku, 1 = na tazne oko auta (lano sa vyvijaha)")
    o0 = tl((0.0, 0.0, 0.0))
    xf, zt, xr = g["xf"], g["zt"], g["xr"]
    for tag, mk in (("ram", "ram"), ("paluba", "paluba"), ("vedenie", "vedenie")):
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_pd_%s_%s" % (mk, key_)])])
    for side in ("L", "P"):
        mount(coll, name, "zabradlie_" + side, body, o0, [("zabradlie_" + side, parts["Pv_pd_zabradlie_%s_%s" % (key_, side)])])
    # najazdy: klb (sklon) -> posuvny uchyt (vysun) -> diel
    for s, side in ((1.0, "L"), (-1.0, "P")):
        hinge = empty(coll, "%s_uchyt_najazd_klb_%s" % (name, side), tl((xr, s * PD_RY, g["zh"])), body)
        hinge.empty_display_type = "ARROWS"
        hinge.empty_display_size = 0.15
        driver(hinge, "rotation_euler", 1, "%.6f * t" % -g["theta"], [prop("t", "Najazd_sklon")])
        slide, _ = mount(coll, name, "najazd_" + side, hinge, (0.0, 0.0, 0.0), [("najazd_" + side, parts["Pv_pd_najazd_" + key_])])
        driver(slide, "location", 0, "%.4f * (1 - v)" % (g["lr"] - 0.05), [prop("v", "Najazd_vysun")])
    # celna stena, drziak a rezerva, navijak s lanom a hakom
    rack, _ = mount(coll, name, "celna_stena", body, tl((xf, 0.0, zt)), [("celna_stena", parts["Pv_pd_celna_stena"])])
    mount(coll, name, "drziak_rezervy", rack, (0.0, 0.0, 0.0), [("drziak_rezervy", parts["Pv_pd_drziak_rezervy"])])
    rk = "%da" % round(p["R"] * 100)
    spare, _ = mount(coll, name, "rezerva", rack, (0.12, 0.0, 0.30), [("rezerva_pneu", parts["Pv_tr_pneu_" + rk]), ("rezerva_disk", parts["Pv_tr_disk_%s_L" % rk])])
    spare.rotation_euler = (0.0, 0.0, -math.pi * 0.5)
    winch, _ = mount(coll, name, "navijak", rack, (-0.22, 0.0, PD_HR + 0.06), [("navijak", parts["Pv_navijak"])])
    drum, _ = mount(coll, name, "buben", winch, (0.0, 0.0, 0.14), [("buben", parts["Pv_navijak_buben"])])
    fair = empty(coll, name + "_navijak_vodiaca", (-0.20, 0.0, 0.05), winch)
    holder = empty(coll, name + "_hak_drziak", (-0.17, -0.19, 0.25), winch)
    hook, _ = mount(coll, name, "hak", holder, (0.0, 0.0, 0.0), [("hak", parts["Pv_hak"])])
    hook.scale = (0.30, 0.30, 0.30)
    con = hook.constraints.new("COPY_LOCATION")
    con.name = "Na_aute"
    cable, _ = mount(coll, name, "lano", fair, (0.0, 0.0, 0.0), [("lano", parts["Pv_lano"])])
    track(cable, hook, "TRACK_Z")
    driver(cable, "scale", 2, "d", [("d", "DIST", (fair, hook))])
    d0 = Vector((-0.17 + 0.20, -0.19, 0.25 - 0.05)).length
    driver(drum, "rotation_euler", 1, "-(d - %.4f) / 0.085" % d0, [("d", "DIST", (fair, hook))])
    # odtahovane auto: volne v scene (dieta korena), polohu, otacanie kolies a viditelnost nesu kluce po snimkach
    auto = new_object(coll, name + "_auto", parts["Pv_auto_" + key_], (0.0, 0.0, 0.0), root)
    wheels = []
    for i, (dx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        wheels.append(new_object(coll, "%s_auto_koleso_%d" % (name, i + 1), parts["Pv_auto_koleso_" + key_],
                                 (dx * car["wb"] * 0.5, sy * (car["w"] * 0.5 - 0.14), 0.0), auto, (0.0, 0.0, 0.0 if sy > 0 else 180.0)))
    eye = empty(coll, name + "_auto_oko", (car["wb"] * 0.5 + car["fo"] + 0.05, 0.0, -car["rw"] + 0.19), auto)
    con.target = eye
    driver(hook, 'constraints["Na_aute"].influence', -1, "k", [prop("k", "Hak_k_autu")])
    tr_animate(tr, r, delay_m, jock=[(1, 0.0), (PD_TL["jock0"], 0.0), (PD_TL["jock1"], 1.0), (PD_TL["jock2"], 1.0), (PD_TL["jock3"], 0.0)],
               lever=[(1, 0.0), (PD_TL["lever0"], 0.0), (PD_TL["lever1"], 1.0), (PD_TL["lever2"], 1.0), (PD_TL["lever3"], 0.0)])
    tr_keys(root, "Najazd_vysun", [(1, 0.0), (PD_TL["out0"], 0.0), (PD_TL["out1"], 1.0), (PD_TL["in0"], 1.0), (PD_TL["in1"], 0.0)])
    tr_keys(root, "Najazd_sklon", [(1, 0.0), (PD_TL["tilt0"], 0.0), (PD_TL["tilt1"], 1.0), (PD_TL["tback0"], 1.0), (PD_TL["tback1"], 0.0)])
    tr_keys(root, "Hak_k_autu", [(1, 0.0), (PD_TL["hook0"], 0.0), (PD_TL["hook1"], 1.0)])
    PD_RIGS[name] = dict(g=g, car=car, auto=auto, wheels=wheels)
    pd_animate_car(p, root)
    return r


def pd_animate_car(p, root):
    # kluce auta po snimkach (v suradniciach privesu): na zemi za podvalom -> vytahovanie po najazdoch na palubu -> stoji na palube
    rig = PD_RIGS[p["name"]]
    g, car, auto = rig["g"], rig["car"], rig["auto"]
    tl_ = PD_TL
    path, surf = pd_rail_path(g, car)
    wb, fo, rw = car["wb"], car["fo"], car["rw"]
    f_end = Vector((g["xf"] - 0.30 - fo, g["zt"] + rw))
    s_end = path_param(path, f_end)
    s_start = path_param(path, Vector((surf[1].x - 1.3 - fo, rw)))

    def ease(u):
        return u * u * (3.0 - 2.0 * u)

    def pose(sf):
        f, r_ = car_pose(path, sf, wb)
        c = (f + r_) * 0.5
        return c, -math.atan2(f.y - r_.y, f.x - r_.x)

    c0, y0 = pose(s_start)
    seq = [(1, c0.x, c0.y, y0, s_start), (tl_["pull0"], c0.x, c0.y, y0, s_start)]
    for f in range(tl_["pull0"] + 2, tl_["pull1"], 2):
        sf = s_start + (s_end - s_start) * ease((f - tl_["pull0"]) / float(tl_["pull1"] - tl_["pull0"]))
        c, ry = pose(sf)
        seq.append((f, c.x, c.y, ry, sf))
    c1, y1 = pose(s_end)
    seq.append((tl_["pull1"], c1.x, c1.y, y1, s_end))
    seq.append((1000, c1.x, c1.y, y1, s_end))
    travel, wheel_keys = 0.0, []
    for f, x, z, ry, sf in seq:
        travel = sf - s_start
        wheel_keys.append((f, travel / rw))
    key(auto, "location", 0, [(f, x) for f, x, z, ry, sf in seq])
    key(auto, "location", 2, [(f, z) for f, x, z, ry, sf in seq])
    key(auto, "rotation_euler", 1, [(f, ry) for f, x, z, ry, sf in seq])
    for wheel in rig["wheels"]:
        key(wheel, "rotation_euler", 1, wheel_keys)
    for obj in [auto] + rig["wheels"]:
        for prop_name in ("hide_viewport", "hide_render"):
            for frame, value in ((1, True), (tl_["show"] - 1, True), (tl_["show"], False)):
                setattr(obj, prop_name, value)
                obj.keyframe_insert(data_path=prop_name, frame=frame)


def _pd_doc():
    lines = ["", "PODVAL NA AUTO (Podval_auto_4_0, Podval_auto_5_2: privesny podvalnik s pevnou riesetkovou palubou a dvoma vysuvnymi najazdami, pociatok = zem pod stredom gule, predok +X, privesok ide do -X):",
             "  Pevne diely (uchyt <Podval>_uchyt_<diel>, pivot v pociatku privesu): ram (modry, dva podlzniky), paluba (modra riesetka z priecnych latiek, bocne nosniky, stredny plech vpredu, zadny nabeh 0.30 m), vedenie (koleje najazdov pod palubou),",
             "    zabradlie_L / _P (rurove), celna_stena (nizka s mriezkou, pivot v strede prednej hrany paluby na vrchu) s drziakom rezervneho kolesa a rezervou (pneu + disk), navijak (maly, na polici celnej steny), buben, hak, lano, vodiaca a hak_drziak (prazdne objekty).",
             "  Najazdy: pre kazdu stranu klb <Podval>_uchyt_najazd_klb_L / _P (na zadnej hrane paluby, kde sa najazd dotyka paluby; rotacia Y o -Najazd_sklon x uhol, zadok dole) a v nom posuvny uchyt <Podval>_uchyt_najazd_L / _P",
             "    (poloha X = (dlzka najazdu - 0.05) x (1 - Najazd_vysun): 0 = zasunuty pod palubou, 1 = vysunuty dozadu); diel Pv_pd_najazd_<kluc> (pivot na hornom konci, v osi najazdu, na hornom povrchu, siaha do -X). Najazd sa najprv vysunie a potom sklopi, koniec sa dotkne zeme.",
             "  Hak ma Copy Location 'Na_aute' na tazne oko auta (vplyv = Hak_k_autu); lano mieri na hak (mierka Z = vzdialenost). Auto (Pv_auto_<kluc>) a 4 kolesa su deti korena; polohu, sklon, otacanie kolies a viditelnost nesu kluce (auto sa objavi v snimku %d, vytiahnutie 590 az 720)." % PD_TL["show"],
             "  Vlastnosti: Najazd_vysun, Najazd_sklon, Hak_k_autu (0 az 1), Opierne_koleso, Spojka, Koleso_otocenie. Animacia: jazda 1 az 300, opierne koleso 420 az 445, vysun najazdov 450 az 500, sklopenie 500 az 550, hak 560 az 590, vytiahnutie 590 az 720, nazad 740 az 840, opierne koleso hore 880 az 910, spojka 920 az 990.",
             "  Zadne svetla su na zadnom naraznik (rozdelenom: stredny dielec a dva koncove, aby sa najazdy mali kde sklopit); krdlove blatniky (kridlo_L / _P, uzke, len nad kolesami) a ostatne spolocne diely ako pri ostatnych privesoch.",
             "  Kolesa su v DVOJMONTAZI (dve pneumatiky vedla seba na kazdej strane): uchyty koleso_N_L_vnut / _von a koleso_N_P_vnut / _von (pneu + disk, uzsie 0.16 m), kazda naprava ma vnutorne a vonkajsie hlavy; rezerva je jedno siroke koleso."]
    for p in PODVALY.values():
        g = pd_geo(p)
        c = PV_CARS[p["key"]]
        lines.append("  %s: paluba %.2f m vo vyske %.2f az %.2f m, najazdy %.2f m (sklon %.1f st.), naprav %d (x = %s), auto %.2f m, rozvor %.2f m" % (
            p["name"], p["Lb"], PD_ZB, PD_ZT, g["lr"], math.degrees(g["theta"]), len(p["axles"]), ", ".join("%.2f" % x for x in p["axles"]), c["L"], c["wb"]))
    return lines


TRAILERS["podval"] = (PODVALY, pd_rig)
PART_MAKERS.append(pd_parts)
DOC_EXTRA.extend(_pd_doc())
CATALOG_EXTRA.append(("PODVAL NA AUTO", ["Pv_pd_%s_%s" % (pp, k) for k in PODVALY for pp in ("ram", "paluba", "vedenie", "najazd")] + ["Pv_pd_zabradlie_%s_L" % k for k in PODVALY] +
                      ["Pv_pd_celna_stena", "Pv_pd_drziak_rezervy", "Pv_navijak", "Pv_navijak_buben", "Pv_hak", "Pv_lano"] + ["Pv_tr_oje_pd_%s" % k for k in PODVALY] +
                      ["Pv_tr_naraznik_pd_%s" % k for k in PODVALY] + ["Pv_tr_kridlo_pd_%s_L" % k for k in PODVALY] + ["Pv_auto_%s" % k for k in PV_CARS] + ["Pv_auto_koleso_%s" % k for k in PV_CARS] +
                      [ax_key(PD_TRACK)]))


# ---------------------------------------------------------------------------
# Vozik na palety: plochy privesny vozik s bocnicami (sklapacie), zadnym celom, celnou stenou a EUR paletami (1.2 x 0.8 m) s nakladom (kartony / vrecia).
# Dve dlzky: Vozik_palety_3_0 (2 rady = 4 palety, jedna naprava) a Vozik_palety_4_2 (3 rady = 6 paliet, tandem). Svetla su na zadnom naraznik.
# Demontovatelne diely: ram, podlaha, celna (celna stena), bocnica_L / _P, zadne_celo, paleta_N + spolocne diely privesov.
# ---------------------------------------------------------------------------

PA_XF = -1.30          # predna hrana podlahy
PA_ZF = 0.78           # horny povrch podlahy
PA_HS = 0.40           # vyska bocnic
PA_WD = 1.80           # vnutorna sirka (dve palety vedla seba po 0.8 m)
PA_TRACK, PA_SY = 0.78, 0.45
PALETY = {
    "3_0": dict(key="3_0", name="Vozik_palety_3_0", Ld=3.00, rows=2, R=0.31, axles=[-2.80]),
    "4_2": dict(key="4_2", name="Vozik_palety_4_2", Ld=4.20, rows=3, R=0.31, axles=[-3.40, -4.50]),
}


def pa_pallets(p):
    # polohy paliet (x, y, druh): rad po rade od predku, najprv lava, potom prava strana
    out = []
    for r in range(p["rows"]):
        x = PA_XF - 0.08 - 0.60 - 1.22 * r
        for k, y in enumerate((0.41, -0.41)):
            out.append((x, y, "karton" if (r + k) % 2 == 0 else "vrecia"))
    return out


def pa_tr(p):
    xr = PA_XF - p["Ld"]
    Ld = p["Ld"]
    return dict(name=p["name"], key="pa_" + p["key"], R=p["R"], axles=p["axles"], track=PA_TRACK, sy=PA_SY,
                oje=dict(xf=PA_XF, hw=0.45, z=0.515, z0=0.68), hang=dict(z=0.55, h=0.16),
                kons=dict(y0=0.425, y1=0.925, zb=0.72), kons_mat=FRAME,
                bump=dict(x=xr - 0.07, w=PA_WD + 0.40, z=0.64),
                markers=[(PA_XF - Ld * 0.5, k * (PA_WD * 0.5 + 0.007), PA_ZF - 0.05, "or") for k in SIDES_LR] +
                        [(PA_XF - 0.02, k * (PA_WD * 0.5 - 0.03), PA_ZF - 0.05, "white") for k in SIDES_LR] +
                        [(xr + 0.02, k * (PA_WD * 0.5 - 0.03), PA_ZF - 0.05, "red") for k in SIDES_LR])


def build_pa_frame(p):
    # ram: dva podlzniky, priecniky s vyloznikmi pod okrajmi podlahy
    Ld, xr = p["Ld"], PA_XF - p["Ld"]
    bm = bmesh.new()
    xc = (PA_XF + xr) * 0.5
    for s in SIDES_LR:
        add_box(bm, (Ld + 0.08, 0.07, 0.12), (xc, s * 0.45, 0.68), FRAME, bev=0.02)
    for k in range(int(Ld / 0.60) + 1):
        x = PA_XF - 0.10 - 0.60 * k
        add_box(bm, (0.06, 0.90, 0.08), (x, 0.0, 0.68), FRAME, bev=0.012)
        for s in SIDES_LR:
            add_box(bm, (0.06, 0.46, 0.04), (x, s * 0.68, 0.72), FRAME, bev=0.008)
    return finish_mesh(bm, "SM_Pv_pa_ram_" + p["key"])


def build_pa_floor(p):
    # podlaha: preglejka s listami, okrajove listy, kapsy na kolik a kotviace oka
    Ld, xr = p["Ld"], PA_XF - p["Ld"]
    bm = bmesh.new()
    xc = (PA_XF + xr) * 0.5
    add_box(bm, (Ld, PA_WD, 0.04), (xc, 0.0, PA_ZF - 0.02), PLY, bev=0.008)
    for k in range(int(Ld / 0.20)):
        add_box(bm, (0.016, PA_WD - 0.02, 0.008), (PA_XF - 0.10 - 0.20 * k, 0.0, PA_ZF + 0.002), DARK)
    for s in SIDES_LR:
        add_box(bm, (Ld, 0.05, 0.07), (xc, s * (PA_WD * 0.5 + 0.015), PA_ZF - 0.075), ALU, bev=0.014)
        for k in range(int(Ld / 0.75) + 1):
            x = PA_XF - 0.20 - 0.75 * k
            if x > xr + 0.10:
                add_box(bm, (0.05, 0.05, 0.10), (x, s * (PA_WD * 0.5 + 0.035), PA_ZF - 0.04), STEEL, bev=0.008)
                add_box(bm, (0.14, 0.03, 0.05), (x, s * (PA_WD * 0.5 + 0.045), PA_ZF - 0.09), STEEL, bev=0.006)
    return finish_mesh(bm, "SM_Pv_pa_podlaha_" + p["key"])


def build_pa_front(p):
    # celna stena (rebrik): oranzovy ram s mriezkou, bocne stlpiky, smerovky
    hw = 0.80
    bm = bmesh.new()
    add_box(bm, (0.05, PA_WD + 0.06, 0.06), (PA_XF + 0.025, 0.0, PA_ZF + hw), PAINT_ORANGE, bev=0.014)
    add_box(bm, (0.05, PA_WD + 0.06, 0.08), (PA_XF + 0.025, 0.0, PA_ZF + 0.04), PAINT_ORANGE, bev=0.012)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.06, hw + 0.05), (PA_XF + 0.03, s * (PA_WD * 0.5 + 0.01), PA_ZF + hw * 0.5 + 0.02), PAINT_ORANGE, bev=0.014)
        add_box(bm, (0.08, 0.14, 0.05), (PA_XF + 0.03, s * (PA_WD * 0.5 - 0.30), PA_ZF + hw + 0.045), LAMP_OR, bev=0.008)
    for k in range(-5, 6):
        add_rod(bm, (PA_XF + 0.025, k * 0.16, PA_ZF + 0.08), (PA_XF + 0.025, k * 0.16, PA_ZF + hw - 0.03), 0.011, STEEL, segments=6)
    add_box(bm, (0.04, PA_WD - 0.06, 0.04), (PA_XF + 0.025, 0.0, PA_ZF + hw * 0.5), PAINT_ORANGE, bev=0.008)
    return finish_mesh(bm, "SM_Pv_pa_celna_" + p["key"])


def build_pa_side(p):
    # bocnica (lava strana; prava je zrkadlo): pivot na spodnej hrane vonkajsej steny v strede dlzky, stoji nahor; pri sklopeni lezi vodorovne ako predlzenie podlahy
    Ld = p["Ld"]
    bm = bmesh.new()
    add_box(bm, (Ld - 0.04, 0.03, PA_HS - 0.01), (0.0, -0.015, PA_HS * 0.5 + 0.005), ALU, bev=0.01)
    for fz in (0.33, 0.66):
        add_box(bm, (Ld - 0.16, 0.012, 0.03), (0.0, 0.006, PA_HS * fz), ALU, bev=0.005)
    add_box(bm, (Ld - 0.02, 0.05, 0.04), (0.0, -0.015, PA_HS - 0.01), PAINT_ORANGE, bev=0.012)
    for k in range(int(Ld / 0.75) + 1):
        x = Ld * 0.5 - 0.15 - 0.75 * k
        if abs(x) < Ld * 0.5 - 0.10:
            add_box(bm, (0.04, 0.05, PA_HS), (x, -0.015, PA_HS * 0.5), STEEL, bev=0.008)
    for sx in (-1.0, 1.0):
        add_cylinder(bm, 0.015, 0.07, along_x((sx * (Ld * 0.5 - 0.10), 0.0, 0.0)), STEEL, segments=8)
        add_box(bm, (0.05, 0.04, 0.05), (sx * (Ld * 0.5 - 0.03), -0.01, PA_HS - 0.05), STEEL, bev=0.008)
    return bm


def build_pa_gate(p):
    # zadne celo: pivot na spodnom pante, stoji nahor, sklapa sa dozadu
    bm = bmesh.new()
    add_box(bm, (0.03, PA_WD - 0.01, PA_HS - 0.01), (-0.016, 0.0, PA_HS * 0.5 + 0.005), ALU, bev=0.01)
    for fz in (0.33, 0.66):
        add_box(bm, (0.012, PA_WD - 0.18, 0.03), (-0.036, 0.0, PA_HS * fz), ALU, bev=0.005)
    add_box(bm, (0.05, PA_WD + 0.02, 0.04), (-0.016, 0.0, PA_HS - 0.01), PAINT_ORANGE, bev=0.012)
    for s in SIDES_LR:
        add_cylinder(bm, 0.018, 0.08, along_y((0.0, s * (PA_WD * 0.5 - 0.06), 0.0)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Pv_pa_zadne_celo_" + p["key"])


def build_pa_pallet(kind):
    # EUR paleta 1.2 x 0.8 x 0.144 m (pivot v strede spodku) s nakladom: kartony s paskou a stretch foliou alebo vrecia s popruhom
    bm = bmesh.new()
    for k in range(3):
        add_box(bm, (1.20, 0.10, 0.022), (0.0, -0.35 + 0.35 * k, 0.011), PALLET, bev=0.003)
        for j in range(3):
            add_box(bm, (0.145, 0.10, 0.10), (-0.52 + 0.52 * j, -0.35 + 0.35 * k, 0.072), PALLET, bev=0.004)
    for k in range(5):
        add_box(bm, (0.145, 0.80, 0.022), (-0.527 + 0.2635 * k, 0.0, 0.133), PALLET, bev=0.003)
    z0 = 0.144
    if kind == "karton":
        for layer in range(3):
            for i in range(3):
                for j in range(2):
                    add_box(bm, (0.385, 0.385, 0.29), (-0.40 + 0.40 * i, -0.195 + 0.39 * j, z0 + 0.145 + 0.30 * layer), CARTON, bev=0.012)
        add_box(bm, (1.19, 0.79, 0.90), (0.0, 0.0, z0 + 0.45), WRAP, bev=0.02)
        for z in (0.30, 0.60):
            add_box(bm, (1.20, 0.80, 0.014), (0.0, 0.0, z0 + z), STRAP, bev=0.003)
        add_box(bm, (0.012, 0.44, 0.24), (0.605, 0.0, z0 + 0.60), WHITE, bev=0.002)
    else:
        for layer in range(5):
            for i in range(2):
                for j in range(2):
                    if layer % 2 == 0:
                        add_box(bm, (0.58, 0.39, 0.19), (-0.295 + 0.59 * i, -0.195 + 0.39 * j, z0 + 0.10 + 0.20 * layer), PAINT_WHITE, bev=0.06)
                    else:
                        add_box(bm, (0.39, 0.58, 0.19), (-0.195 + 0.39 * i, -0.295 + 0.59 * j, z0 + 0.10 + 0.20 * layer), PAINT_WHITE, bev=0.06)
        add_box(bm, (1.18, 0.78, 0.014), (0.0, 0.0, z0 + 0.60), STRAP, bev=0.003)
        add_box(bm, (0.014, 0.78, 1.0), (0.0, 0.0, z0 + 0.50), STRAP, bev=0.003)
    return finish_mesh(bm, "SM_Pv_pa_paleta_" + kind)


def pa_parts(put, put_lr):
    for kind in ("karton", "vrecia"):
        put(build_pa_pallet(kind))
    for p in PALETY.values():
        tr_type_parts(put, put_lr, pa_tr(p))
        put(build_pa_frame(p))
        put(build_pa_floor(p))
        put(build_pa_front(p))
        put(build_pa_gate(p))
        put_lr(build_pa_side(p), "SM_Pv_pa_bocnica_" + p["key"])


def pa_rig(coll, p, parts, mats, ball_src, x_pos, y_pos, delay_m):
    key_, name = p["key"], p["name"]
    tr = pa_tr(p)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, prop = r["root"], r["body"], r["prop"]
    pal = pa_pallets(p)
    set_prop(root, "Zadne_celo", 0.0, 0.0, 1.0, "Zadne celo: 0 = zatvorene, 1 = sklopene dozadu (90 st.)")
    set_prop(root, "Bocnice", 0.0, 0.0, 1.0, "Bocnice: 0 = zatvorene, 1 = sklopene von (90 st.)")
    set_prop(root, "Naklad", float(len(pal)), 0.0, float(len(pal)), "Pocet nalozenych paliet (0 az %d; palety miznu od zadnej)" % len(pal))
    o0 = tl((0.0, 0.0, 0.0))
    for tag in ("ram", "podlaha", "celna"):
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_pa_%s_%s" % (tag, key_)])])
    xr = PA_XF - p["Ld"]
    gate, _ = mount(coll, name, "zadne_celo", body, tl((xr, 0.0, PA_ZF)), [("zadne_celo", parts["Pv_pa_zadne_celo_" + key_])])
    driver(gate, "rotation_euler", 1, "-g * 1.5708", [prop("g", "Zadne_celo")])
    xc = (PA_XF + xr) * 0.5
    for s, side in ((1.0, "L"), (-1.0, "P")):
        sd, _ = mount(coll, name, "bocnica_" + side, body, tl((xc, s * PA_WD * 0.5, PA_ZF)), [("bocnica_" + side, parts["Pv_pa_bocnica_%s_%s" % (key_, side)])])
        driver(sd, "rotation_euler", 0, "%.0f * b * 1.5708" % -s, [prop("b", "Bocnice")])
    for i, (x, y, kind) in enumerate(pal):
        sock, objs = mount(coll, name, "paleta_%d" % (i + 1), body, tl((x, y, PA_ZF)), [("paleta_%d" % (i + 1), parts["Pv_pa_paleta_" + kind])])
        sock.rotation_euler = (0.0, 0.0, 0.0 if i % 2 == 0 else math.pi)
        for attr in ("hide_viewport", "hide_render"):
            driver(objs[0], attr, -1, "n < %.1f" % (i + 0.5), [prop("n", "Naklad")])
    tr_animate(tr, r, delay_m)
    n = float(len(pal))
    tr_keys(root, "Bocnice", [(1, 0.0), (330, 0.0), (360, 1.0), (430, 1.0), (460, 0.0)])
    tr_keys(root, "Zadne_celo", [(1, 0.0), (470, 0.0), (500, 1.0), (560, 1.0), (590, 0.0)])
    tr_keys(root, "Naklad", [(1, n), (700, n), (840, 0.0), (880, 0.0), (980, n)])
    return r


def _pa_doc():
    lines = ["", "VOZIK NA PALETY (Vozik_palety_3_0, Vozik_palety_4_2: plochy privesny vozik s bocnicami a EUR paletami; pociatok = zem pod stredom gule, predok +X, vozik ide do -X):"]
    for p in PALETY.values():
        lines.append("  %s: podlaha %.2f x %.2f m vo vyske %.2f m, bocnice %.2f m, %d palety v %d radoch, naprav %d (x = %s), rozchod %.2f m (kolesa R %.2f, blatniky len nad osou)" % (
            p["name"], p["Ld"], PA_WD, PA_ZF, PA_HS, len(pa_pallets(p)), p["rows"], len(p["axles"]), ", ".join("%.2f" % x for x in p["axles"]), PA_TRACK * 2.0, p["R"]))
    lines += [
        "  Typove diely (uchyt <Vozik>_uchyt_<diel>): ram, podlaha, celna (celna stena), bocnica_L / _P (pivot na spodnej hrane vonkajsej steny, rotacia X o -/+ Bocnice x 90 st.), zadne_celo (rotacia Y o -Zadne_celo x 90 st.), paleta_N.",
        "  EUR paleta (Pv_pa_paleta_karton: 18 kartonov s paskou a foliou, Pv_pa_paleta_vrecia: 20 vriec s popruhom): pivot v strede spodku palety, 1.20 x 0.80 m; vlastnost Naklad = pocet nalozenych paliet (palety miznu od zadnej).",
        "  Spolocne diela (oje, naprava, pera, kolesa, blatniky, naraznik so svetlami ...) ako pri malom vozikoch.",
    ]
    return lines


TRAILERS["palety"] = (PALETY, pa_rig)
PART_MAKERS.append(pa_parts)
DOC_EXTRA.extend(_pa_doc())
CATALOG_EXTRA.append(("VOZIK NA PALETY", ["Pv_pa_%s_%s" % (pp, k) for k in PALETY for pp in ("ram", "podlaha", "celna", "zadne_celo")] +
                      ["Pv_pa_bocnica_%s_%s" % (k, sd) for k in PALETY for sd in ("L", "P")] + ["Pv_pa_paleta_karton", "Pv_pa_paleta_vrecia"] +
                      ["Pv_tr_oje_pa_%s" % k for k in PALETY] + ["Pv_tr_naraznik_pa_%s" % k for k in PALETY] + [ax_key(PA_TRACK)]))


# ---------------------------------------------------------------------------
# Cisternovy vozik (privesny vozik s cisternou na vodu / hnojivo / palivo) v tvare cisternoveho navesu: oval nadrze (zaoblena elipsa) s klenbami a obruceami medzi komorami,
# poklopy na kominoch (otvaraju sa), ochranne trubky, ADR tabulky, skrinka s ventilmi vzadu s dvomi dverami (otvaraju sa) a armaturou (zberne potrubie, tri ventily,
# vypust s hadicovou spojkou) v ROVNAKOM ROZMERE ako na cisternovom naves. Zadny naraznik so svetlami, oje s opiernym kolesom a spojkou, jedna naprava.
# Dve velkosti: Vozik_cisterna_1_5 (jedna komora, asi 1.5 m3) a Vozik_cisterna_3_0 (dve komory, asi 3 m3).
# ---------------------------------------------------------------------------

CS_XF = -1.10          # predna hrana ramu
CS_ZB = 0.78           # spodok nadrze
CS_EXP, CS_N = 2.5, 20          # tvar prierezu nadrze (zaoblena elipsa), pocet bodov prierezu
CS_HEAD = ((0.0, 1.0), (0.30, 0.955), (0.60, 0.84), (0.83, 0.66), (1.0, 0.42))    # klenba: (podiel dlzky klenby od valca, mierka prierezu)
CS_RING_S, CS_RING_W = 1.04, 0.035   # obruce medzi komorami
CS_MH_R, CS_MH_H = 0.22, 0.12        # poklop: polomer, vyska komina
CS_CAB_D, CS_CAB_H = 0.44, 0.58      # skrinka s ventilmi: hlbka a vyska (rovnako ako na naves)
CS_CAB_Z0 = 0.68
CS_DOOR_OPEN, CS_LID_OPEN = 1.75, 1.85
CISTERNY = {
    "1_5": dict(key="1_5", name="Vozik_cisterna_1_5", Lb=1.60, Wt=1.15, Ht=0.85, R=0.30, comps=1, head=0.22, mat=PAINT_WHITE),
    "3_0": dict(key="3_0", name="Vozik_cisterna_3_0", Lb=2.40, Wt=1.35, Ht=1.05, R=0.30, comps=2, head=0.26, mat=PAINT_RED),
}


def cs_geo(c):
    xt0 = CS_XF - 0.10
    xb0 = xt0 - c["head"]
    xb1 = xb0 - c["Lb"]
    xt1 = xb1 - c["head"]
    xr = xt1 - 0.62
    xax = (xb0 + xb1) * 0.5 - 0.10
    track = c["Wt"] * 0.5 + 0.165
    top = CS_ZB + c["Ht"]
    xcab = xt1 - 0.50                      # zadna rovina skrinky (dvere)
    hw = min(0.60, c["Wt"] * 0.5)
    comp_len = c["Lb"] / c["comps"]
    mh = [xb0 - comp_len * (i + 0.5) for i in range(c["comps"])]
    rings = [xb0 - comp_len * i for i in range(1, c["comps"])]
    return dict(xt0=xt0, xb0=xb0, xb1=xb1, xt1=xt1, xr=xr, xax=xax, track=track, sy=0.45, top=top, xcab=xcab, hw=hw, mh=mh, rings=rings,
                zc=CS_ZB + c["Ht"] * 0.5)


def cs_tr(c):
    g = cs_geo(c)
    Wt = c["Wt"]
    return dict(name=c["name"], key="cs_" + c["key"], R=c["R"], axles=[g["xax"]], track=g["track"], sy=g["sy"],
                oje=dict(xf=CS_XF, hw=0.45, z=0.515, z0=0.55), hang=dict(z=0.43, h=0.14),
                kons=dict(y0=0.42, y1=g["track"] - 0.09, zb=0.70), kons_mat=FRAME,
                bump=dict(x=g["xr"] - 0.10, w=2 * g["hw"] + 0.44, z=0.56),
                markers=[(g["xb0"] - 0.05, k * 0.49, 0.55, "or") for k in SIDES_LR] + [(g["xax"] - 0.90, k * 0.49, 0.55, "or") for k in SIDES_LR] +
                        [(g["xr"] + 0.30, k * 0.49, 0.55, "red") for k in SIDES_LR])


def cs_ring(c, sy, sz=None):
    # prierez nadrze (y, z) v mierke sy, sz okolo osi nadrze: zaoblena elipsa |y|^e + |z|^e = 1
    g = cs_geo(c)
    sz = sy if sz is None else sz
    hw, hh = c["Wt"] * 0.5, c["Ht"] * 0.5
    pts = []
    for k in range(CS_N):
        a = 2.0 * math.pi * k / CS_N
        co, si = math.cos(a), math.sin(a)
        pts.append((hw * sy * math.copysign(abs(co) ** (2.0 / CS_EXP), co), g["zc"] + hh * sz * math.copysign(abs(si) ** (2.0 / CS_EXP), si)))
    return pts


def cs_tank_z(c, y):
    # vyska povrchu nadrze (hore) v danom y
    t = min(abs(y) / (c["Wt"] * 0.5), 1.0) ** CS_EXP
    return cs_geo(c)["zc"] + c["Ht"] * 0.5 * (1.0 - t) ** (1.0 / CS_EXP)


def build_cs_frame(c):
    # ram: dva podlzniky a priecniky (nosne)
    g = cs_geo(c)
    xr = g["xr"]
    bm = bmesh.new()
    xc, ln = (CS_XF + xr) * 0.5, CS_XF - xr
    for s in SIDES_LR:
        add_box(bm, (ln + 0.06, 0.07, 0.10), (xc, s * 0.45, 0.55), FRAME, bev=0.02)
    for k in range(int(ln / 0.55) + 1):
        add_box(bm, (0.06, 0.92, 0.06), (CS_XF - 0.10 - 0.55 * k, 0.0, 0.63), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_cs_ram_" + c["key"])


def build_cs_platform(c):
    # plosina za nadrzou pod skrinkou
    g = cs_geo(c)
    bm = bmesh.new()
    x0, x1 = g["xr"], g["xt1"] + 0.15
    add_box(bm, (x1 - x0, 2 * g["hw"], 0.04), ((x0 + x1) * 0.5, 0.0, CS_CAB_Z0 - 0.02), GRAY, bev=0.012)
    return finish_mesh(bm, "SM_Pv_cs_plosina_" + c["key"])


def build_cs_saddle(c):
    # dve nosne kolebky nadrze (siva doska s lemom)
    g = cs_geo(c)
    bm = bmesh.new()
    for x in (g["xb0"] - 0.30, g["xb1"] + 0.30):
        add_box(bm, (0.16, c["Wt"] * 0.66, CS_ZB - 0.66), (x, 0.0, (CS_ZB + 0.66) * 0.5 - 0.0), GRAY, bev=0.02)
    return finish_mesh(bm, "SM_Pv_cs_sedlo_" + c["key"])


def cs_loft(bm, c, stations):
    # prierez pretiahnuty pozdlz X; stanica (x, mierka y, mierka z, material pasu po dalsiu stanicu); na koncoch ploche steny
    rings = [[bm.verts.new((x, p[0], p[1])) for p in cs_ring(c, sy, sz)] for x, sy, sz, _ in stations]
    faces = [bm.faces.new(rings[0]), bm.faces.new(rings[-1][::-1])]
    mats = [None, None]
    for k in range(len(stations) - 1):
        for i in range(CS_N):
            j = (i + 1) % CS_N
            faces.append(bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i])))
            mats.append(stations[k][3])
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    for f, m in zip(faces, mats):
        f.material_index = c["mat"] if m is None else m


def build_cs_tank(c):
    # nadrz: predna klenba, valec s obruceami medzi komorami, zadna klenba
    g = cs_geo(c)
    hl = c["head"]
    bm = bmesh.new()
    st = [(g["xb0"] + d * hl, s, s, c["mat"]) for d, s in reversed(CS_HEAD)]
    marks = [g["xb0"] - 0.05] + g["rings"] + [g["xb1"] + 0.05]
    for xc in marks:
        st += [(xc + CS_RING_W, 1.0, 1.0, ALU), (xc + CS_RING_W, CS_RING_S, CS_RING_S, ALU), (xc - CS_RING_W, CS_RING_S, CS_RING_S, ALU), (xc - CS_RING_W, 1.0, 1.0, c["mat"])]
    st += [(g["xb1"] - d * hl, s, s, c["mat"]) for d, s in CS_HEAD]
    cs_loft(bm, c, st)
    return finish_mesh(bm, "SM_Pv_cs_nadrz_" + c["key"])


def build_cs_komin(c, i):
    # komin poklopu s prirubou, skrutkami, uchami a odvetranim (ventil s hlavicou) za nim; i = poradie komory od predku
    g = cs_geo(c)
    mx = g["mh"][i]
    top = g["top"]
    bm = bmesh.new()
    add_cylinder(bm, CS_MH_R, CS_MH_H + 0.08, along_z((mx, 0.0, top + (CS_MH_H - 0.08) * 0.5)), STEEL, segments=16, bev=0.006)
    add_cylinder(bm, CS_MH_R + 0.03, 0.04, along_z((mx, 0.0, top + CS_MH_H - 0.02)), STEEL, segments=16, bev=0.004)
    for k in range(8):
        a = 2.0 * math.pi * (k + 0.5) / 8.0
        add_box(bm, (0.035, 0.035, 0.03), (mx + (CS_MH_R + 0.015) * math.cos(a), (CS_MH_R + 0.015) * math.sin(a), top + CS_MH_H + 0.01), DARK, bev=0.004)
    for s in SIDES_LR:
        add_box(bm, (0.06, 0.05, 0.09), (mx + CS_MH_R + 0.04, s * 0.11, top + CS_MH_H + 0.04), STEEL, bev=0.006)
    add_cylinder(bm, 0.04, 0.14, along_z((mx - 0.36, 0.0, top + 0.04)), STEEL, segments=10, bev=0.004)
    add_cylinder(bm, 0.062, 0.035, along_z((mx - 0.36, 0.0, top + 0.125)), DARK, segments=10, bev=0.004)
    return finish_mesh(bm, "SM_Pv_cs_komin_%s_%d" % (c["key"], i + 1))


def build_cs_lid():
    # poklop: pivot v osi pantu na zadnom okraji komina (os Y); poklop lezi pred pivotom (-X je zadok, preto poklop smeruje do -X)
    bm = bmesh.new()
    r = CS_MH_R + 0.03
    add_cylinder(bm, r, 0.05, along_z((-r, 0.0, 0.005)), STEEL, segments=16, bev=0.006)
    add_cylinder(bm, 0.065, 0.04, along_z((-r, 0.0, 0.045)), ALU, segments=10, bev=0.004)
    add_box(bm, (0.18, 0.04, 0.03), (-r, 0.0, 0.075), ALU, bev=0.006)
    for s in SIDES_LR:
        add_box(bm, (0.04, 0.04, 0.04), (-r - 0.08 * s, 0.0, 0.055), ALU, bev=0.004)
        add_box(bm, (0.05, 0.06, 0.06), (-2.0 * r + 0.01, s * 0.10, 0.0), DARK, bev=0.006)
        add_box(bm, (0.05, 0.05, 0.05), (0.0, s * 0.11, 0.0), STEEL, bev=0.006)
    add_cylinder(bm, 0.02, 0.26, along_y((0.0, 0.0, 0.0)), CHROME, segments=8)
    return finish_mesh(bm, "SM_Pv_cs_poklop")


def build_cs_guard(c):
    # ochranne trubky nad nadrzou (proti prevrateniu): dve trubky po stranach poklopov na stojkach
    g = cs_geo(c)
    top = g["top"]
    zr = top + 0.26
    ry = c["Wt"] * 0.5 * 0.55
    x0, x1 = g["xb0"] - 0.12, g["xb1"] + 0.12
    bm = bmesh.new()
    zs = cs_tank_z(c, ry) - 0.03
    xs = [x0 - 0.12, x1 + 0.12] + g["rings"]
    for s in SIDES_LR:
        y = s * ry
        add_rod(bm, (x0, y, zr), (x1, y, zr), 0.022, ALU, segments=8)
        for x in xs:
            add_rod(bm, (x, y, zr), (x, y, zs), 0.022, ALU, segments=8)
            add_box(bm, (0.09, 0.09, 0.025), (x, y, zs - 0.008), STEEL, bev=0.004)
    for x in (x0, x1):
        add_rod(bm, (x, -ry, zr), (x, ry, zr), 0.022, ALU, segments=8)
    return finish_mesh(bm, "SM_Pv_cs_obrubnik_" + c["key"])


def build_cs_adr():
    # oranzova tabulka (ADR) s cernym okrajom: pivot v strede, plocha smeruje do -X
    bm = bmesh.new()
    add_box(bm, (0.02, 0.34, 0.25), (-0.01, 0.0, 0.0), DARK, bev=0.004)
    add_box(bm, (0.012, 0.31, 0.22), (-0.026, 0.0, 0.0), ADR_MAT, bev=0.003)
    add_box(bm, (0.014, 0.31, 0.010), (-0.028, 0.0, 0.0), DARK)
    return finish_mesh(bm, "SM_Pv_cs_adr")


def build_cs_side_lights(c):
    # bocne obrysove svetla na obruciach nadrze
    g = cs_geo(c)
    bm = bmesh.new()
    for x in [g["xb0"] - 0.05] + g["rings"] + [g["xb1"] + 0.05]:
        for s in SIDES_LR:
            add_box(bm, (0.12, 0.02, 0.05), (x, s * (c["Wt"] * 0.5 * CS_RING_S + 0.009), g["zc"]), LAMP_OR, bev=0.004)
    return finish_mesh(bm, "SM_Pv_cs_bocne_svetla_" + c["key"])


def build_cs_cabinet(c):
    # skrinka s ventilmi vzadu (rovnaky tvar a rozmer ako na naves): podlaha, strop, predna stena, bocnice; zadna strana je otvor pre dvere
    g = cs_geo(c)
    xb = g["xcab"]
    xf = xb + CS_CAB_D
    xm = (xb + xf) * 0.5
    z0, z1 = CS_CAB_Z0, CS_CAB_Z0 + CS_CAB_H
    zm = (z0 + z1) * 0.5
    hw = g["hw"]
    bm = bmesh.new()
    add_box(bm, (CS_CAB_D, 2.0 * hw, 0.03), (xm, 0.0, z0 + 0.015), FRAME, bev=0.008)
    add_box(bm, (CS_CAB_D + 0.02, 2.0 * hw + 0.02, 0.03), (xm - 0.01, 0.0, z1 - 0.015), c["mat"], bev=0.012)
    add_box(bm, (0.03, 2.0 * hw, CS_CAB_H), (xf - 0.015, 0.0, zm), DARK, bev=0.008)
    for s in SIDES_LR:
        add_box(bm, (CS_CAB_D, 0.03, CS_CAB_H), (xm, s * (hw - 0.015), zm), c["mat"], bev=0.008)
        add_box(bm, (0.04, 0.05, CS_CAB_H), (xb + 0.02, s * (hw - 0.025), zm), ALU, bev=0.008)
    return finish_mesh(bm, "SM_Pv_cs_skrinka_" + c["key"])


def build_cs_fittings(c):
    # armatura v skrinke (rovnaky rozmer ako na naves): zberne potrubie, tri ventily s cervenymi kolieskami, dve potrubia k nadrzi, vypust s hadicovou spojkou
    g = cs_geo(c)
    xb = g["xcab"]
    zp, xp = CS_CAB_Z0 + 0.20, xb + 0.22
    hw = g["hw"]
    bm = bmesh.new()
    add_cylinder(bm, 0.055, 2.0 * hw - 0.14, along_y((xp, 0.0, zp)), STEEL, segments=12)
    for y in (-0.34, 0.0, 0.34):
        add_box(bm, (0.14, 0.13, 0.15), (xp, y, zp), STEEL, bev=0.015)
        add_cylinder(bm, 0.018, 0.14, along_z((xp, y, zp + 0.14)), CHROME, segments=8)
        add_cylinder(bm, 0.075, 0.018, along_z((xp, y, zp + 0.22)), PAINT_RED, segments=14, bev=0.003)
    x_end = g["xt1"] + 0.22
    for s in SIDES_LR:
        add_cylinder(bm, 0.045, x_end - xp, along_x(((xp + x_end) * 0.5, s * 0.22, zp)), STEEL, segments=10)
    add_cylinder(bm, 0.05, xp - xb - 0.02, along_x((xb + 0.02 + (xp - xb - 0.02) * 0.5, 0.0, zp)), STEEL, segments=12)
    add_cylinder(bm, 0.075, 0.05, along_x((xb + 0.045, 0.0, zp)), CHROME, segments=14, bev=0.006)
    add_cylinder(bm, 0.06, 0.02, along_x((xb + 0.015, 0.0, zp)), DARK, segments=12)
    return finish_mesh(bm, "SM_Pv_cs_armatura_" + c["key"])


def build_cs_door(c):
    # dvere skrinky (lave; prave je zrkadlo): pivot na zaves vonku (zadna rovina skrinky, y = polsirka, z = spodok dveri), dvere siahaju do -Y a su pred zavesom (-X)
    dw = cs_geo(c)["hw"] - 0.012
    h = CS_CAB_H - 0.02
    bm = bmesh.new()
    add_box(bm, (0.03, dw, h), (-0.015, -dw * 0.5, h * 0.5), c["mat"], bev=0.012)
    add_box(bm, (0.012, dw - 0.10, h - 0.10), (-0.036, -dw * 0.5, h * 0.5), ALU, bev=0.006)
    add_box(bm, (0.014, dw - 0.14, h - 0.14), (-0.040, -dw * 0.5, h * 0.5), c["mat"], bev=0.006)
    for z in (0.10, h - 0.10):
        add_box(bm, (0.05, 0.05, 0.09), (-0.02, 0.0, z), STEEL, bev=0.01)
    add_box(bm, (0.04, 0.03, 0.15), (-0.05, -dw + 0.07, h * 0.5), DARK, bev=0.01)
    add_box(bm, (0.016, 0.10, 0.03), (-0.045, -dw + 0.07, h - 0.06), RED, bev=0.003)
    return bm


CS_TAGS = ("ram", "plosina", "sedlo", "nadrz", "obrubnik", "bocne_svetla", "skrinka", "armatura")


def cs_parts(put, put_lr):
    put(build_cs_lid())
    put(build_cs_adr())
    for c in CISTERNY.values():
        tr_type_parts(put, put_lr, cs_tr(c))
        for fn in (build_cs_frame, build_cs_platform, build_cs_saddle, build_cs_tank, build_cs_guard, build_cs_side_lights, build_cs_cabinet, build_cs_fittings):
            put(fn(c))
        for i in range(c["comps"]):
            put(build_cs_komin(c, i))
        put_lr(build_cs_door(c), "SM_Pv_cs_dvere_" + c["key"])


def cs_rig(coll, c, parts, mats, ball_src, x_pos, y_pos, delay_m):
    g = cs_geo(c)
    key_, name = c["key"], c["name"]
    tr = cs_tr(c)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, prop = r["root"], r["body"], r["prop"]
    n = c["comps"]
    set_prop(root, "Poklopy", 0.0, 0.0, 1.0, "Poklopy komor: 0 = zatvorene, 1 = otvorene (106 st., postupne od zadneho)")
    set_prop(root, "Dvere_skrinky", 0.0, 0.0, 1.0, "Dvere skrinky s ventilmi: 0 = zatvorene, 1 = otvorene dozadu (100 st.)")
    o0 = tl((0.0, 0.0, 0.0))
    for tag in CS_TAGS:
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_cs_%s_%s" % (tag, key_)])])
    for i in range(n):
        mount(coll, name, "komin_%d" % (i + 1), body, o0, [("komin_%d" % (i + 1), parts["Pv_cs_komin_%s_%d" % (key_, i + 1)])])
        lid, _ = mount(coll, name, "poklop_%d" % (i + 1), body, tl((g["mh"][i] + CS_MH_R + 0.03, 0.0, g["top"] + CS_MH_H + 0.0)), [("poklop_%d" % (i + 1), parts["Pv_cs_poklop"])])
        # zadny poklop (najvyssie i) sa otvara prvy, ostatne postupne za nim
        driver(lid, "rotation_euler", 1, "-min(max(p * %.3f - %.2f, 0), 1) * %.2f" % (1.0 + 0.5 * (n - 1), 0.5 * (n - 1 - i), CS_LID_OPEN), [prop("p", "Poklopy")])
    mount(coll, name, "adr_pred", body, tl((g["xt0"] + 0.01, 0.0, g["zc"])), [("adr_pred", parts["Pv_cs_adr"])])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        d, _ = mount(coll, name, "dvere_skrinky_" + side, body, tl((g["xcab"], s * g["hw"], CS_CAB_Z0 + 0.01)), [("dvere_skrinky_" + side, parts["Pv_cs_dvere_%s_%s" % (key_, side)])])
        driver(d, "rotation_euler", 2, "%.0f * p * %.2f" % (-s, CS_DOOR_OPEN), [prop("p", "Dvere_skrinky")])
        if side == "L":
            mount(coll, name, "adr_zad", d, (-0.05, -0.25, 0.38), [("adr_zad", parts["Pv_cs_adr"])])
    tr_animate(tr, r, delay_m)
    tr_keys(root, "Poklopy", [(1, 0.0), (330, 0.0), (390, 1.0), (460, 1.0), (520, 0.0)])
    tr_keys(root, "Dvere_skrinky", [(1, 0.0), (540, 0.0), (580, 1.0), (650, 1.0), (690, 0.0)])
    return r


def _cs_doc():
    lines = ["", "CISTERNOVY VOZIK (Vozik_cisterna_1_5, Vozik_cisterna_3_0: privesny vozik s cisternou v tvare cisternoveho navesu, jedna naprava; pociatok = zem pod stredom gule, predok +X, vozik ide do -X):"]
    for c in CISTERNY.values():
        g = cs_geo(c)
        lines.append("  %s: nadrz %.2f x %.2f x %.2f m (valec %.2f m + dve klenby po %.2f m, %d komory, spodok vo vyske %.2f m), naprava x = %.2f, rozchod %.2f m (kolesa R %.2f), skrinka s ventilmi: zadna rovina x = %.2f, hlbka %.2f m, vyska %.2f m, sirka %.2f m" % (
            c["name"], c["Lb"] + 2 * c["head"], c["Wt"], c["Ht"], c["Lb"], c["head"], c["comps"], CS_ZB, g["xax"], g["track"] * 2.0, c["R"], g["xcab"], CS_CAB_D, CS_CAB_H, 2 * g["hw"]))
    lines += [
        "  Typove diely (uchyt <Vozik>_uchyt_<diel>): ram, plosina (za nadrzou), sedlo (dve kolebky), nadrz (oval s klenbami a obruceami), komin_N (komin poklopu s odvetranim), poklop_N (pivot v osi pantu na zadnom okraji komina, rotacia Y o -Poklopy x 106 st., postupne od zadneho),",
        "    obrubnik (ochranne trubky), bocne_svetla, adr_pred (tabulka ADR vpredu), skrinka (pevne telo), armatura (zberne potrubie s tromi ventilmi, dve potrubia k nadrzi, vypust s hadicovou spojkou - rovnaky rozmer ako na cisternovom naves),",
        "    dvere_skrinky_L / _P (pivot na zavese pri vonkajsej hrane, rotacia Z o -/+ Dvere_skrinky x 100 st.; na lavych dverach je tabulka ADR zadu).",
        "  Spolocne diely (oje, naprava, pero, kolesa, blatniky, naraznik so svetlami ...) ako pri malom vozikoch. Vlastnosti: Poklopy, Dvere_skrinky (0 az 1) + spolocne.",
    ]
    return lines


TRAILERS["cisterna"] = (CISTERNY, cs_rig)
PART_MAKERS.append(cs_parts)
DOC_EXTRA.extend(_cs_doc())
CATALOG_EXTRA.append(("CISTERNOVY VOZIK", ["Pv_cs_%s_%s" % (pp, k) for k in CISTERNY for pp in CS_TAGS] + ["Pv_cs_komin_%s_%d" % (k, i + 1) for k in CISTERNY for i in range(CISTERNY[k]["comps"])] +
                      ["Pv_cs_poklop", "Pv_cs_adr"] + ["Pv_cs_dvere_%s_L" % k for k in CISTERNY] + ["Pv_tr_oje_cs_%s" % k for k in CISTERNY] + ["Pv_tr_naraznik_cs_%s" % k for k in CISTERNY] +
                      [ax_key(cs_geo(c)["track"]) for c in CISTERNY.values()]))


# ---------------------------------------------------------------------------
# Vozik na drevo (privesny vozik na kmene / drevo): dlhy ram s dvoma podlozkami (lozisko), sklopnymi kolikmi na bokoch, naloz z kmenov s retazami, kolesa s oblukovymi blatnikmi.
# Dve velkosti: Vozik_drevo_4_0 (rozpetie podlozok 2.4 m, jedna naprava) a Vozik_drevo_6_0 (3.8 m, tandem).
# ---------------------------------------------------------------------------

DR_XF = -1.40          # predna hrana ramu
DR_ZT = 0.745          # horny povrch podlozky (loze kmenov)
DR_HALF = 0.92         # polsirka podlozky (poloha kolikov)
DREVA = {
    "4_0": dict(key="4_0", name="Vozik_drevo_4_0", span=2.40, R=0.31),
    "6_0": dict(key="6_0", name="Vozik_drevo_6_0", span=3.80, R=0.31),
}


def dr_geo(d):
    xb1 = DR_XF - 0.40
    xb2 = xb1 - d["span"]
    xc = (xb1 + xb2) * 0.5
    axles = [xc - 0.10] if d["span"] < 3.0 else [xc - 0.10 + 0.55, xc - 0.10 - 0.55]
    track = DR_HALF + 0.045 + 0.13 + 0.02
    xr = xb2 - 0.42
    return dict(xb1=xb1, xb2=xb2, xc=xc, axles=axles, track=track, sy=0.32, xr=xr)


def dr_tr(d):
    g = dr_geo(d)
    return dict(name=d["name"], key="dr_" + d["key"], R=d["R"], axles=g["axles"], track=g["track"], sy=g["sy"],
                oje=dict(xf=DR_XF, hw=0.32, z=0.515, z0=0.60), hang=dict(z=0.48, h=0.14),
                kons=dict(y0=0.30, y1=g["track"] - 0.08, zb=0.64, zt=0.70, yr=g["track"] - 0.10), kons_mat=FRAME,
                bump=dict(x=g["xr"] - 0.09, w=2 * DR_HALF + 0.30, z=0.60),
                markers=[(g["xr"] - 0.05, k * (DR_HALF + 0.058), 0.60, "or") for k in SIDES_LR] + [(g["xb1"] + 0.4, k * 0.364, 0.60, "or") for k in SIDES_LR])


def dr_logs(d):
    # polohy kmenov: (x stred, y, z stred, dlzka, polomer): tri vrstvy 5 + 4 + 3
    g = dr_geo(d)
    r = 0.17
    out = []
    base_len = d["span"] + 1.0
    k = 0
    for row, (count, z) in enumerate(((5, DR_ZT + r), (4, DR_ZT + r + 0.294), (3, DR_ZT + r + 0.588))):
        for i in range(count):
            y = (i - (count - 1) * 0.5) * 0.34
            wob = ((k * 7) % 5 - 2) * 0.06
            ln = base_len + ((k * 3) % 4 - 1.5) * 0.12
            out.append((g["xc"] + wob, y, z, ln, r * (0.95 + 0.05 * ((k * 5) % 3))))
            k += 1
    return out


def build_dr_frame(d):
    # ram: dva podlzniky a priecniky (nosne)
    g = dr_geo(d)
    xr = g["xr"]
    bm = bmesh.new()
    xc, ln = (DR_XF + xr) * 0.5, DR_XF - xr
    for s in SIDES_LR:
        add_box(bm, (ln + 0.06, 0.08, 0.12), (xc, s * 0.32, 0.60), FRAME, bev=0.02)
    for k in range(int(ln / 0.60) + 1):
        add_box(bm, (0.06, 0.64, 0.07), (DR_XF - 0.10 - 0.60 * k, 0.0, 0.58), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_dr_ram_" + d["key"])


def build_dr_bolster(d, which):
    # podlozka (loze kmenov): zahnuty plech s okrajmi, kapsy na kolik a ucha; which 1 = predna, 2 = zadna
    g = dr_geo(d)
    xb = g["xb1"] if which == 1 else g["xb2"]
    bm = bmesh.new()
    saddle = [(-DR_HALF - 0.02, 0.64), (-DR_HALF - 0.02, 0.80), (-DR_HALF + 0.06, 0.80), (-DR_HALF + 0.08, DR_ZT), (DR_HALF - 0.08, DR_ZT),
              (DR_HALF - 0.06, 0.80), (DR_HALF + 0.02, 0.80), (DR_HALF + 0.02, 0.64)]
    add_extruded_yz(bm, saddle, xb - 0.09, xb + 0.09, FRAME, bev=0.014)
    for s in SIDES_LR:
        add_box(bm, (0.13, 0.10, 0.10), (xb, s * DR_HALF, 0.69), STEEL, bev=0.014)
        add_cylinder(bm, 0.022, 0.12, along_x((xb, s * DR_HALF, DR_ZT + 0.03)), STEEL, segments=10)
    return finish_mesh(bm, "SM_Pv_dr_podlozka_%s_%d" % (d["key"], which))


def build_dr_stakes(d):
    # kolik na jednej strane (lava; prava je zrkadlo): dva kolky (pri prednej a zadnej podlozke) spojene na pivote v osi X (y = polsirka, z = horny povrch podlozky); stoja nahor, sklapaju sa von
    g = dr_geo(d)
    bm = bmesh.new()
    for xb in (g["xb1"], g["xb2"]):
        x = xb - g["xc"]
        add_rod(bm, (x, 0.0, 0.0), (x, 0.03, 1.08), 0.030, STEEL, segments=10)
        add_box(bm, (0.07, 0.07, 0.05), (x, 0.03, 1.09), STEEL, bev=0.012)
        add_box(bm, (0.06, 0.04, 0.05), (x, -0.02, 0.45), STEEL, bev=0.008)
        add_cylinder(bm, 0.02, 0.10, along_x((x, 0.0, 0.0)), STEEL, segments=8)
    return bm


def add_log(bm, c, r, length):
    # kmen: valec s mierne rozdielnymi polomermi koncov, plast = kora, celne plochy = rez dreva
    seg = 10
    verts = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r * 0.96, radius2=r * 1.04, depth=length, matrix=along_x(c))["verts"]
    for f in faces_of(verts):
        f.material_index = WOODCUT if len(f.verts) == seg else BARK


def build_dr_load(d):
    # naklad: kmene (3 vrstvy) a dva retazove popruhy cez vrch pri podlozkach
    g = dr_geo(d)
    bm = bmesh.new()
    for x, y, z, ln, r in dr_logs(d):
        add_log(bm, (x, y, z), r, ln)
    ztop = DR_ZT + 0.17 * 2 + 0.588 + 0.03
    for xb in (g["xb1"], g["xb2"]):
        for s in SIDES_LR:
            add_rod(bm, (xb + 0.12, s * (DR_HALF - 0.02), 1.09 + DR_ZT), (xb + 0.12, 0.0, ztop), 0.012, STRAP, segments=6)
        add_box(bm, (0.08, 0.10, 0.06), (xb + 0.12, 0.0, ztop), STEEL, bev=0.012)
    return finish_mesh(bm, "SM_Pv_dr_naklad_" + d["key"])


def dr_parts(put, put_lr):
    for d in DREVA.values():
        tr_type_parts(put, put_lr, dr_tr(d))
        put(build_dr_frame(d))
        put(build_dr_bolster(d, 1))
        put(build_dr_bolster(d, 2))
        put_lr(build_dr_stakes(d), "SM_Pv_dr_koliky_" + d["key"])
        put(build_dr_load(d))


def dr_rig(coll, d, parts, mats, ball_src, x_pos, y_pos, delay_m):
    g = dr_geo(d)
    key_, name = d["key"], d["name"]
    tr = dr_tr(d)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, prop = r["root"], r["body"], r["prop"]
    set_prop(root, "Koliky", 0.0, 0.0, 1.0, "Koliky: 0 = stoja nahor, 1 = sklopene von (95 st.)")
    set_prop(root, "Naklad", 1.0, 0.0, 1.0, "Naklad kmenov: 1 = nalozeny, 0 = prazdny")
    o0 = tl((0.0, 0.0, 0.0))
    mount(coll, name, "ram", body, o0, [("ram", parts["Pv_dr_ram_" + key_])])
    for i in (1, 2):
        mount(coll, name, "podlozka_%d" % i, body, o0, [("podlozka_%d" % i, parts["Pv_dr_podlozka_%s_%d" % (key_, i)])])
    for s, side in ((1.0, "L"), (-1.0, "P")):
        st, _ = mount(coll, name, "koliky_" + side, body, tl((g["xc"], s * DR_HALF, DR_ZT + 0.015)), [("koliky_" + side, parts["Pv_dr_koliky_%s_%s" % (key_, side)])])
        driver(st, "rotation_euler", 0, "%.0f * k * 1.66" % -s, [prop("k", "Koliky")])
    load, objs = mount(coll, name, "naklad", body, o0, [("naklad", parts["Pv_dr_naklad_" + key_])])
    for attr in ("hide_viewport", "hide_render"):
        driver(objs[0], attr, -1, "n < 0.5", [prop("n", "Naklad")])
    tr_animate(tr, r, delay_m)
    tr_keys(root, "Koliky", [(1, 0.0), (330, 0.0), (370, 1.0), (440, 1.0), (480, 0.0)])
    tr_keys(root, "Naklad", [(1, 1.0), (520, 1.0), (521, 0.0), (640, 0.0), (641, 1.0)])
    return r


def _dr_doc():
    lines = ["", "VOZIK NA DREVO (Vozik_drevo_4_0, Vozik_drevo_6_0: privesny vozik na kmene; pociatok = zem pod stredom gule, predok +X, vozik ide do -X):"]
    for d in DREVA.values():
        g = dr_geo(d)
        lines.append("  %s: rozpetie podlozok %.2f m (x = %.2f a %.2f), naprav %d (x = %s), rozchod %.2f m (kolesa R %.2f), %d kmenov dlhych asi %.1f m" % (
            d["name"], d["span"], g["xb1"], g["xb2"], len(g["axles"]), ", ".join("%.2f" % x for x in g["axles"]), g["track"] * 2.0, d["R"], len(dr_logs(d)), d["span"] + 1.0))
    lines += [
        "  Typove diely (uchyt <Vozik>_uchyt_<diel>): ram, podlozka_1 / _2 (loze kmenov pri prednej a zadnej podlozke), koliky_L / _P (2 koliky na strane, pivot v osi X nad okrajom podlozky y = +-%.2f, z = %.2f, rotacia X o -/+ Koliky x 95 st.), naklad." % (DR_HALF, DR_ZT),
        "  Naklad (Pv_dr_naklad_<kluc>): 12 kmenov v troch vrstvach s retazovymi popruhmi; viditelnost riadi vlastnost Naklad (1 / 0). Vlastnosti: Koliky, Naklad + spolocne (Koleso_otocenie, Opierne_koleso, Spojka).",
        "  Spolocne diela (oje, naprava, pera, kolesa, blatniky, naraznik so svetlami ...) ako pri malom vozikoch.",
    ]
    return lines


TRAILERS["drevo"] = (DREVA, dr_rig)
PART_MAKERS.append(dr_parts)
DOC_EXTRA.extend(_dr_doc())
CATALOG_EXTRA.append(("VOZIK NA DREVO", ["Pv_dr_%s_%s" % (pp, k) for k in DREVA for pp in ("ram", "naklad")] + ["Pv_dr_podlozka_%s_%d" % (k, i) for k in DREVA for i in (1, 2)] +
                      ["Pv_dr_koliky_%s_%s" % (k, sd) for k in DREVA for sd in ("L", "P")] + ["Pv_tr_oje_dr_%s" % k for k in DREVA] + ["Pv_tr_naraznik_dr_%s" % k for k in DREVA] +
                      [ax_key(dr_geo(d)["track"]) for d in DREVA.values()]))


# ---------------------------------------------------------------------------
# Skrinovy vozik (zatvoreny privesny vozik na naradie, motorku, zahradu): biela skrina so zaoblenou strechou, zadna rampa na pante (sklopi sa na zem),
# bocne dvere vpravo, vetrak na streche, oblukove blatniky, oje s opiernym kolesom a spojkou.
# Dve velkosti: Vozik_skrina_2_5 (skrina 2.5 m, jedna naprava) a Vozik_skrina_3_6 (3.6 m, tandem).
# ---------------------------------------------------------------------------

SK_XF = -1.20          # predna stena skrine
SK_ZF = 0.66           # horny povrch podlahy
SKRINE = {
    "2_5": dict(key="2_5", name="Vozik_skrina_2_5", Lb=2.50, Wb=1.40, Hb=1.45, R=0.30),
    "3_6": dict(key="3_6", name="Vozik_skrina_3_6", Lb=3.60, Wb=1.70, Hb=1.65, R=0.31),
}


def sk_geo(s):
    xr = SK_XF - s["Lb"]
    xc = (xr + SK_XF) * 0.5
    axles = [xc - 0.10] if s["Lb"] < 3.0 else [xc + 0.45, xc - 0.65]
    track = s["Wb"] * 0.5 + 0.165
    sy = s["Wb"] * 0.5 - 0.20
    xdf = SK_XF - 0.55
    xdr = xdf - 0.80
    return dict(xr=xr, xc=xc, axles=axles, track=track, sy=sy, xdf=xdf, xdr=xdr, hd=s["Hb"] - 0.20, ztop=SK_ZF + s["Hb"] + 0.05)


def sk_tr(s):
    g = sk_geo(s)
    Wb = s["Wb"]
    top = SK_ZF + s["Hb"]
    return dict(name=s["name"], key="sk_" + s["key"], R=s["R"], axles=g["axles"], track=g["track"], sy=g["sy"],
                oje=dict(xf=SK_XF, hw=g["sy"], z=0.515, z0=0.54), hang=dict(z=0.46, h=0.14),
                kons=dict(y0=g["sy"] - 0.02, y1=g["track"] - 0.08, zb=0.63, zt=0.69, yr=g["track"] - 0.10), kons_mat=FRAME,
                bump=dict(x=g["xr"] - 0.10, w=Wb + 0.40, z=0.44),
                markers=[(g["xc"], k * (Wb * 0.5 + 0.007), SK_ZF + 0.24, "or") for k in SIDES_LR] + [(SK_XF, k * (Wb * 0.5 - 0.04), top, "white") for k in SIDES_LR])


def build_sk_frame(s):
    # ram: dva podlzniky a priecniky (nosne)
    g = sk_geo(s)
    Lb, Wb, xr = s["Lb"], s["Wb"], g["xr"]
    bm = bmesh.new()
    for k in (-1.0, 1.0):
        add_box(bm, (Lb + 0.10, 0.07, 0.12), (g["xc"], k * g["sy"], 0.54), FRAME, bev=0.02)
    for i in range(int(Lb / 0.55) + 1):
        add_box(bm, (0.06, Wb - 0.34, 0.07), (SK_XF - 0.10 - 0.55 * i, 0.0, 0.55), FRAME, bev=0.012)
    return finish_mesh(bm, "SM_Pv_sk_ram_" + s["key"])


def build_sk_floor(s):
    # podlaha (preglejka) so zachytnymi listami a vnutornymi kotviacimi kolajnicami
    g = sk_geo(s)
    Lb, Wb = s["Lb"], s["Wb"]
    bm = bmesh.new()
    add_box(bm, (Lb, Wb, 0.06), (g["xc"], 0.0, SK_ZF - 0.03), PLY, bev=0.012)
    for k in range(int(Lb / 0.14)):
        add_box(bm, (0.03, Wb - 0.12, 0.008), (SK_XF - 0.10 - 0.14 * k, 0.0, SK_ZF + 0.004), DARK)
    return finish_mesh(bm, "SM_Pv_sk_podlaha_" + s["key"])


def sk_wall(bm, s, x_front, x_rear, y_sign, with_rails=True):
    # kus steny: plech s rebrami, spodnym plechom a kotviacou kolajnicou vo vnutri
    Wb, Hb = s["Wb"], s["Hb"]
    t = 0.04
    xm, ln = (x_front + x_rear) * 0.5, x_front - x_rear
    zc = SK_ZF + Hb * 0.5
    add_box(bm, (ln, t, Hb), (xm, y_sign * (Wb * 0.5 - t * 0.5), zc), PAINT_WHITE, bev=0.02)
    add_box(bm, (ln + 0.02, 0.012, 0.14), (xm, y_sign * (Wb * 0.5 + 0.004), SK_ZF + 0.07), GRAY, bev=0.006)
    for z in (0.35, 0.65):
        add_box(bm, (max(ln - 0.20, 0.1), 0.012, 0.035), (xm, y_sign * (Wb * 0.5 + 0.002), SK_ZF + Hb * z), ALU, bev=0.004)
    if with_rails:
        for z in (0.35, 0.70):
            add_box(bm, (max(ln - 0.12, 0.1), 0.012, 0.03), (xm, y_sign * (Wb * 0.5 - t - 0.006), SK_ZF + z), STEEL, bev=0.004)


def build_sk_wall_l(s):
    g = sk_geo(s)
    bm = bmesh.new()
    sk_wall(bm, s, SK_XF, g["xr"], 1.0)
    return finish_mesh(bm, "SM_Pv_sk_stena_L_" + s["key"])


def build_sk_wall_rf(s):
    g = sk_geo(s)
    bm = bmesh.new()
    sk_wall(bm, s, SK_XF, g["xdf"], -1.0)
    return finish_mesh(bm, "SM_Pv_sk_stena_P_pred_" + s["key"])


def build_sk_wall_rr(s):
    g = sk_geo(s)
    bm = bmesh.new()
    sk_wall(bm, s, g["xdr"], g["xr"], -1.0)
    return finish_mesh(bm, "SM_Pv_sk_stena_P_zad_" + s["key"])


def build_sk_lintel(s):
    # nadvlak nad bocnymi dverami
    g = sk_geo(s)
    Wb, Hb = s["Wb"], s["Hb"]
    bm = bmesh.new()
    add_box(bm, (g["xdf"] - g["xdr"], 0.04, Hb - g["hd"]), ((g["xdf"] + g["xdr"]) * 0.5, -Wb * 0.5 + 0.02, SK_ZF + g["hd"] + (Hb - g["hd"]) * 0.5), PAINT_WHITE, bev=0.02)
    return finish_mesh(bm, "SM_Pv_sk_nadvlak_" + s["key"])


def build_sk_front(s):
    # predna stena
    Wb, Hb = s["Wb"], s["Hb"]
    bm = bmesh.new()
    add_box(bm, (0.04, Wb, Hb), (SK_XF - 0.02, 0.0, SK_ZF + Hb * 0.5), PAINT_WHITE, bev=0.03)
    return finish_mesh(bm, "SM_Pv_sk_predna_" + s["key"])


def build_sk_roof(s):
    # strecha: priecny rez s klenutim a zaoblenymi hranami, presahuje o 2 cm
    g = sk_geo(s)
    Wb, Hb = s["Wb"], s["Hb"]
    top = SK_ZF + Hb
    roof = [(-Wb * 0.5 - 0.02, top - 0.04), (-Wb * 0.5 - 0.02, top + 0.02), (-Wb * 0.5 + 0.08, top + 0.055), (-0.35, top + 0.075), (0.35, top + 0.075), (Wb * 0.5 - 0.08, top + 0.055),
            (Wb * 0.5 + 0.02, top + 0.02), (Wb * 0.5 + 0.02, top - 0.04)]
    bm = bmesh.new()
    add_extruded_yz(bm, roof, g["xr"] - 0.02, SK_XF + 0.03, PAINT_WHITE, bev=0.02)
    return finish_mesh(bm, "SM_Pv_sk_strecha_" + s["key"])


def build_sk_vent(s):
    # strosny vetrak
    g = sk_geo(s)
    top = SK_ZF + s["Hb"]
    bm = bmesh.new()
    add_box(bm, (0.50, 0.40, 0.04), (g["xc"], 0.0, top + 0.095), ALU, bev=0.025)
    add_box(bm, (0.36, 0.28, 0.025), (g["xc"], 0.0, top + 0.125), GRAY, bev=0.012)
    return finish_mesh(bm, "SM_Pv_sk_vetrak_" + s["key"])


def build_sk_trim(s):
    # rohove listy (4 stlpiky) a horny ram zadneho otvoru
    g = sk_geo(s)
    Wb, Hb = s["Wb"], s["Hb"]
    zc = SK_ZF + Hb * 0.5
    top = SK_ZF + Hb
    bm = bmesh.new()
    for k in (-1.0, 1.0):
        add_box(bm, (0.05, 0.05, Hb + 0.02), (SK_XF - 0.015, k * (Wb * 0.5 - 0.005), zc), ALU, bev=0.02)
        add_box(bm, (0.05, 0.05, Hb + 0.02), (g["xr"] + 0.02, k * (Wb * 0.5 - 0.005), zc), ALU, bev=0.02)
    add_box(bm, (0.08, Wb - 0.04, 0.07), (g["xr"] + 0.01, 0.0, top - 0.02), ALU, bev=0.015)
    return finish_mesh(bm, "SM_Pv_sk_listy_" + s["key"])


def build_sk_ramp(s):
    # zadna rampa / dvere: pivot na spodnom pante (x = zadna hrana, z = podlaha), stoji nahor; pri otvoreni sa sklopi dozadu o 116 st. a lezie na zemi; na vnutornej strane protismykove listy
    Wb, hd = s["Wb"], s["Hb"] - 0.12
    bm = bmesh.new()
    add_box(bm, (0.05, Wb - 0.06, hd), (-0.025, 0.0, hd * 0.5), PAINT_WHITE, bev=0.02)
    add_box(bm, (0.06, Wb - 0.02, 0.05), (-0.025, 0.0, hd - 0.025), ALU, bev=0.012)
    add_box(bm, (0.06, Wb - 0.02, 0.05), (-0.025, 0.0, 0.025), ALU, bev=0.012)
    for k in (-1.0, 1.0):
        add_box(bm, (0.06, 0.05, hd), (-0.025, k * (Wb * 0.5 - 0.055), hd * 0.5), ALU, bev=0.012)
    add_box(bm, (0.012, Wb - 0.30, 0.04), (-0.056, 0.0, hd * 0.55), ALU, bev=0.004)
    for z in (0.15, 0.35, 0.55, 0.75, 0.95):
        if z < hd - 0.05:
            add_box(bm, (0.014, Wb - 0.20, 0.035), (0.007, 0.0, z * hd / 1.0 if z * hd < hd - 0.06 else hd - 0.1), DARK, bev=0.003)
    for k in (-1.0, 1.0):
        add_box(bm, (0.06, 0.08, 0.05), (-0.03, k * 0.22, hd - 0.10), STEEL, bev=0.01)                 # zamok
        add_cylinder(bm, 0.022, 0.09, along_y((0.0, k * (Wb * 0.25), 0.0)), STEEL, segments=10)         # pant
    return finish_mesh(bm, "SM_Pv_sk_rampa_" + s["key"])


def build_sk_door(s):
    # bocne dvere (prava strana): pivot na zavese na prednej hrane otvoru (x = 0), panel siaha do -X; vonkajsia strana v y = -(sirka / 2)
    hd, wd = sk_geo(s)["hd"], 0.80
    bm = bmesh.new()
    add_box(bm, (wd - 0.02, 0.04, hd - 0.02), (-wd * 0.5, -0.02, hd * 0.5), PAINT_WHITE, bev=0.02)
    add_box(bm, (wd - 0.14, 0.012, 0.045), (-wd * 0.5, -0.045, hd * 0.55), ALU, bev=0.004)
    add_box(bm, (0.14, 0.04, 0.05), (-wd + 0.12, -0.056, hd * 0.50), CHROME, bev=0.012)
    add_cylinder(bm, 0.016, 0.04, along_y((-wd + 0.07, -0.05, hd * 0.50)), STEEL, segments=8)
    for z in (0.18, hd - 0.18):
        add_cylinder(bm, 0.016, 0.10, along_z((0.0, -0.01, z)), STEEL, segments=8)
    return finish_mesh(bm, "SM_Pv_sk_dvere_" + s["key"])


def sk_parts(put, put_lr):
    for s in SKRINE.values():
        tr_type_parts(put, put_lr, sk_tr(s))
        for fn in (build_sk_frame, build_sk_floor, build_sk_wall_l, build_sk_wall_rf, build_sk_wall_rr, build_sk_lintel, build_sk_front, build_sk_roof, build_sk_vent, build_sk_trim,
                   build_sk_ramp, build_sk_door):
            put(fn(s))


SK_TAGS = (("ram", "ram"), ("podlaha", "podlaha"), ("stena_L", "stena_L"), ("stena_P_pred", "stena_P_pred"), ("stena_P_zad", "stena_P_zad"), ("nadvlak", "nadvlak"),
           ("predna_stena", "predna"), ("strecha", "strecha"), ("vetrak", "vetrak"), ("listy", "listy"))


def sk_rig(coll, s, parts, mats, ball_src, x_pos, y_pos, delay_m):
    g = sk_geo(s)
    key_, name = s["key"], s["name"]
    tr = sk_tr(s)
    r = tr_rig(coll, tr, parts, mats, ball_src, x_pos, y_pos, delay_m)
    root, body, prop = r["root"], r["body"], r["prop"]
    set_prop(root, "Rampa", 0.0, 0.0, 1.0, "Zadna rampa: 0 = zatvorena, 1 = sklopena na zem (116 st.)")
    set_prop(root, "Dvere", 0.0, 0.0, 1.0, "Bocne dvere: 0 = zatvorene, 1 = otvorene (100 st.)")
    o0 = tl((0.0, 0.0, 0.0))
    for tag, mk in SK_TAGS:
        mount(coll, name, tag, body, o0, [(tag, parts["Pv_sk_%s_%s" % (mk, key_)])])
    ramp, _ = mount(coll, name, "rampa", body, tl((g["xr"], 0.0, SK_ZF)), [("rampa", parts["Pv_sk_rampa_" + key_])])
    driver(ramp, "rotation_euler", 1, "-r * 2.025", [prop("r", "Rampa")])
    door, _ = mount(coll, name, "dvere", body, tl((g["xdf"], -s["Wb"] * 0.5, SK_ZF + 0.01)), [("dvere", parts["Pv_sk_dvere_" + key_])])
    driver(door, "rotation_euler", 2, "d * 1.75", [prop("d", "Dvere")])
    tr_animate(tr, r, delay_m)
    tr_keys(root, "Rampa", [(1, 0.0), (330, 0.0), (380, 1.0), (450, 1.0), (500, 0.0)])
    tr_keys(root, "Dvere", [(1, 0.0), (520, 0.0), (560, 1.0), (620, 1.0), (660, 0.0)])
    return r


def _sk_doc():
    lines = ["", "SKRINOVY VOZIK (Vozik_skrina_2_5, Vozik_skrina_3_6: zatvoreny privesny vozik; pociatok = zem pod stredom gule, predok +X, vozik ide do -X):"]
    for s in SKRINE.values():
        g = sk_geo(s)
        lines.append("  %s: skrina %.2f x %.2f x %.2f m (podlaha vo vyske %.2f m), naprav %d (x = %s), rozchod %.2f m (kolesa R %.2f), bocne dvere v x = %.2f az %.2f" % (
            s["name"], s["Lb"], s["Wb"], s["Hb"], SK_ZF, len(g["axles"]), ", ".join("%.2f" % x for x in g["axles"]), g["track"] * 2.0, s["R"], g["xdf"], g["xdr"]))
    lines += [
        "  Typove diely (uchyt <Vozik>_uchyt_<diel>): ram, podlaha, stena_L, stena_P_pred, stena_P_zad, nadvlak (nad dverami), predna_stena, strecha, vetrak, listy (rohove listy), rampa, dvere.",
        "  Zadna rampa: pivot na spodnom pante (x = zadna hrana, z = podlaha), rotacia Y o -Rampa x 116 st. (lezi na zemi, vnutorna strana s protismykovymi listami je hore).",
        "  Bocne dvere (vpravo): pivot na zavese pri prednej hrane otvoru, rotacia Z o +Dvere x 100 st. Vlastnosti: Rampa, Dvere (0 az 1) + spolocne. Spolocne diela (oje, naprava, pero, kolesa, blatniky, naraznik so svetlami ...) ako pri malom vozikoch.",
    ]
    return lines


TRAILERS["skrina"] = (SKRINE, sk_rig)
PART_MAKERS.append(sk_parts)
DOC_EXTRA.extend(_sk_doc())
CATALOG_EXTRA.append(("SKRINOVY VOZIK", ["Pv_sk_%s_%s" % (mk, k) for k in SKRINE for mk in ("ram", "podlaha", "stena_L", "stena_P_pred", "stena_P_zad", "nadvlak", "predna", "strecha", "vetrak", "listy", "rampa", "dvere")] +
                      ["Pv_tr_oje_sk_%s" % k for k in SKRINE] + ["Pv_tr_naraznik_sk_%s" % k for k in SKRINE] + [ax_key(sk_geo(s)["track"]) for s in SKRINE.values()]))


# ---------------------------------------------------------------------------
# Rozmiestnenie privesov v scene: zapriahnute za pickupom (gula pickupu riadi telo privesu) a samostatne v dalsich radoch
# ---------------------------------------------------------------------------

STANDALONE_X = -4.6
TRAILER_PLAN = [
    ("vozik", "2_6", "jednokabina", -6.0),
    ("podval", "4_0", "dvojkabina", 0.0),
    ("vozik", "2_0", None, -12.0),
    ("podval", "5_2", None, -18.0),
    ("palety", "3_0", None, -24.0),
    ("palety", "4_2", None, -30.0),
    ("cisterna", "1_5", None, -36.0),
    ("cisterna", "3_0", None, -42.0),
    ("drevo", "4_0", None, -48.0),
    ("drevo", "6_0", None, -54.0),
    ("skrina", "2_5", None, -60.0),
    ("skrina", "3_6", None, -66.0),
]


def trailer_scene(coll, parts, mats):
    roots = []
    for typ, key, hitch, y in TRAILER_PLAN:
        if typ not in TRAILERS:
            continue
        variants, rig = TRAILERS[typ]
        v = variants[key]
        sub = child_collection(coll, v["name"])
        if hitch:
            pk = PK_RIGS[hitch]
            r = rig(sub, v, parts, mats, pk["ball"], pk_ball_x(pk["pk"]), pk["pk"]["y"], pk["pk"]["wb"] + 1.60)
        else:
            r = rig(sub, v, parts, mats, None, STANDALONE_X, y, 0.0)
        roots.append(r["root"])
    return roots


SCENE_BUILDERS.append(trailer_scene)


# ---------------------------------------------------------------------------
# Zostavenie sceny, katalog dielov, export
# ---------------------------------------------------------------------------

def build_parts(mats):
    built = {}

    def put(mesh):
        key_ = mesh.name[3:].split(".")[0]
        if key_ in built:
            bpy.data.meshes.remove(mesh)       # zdielany diel (napr. naprava) sa postavi len raz
            return
        built[key_] = mesh

    def put_lr(bm, name):
        mirrored = mirror_y(bm)
        put(finish_mesh(bm, name + "_L"))
        put(finish_mesh(mirrored, name + "_P"))

    for maker in PART_MAKERS:
        maker(put, put_lr)
    for mesh in built.values():
        mesh["pickup_vozik"] = 1
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
    scene.frame_start, scene.frame_end = 1, 1000
    scene.frame_set(1)

    kit = child_collection(coll, "Pickup_vozik_diely")
    lines = ["Pickup a voziky - diely (rozmery X x Y x Z v metroch). Predok = +X, lava = +Y.", ""]
    y_cursor = 3.0
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
        with open(os.path.join(EXPORT_DIR, "Pickup_vozik.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Ulozene do:", EXPORT_DIR)
    select_only(roots[0])
    print("\n".join(lines))


main()
