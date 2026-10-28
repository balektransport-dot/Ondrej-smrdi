# Low poly lopata pre Blender 3.0 a novsi.
#
# Pouzitie: Blender -> zalozka Scripting -> Open (alebo New a vloz text) -> Run Script (Alt+P).
# Vytvori objekt "SM_Lopata" v kolekcii "Lopata" a ulozi ho ako FBX do domovskeho priecinka
# (Windows: C:\Users\<meno>\SM_Lopata.fbx), odkial ho pretiahnes do Unrealu.
# Pivot (pociatok) je v strede rukovate hore - tam ju drzi ruka.
# Skript sa da spustit znova: stara lopata sa nahradi novou.

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

NAME = "SM_Lopata"
COLLECTION = "Lopata"
EXPORT_FBX = True
EXPORT_PATH = os.path.join(os.path.expanduser("~"), NAME + ".fbx")

# Rozmery v metroch
SHAFT_LEN = 0.85    # dlzka porisa
SHAFT_R = 0.017     # hrubka porisa (polomer)
SIDES = 6           # pocet hran valcov - menej = viac low poly
BLADE_W = 0.24      # sirka listu
BLADE_H = 0.31      # vyska listu po spicku

# (nazov, farba, kovovost, drsnost)
MATERIALS = [
    ("Lopata_Drevo", (0.45, 0.27, 0.11, 1.0), 0.0, 0.8),
    ("Lopata_Kov", (0.42, 0.44, 0.47, 1.0), 0.8, 0.45),
    ("Lopata_Rukovat", (0.06, 0.06, 0.06, 1.0), 0.0, 0.7),
]
WOOD, METAL, GRIP = 0, 1, 2


def set_material(faces, index):
    for f in faces:
        f.material_index = index


def faces_of(verts):
    return {f for v in verts for f in v.link_faces}


def add_cylinder(bm, r_bottom, r_top, depth, matrix, mat, segments=SIDES):
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                                radius1=r_bottom, radius2=r_top, depth=depth, matrix=matrix)
    set_material(faces_of(res["verts"]), mat)


def add_box(bm, size, location, mat):
    matrix = Matrix.Translation(Vector(location)) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    res = bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)
    set_material(faces_of(res["verts"]), mat)


def add_blade(bm, top, mat):
    half = BLADE_W * 0.5
    xs = [-half, -half * 0.5, 0.0, half * 0.5, half]
    rows = [
        (top, xs),                                     # horna hrana
        (top - BLADE_H * 0.5, xs),                     # rovne boky
        (top - BLADE_H * 0.8, [x * 0.65 for x in xs]),  # zuzenie k spicke
    ]

    def cup(x):
        # okraje listu su vpredu -> list je jemne prehnuty ako miska
        return 0.025 * (abs(x) / half) ** 2

    grid = [[bm.verts.new((x, cup(x), z)) for x in row_xs] for z, row_xs in rows]
    tip = bm.verts.new((0.0, 0.0, top - BLADE_H))

    faces = []
    for upper, lower in zip(grid, grid[1:]):
        for i in range(len(upper) - 1):
            faces.append(bm.faces.new((upper[i], lower[i], lower[i + 1], upper[i + 1])))
    last = grid[-1]
    for i in range(len(last) - 1):
        faces.append(bm.faces.new((last[i], tip, last[i + 1])))

    # hrubka plechu
    res = bmesh.ops.solidify(bm, geom=faces, thickness=0.007)
    set_material(faces, mat)
    set_material([g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)], mat)


def add_uvs(bm):
    # jednoducha projekcia podla smeru steny (staci pre farby, Unreal nebude hlasit chybajuce UV)
    bm.normal_update()
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        axis = max(range(3), key=lambda i: abs(f.normal[i]))
        for loop in f.loops:
            co = loop.vert.co
            u, v = ((co.y, co.z), (co.x, co.z), (co.x, co.y))[axis]
            loop[uv].uv = (u * 4.0, v * 4.0)


def build_mesh():
    bm = bmesh.new()
    rot_x = Matrix.Rotation(math.radians(90.0), 4, "Y")  # valec polozeny pozdlz osi X

    # rukovat (T) - pivot je v jej strede
    add_cylinder(bm, 0.017, 0.017, 0.13, rot_x, GRIP)
    # kovovy kruzok pod rukovatou
    add_cylinder(bm, 0.021, 0.021, 0.03, Matrix.Translation((0.0, 0.0, -0.035)), METAL)
    # porisko
    add_cylinder(bm, SHAFT_R, SHAFT_R, SHAFT_LEN, Matrix.Translation((0.0, 0.0, -0.01 - SHAFT_LEN * 0.5)), WOOD)
    # objimka medzi poriskom a listom (dole sirsia)
    add_cylinder(bm, 0.032, 0.021, 0.12, Matrix.Translation((0.0, 0.0, -SHAFT_LEN - 0.06)), METAL)

    blade_top = -SHAFT_LEN - 0.11
    add_blade(bm, blade_top, METAL)
    # nasliapnutie na hornej hrane listu
    add_box(bm, (BLADE_W, 0.03, 0.014), (0.0, 0.012, blade_top), METAL)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    add_uvs(bm)

    mesh = bpy.data.meshes.new(NAME)
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False  # ostre hrany = low poly vzhlad
    return mesh


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


def remove_old():
    old = bpy.data.objects.get(NAME)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)


def main():
    remove_old()

    scene = bpy.context.scene
    coll = bpy.data.collections.get(COLLECTION) or bpy.data.collections.new(COLLECTION)
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)

    obj = bpy.data.objects.new(NAME, build_mesh())
    for name, color, metallic, roughness in MATERIALS:
        obj.data.materials.append(get_material(name, color, metallic, roughness))
    coll.objects.link(obj)

    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if EXPORT_FBX:
        try:
            bpy.ops.export_scene.fbx(filepath=EXPORT_PATH, use_selection=True, object_types={"MESH"},
                                     apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE")
            print("Lopata ulozena:", EXPORT_PATH)
        except Exception as error:
            print("FBX sa nepodarilo ulozit:", error)

    print("Hotovo: %s (%d vrcholov, %d stien)" % (NAME, len(obj.data.vertices), len(obj.data.polygons)))


main()
