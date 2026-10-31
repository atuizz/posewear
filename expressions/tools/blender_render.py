"""Headless Blender renderer for PoseWear expression library.
Usage: blender -b -P blender_render.py -- jobs.json
jobs.json: {"npz":..., "faces":..., "out_tmp":..., "jobs":[{"key":..., "weights":{...}, "angle":...}]}
Per job writes <out_tmp>/<key>_src.png (RGBA), <key>_z.npy (float32 camera depth), <key>_uv.npy (projected 2D px for all verts)
"""
import bpy, sys, json, os, math, numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rig

args = json.load(open(sys.argv[sys.argv.index('--') + 1]))
W, H = rig.W, rig.H
data = np.load(args['npz'])
base, deltas, names = data['base'], data['deltas'], [str(n) for n in data['names']]
F = json.load(open(args['faces']))
keep = [(f, m) for f, m in zip(F['faces'], F['mats']) if m in rig.KEEP_MATS]
faces = [f for f, m in keep]
os.makedirs(args['out_tmp'], exist_ok=True)

# ---- scene ----
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 64
sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
world = bpy.data.worlds.new('w'); sc.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = rig.AMBIENT

me = bpy.data.meshes.new('head')
me.from_pydata(base.tolist(), [], faces)
me.update()
for p in me.polygons: p.use_smooth = True
ob = bpy.data.objects.new('head', me); sc.collection.objects.link(ob)
mat = bpy.data.materials.new('gray_lambert'); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
d = nt.nodes.new('ShaderNodeBsdfDiffuse'); d.inputs[0].default_value = (*[rig.GRAY]*3, 1); d.inputs[1].default_value = 0.0
o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(d.outputs[0], o.inputs[0])
ob.data.materials.append(mat)
wm = ob.modifiers.new('weld', 'WELD'); wm.merge_threshold = 0.0005

# procedural tongue (ICT light rig has no tongue blendshape)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0)
tongue = bpy.context.active_object; tongue.data.materials.append(mat)
for p in tongue.data.polygons: p.use_smooth = True

cam_data = bpy.data.cameras.new('cam'); cam_data.lens = rig.LENS
cam_data.sensor_fit = 'VERTICAL'; cam_data.sensor_height = 36.0
cam_data.clip_start = 1; cam_data.clip_end = 1000
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (rig.PIVOT[0], rig.PIVOT[1], rig.PIVOT[2] + rig.CAM_DIST)
sun_d = bpy.data.lights.new('key', 'SUN'); sun_d.energy = rig.KEY_ENERGY; sun_d.angle = math.radians(15)
for _a in ('use_shadow',):
    if hasattr(sun_d, _a): setattr(sun_d, _a, False)
sun = bpy.data.objects.new('key', sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = tuple(math.radians(a) for a in rig.KEY_ROT)
fill_d = bpy.data.lights.new('fill', 'SUN'); fill_d.energy = rig.FILL_ENERGY; fill_d.use_shadow = False
fill = bpy.data.objects.new('fill', fill_d); sc.collection.objects.link(fill)
fill.rotation_euler = tuple(math.radians(a) for a in rig.FILL_ROT)

vl = sc.view_layers[0]; vl.use_pass_z = True
sc.use_nodes = True
ct = sc.node_tree; ct.nodes.clear()
rl = ct.nodes.new('CompositorNodeRLayers')
comp = ct.nodes.new('CompositorNodeComposite'); ct.links.new(rl.outputs['Image'], comp.inputs[0])
fo = ct.nodes.new('CompositorNodeOutputFile'); fo.format.file_format = 'OPEN_EXR'; fo.format.color_depth = '32'
fo.base_path = args['out_tmp']
ct.links.new(rl.outputs['Depth'], fo.inputs[0])

cam_w2c = None
for j in args['jobs']:
    key = j['key']
    if all(os.path.exists(os.path.join(args['out_tmp'], key + s)) for s in ('_src.png', '_z.npy', '_uv.npy')) and not args.get('force'):
        continue
    V, tinfo = rig.deform(base, deltas, names, j['weights'])
    me.vertices.foreach_set('co', V[:len(me.vertices)].astype(np.float32).ravel())
    me.update()
    R = rig.angle_matrix(j['angle'])  # 3x3, rotation about pivot
    piv = Vector(rig.PIVOT)
    M = Matrix.Translation(piv) @ Matrix(R.tolist()).to_4x4() @ Matrix.Translation(-piv)
    ob.matrix_world = M
    if tinfo is None:
        tongue.hide_render = True
    else:
        tongue.hide_render = False
        tongue.matrix_world = M @ Matrix(tinfo)
    fo.file_slots[0].path = key + '_z_'
    sc.render.filepath = os.path.join(args['out_tmp'], key + '_src.png')
    bpy.ops.render.render(write_still=True)
    # depth from EXR
    exr = os.path.join(args['out_tmp'], key + '_z_%04d.exr' % sc.frame_current)
    img = bpy.data.images.load(exr)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1, :, 0]
    bpy.data.images.remove(img); os.remove(exr)
    np.save(os.path.join(args['out_tmp'], key + '_z.npy'), px)
    # projection of all verts
    Vh = np.c_[V, np.ones(len(V))] @ np.array(M).T
    P = np.array(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=W, y=H)) @ np.array(cam.matrix_world.inverted())
    c = Vh @ P.T
    ndc = c[:, :3] / c[:, 3:4]
    uv = np.c_[(ndc[:, 0] + 1) / 2 * W, (1 - ndc[:, 1]) / 2 * H, c[:, 3]]
    np.save(os.path.join(args['out_tmp'], key + '_uv.npy'), uv.astype(np.float32))
    print('DONE', key, flush=True)
