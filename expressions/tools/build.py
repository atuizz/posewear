#!/usr/bin/env python3
"""PoseWear 表情库构建：python3 tools/build.py [--only id1,id2] [--angles front,...] [--defs expressions.json] [--force]
步骤：解析 ICT-FaceKit → Blender 无头渲染 → 深度图/线稿/manifest/联系表。"""
import argparse, json, os, subprocess, sys, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); import rig
ap = argparse.ArgumentParser()
ap.add_argument('--defs', default=os.path.join(HERE, 'expressions.json'))
ap.add_argument('--ict', default=os.environ.get('ICT_FACEKIT', '/workspace/ICT-FaceKit'))
ap.add_argument('--blender', default=os.environ.get('BLENDER', '/workspace/blender/blender'))
ap.add_argument('--only', default=''); ap.add_argument('--angles', default=','.join(rig.ANGLES))
ap.add_argument('--force', action='store_true'); ap.add_argument('--skip-render', action='store_true')
a = ap.parse_args()
CACHE = os.path.join(ROOT, '.cache'); os.makedirs(CACHE, exist_ok=True)
NPZ, FJ = os.path.join(CACHE, 'ict.npz'), os.path.join(CACHE, 'faces.json')
COMMIT = subprocess.run(['git', '-C', a.ict, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip() or 'unknown'

def parse_ict():
    D = os.path.join(a.ict, 'FaceXModel') + '/'
    rv = lambda p: np.array([l.split()[1:4] for l in open(p) if l.startswith('v ')], dtype=np.float64)
    names = json.load(open(D + 'vertex_indices.json'))['expressions']
    base = rv(D + 'generic_neutral_mesh.obj')  # mean face = all identity coefficients zero; identity*.obj never read
    deltas = np.stack([rv(D + n + '.obj') - base for n in names]).astype(np.float32)
    faces, mats, cur = [], [], None
    for l in open(D + 'generic_neutral_mesh.obj'):
        if l.startswith('usemtl'): cur = l.split()[1]
        elif l.startswith('f '): faces.append([int(t.split('/')[0]) - 1 for t in l.split()[1:]]); mats.append(cur)
    np.savez(NPZ, base=base, deltas=deltas, names=np.array(names)); json.dump({'faces': faces, 'mats': mats}, open(FJ, 'w'))
if not os.path.exists(NPZ): parse_ict()
names = [str(n) for n in np.load(NPZ)['names']]

def expand(w):
    out = {}
    for k, v in w.items():
        if k in names or k in ('eyeRollUp', 'tongueOut'): out[k] = out.get(k, 0) + v
        elif k + '_L' in names: out[k + '_L'] = out.get(k + '_L', 0) + v; out[k + '_R'] = out.get(k + '_R', 0) + v
        else: raise SystemExit('unknown blendshape: ' + k)
    return {k: round(min(v, 1.0), 3) for k, v in sorted(out.items())}

defs = json.load(open(a.defs)); angles = a.angles.split(','); only = set(filter(None, a.only.split(',')))
TMP = os.path.join(CACHE, 'renders')
jobs = []
for pack in ('general', 'adult'):
    for e in defs.get(pack, []):
        e['_w'] = expand(e['weights'])
        if only and e['id'] not in only: continue
        for ang in angles: jobs.append({'key': f"{e['id']}_{ang}", 'weights': e['_w'], 'angle': ang})
if not a.skip_render and jobs:
    jf = os.path.join(CACHE, 'jobs.json')
    json.dump({'npz': NPZ, 'faces': FJ, 'out_tmp': TMP, 'force': a.force, 'jobs': jobs}, open(jf, 'w'))
    subprocess.run([a.blender, '-b', '-noaudio', '-P', os.path.join(HERE, 'blender_render.py'), '--', jf], check=True, stdout=subprocess.DEVNULL)

# ---------- landmarks (fixed ICT vertex ids -> MediaPipe-style contour groups) ----------
L68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
def oval_ids():
    """jawline = Multi-PIE 0..16; forehead arc = front-facing verts nearest to an ellipse through the jaw ends."""
    base = np.load(NPZ)['base'][:9409]
    j0, j16 = base[L68[0]], base[L68[16]]; brow = base[[L68[i] for i in range(17, 27)], 1].max()
    cy = (j0[1] + j16[1]) / 2; ax = (j16[0] - j0[0]) / 2; top = brow + 0.75 * (brow - base[L68[8], 1]) * 0.5
    front = np.where(base[:, 2] > 4.0)[0]
    ids = list(L68[0:17])
    for t in np.linspace(0, np.pi, 15)[1:-1]:  # from subject-left (j16) over the top to subject-right (j0)
        p = np.array([ax * np.cos(t), cy + (top - cy) * np.sin(t)])
        k = front[np.argmin(np.linalg.norm(base[front, :2] - p, axis=1) - 0.05 * base[front, 2])]
        ids.append(int(k))
    return ids
OVAL = oval_ids()
COL = {'oval': (10, 200, 10), 'r_eye': (10, 200, 180), 'r_brow': (10, 220, 180), 'l_eye': (180, 200, 10), 'l_brow': (180, 220, 10),
       'mouth': (10, 180, 10), 'r_iris': (10, 200, 250), 'l_iris': (250, 200, 10)}
G = {  # subject-right = 68pt 36-41 (image left in front view)
    'oval': (OVAL, True), 'r_brow': ([L68[i] for i in range(17, 22)], False), 'l_brow': ([L68[i] for i in range(22, 27)], False),
    'mouth_o': ([L68[i] for i in range(48, 60)], True), 'mouth_i': ([L68[i] for i in range(60, 68)], True)}
EYES = {'r': [L68[i] for i in range(36, 42)], 'l': [L68[i] for i in range(42, 48)]}
def cr(P, closed, n=8):  # Catmull-Rom densify
    P = np.asarray(P); m = len(P); out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1, p2, p3 = P[(i - 1) % m if closed else max(i - 1, 0)], P[i], P[(i + 1) % m], P[(i + 2) % m if closed else min(i + 2, m - 1)]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(P[-1])
    return [tuple(map(float, q)) for q in out]
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1: c = not c
    return c
def draw_landmarks(uv, w, z=None):
    im = Image.new('RGB', (rig.W, rig.H), (0, 0, 0)); d = ImageDraw.Draw(im)
    def vis(q):
        if z is None: return True
        x, y = int(round(q[0])), int(round(q[1]))
        if not (0 <= x < rig.W and 0 <= y < rig.H): return False
        win = z[max(y-2,0):y+3, max(x-2,0):x+3]
        return q[2] <= win.max() + 0.35 and q[2] <= win.min() + 2.5
    def line(pts, c):
        for p0, p1 in zip(pts[:-1], pts[1:]):
            if vis(p0) and vis(p1): d.line([p0[:2], p1[:2]], fill=c, width=2)
    line(cr(uv[OVAL], True) + [tuple(map(float, uv[OVAL[0]]))], COL['oval'])
    for k in ('r_brow', 'l_brow'): line(cr(uv[G[k][0]], False), COL[k])
    for k in ('mouth_o', 'mouth_i'): p = cr(uv[G[k][0]], True); line(p + [p[0]], COL['mouth'])
    for side, (ia, ib) in (('r', rig.IRIS_R), ('l', rig.IRIS_L)):
        e = EYES[side]; ccol = COL[side + '_eye']
        blink = w.get('eyeBlink_' + ('R' if side == 'r' else 'L'), 0)
        upper = [e[0], e[1], e[2], e[3]]; lower = [e[3], e[4], e[5], e[0]]
        if blink >= 0.85:  # closed: single lid line, no iris
            line(cr(uv[upper], False), ccol); continue
        p = cr(uv[upper], False) + cr(uv[lower], False)[1:]; line(p, ccol); p2 = [q[:2] for q in p]
        # pupil: iris centre, only if inside the eye opening polygon
        ir = uv[ia:ib]; front = ir[ir[:, 2] <= np.percentile(ir[:, 2], 30)]
        cx, cy = front[:, 0].mean(), front[:, 1].mean()
        if inside(p2, cx, cy) and vis((cx, cy, front[:, 2].min())):
            d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=COL[side + '_iris'])
    return im

# ---------- depth normalisation (fixed range relative to head bbox, identical for all images) ----------
base = np.load(NPZ)['base']; keepv = base[:21451]
R = np.linalg.norm(keepv - np.array(rig.PIVOT), axis=1).max()
NEAR, FAR = rig.CAM_DIST - R, rig.CAM_DIST + R * 0.6
def depth_imgs(z):
    valid = z < 1e5
    v = np.clip((FAR - z) / (FAR - NEAR), 0, 1); v[~valid] = 0
    return Image.fromarray((v * 255 + 0.5).astype(np.uint8)), Image.fromarray((v * 65535 + 0.5).astype(np.uint16))

BG = (235, 235, 235)
for pack in ('general', 'adult'):
    P = os.path.join(ROOT, pack)
    for sub in ('source', 'depth', 'depth16', 'landmarks'): os.makedirs(os.path.join(P, sub), exist_ok=True)
    entries = []
    for e in defs.get(pack, []):
        for ang in rig.ANGLES:
            key = f"{e['id']}_{ang}"; src = os.path.join(TMP, key + '_src.png')
            if not os.path.exists(src): continue
            if not only or e['id'] in only:
                im = Image.open(src).convert('RGBA'); bg = Image.new('RGBA', im.size, BG + (255,)); bg.alpha_composite(im)
                bg.convert('RGB').save(os.path.join(P, 'source', key + '.png'))
                d8, d16 = depth_imgs(np.load(os.path.join(TMP, key + '_z.npy')))
                d8.save(os.path.join(P, 'depth', key + '.png')); d16.save(os.path.join(P, 'depth16', key + '.png'))
                draw_landmarks(np.load(os.path.join(TMP, key + '_uv.npy')), e['_w'], np.load(os.path.join(TMP, key + '_z.npy'))).save(os.path.join(P, 'landmarks', key + '.png'))
            entries.append({'id': key, 'name_zh': e['name_zh'], 'name_en': e['name_en'], 'tags': e['tags'], 'angle': ang,
                            'group': e['id'], 'prompt_zh': e['prompt_zh'], 'prompt_en': e['prompt_en'], 'w': rig.W, 'h': rig.H,
                            'source': f'source/{key}.png', 'depth': f'depth/{key}.png', 'depth16': f'depth16/{key}.png',
                            'landmarks': f'landmarks/{key}.png', 'blendshape_weights': e['_w']})
    man = {'version': '0.2.0', 'pack': pack, 'license': 'Rendered assets © PoseWear; base mesh ICT-FaceKit (MIT), see THIRD_PARTY_LICENSES.txt',
           'source': 'ICT-FaceKit (MIT) rendered in-house', 'upstream': {'repo': 'https://github.com/ICT-VGL/ICT-FaceKit', 'commit': COMMIT,
           'model': 'ICT Face Model Light, generic_neutral_mesh (mean face, identity coefficients = 0)'},
           'spec': {'size': [rig.W, rig.H], 'angles': {k: {'yaw': v[0], 'pitch': v[1]} for k, v in rig.ANGLES.items()},
                    'camera': {'lens_mm': rig.LENS, 'distance': rig.CAM_DIST}, 'depth': {'near': round(NEAR, 3), 'far': round(FAR, 3), 'encoding': 'white=near, 0=background, 8-bit depth/, 16-bit depth16/'},
                    'landmarks': 'CrucibleAI ControlNetMediaPipeFace colour scheme, black background, 2px lines'},
           'count': len(entries), 'entries': entries}
    if pack == 'adult': man['content_rating'] = '18+'
    json.dump(man, open(os.path.join(P, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
    # contact sheets: one per angle
    os.makedirs(os.path.join(P, 'contact_sheets'), exist_ok=True)
    from PIL import ImageFont
    try: font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 15)
    except Exception: font = ImageFont.load_default()
    for ang in rig.ANGLES:
        es = [x for x in entries if x['angle'] == ang]
        if not es: continue
        cols = 6; tw, th = 180, 240; rows = (len(es) + cols - 1) // cols
        for kind in ('source', 'depth', 'landmarks'):
            sh = Image.new('RGB', (cols * tw, rows * (th + 48)), 'white'); dr = ImageDraw.Draw(sh)
            for i, x in enumerate(es):
                c, r = i % cols, i // cols
                sh.paste(Image.open(os.path.join(P, x[kind])).convert('RGB').resize((tw, th)), (c * tw, r * (th + 48)))
                dr.text((c * tw + 4, r * (th + 48) + th + 2), f"{x['group']}\n{x['name_zh']}", fill='black', font=font)
            sh.save(os.path.join(P, 'contact_sheets', f'{ang}_{kind}.png'))
print('built', len(jobs), 'renders')
