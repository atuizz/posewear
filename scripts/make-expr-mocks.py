#!/usr/bin/env python3
"""生成占位表情包（不是 ICT-FaceKit 渲染）。正式素材用 import-expressions.py 替换。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import expr
from PIL import Image, ImageDraw

W, H = 900, 1200
DEST = expr.ROOT
LICENSE = expr.FACEKIT_LICENSE
NOTE = '当前图片是占位图（scripts/make-expr-mocks.py 生成），不是 ICT-FaceKit 的渲染结果。正式素材放到 posewear-expressions-v2 后，用 scripts/import-expressions.py 导入替换。'


def _shift(angle):
    return -110 if angle == 'three_quarter' else 0


def source(angle, kind):
    im = Image.new('RGB', (W, H), (28, 28, 30))
    d = ImageDraw.Draw(im)
    ox = _shift(angle)
    cx, skin = 450 + ox, (176, 176, 178)
    d.polygon([(cx - 78, 760), (cx + 78, 760), (cx + 120, 1188), (cx - 120, 1188)], fill=(150, 150, 152))
    d.ellipse((cx - 230, 150, cx + 230, 780), fill=skin)
    d.ellipse((cx - 250, 300, cx - 190, 430), fill=(160, 160, 162))
    d.ellipse((cx + 190, 300, cx + 250, 430), fill=(160, 160, 162))
    ink = (70, 70, 72)
    if kind == 'happy':
        d.arc((cx - 130, 340, cx - 40, 430), 200, 340, fill=ink, width=10)
        d.arc((cx + 40, 340, cx + 130, 430), 200, 340, fill=ink, width=10)
        d.arc((cx - 90, 500, cx + 90, 640), 20, 160, fill=ink, width=12)
    elif kind == 'calm':
        d.ellipse((cx - 120, 370, cx - 55, 425), fill=ink)
        d.ellipse((cx + 55, 370, cx + 120, 425), fill=ink)
        d.arc((cx - 60, 540, cx + 60, 610), 20, 160, fill=ink, width=8)
    else:
        d.arc((cx - 130, 350, cx - 40, 430), 200, 340, fill=ink, width=10)
        d.ellipse((cx + 60, 375, cx + 115, 425), fill=ink)
        d.arc((cx - 40, 530, cx + 110, 640), 10, 150, fill=ink, width=12)
    d.polygon([(cx - 16, 430), (cx + 16, 430), (cx + 8, 520), (cx - 8, 520)], fill=(150, 150, 152))
    return im


def depth(angle):
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    ox = _shift(angle)
    cx = 450 + ox
    d.polygon([(cx - 78, 760), (cx + 78, 760), (cx + 120, 1188), (cx - 120, 1188)], fill=140)
    d.ellipse((cx - 230, 150, cx + 230, 780), fill=220)
    d.ellipse((cx - 36, 430, cx + 36, 540), fill=255)
    return im


def lines(angle, kind):
    im = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    ox = _shift(angle)
    cx, pen = 450 + ox, (255, 255, 255)
    d.ellipse((cx - 230, 150, cx + 230, 780), outline=pen, width=4)
    d.line([(cx - 78, 760), (cx - 120, 1100), (cx + 120, 1100), (cx + 78, 760)], fill=pen, width=3)
    if kind == 'happy':
        d.arc((cx - 130, 340, cx - 40, 430), 200, 340, fill=pen, width=4)
        d.arc((cx + 40, 340, cx + 130, 430), 200, 340, fill=pen, width=4)
        d.arc((cx - 90, 500, cx + 90, 640), 20, 160, fill=pen, width=4)
    elif kind == 'calm':
        d.ellipse((cx - 120, 370, cx - 55, 425), outline=pen, width=4)
        d.ellipse((cx + 55, 370, cx + 120, 425), outline=pen, width=4)
        d.arc((cx - 60, 540, cx + 60, 610), 20, 160, fill=pen, width=3)
    else:
        d.arc((cx - 130, 350, cx - 40, 430), 200, 340, fill=pen, width=4)
        d.ellipse((cx + 60, 375, cx + 115, 425), outline=pen, width=4)
        d.arc((cx - 40, 530, cx + 110, 640), 10, 150, fill=pen, width=4)
    d.line([(cx, 450), (cx, 530)], fill=pen, width=3)
    return im


def item(kind, angle, zh, en, tags, prompt_zh, prompt_en, weights):
    iid = '%s_%s' % (kind, angle)
    return {
        'id': iid, 'name_zh': zh, 'name_en': en, 'tags': tags, 'angle': angle, 'group': kind,
        'prompt_zh': prompt_zh, 'prompt_en': prompt_en, 'w': W, 'h': H, 'pack': None,
        'blendshape_weights': weights,
        'source': 'source/%s.png' % iid, 'depth': 'depth/%s.png' % iid, 'landmarks': 'landmarks/%s.png' % iid,
    }


def write_pack(pid, manifest, kinds):
    base = os.path.join(DEST, pid)
    for sub in ('source', 'depth', 'landmarks'):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    for kind, angle in kinds:
        source(angle, kind).save(os.path.join(base, 'source', '%s_%s.png' % (kind, angle)))
        depth(angle).save(os.path.join(base, 'depth', '%s_%s.png' % (kind, angle)))
        lines(angle, kind).save(os.path.join(base, 'landmarks', '%s_%s.png' % (kind, angle)))
    for it in manifest['items']:
        it['pack'] = pid
    up = manifest.get('upstream') or expr.FACEKIT_UPSTREAM
    with open(os.path.join(base, expr.THIRD_PARTY), 'w', encoding='utf-8') as f:
        f.write(expr.third_party_text(up['repo'], up['variant'], up['commit']))
    with open(os.path.join(base, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    common = dict(version='0.2.0-mock', license=LICENSE, model='ICT-FaceKit', placeholder=True, note=NOTE,
                  upstream=dict(expr.FACEKIT_UPSTREAM),
                  source='占位图。模型锁定 ICT-FaceKit Light @ %s。正式渲染用导入命令替换，仍只用 Light。' % expr.FACEKIT_COMMIT,
                  author='衣姿 PoseWear', url=expr.FACEKIT_REPO)
    general = dict(common, id='general', name_zh='通用表情', name_en='General expressions', gated=False, items=[
        item('happy', 'front', '开心', 'happy', ['正面情绪', '笑', '正面'],
             '灰色人台头，正面，开心，嘴角上扬。', 'gray mannequin head, front view, happy smile.',
             {'mouthSmile_L': 0.7, 'mouthSmile_R': 0.7, 'cheekSquint_L': 0.35, 'cheekSquint_R': 0.35}),
        item('happy', 'three_quarter', '开心', 'happy', ['正面情绪', '笑', '3/4 侧'],
             '灰色人台头，斜侧，开心，嘴角上扬。', 'gray mannequin head, three-quarter view, happy smile.',
             {'mouthSmile_L': 0.7, 'mouthSmile_R': 0.55, 'cheekSquint_L': 0.3, 'cheekSquint_R': 0.2}),
        item('calm', 'front', '平静', 'calm', ['中性情绪', '正面'],
             '灰色人台头，正面，平静，嘴巴放松。', 'gray mannequin head, front view, calm relaxed mouth.',
             {'eyeBlink_L': 0.05, 'eyeBlink_R': 0.05}),
        item('calm', 'three_quarter', '平静', 'calm', ['中性情绪', '3/4 侧'],
             '灰色人台头，斜侧，平静，嘴巴放松。', 'gray mannequin head, three-quarter view, calm.',
             {'eyeBlink_L': 0.05, 'eyeBlink_R': 0.05}),
    ])
    adult = dict(common, id='adult', name_zh='成人向表情', name_en='Adult expressions', gated=True,
                 ageGate='18+', badge='18+', switch='成人表情',
                 gateTitle='显示成人向表情？',
                 gateBody='这些是 18+ 的面部表情，只有灰色人台头，没有身体，也没有裸露。仅适合已满 18 岁的用户。',
                 confirm='我已满 18 岁，打开', cancel='暂不',
                 noticeZh='18+ 面部表情。灰色人台头，没有身体，没有裸露。',
                 noticeEn='18+ facial expression. Gray mannequin head only, no body and no nudity.',
                 items=[
        item('smirk', 'front', '坏笑', 'smirk', ['正面情绪', '单侧', '正面'],
             '灰色人台头，正面，一侧挑眉、嘴角单边上扬。', 'gray mannequin head, front view, one-sided smirk.',
             {'mouthSmile_L': 0.85, 'browOuterUp_L': 0.45, 'eyeSquint_L': 0.35}),
        item('smirk', 'three_quarter', '坏笑', 'smirk', ['正面情绪', '单侧', '3/4 侧'],
             '灰色人台头，斜侧，一侧挑眉、嘴角单边上扬。', 'gray mannequin head, three-quarter view, one-sided smirk.',
             {'mouthSmile_L': 0.8, 'browOuterUp_L': 0.4, 'eyeSquint_L': 0.3}),
    ])
    write_pack('general', general, [('happy', 'front'), ('happy', 'three_quarter'), ('calm', 'front'), ('calm', 'three_quarter')])
    write_pack('adult', adult, [('smirk', 'front'), ('smirk', 'three_quarter')])
    expr.load_packs(DEST)
    print('wrote', DEST)


if __name__ == '__main__':
    main()
