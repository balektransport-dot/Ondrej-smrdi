# Pomocny skript: spusti model-skript a vyrenderuje nahlad. Pouzitie: python render_preview.py skript.py vystup.png camX camY camZ cielX cielY cielZ
import bpy, runpy, math, sys
from mathutils import Vector
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
script, out = args[0], args[1]
cam_loc = Vector(tuple(float(a) for a in args[2:5]))
target = Vector(tuple(float(a) for a in args[5:8]))
runpy.run_path(script)
sc = bpy.context.scene
for n in ("Cube",):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
floor = bpy.context.active_object
fm = bpy.data.materials.new("Floor")
b = fm.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (0.32, 0.32, 0.30, 1); b.inputs["Roughness"].default_value = 0.9
floor.data.materials.append(fm)
light = bpy.data.objects["Light"]; light.data.type = "SUN"; light.data.energy = 3.0; light.data.angle = math.radians(3)
light.rotation_euler = (math.radians(45), math.radians(15), math.radians(-60))
bg = sc.world.node_tree.nodes.get("Background")
sky = sc.world.node_tree.nodes.new("ShaderNodeTexSky")
sc.world.node_tree.links.new(sky.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.15
cam = bpy.data.objects["Camera"]; cam.location = cam_loc
cam.rotation_euler = (target - cam_loc).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = 35
sc.camera = cam
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 64
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
sc.render.resolution_x = 1000; sc.render.resolution_y = 800
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("render ok", out)
