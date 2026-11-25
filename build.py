"""Build entry point for PoseWear: converts raw assets, generates catalogs, and invokes post.run(ctx)."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
import os
import shutil

from PIL import Image

from costume_text import gen2
import depthpack
import post


# 素材目录：默认 ./assets-raw，可用环境变量 POSEWEAR_RAW 指定（见 scripts/fetch-assets.py）
RAW_DIR = os.environ.get('POSEWEAR_RAW', 'assets-raw')
DIST_DIR = 'dist'
# 分离部署：设 POSEWEAR_ASSET_HOST 后，缩略图与原图输出到 dist-assets（独立 Pages 站），主站文件数压回免费版上限内；不设则单站构建，行为不变
ASSET_HOST = os.environ.get('POSEWEAR_ASSET_HOST', '').rstrip('/')
ASSETS_DIST_DIR = 'dist-assets'
ASSET_ROOT = ASSETS_DIST_DIR if ASSET_HOST else DIST_DIR

EXTENSION_ARCHIVES = (
    [f'{kind}/data.json' for kind in ('expression', 'dynasty', 'scene', 'light', 'prop', 'furn')]
    + ['charadb/hair.json', 'charadb/outfits.json']
)

LINE = {
    '全身1人・セクシー系': ('全身·性感', 'full body, solo, sexy'),
    '全身1人・標準系': ('全身·标准', 'full body, solo'),
    '上半身1人': ('上半身', 'upper body, solo'),
    '2人絡み': ('双人互动', 'two people, couple'),
}

CAT = {
    '寝そべり': '躺卧', 'セクシー・露骨寄り系': '性感·大胆', '立ち': '站姿', '座り': '坐姿',
    'かわいい系': '可爱', '胸寄せ・谷間強調系': '挤胸·乳沟', '膝立ち・四つん這い': '跪立·趴姿',
    '特殊': '特殊', '正常位': '正面位', '膝立ち': '跪立', '横座り・女の子座り': '侧坐·鸭子坐',
    '後背位': '后入位', '背面座位': '背面坐位', 'しゃがみ': '蹲姿', '前かがみ': '前倾',
    '顔寄せ系': '贴脸', '騎乗位': '骑乘位', '立位': '立位', '立位密着': '立位贴身',
    'のけぞり・反り': '后仰', 'ひねり': '扭身', '側位': '侧位', '座位': '坐位',
    '対面座位': '对面坐位', '座位密着': '坐位贴身', '密着': '贴身',
}

ANG = {
    '正面': ('正面', 'front view'),
    '上から': ('俯拍', 'high angle, from above'),
    '下から': ('仰拍', 'low angle, from below'),
    '横': ('侧面', 'side view'),
    '斜め': ('斜侧', 'three-quarter view'),
}

CC = {
    '春': ('春季', 'spring'),
    '夏': ('夏季', 'summer'),
    '秋': ('秋季', 'autumn'),
    '冬': ('冬季', 'winter'),
    'ランジェリー': ('内衣', 'lingerie'),
    'パーティ': ('派对礼服', 'party'),
    '水着': ('泳装', 'swimsuit'),
    'セクシー': ('性感', 'sexy'),
}

# 双人 分类人工复核（看图）
PAIR_CAT_FIXES = {
    'pair60_P031': '坐位',
    'pair60_P053': '立位贴身',
    'pair60_P055': '侧位',
    'pair60_P058': '贴脸',
}

ADULT_LINES = {'双人互动', '全身·性感'}
ADULT_CATS = {'挤胸·乳沟', '性感·大胆'}
ADULT_COS = {'内衣', '性感'}

PORTRAIT_HAIR = {
    'ショート': ('短发', 'short hair'),
    'ミディアム': ('中长发', 'medium-length hair'),
    'セミロング': ('半长发', 'shoulder-length hair'),
    'ロング': ('长发', 'long hair'),
}

PORTRAIT_SECTION = {
    'face': ('正脸', 'front-facing head-and-shoulders portrait, plain light grey background, soft even lighting'),
    'styling': ('生活照', 'casual selfie-style lifestyle photo, indoor natural light'),
}

VIEW_MAP = {
    'front': ('正面', 'front view'),
    'diag': ('斜侧', 'three-quarter view'),
    'side': ('侧面', 'side view'),
    'back': ('背面', 'back view'),
    'above': ('俯视', 'high angle, from above'),
    'below': ('仰视', 'low angle, from below'),
    'eye': ('平视', 'eye-level view'),
    'tq': ('3/4 侧', 'three-quarter view'),
}


def _dump_json(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def _collect_origins(obj):
    origins = set()

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and node.startswith('https://'):
            origins.add('/'.join(node.split('/')[:3]))

    walk(obj)
    return origins


def _load_view_module(raw_dir, sub, prefix):
    path = f'{raw_dir}/{sub}/data.json'
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as fh:
        records = json.load(fh)
    for it in records:
        item = {
            'id': it['id'],
            'cat': it['cat'],
            'ti': it['ti'],
            'zh': it['zh'],
            'en': it['en'],
            'ja': it.get('ja', ''),
            'line': it['line'],
            'lineEn': it['lineEn'],
            'no': it['id'],
            'angles': [
                {
                    'zh': VIEW_MAP[view][0],
                    'en': VIEW_MAP[view][1],
                    't': f'{prefix}/t/{it["id"]}_{view}.webp',
                    'i': f'{prefix}/i/{it["id"]}_{view}.webp',
                    'o': f'o/{prefix}/{it["id"]}_{view}.webp',
                    '_3': filename,
                    '_9': filename,
                }
                for view, filename in it['views'].items()
            ],
        }
        item.update(it.get('extra') or {})
        out.append(item)
    return out


def _copy_new_module(raw_dir, dist_dir, asset_root, sub, items):
    for it in items:
        for angle in it['angles']:
            f3, f9 = angle.pop('_3'), angle.pop('_9')
            for src_file, tier, dest in (
                (f3, 'w300', f'{asset_root}/{angle["t"]}'),
                (f9, 'w900', f'{dist_dir}/{angle["i"]}'),
                (f9, 'w900', f'{asset_root}/{angle["o"]}'),
            ):
                if not os.path.exists(dest):
                    shutil.copy(f'{raw_dir}/{sub}/files/{tier}/{src_file}', dest)


def _convert_pose(raw_dir, dist_dir, asset_root, record):
    thumb = f"{asset_root}/p/t/{record['id']}.webp"
    if not os.path.exists(thumb):
        im = Image.open(f"{raw_dir}/pose/{record['サムネ']}").convert('RGB')
        im.save(thumb, 'WEBP', quality=80, method=6)
    orig = f"{asset_root}/o/p/{record['id']}.png"
    if not os.path.exists(orig):
        os.link(f"{raw_dir}/pose/{record['原寸']}", orig)
    mid = f"{dist_dir}/p/i/{record['id']}.webp"
    if not os.path.exists(mid):
        im = Image.open(f"{raw_dir}/pose/{record['原寸']}").convert('RGB')
        im.thumbnail((1200, 1200))
        im.save(mid, 'WEBP', quality=82)


def _convert_costume(raw_dir, dist_dir, asset_root, folder, prefix, record):
    mid = f"{dist_dir}/{prefix}/m/{record['id']}.webp"
    if not os.path.exists(mid):
        im = Image.open(f"{raw_dir}/{folder}/{record['画像']}").convert('RGB')
        im.thumbnail((1080, 1620))
        im.save(mid, 'WEBP', quality=80)
    orig = f"{asset_root}/o/{prefix}/{record['id']}.png"
    if not os.path.exists(orig):
        os.link(f"{raw_dir}/{folder}/{record['原寸']}", orig)


def _convert_portrait(raw_dir, dist_dir, asset_root, record):
    thumb = f"{asset_root}/r/t/{record['id']}.webp"
    if not os.path.exists(thumb):
        shutil.copy(f"{raw_dir}/portrait/{record['thumb']}", thumb)
    mid = f"{dist_dir}/r/m/{record['id']}.webp"
    if not os.path.exists(mid):
        im = Image.open(f"{raw_dir}/portrait/{record['full']}").convert('RGB')
        im.thumbnail((1080, 1350))
        im.save(mid, 'WEBP', quality=80)
    orig = f"{asset_root}/o/r/{record['id']}.png"
    if not os.path.exists(orig):
        os.link(f"{raw_dir}/portrait/{record['full']}", orig)


def _check_archives(raw_dir):
    missing = []
    for archive in EXTENSION_ARCHIVES:
        path = os.path.join(raw_dir, archive)
        if not os.path.isfile(path):
            missing.append(archive)
            continue
        with open(path) as source:
            items = json.load(source)
        if not isinstance(items, list) or not items:
            missing.append(archive)
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build the PoseWear static site')
    parser.add_argument('--allow-partial', action='store_true', help='allow missing extension archives for local development')
    options = parser.parse_args(argv)

    raw_dir = RAW_DIR
    dist_dir = DIST_DIR
    asset_host = ASSET_HOST
    assets_dist_dir = ASSETS_DIST_DIR
    asset_root = ASSET_ROOT

    missing = _check_archives(raw_dir)
    if missing and not options.allow_partial:
        parser.error('Missing or empty extension archives: ' + ', '.join(missing) + '. See AGENTS.md or use --allow-partial for local development.')

    if asset_host:
        os.makedirs(assets_dist_dir, exist_ok=True)

    with open('tr_pose.txt') as fh:
        tr_pose = {line.split('|')[0]: line.split('|')[1:] for line in fh.read().strip().split('\n')}
    with open(f'{raw_dir}/pose/data.json') as fh:
        pd = json.load(fh)['D']
    with open(f'{raw_dir}/costume/data.json') as fh:
        cd = json.load(fh)['D']
    with open(f'{raw_dir}/anime/data.json') as fh:
        ad = json.load(fh)['D']

    poses = {}
    for d in pd:
        key = d['id'].rsplit('_', 1)[0]
        zh, en = tr_pose[d['ポーズ名']]
        entry = poses.setdefault(key, {
            'id': key,
            'no': d['ポーズ番号'],
            'line': LINE[d['系統']][0],
            'cat': CAT[d['分類']],
            'ja': d['ポーズ名'],
            'zh': zh,
            'en': en,
            'lineEn': LINE[d['系統']][1],
            'angles': [],
        })
        ang = ANG[d['アングル']]
        entry['angles'].append({
            'zh': ang[0],
            'en': ang[1],
            't': 'p/t/' + d['id'] + '.webp',
            'i': 'p/i/' + d['id'] + '.webp',
            'o': 'o/p/' + d['id'] + '.png',
        })

    cos = [
        {
            'id': d['id'],
            'cat': CC[d['カテゴリ']][0],
            'catEn': CC[d['カテゴリ']][1],
            'kw': d['キーワード'],
            **dict(zip(('zh', 'en', 'ti'), gen2(d['キーワード'], CC[d['カテゴリ']][1], d['id']))),
            't': 'c/t/' + os.path.basename(d['サムネ']),
            'm': 'c/m/' + d['id'] + '.webp',
            'i': 'c/i/' + os.path.basename(d['画像']),
            'o': 'o/c/' + d['id'] + '.png',
        }
        for d in cd
    ]
    acs = [
        {
            'id': d['id'],
            'cat': CC[d['カテゴリ']][0],
            'catEn': CC[d['カテゴリ']][1],
            'kw': d['キーワード'],
            **dict(zip(('zh', 'en', 'ti'), gen2(d['キーワード'], CC[d['カテゴリ']][1], d['id']))),
            't': 'a/t/' + os.path.basename(d['サムネ']),
            'm': 'a/m/' + d['id'] + '.webp',
            'i': 'a/i/' + os.path.basename(d['画像']),
            'o': 'o/a/' + d['id'] + '.png',
        }
        for d in ad
    ]

    for key, cat_name in PAIR_CAT_FIXES.items():
        poses[key]['cat'] = cat_name

    for p in poses.values():
        if p['line'] in ADULT_LINES or p['cat'] in ADULT_CATS:
            p['a'] = 1
    for c in cos:
        if c['cat'] in ADULT_COS:
            c['a'] = 1
    for c in acs:
        if c['cat'] in ADULT_COS:
            c['a'] = 1

    os.makedirs(dist_dir, exist_ok=True)
    partial_marker = os.path.join(dist_dir, '.posewear-partial')
    if missing:
        with open(partial_marker, 'w') as marker:
            marker.write('\n'.join(missing))
    elif os.path.exists(partial_marker):
        os.remove(partial_marker)

    for filename in os.listdir('src'):
        shutil.copy('src/' + filename, dist_dir)

    # 安全内容排在前面（默认落地页无露骨内容）
    poses_list = sorted(poses.values(), key=lambda p: p.get('a', 0))

    # CharaDB 服装 440 条并入动画服装（元数据自存、图片热链原站，见 scripts/prep-modules.py）
    cdb_path = f'{raw_dir}/charadb/outfits.json'
    if os.path.exists(cdb_path):
        with open(cdb_path) as fh:
            for d in json.load(fh):
                item = {
                    'id': d['id'],
                    'cat': d['cat'],
                    'catEn': d['catEn'],
                    'kw': d['kw'],
                    'zh': d['name'] + '，' + '、'.join(d['tagsZh'][1:]) + '。',
                    'en': d['kw'],
                    'ti': d['name'],
                    't': d['t'],
                    'm': d['m'],
                    'i': d['i'],
                    'o': '',
                    'ext': 1,
                }
                if d.get('sens'):
                    item['a'] = 1
                acs.append(item)

    # ---------- 人像库（AI Portrait Gallery，CC0，@agi_aibusi）----------
    with open(f'{raw_dir}/portrait/images.js') as fh:
        rt = fh.read()
    rd = json.loads(rt[rt.index('['):rt.rindex(']') + 1])
    with open(f'{raw_dir}/portrait/ranking.js') as fh:
        rk_text = fh.read()
    rk = json.loads(rk_text[rk_text.index('{'):rk_text.rindex('}') + 1])
    with open('tr_portrait.txt') as fh:
        tr_portrait = {line.split('|')[0]: line.split('|')[1:] for line in fh.read().strip().split('\n')}

    rank_all = {item_id: idx + 1 for idx, item_id in enumerate(rk['top']['総合'])}
    rank_cat = {}
    for cat_key, entries in rk['top'].items():
        if cat_key != '総合':
            for idx, item_id in enumerate(entries):
                rank_cat[item_id] = idx + 1

    portraits = []
    seq = {}
    for d in rd:
        sec = PORTRAIT_SECTION[d['section']]
        hair = PORTRAIT_HAIR[d['hair']]
        sz, se = tr_portrait.get(d['style'], ['', ''])
        seq[d['section']] = seq.get(d['section'], 0) + 1
        no = ('F' if d['section'] == 'face' else 'S') + str(seq[d['section']]).zfill(3)
        zh = f"一位亚洲年轻女性，{hair[0]}{'，' + sz if sz else ''}，{'正面半身肖像，浅灰纯色背景，柔和均匀的光线' if d['section'] == 'face' else '自拍风生活照，室内自然光'}。作为人物面部参考，保持五官和脸型一致。"
        en = f"young Asian woman, {hair[1]}{', ' + se if se else ''}, {sec[1]}, consistent facial features, face reference"
        item = {
            'id': d['id'],
            'no': no,
            'sec': sec[0],
            'len': hair[0],
            'st': sz,
            'ti': sz or f'{hair[0]} · {sec[0]}',
            'zh': zh,
            'en': en,
            'ja': d['style'] or d['hair'],
            't': 'r/t/' + d['id'] + '.webp',
            'm': 'r/m/' + d['id'] + '.webp',
            'i': 'r/m/' + d['id'] + '.webp',
            'o': 'o/r/' + d['id'] + '.png',
            'w': d['w'],
            'h': d['h'],
        }
        if d['id'] in rank_all:
            item['rk'] = rank_all[d['id']]
        if d['id'] in rank_cat:
            item['rc'] = rank_cat[d['id']]
        portraits.append(item)

    # ---------- 新模块（数据由 scripts/prep-modules.py 从本地档案生成到 assets-raw，构建不访问外网）----------
    exp_items = _load_view_module(raw_dir, 'expression', 'e')
    dyn_items = _load_view_module(raw_dir, 'dynasty', 'y')
    sce_items = _load_view_module(raw_dir, 'scene', 's')
    lig_items = _load_view_module(raw_dir, 'light', 'l')
    pro_items = _load_view_module(raw_dir, 'prop', 't')
    fur_items = _load_view_module(raw_dir, 'furn', 'f')
    hair_path = f'{raw_dir}/charadb/hair.json'
    hair_items = json.load(open(hair_path)) if os.path.exists(hair_path) else []

    # 热链图片的源站（CharaDB 等）：post.py 据此放行 CSP 的 img-src/connect-src，
    # 否则浏览器会拦截全部热链图片（2026-11-23 发型库全图加载失败的根因）。
    hotlink_origins = set()
    for rel in ('charadb/outfits.json', 'charadb/hair.json'):
        full = f'{raw_dir}/{rel}'
        if os.path.exists(full):
            with open(full) as fh:
                hotlink_origins |= _collect_origins(json.load(fh))
    hotlink_origins = sorted(hotlink_origins)

    new_modules = [
        ('expression', exp_items),
        ('dynasty', dyn_items),
        ('scene', sce_items),
        ('light', lig_items),
        ('prop', pro_items),
        ('furn', fur_items),
    ]

    if os.path.exists(f'{dist_dir}/data.js'):
        os.remove(f'{dist_dir}/data.js')
    for src_sub, dst_sub in (('costume/thumbs', 'c/t'), ('costume/img', 'c/i'), ('anime/thumbs', 'a/t'), ('anime/img', 'a/i')):
        shutil.copytree(f'{raw_dir}/{src_sub}', f'{asset_root if dst_sub.endswith("/t") else dist_dir}/{dst_sub}', dirs_exist_ok=True)
    os.makedirs(f'{dist_dir}/p/i', exist_ok=True)

    dirs = [
        'p/t', 'c/m', 'o/p', 'o/c', 'a/m', 'o/a', 'r/t', 'r/m', 'o/r',
        'e/t', 'e/i', 'o/e', 'y/t', 'y/i', 'o/y', 's/t', 's/i', 'o/s',
        'l/t', 'l/i', 'o/l', 't/t', 't/i', 'o/t', 'f/t', 'f/i', 'o/f',
    ]
    for sub in dirs:
        base = asset_root if sub.endswith('/t') or sub.startswith('o/') else dist_dir
        os.makedirs(f'{base}/{sub}', exist_ok=True)

    if asset_host:
        # 分离模式下缩略图/原图改写到 dist-assets，删掉 dist 里上一轮单站构建残留的旧文件，
        # 否则主站仍含这批文件、文件数压不回 2 万上限（Codex review on PR #4）
        for stale in ('p/t', 'c/t', 'a/t', 'r/t', 'e/t', 'y/t', 's/t', 'l/t', 't/t', 'f/t', 'o'):
            shutil.rmtree(f'{dist_dir}/{stale}', ignore_errors=True)

    pose_thumbs = f'{asset_root}/p/t'
    if os.path.exists(pose_thumbs):
        for fname in os.listdir(pose_thumbs):
            if fname.endswith('.jpg'):
                os.remove(f'{pose_thumbs}/{fname}')

    if asset_host:
        with open(f'{assets_dist_dir}/_headers', 'w') as fh:
            fh.write('/*\n  Cache-Control: public, max-age=31536000, immutable\n  Access-Control-Allow-Origin: *\n/o/*\n  Content-Disposition: attachment\n')

    with ProcessPoolExecutor() as pool:
        for fn, records in (
            (partial(_convert_pose, raw_dir, dist_dir, asset_root), pd),
            (partial(_convert_costume, raw_dir, dist_dir, asset_root, 'costume', 'c'), cd),
            (partial(_convert_costume, raw_dir, dist_dir, asset_root, 'anime', 'a'), ad),
            (partial(_convert_portrait, raw_dir, dist_dir, asset_root), rd),
        ):
            list(pool.map(fn, records))

    for sub, items in new_modules:
        _copy_new_module(raw_dir, dist_dir, asset_root, sub, items)

    # 深度姿势：只解析素材包里的文本，热链包不复制图片（见 depthpack.py）
    depth_cat = depthpack.catalog()
    dj = _dump_json(depth_cat['payload'])
    depth_origins = depth_cat['origins']
    if asset_host:
        # 图片自存模式：深度图已全量存入图片域名下的 d/ 前缀（上游 /thumbs/→/d/thumbs/、/img/→/d/img/），
        # 条目地址改走自存，不再热链原站（原站不可用时前端会整批找不到图）；署名用的裸域名链接不在替换范围内。
        dj = (
            dj.replace('https://ai-pose-depth-gallery.pages.dev/thumbs/', asset_host + '/d/thumbs/')
            .replace('https://ai-pose-depth-gallery.pages.dev/img/', asset_host + '/d/img/')
        )
    for src_file, rel in depth_cat['copies']:
        dest = f'{dist_dir}/{rel}'
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src_file, dest)

    # 重要：_copy_new_module 已 pop 掉 _3/_9 临时字段后再序列化新模块 JSON
    catalogs = {
        'poses.json': _dump_json(poses_list),
        'costumes.json': _dump_json(cos),
        'anime.json': _dump_json(acs),
        'portraits.json': _dump_json(portraits),
        'depths.json': dj,
        'expressions.json': _dump_json(exp_items),
        'hair.json': _dump_json(hair_items),
        'dynasties.json': _dump_json(dyn_items),
        'scenes.json': _dump_json(sce_items),
        'lights.json': _dump_json(lig_items),
        'props.json': _dump_json(pro_items),
        'furniture.json': _dump_json(fur_items),
    }

    ctx = {
        'raw_dir': raw_dir,
        'dist_dir': dist_dir,
        'src_dir': 'src',
        'functions_dir': 'functions',
        'asset_host': asset_host,
        'catalogs': catalogs,
        'data': {
            'poses': poses,
            'poses_list': poses_list,
            'costumes': cos,
            'anime': acs,
            'portraits': portraits,
        },
        'depth_origins': depth_origins,
        'hotlink_origins': hotlink_origins,
    }
    post.run(ctx)
    print(
        len(poses), len(cos), len(acs), len(depth_cat['payload']['items']),
        '| new:', len(exp_items), len(hair_items), len(dyn_items), len(sce_items), len(lig_items), len(pro_items), len(fur_items),
    )


if __name__ == '__main__':
    main()
