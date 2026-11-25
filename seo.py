"""SEO builder: static home SSR, category/tag/detail pages, /en/ site, sitemaps and IndexNow."""

import datetime
import html as html_lib
import json
import os
import re
import secrets
import shutil


CC0_URL = 'https://creativecommons.org/publicdomain/zero/1.0/'

SOURCES = {
    'pose': ('AI Pose Gallery', 'https://ai-pose-gallery.pages.dev', '@giaaibusi', 'https://x.com/giaaibusi'),
    'costume': ('AI Costume Gallery', 'https://ai-costume-gallery.pages.dev', '@giaaibusi', 'https://x.com/giaaibusi'),
    'anime': ('AI Costume Anime Gallery', 'https://ai-costume-anime-gallery.pages.dev', '@giaaibusi', 'https://x.com/giaaibusi'),
    'portrait': ('AI Portrait Gallery', 'https://ai-portrait-gallery.pages.dev', '@agi_aibusi', 'https://x.com/agi_aibusi'),
}

POSE_CATEGORIES = {
    '可爱': ('cute', 'Cute'),
    '坐姿': ('sitting', 'Sitting'),
    '站姿': ('standing', 'Standing'),
    '跪立': ('kneeling', 'Kneeling'),
    '躺卧': ('lying', 'Lying down'),
    '侧坐·鸭子坐': ('side-sitting', 'Side sitting'),
    '蹲姿': ('squatting', 'Squatting'),
    '前倾': ('leaning-forward', 'Leaning forward'),
    '后仰': ('leaning-back', 'Leaning back'),
    '扭身': ('twisting', 'Twisting'),
}

COSTUME_CATEGORIES = {
    '春季': ('spring', 'Spring'),
    '夏季': ('summer', 'Summer'),
    '秋季': ('autumn', 'Autumn'),
    '冬季': ('winter', 'Winter'),
    '派对礼服': ('party', 'Party dresses'),
    '泳装': ('swimsuit', 'Swimwear'),
}

PORTRAIT_SECTIONS = {
    '正脸': ('front-face', 'Front face'),
    '生活照': ('lifestyle', 'Lifestyle'),
}

PORTRAIT_LENGTHS = {
    '短发': ('short-hair', 'Short hair'),
    '中长发': ('medium-hair', 'Medium hair'),
    '半长发': ('shoulder-length-hair', 'Shoulder-length hair'),
    '长发': ('long-hair', 'Long hair'),
}

COLORS = {
    '黑': 'black', '白': 'white', '红': 'red', '粉': 'pink', '蓝': 'blue',
    '藏青': 'navy', '棕': 'brown', '米': 'beige', '象牙白': 'ivory', '灰': 'grey',
    '绿': 'green', '黄': 'yellow', '紫': 'purple', '金': 'gold', '银': 'silver',
    '卡其': 'khaki', '酒红': 'burgundy', '橙': 'orange', '奶油': 'cream',
    '薄荷': 'mint', '薰衣草': 'lavender', '橄榄': 'olive',
}

GARMENT_ITEMS = {
    '连衣裙': 'dress', '半身裙': 'skirt', '短裤': 'shorts', '长裤': 'trousers',
    '牛仔裤': 'jeans', '大衣': 'coat', '夹克': 'jacket', '开衫': 'cardigan',
    '衬衫': 'blouse', '毛衣': 'sweater', '吊带': 'camisole', '泳衣': 'swimsuit',
    '靴子': 'boots', '高跟鞋': 'high heels', '运动鞋': 'sneakers', '凉鞋': 'sandals',
    '连裤袜': 'tights', '长筒袜': 'stockings',
}

THUMB_DIMENSIONS = {
    'pose': (300, 400),
    'costume': (360, 540),
    'anime': (360, 540),
    'portrait': (400, 500),
}

# Portrait detail count is large; English edition publishes category/hub pages only (Cloudflare Pages 20k file limit).
HAS_EN = {'pose', 'costume', 'anime'}

LABELS = {
    'zh': {'pose': '姿势', 'costume': '服装', 'anime': '动画服装', 'portrait': '人像', 'tag': '标签', 'home': '首页'},
    'en': {'pose': 'Poses', 'costume': 'Outfits', 'anime': 'Anime outfits', 'portrait': 'Portraits', 'tag': 'Tags', 'home': 'Home'},
}

HUB_NAMES = {
    'pose': ('姿势参考图库', 'Pose Reference Library'),
    'costume': ('服装穿搭参考图库', 'Outfit Reference Library'),
    'anime': ('动画服装参考图库', 'Anime Outfit Reference Library'),
    'portrait': ('人像脸模参考图库', 'Portrait Face References'),
    'tag': ('穿搭标签', 'Outfit Tags'),
}

LISTING_INTROS = {
    'pose': (
        '{c}姿势参考图，共 {n} 个姿势，每个都有正面、俯拍、仰拍等多个角度，附中英文提示词，画画、拍照和 AI 出图都能用。',
        '{c} pose references: {n} poses, each shot from several camera angles, with English prompts for drawing, photography and AI image generation.',
    ),
    'costume': (
        '{c}穿搭参考图，共 {n} 套，每套都有中文描述和英文提示词，可以在衣姿里上传照片在线试穿。',
        '{c} outfit references: {n} looks, each with a description and an English prompt. Upload a photo to try them on in PoseWear.',
    ),
    'anime': (
        '{c}动画风穿搭参考图，共 {n} 套，每套都有中文描述和英文提示词，可以在衣姿里上传照片在线试穿。',
        '{c} anime-style outfit references: {n} looks, each with a description and an English prompt. Upload a photo to try them on in PoseWear.',
    ),
    'portrait': (
        '{c}人像脸模参考，共 {n} 张，AI 生成的虚构人物，CC0 1.0，可作 AI 绘图和视频的人物面部参考。',
        '{c} face references: {n} AI-generated fictional people, CC0 1.0, for consistent characters in AI images and video.',
    ),
    'tag': (
        '带「{c}」的穿搭参考图，共 {n} 套，附中英文提示词。',
        'Outfit references with {c}: {n} looks with English prompts.',
    ),
}

HUB_INTROS = {
    'pose': (
        '按分类浏览 {n} 个姿势参考，每个姿势都有多个拍摄角度和中英文提示词。',
        'Browse {n} pose references by category, each with several camera angles and prompts.',
    ),
    'costume': (
        '按季节和场合浏览 {n} 套服装穿搭参考，附中英文提示词，可在线 AI 试穿。',
        'Browse {n} outfit references by season and occasion, with prompts and online AI try-on.',
    ),
    'anime': (
        '按季节和场合浏览 {n} 套动画风服装穿搭参考，附中英文提示词，可在线 AI 试穿。',
        'Browse {n} anime-style outfit references by season and occasion, with prompts and online AI try-on.',
    ),
    'portrait': (
        '按类型和发长浏览 {n} 张人像脸模参考，CC0 1.0。',
        'Browse {n} CC0 portrait face references by type and hair length.',
    ),
    'tag': (
        '按单品和颜色浏览穿搭参考，共 {n} 个标签。',
        'Browse outfits by garment and colour: {n} tags.',
    ),
}

SEO_EXTRA_CSS = '''
.bc ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px}.bc li+li:before{content:"›";margin-right:4px;color:#aaa}.bc a{text-decoration:none}.bc a:hover{text-decoration:underline}
.tg{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.tg a{font-size:13px;background:var(--surface);border-radius:999px;padding:4px 12px;text-decoration:none}.tg a:hover{background:var(--surface-hover)}
header nav{margin-left:auto;display:flex;gap:16px;font-size:14px}header nav a{font-weight:500;color:var(--muted)}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px}.wrap h1{font-size:28px}.lead{color:var(--muted);max-width:720px;margin:6px 0 18px}
.cg{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:20px 14px}.cg a{text-decoration:none;font-size:13px;display:block}.cg img{width:100%;height:auto;border-radius:12px;background:var(--surface);display:block;margin-bottom:6px}.cg span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pg{display:flex;gap:8px;justify-content:center;margin:28px 0}.pg a,.pg b{padding:6px 14px;border-radius:999px;background:var(--surface);text-decoration:none;font-size:14px}.pg b{background:var(--ink);color:var(--paper)}
.sec h2{font-size:18px;margin:28px 0 10px}pre{white-space:pre-wrap;margin:0;font:inherit}
.static-dock{position:fixed;right:max(16px,env(safe-area-inset-right));bottom:max(16px,env(safe-area-inset-bottom));width:48px;height:48px;z-index:3;display:grid;place-items:center;background:var(--ink);color:var(--paper);border:1px solid #ffffff36;border-radius:16px;box-shadow:0 5px 16px #0002;text-decoration:none}
.static-dock svg{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:1.65;stroke-linecap:round;stroke-linejoin:round}.static-dock:focus-visible{outline:3px solid #ff2442;outline-offset:3px}
@media(max-width:760px){header{flex-wrap:wrap;padding:10px 14px}header nav{margin:0;width:100%;flex-wrap:wrap;gap:4px 14px}header nav a{min-height:32px}main{grid-template-columns:minmax(0,1fr);padding:16px 14px;gap:20px}main>div{min-width:0;overflow-wrap:anywhere}.cg{grid-template-columns:repeat(2,minmax(0,1fr))}footer{padding-bottom:76px}}'''

EXTRA_CATALOG_STATS = (
    ('depth', 'depths.json'),
    ('exp', 'expressions.json'),
    ('hair', 'hair.json'),
    ('dyn', 'dynasties.json'),
    ('scene', 'scenes.json'),
    ('light', 'lights.json'),
    ('prop', 'props.json'),
    ('furn', 'furniture.json'),
)


def _esc(value):
    return html_lib.escape(str(value), quote=True)


def _cap(text):
    return text[:1].upper() + text[1:]


def _color_zh(name):
    return name if name.endswith('白') else name + '色'


def _costume_tags(item):
    words = ' ' + item['kw'] + ' '
    english = ' ' + item['en'].replace(',', ' ') + ' '
    items = [('item', zh, en) for zh, en in GARMENT_ITEMS.items() if ' ' + en + ' ' in english]
    colors = [('col', zh, en) for zh, en in COLORS.items() if ' ' + en + ' ' in words]
    return items + colors


def _en_title(kind, item):
    if kind == 'pose':
        return _cap(item['en'])
    if kind in ('costume', 'anime'):
        parts = [part.strip() for part in item['en'].split(',')][1:3]
        return _cap(' + '.join(parts)) if parts else _cap(item['en'])
    parts = item['en'].split(',')
    return _cap((parts[1] if len(parts) > 1 else parts[0]).strip()) + ' portrait'


def _zh_title(kind, item):
    return item['zh'] if kind == 'pose' else item['ti']


def _thumb(kind, item):
    return item['angles'][0]['t'] if kind == 'pose' else item['t']


def _big(kind, item):
    return item['angles'][0]['i'] if kind == 'pose' else item['m']


def _category_of(kind, item):
    if kind == 'pose':
        slug, en = POSE_CATEGORIES[item['cat']]
        return ('pose', slug, item['cat'], en)
    if kind in ('costume', 'anime'):
        slug, en = COSTUME_CATEGORIES[item['cat']]
        return (kind, slug, item['cat'], en)
    slug, en = PORTRAIT_LENGTHS[item['len']]
    return ('portrait', slug, item['len'], en)


def _mtime_iso(path, fallback):
    if path and os.path.exists(path):
        return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    return fallback


def run(ctx):
    """Generate static SEO pages, English site, SSR home fragment, sitemaps, and robots.txt."""
    raw_dir = ctx.get('raw_dir', 'assets-raw')
    dist_dir = ctx['dist_dir']
    site = ctx['site'].rstrip('/')
    asset_host = ctx.get('asset_host', '').rstrip('/')
    theme_head = ctx['theme_head']
    css2 = ctx['base_css'] + SEO_EXTRA_CSS
    logo = ctx['logo']
    catalogs = ctx['catalogs']
    data = ctx['data']
    urls_path = ctx.get('urls_path', 'urls.txt')
    indexnow_key_path = ctx.get('indexnow_key_path', 'indexnow.key')

    today = datetime.date.today().isoformat()
    explicit_lm = ctx.get('last_modified') or {}
    last_mod = {
        'pose': explicit_lm.get('pose') or _mtime_iso(os.path.join(raw_dir, 'pose/data.json'), today),
        'costume': explicit_lm.get('costume') or _mtime_iso(os.path.join(raw_dir, 'costume/data.json'), today),
        'anime': explicit_lm.get('anime') or _mtime_iso(os.path.join(raw_dir, 'anime/data.json'), today),
        'portrait': explicit_lm.get('portrait') or _mtime_iso(os.path.join(raw_dir, 'portrait/images.js'), today),
    }

    def thumb_url(path):
        if path.startswith('http'):
            return path
        return f'{asset_host}/{path}' if asset_host else f'/{path}'

    def thumb_abs(path):
        if path.startswith('http'):
            return path
        return f'{asset_host}/{path}' if asset_host else f'{site}/{path}'

    for sub in ('en', 'tag'):
        target = os.path.join(dist_dir, sub)
        if os.path.exists(target):
            shutil.rmtree(target)

    if not os.path.exists(indexnow_key_path):
        with open(indexnow_key_path, 'w') as fh:
            fh.write(secrets.token_hex(16))
    with open(indexnow_key_path) as fh:
        indexnow_key = fh.read().strip()
    with open(os.path.join(dist_dir, f'{indexnow_key}.txt'), 'w') as fh:
        fh.write(indexnow_key)

    poses = data['poses']
    poses_list = data['poses_list']
    costumes = data['costumes']
    anime = data['anime']
    portraits = data['portraits']

    na_total = sum(len(p['angles']) for p in poses.values())
    safe_poses = [p for p in poses_list if not p.get('a')]
    na_pub = sum(len(p['angles']) for p in safe_poses)
    safe_costumes = [c for c in costumes if not c.get('a')]
    safe_anime = [c for c in anime if not c.get('a') and not c.get('ext')]
    anime_pub = sum(1 for c in anime if not c.get('a'))
    safe_portraits = portraits

    tags_map = {}
    for item in safe_costumes:
        for kind_t, zh, en in _costume_tags(item):
            slug = en.replace(' ', '-')
            entry = tags_map.setdefault(slug, {'k': kind_t, 'zh': zh if kind_t == 'item' else _color_zh(zh), 'en': en, 'L': []})
            entry['L'].append(item)
    tags_map = {slug: entry for slug, entry in tags_map.items() if len(entry['L']) >= 4}

    def page_url(lang, path):
        return site + ('/en' if lang == 'en' else '') + path

    def hreflang_tags(path, has_en=True):
        if not has_en:
            return f'<link rel="canonical" href="{page_url("zh", path)}">'
        return (
            f'<link rel="alternate" hreflang="zh-CN" href="{page_url("zh", path)}">'
            f'<link rel="alternate" hreflang="en" href="{page_url("en", path)}">'
            f'<link rel="alternate" hreflang="x-default" href="{page_url("zh", path)}">'
        )

    def crumbs_ld(cr, bid=None):
        return {
            '@type': 'BreadcrumbList',
            **({'@id': bid} if bid else {}),
            'itemListElement': [
                {'@type': 'ListItem', 'position': idx + 1, 'name': name, **({'item': site + href} if href else {})}
                for idx, (name, href) in enumerate(cr)
            ],
        }

    def crumbs_html(cr):
        parts = [f'<a href="{_esc(href)}">{_esc(name)}</a>' if href else f'<span aria-current="page">{_esc(name)}</span>' for name, href in cr]
        return '<nav class="bc" aria-label="breadcrumb"><ol>' + ''.join(f'<li>{p}</li>' for p in parts) + '</ol></nav>'

    def shell(lang, path, title, desc, body, ld, has_en=True, og=None, ogt='website', credit='', workbench='/#workbench'):
        dock_label = 'Open image studio' if lang == 'en' else '打开生图工作台'
        prefix = '/en' if lang == 'en' else ''
        switch = (
            f'<a href="/en{path}" hreflang="en" lang="en">EN</a>'
            if lang == 'zh' and has_en
            else f'<a href="{path}" hreflang="zh-CN" lang="zh-CN">中文</a>'
            if lang == 'en'
            else ''
        )
        nav = (
            f'<nav><a href="{prefix}/pose/">{LABELS[lang]["pose"]}</a>'
            f'<a href="{prefix}/costume/">{LABELS[lang]["costume"]}</a>'
            f'<a href="{prefix}/anime/">{LABELS[lang]["anime"]}</a>'
            f'<a href="{prefix}/portrait/">{LABELS[lang]["portrait"]}</a>'
            f'<a href="https://github.com/atuizz/posewear" target="_blank" rel="noopener">GitHub</a>'
            f'{switch}</nav>'
        )
        default_foot = (
            'Images from AI Pose Gallery / AI Costume Gallery (by @giaaibusi) and AI Portrait Gallery (by @agi_aibusi, CC0 1.0). All AI-generated.'
            if lang == 'en'
            else '图片来自 AI Pose Gallery / AI Costume Gallery（原作者 @giaaibusi）与 AI Portrait Gallery（@agi_aibusi，CC0 1.0），均为 AI 生成图，中文描述由本站整理。'
        )
        ld_json = json.dumps({'@context': 'https://schema.org', '@graph': ld}, ensure_ascii=False, separators=(',', ':'))
        return (
            f'<!doctype html><html lang="{"en" if lang == "en" else "zh-CN"}"><head>'
            f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_esc(title)}</title><meta name="description" content="{_esc(desc[:160])}">'
            f'<link rel="canonical" href="{page_url(lang, path)}">{hreflang_tags(path) if has_en else ""}'
            f'<meta property="og:type" content="{ogt}"><meta property="og:site_name" content="衣姿 PoseWear">'
            f'<meta property="og:title" content="{_esc(title)}"><meta property="og:description" content="{_esc(desc[:160])}">'
            f'<meta property="og:image" content="{site}/{og or "og.png"}"><meta property="og:url" content="{page_url(lang, path)}">'
            f'<meta property="og:locale" content="{"en_US" if lang == "en" else "zh_CN"}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:description" content="{_esc(desc[:160])}">'
            f'<link rel="icon" href="/favicon.svg" type="image/svg+xml">{theme_head}<style>{css2}</style>'
            f'<script type="application/ld+json">{ld_json}</script></head><body>'
            f'<header><a href="{prefix}/">{logo}衣姿 PoseWear</a>{nav}</header>'
            f'{body}'
            f'<a class="static-dock" href="{_esc(workbench)}" aria-label="{dock_label}" title="{dock_label}">'
            f'<svg viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="M3.5 10V7.8a2 2 0 0 1 2-2H9M19.8 12.7v5.5a2 2 0 0 1-2 2H5.5a2 2 0 0 1-2-2V10m3.3 6.4 3.4-3.6 2.2 2.3 1.2-1.2 2.5 2.5"/>'
            f'<path d="m16.4 2.7.9 3.1 3.1.9-3.1.9-.9 3.1-.9-3.1-3.1-.9 3.1-.9z"/></svg></a>'
            f'<footer>{credit or default_foot} <a href="{prefix}/">{"PoseWear home" if lang == "en" else "返回首页"}</a></footer></body></html>'
        )

    def write_page(path, content):
        out_dir = os.path.join(dist_dir, path.lstrip('/'))
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'index.html'), 'w') as fh:
            fh.write(content)

    sitemaps = {'pose': [], 'costume': [], 'anime': [], 'portrait': [], 'pages': []}

    def add_sitemap(sm, path, lm, imgs=(), has_en=True):
        sitemaps[sm].append((page_url('zh', path), lm, imgs))
        if has_en:
            sitemaps[sm].append((page_url('en', path), lm, imgs))

    def card_li(lang, kind, item, href=None):
        title = _en_title(kind, item) if lang == 'en' else _zh_title(kind, item)
        w, h = THUMB_DIMENSIONS[kind]
        target = href or (('/en' if lang == 'en' and kind in HAS_EN else '') + f'/{kind}/{item["id"]}/')
        return (
            f'<li><a href="{target}">'
            f'<img src="{thumb_url(_thumb(kind, item))}" alt="{_esc(title)}" width="{w}" height="{h}" loading="lazy" decoding="async">'
            f'<span>{_esc(title)}</span></a></li>'
        )

    def detail_page(lang, kind, item, related):
        is_zh = lang == 'zh'
        prefix = '' if is_zh else '/en'
        src = SOURCES[kind]
        _, slug, cz_, cen = _category_of(kind, item)
        tz, te = _zh_title(kind, item), _en_title(kind, item)
        title = tz if is_zh else te
        img = _big(kind, item)
        th = _thumb(kind, item)
        if kind == 'portrait':
            w, h = 1080, round(1080 * item['h'] / item['w'])
        elif kind == 'pose':
            w, h = 900, 1200
        else:
            w, h = 1080, 1620
        angles = item.get('angles', [])

        if kind == 'pose':
            prz = f"{item['zh']}，{item['line']}，{item['cat']}。"
            pzh = f"{item['zh']}，{item['line']}，{item['cat']}姿势"
            pre = f"{item['en']}, {item['lineEn']}"
            desc = (
                f"{item['zh']}：{item['line']} · {item['cat']}姿势参考，{len(angles)} 个拍摄角度（{'、'.join(a['zh'] for a in angles)}），附中英文提示词。"
                if is_zh
                else f"{te} — {item['lineEn']} pose reference ({cen.lower()}), {len(angles)} camera angles ({', '.join(a['en'] for a in angles)}), with an English prompt."
            )
            ttl = f"{tz} · {item['cat']}姿势参考 | 衣姿 PoseWear" if is_zh else f"{te} – {cen} Pose Reference | PoseWear"
        elif kind in ('costume', 'anime'):
            prz = item['zh']
            pre = item['en']
            pzh = f"{item['cat']}穿搭，" + item['zh'].rstrip('。').replace('。', '，')
            desc = (
                f"{item['ti']}：{item['cat']}穿搭参考图。{item['zh']}附英文提示词，可在线 AI 试穿。"
                if is_zh
                else f"{te} – {cen.lower()} outfit reference image with an AI prompt: {item['en']}. Try it on online."
            )
            ttl = f"{tz} · {item['cat']}穿搭参考 | 衣姿 PoseWear" if is_zh else f"{te} – {cen} Outfit Reference | PoseWear"
        else:
            prz = item['zh']
            pre = item['en']
            pzh = item['zh'].rstrip('。').replace('。', '，')
            desc = f"{item['ti']}：{item['sec']}人像脸模参考（{item['len']}{'，' + item['st'] if item['st'] else ''}）。AI 生成的虚构人物，CC0 1.0，附中英文提示词。"
            ttl = f"{tz} · 人像脸模参考 {item['no']} | 衣姿 PoseWear"

        path = f'/{kind}/{item["id"]}/'
        crumbs = [
            (LABELS[lang]['home'], prefix + '/'),
            (LABELS[lang][kind], f'{prefix}/{kind}/'),
            (cz_ if is_zh else cen, f'{prefix}/{kind}/{slug}/'),
            (title, None),
        ]
        kws = (
            [cz_, cen]
            + ([item['line'], item['lineEn']] if kind == 'pose' else [])
            + ([x[1] if x[0] == 'item' else _color_zh(x[1]) for x in _costume_tags(item)] if kind in ('costume', 'anime') else [])
            + ([item['sec'], item['st']] if kind == 'portrait' else [])
        )
        kws = [kw for kw in kws if kw]
        creator = {'@type': 'Person', 'name': src[2], 'url': src[3]}
        image_obj = {
            '@type': 'ImageObject',
            '@id': page_url(lang, path) + '#image',
            'name': title,
            'description': desc,
            'contentUrl': f'{site}/{img}',
            'thumbnailUrl': thumb_abs(th),
            'url': page_url(lang, path),
            'width': w,
            'height': h,
            'encodingFormat': 'image/webp',
            'inLanguage': 'zh-CN' if is_zh else 'en',
            'keywords': ', '.join(kws),
            'creator': creator,
            'creditText': f'{src[0]} ({src[2]})',
            'acquireLicensePage': src[1],
            'isPartOf': {'@type': 'WebSite', 'name': '衣姿 PoseWear', 'url': site + '/'},
            'dateModified': last_mod[kind],
        }
        if kind == 'portrait':
            image_obj.update({'license': CC0_URL, 'copyrightNotice': 'CC0 1.0 (public domain dedication) by @agi_aibusi'})

        item_tags = []
        if kind in ('costume', 'anime'):
            item_tags = [
                (x[1] if x[0] == 'item' else _color_zh(x[1]), x[2])
                for x in _costume_tags(item)
                if x[2].replace(' ', '-') in tags_map
            ]
        tag_html = (
            '<div class="tg">'
            + f'<a href="{prefix}/{kind}/{slug}/">{_esc(cz_ if is_zh else cen)}</a>'
            + ''.join(f'<a href="{prefix}/tag/{en.replace(" ", "-")}/">{_esc(z if is_zh else en)}</a>' for z, en in item_tags)
            + (f'<a href="/portrait/{PORTRAIT_SECTIONS[item["sec"]][0]}/">{_esc(item["sec"])}</a>' if kind == 'portrait' else '')
            + '</div>'
        )
        angle_html = ''
        if kind == 'pose':
            angle_html = (
                '<div class="box"><small>'
                + ('拍摄角度' if is_zh else 'Camera angles')
                + '</small><ul>'
                + ''.join(
                    f'<li><a href="/{a["i"]}">{_esc(a["zh"] if is_zh else a["en"])}</a> · <code>{_esc(a["en"])}</code></li>'
                    for a in angles
                )
                + '</ul></div>'
            )

        if kind == 'portrait':
            lic_inner = f'许可：<a href="{CC0_URL}" rel="license">CC0 1.0</a>，可商用、可修改，无需署名；原作者希望不要原样批量转载。来源：<a href="{src[1]}" rel="noopener">{src[0]}</a>（<a href="{src[3]}" rel="noopener">{src[2]}</a>）。'
        elif is_zh:
            lic_inner = f'来源：<a href="{src[1]}" rel="noopener">{src[0]}</a>，原作者 <a href="{src[3]}" rel="noopener">{src[2]}</a>。原站未标明授权，转载或商用请先联系原作者。'
        else:
            lic_inner = f'Source: <a href="{src[1]}" rel="noopener">{src[0]}</a> by <a href="{src[3]}" rel="noopener">{src[2]}</a>. No license is stated by the source; ask the author before reuse.'
        lic = f'<p class="mu">{lic_inner}</p>'

        if is_zh:
            boxes = (
                f'<div class="box"><small>中文描述</small><p>{_esc(prz)}</p></div>'
                f'<div class="box"><small>中文提示词</small><p>{_esc(pzh)}</p></div>'
                f'<div class="box"><small>英文提示词 · PROMPT</small><p>{_esc(pre)}</p></div>'
            )
        else:
            boxes = (
                f'<div class="box"><small>PROMPT</small><p>{_esc(pre)}</p></div>'
                f'<div class="box" lang="zh-CN"><small>中文提示词 · Chinese prompt</small><p>{_esc(pzh)}</p></div>'
            )

        workbench = f'/#workbench/{kind}/{item["id"]}'
        rel_html = ''.join(card_li(lang, kind, r) for r in related)
        meta_line = (
            (item['line'] + ' · ' + item['cat'] if is_zh else item['lineEn'] + ' · ' + cen)
            if kind == 'pose'
            else (cz_ if is_zh else cen)
        )
        more_heading = ('同类' + ('姿势' if kind == 'pose' else '穿搭' if kind in ('costume', 'anime') else '人像')) if is_zh else 'More like this'
        body = (
            f'<main><div class="im"><img src="/{img}" alt="{_esc(title)}" width="{w}" height="{h}" fetchpriority="high"></div>'
            f'<div>{crumbs_html(crumbs)}<h1>{_esc(title)}</h1>'
            f'<div class="mu">{_esc(meta_line)} · {"编号" if is_zh else "No."} {_esc(item.get("no") or item["id"])}</div>{tag_html}'
            f'{boxes}{angle_html}'
            f'<a class="go" href="/#{kind}/{item["id"]}">{"在衣姿中打开" if is_zh else "Open in PoseWear"}</a>'
            f'<a class="go secondary" href="{_esc(workbench)}">{"用作参考图" if is_zh else "Use as reference"}</a></div>'
            f'<section class="rel"><h2>{more_heading}</h2><ul>{rel_html}</ul></section></main>'
        )
        bid = page_url(lang, path) + '#breadcrumb'
        ld = [
            image_obj,
            crumbs_ld(crumbs, bid),
            {
                '@type': 'WebPage',
                '@id': page_url(lang, path),
                'url': page_url(lang, path),
                'name': ttl,
                'inLanguage': 'zh-CN' if is_zh else 'en',
                'primaryImageOfPage': {'@id': page_url(lang, path) + '#image'},
                'breadcrumb': {'@id': bid},
            },
        ]
        return shell(lang, path, ttl, desc, body, ld, has_en=kind in HAS_EN, og=img, ogt='article', credit=lic, workbench=workbench)

    # 1. Detail pages
    for kind, items in (('pose', safe_poses), ('costume', safe_costumes), ('anime', safe_anime), ('portrait', safe_portraits)):
        for i, item in enumerate(items):
            cat_slug = _category_of(kind, item)[1]
            same = [x for x in items if _category_of(kind, x)[1] == cat_slug and x['id'] != item['id']]
            pos = sum(1 for x in items[:i] if _category_of(kind, x)[1] == cat_slug)
            related = (same[pos:] + same[:pos])[:8]
            imgs = [a['i'] for a in item['angles']] if kind == 'pose' else [item['m']]
            for lang in (['zh', 'en'] if kind in HAS_EN else ['zh']):
                prefix = '/en' if lang == 'en' else ''
                write_page(f'{prefix}/{kind}/{item["id"]}/', detail_page(lang, kind, item, related))
            add_sitemap(kind, f'/{kind}/{item["id"]}/', last_mod[kind], [(site + '/' + x, _zh_title(kind, item)) for x in imgs], has_en=kind in HAS_EN)

    # 2. Category / tag / hub pages
    per_page = 96

    def listing_page(lang, kind, base, slug, cz_, cen, items, item_kind=None, has_en=True, sm='pages'):
        is_zh = lang == 'zh'
        prefix = '' if is_zh else '/en'
        item_kind = item_kind or kind
        total = len(items)
        label = cz_ if is_zh else cen
        pages = max(1, -(-total // per_page))
        zh_suffix = '' if kind == 'tag' else {'pose': '姿势', 'costume': '穿搭', 'anime': '动画穿搭', 'portrait': '人像'}[kind]
        en_suffix = 'Outfit' if kind in ('costume', 'tag', 'anime') else {'pose': 'Pose', 'portrait': 'Portrait'}[kind]
        for pg in range(1, pages + 1):
            path = f'{base}{slug}/' + (f'{pg}/' if pg > 1 else '')
            crumbs = [
                (LABELS[lang]['home'], prefix + '/'),
                (LABELS[lang][kind], f'{prefix}{base}'),
                (label, None if pg == 1 else f'{prefix}{base}{slug}/'),
            ] + ([(f'第 {pg} 页' if is_zh else f'Page {pg}', None)] if pg > 1 else [])
            ttl = (
                f"{label}{zh_suffix}参考图{'' if pg == 1 else f'（第 {pg} 页）'} | 衣姿 PoseWear"
                if is_zh
                else f"{label} {en_suffix} References{'' if pg == 1 else f' – Page {pg}'} | PoseWear"
            )
            desc = LISTING_INTROS[kind][0 if is_zh else 1].format(c=label, n=total)
            slice_items = items[(pg - 1) * per_page : pg * per_page]
            pgn = ''
            if pages > 1:
                pgn = '<nav class="pg" aria-label="pagination">' + ''.join(
                    f'<b>{i}</b>' if i == pg else f'<a href="{prefix}{base}{slug}/{"" if i == 1 else str(i) + "/"}">{i}</a>'
                    for i in range(1, pages + 1)
                ) + '</nav>'
            body = (
                f'<div class="wrap">{crumbs_html(crumbs)}<h1>{_esc(ttl.split(" | ")[0])}</h1>'
                f'<p class="lead">{_esc(desc)}</p>'
                f'<ul class="cg">{"".join(card_li(lang, item_kind, it) for it in slice_items)}</ul>{pgn}</div>'
            )
            ld = [
                {
                    '@type': 'CollectionPage',
                    '@id': page_url(lang, path),
                    'url': page_url(lang, path),
                    'name': ttl,
                    'description': desc,
                    'inLanguage': 'zh-CN' if is_zh else 'en',
                    'isPartOf': {'@type': 'WebSite', 'name': '衣姿 PoseWear', 'url': site + '/'},
                },
                crumbs_ld(crumbs),
                {
                    '@type': 'ItemList',
                    'numberOfItems': len(slice_items),
                    'itemListElement': [
                        {
                            '@type': 'ListItem',
                            'position': i + 1,
                            'url': site + ('/en' if not is_zh and item_kind in HAS_EN else '') + f'/{item_kind}/{it["id"]}/',
                        }
                        for i, it in enumerate(slice_items)
                    ],
                },
            ]
            write_page(prefix + path, shell(lang, path, ttl, desc, body, ld, has_en=has_en))
            if is_zh:
                add_sitemap(sm, path, last_mod[item_kind], has_en=has_en)

    cats = {
        'pose': [(POSE_CATEGORIES[k][0], k, POSE_CATEGORIES[k][1], L) for k in POSE_CATEGORIES if (L := [p for p in safe_poses if p['cat'] == k])],
        'costume': [(COSTUME_CATEGORIES[k][0], k, COSTUME_CATEGORIES[k][1], L) for k in COSTUME_CATEGORIES if (L := [c for c in safe_costumes if c['cat'] == k])],
        'anime': [(COSTUME_CATEGORIES[k][0], k, COSTUME_CATEGORIES[k][1], L) for k in COSTUME_CATEGORIES if (L := [c for c in safe_anime if c['cat'] == k])],
        'portrait': (
            [(PORTRAIT_SECTIONS[k][0], k, PORTRAIT_SECTIONS[k][1], L) for k in PORTRAIT_SECTIONS if (L := [r for r in safe_portraits if r['sec'] == k])]
            + [(PORTRAIT_LENGTHS[k][0], k, PORTRAIT_LENGTHS[k][1], L) for k in PORTRAIT_LENGTHS if (L := [r for r in safe_portraits if r['len'] == k])]
        ),
    }

    for lang in ('zh', 'en'):
        for kind, cat_list in cats.items():
            for slug, zh_name, en_name, items in cat_list:
                listing_page(lang, kind, f'/{kind}/', slug, zh_name, en_name, items)
        for slug, tag_entry in tags_map.items():
            listing_page(lang, 'tag', '/tag/', slug, tag_entry['zh'], tag_entry['en'], tag_entry['L'], item_kind='costume')

    counts = {
        'pose': len(safe_poses),
        'costume': len(safe_costumes),
        'anime': len(safe_anime),
        'portrait': len(safe_portraits),
        'tag': len(tags_map),
    }

    def hub_page(lang, kind):
        is_zh = lang == 'zh'
        prefix = '' if is_zh else '/en'
        path = f'/{kind}/'
        name = HUB_NAMES[kind][0 if is_zh else 1]
        if kind != 'tag':
            entries = [(s, z, e, len(items)) for s, z, e, items in cats[kind]]
            first = {s: items[0] for s, _, _, items in cats[kind]}
        else:
            entries = [(s, t['zh'], t['en'], len(t['L'])) for s, t in sorted(tags_map.items(), key=lambda pair: -len(pair[1]['L']))]
            first = {s: t['L'][0] for s, t in tags_map.items()}
        desc = HUB_INTROS[kind][0 if is_zh else 1].format(n=counts[kind])
        crumbs = [(LABELS[lang]['home'], prefix + '/'), (LABELS[lang][kind], None)]
        item_kind = 'costume' if kind == 'tag' else kind
        tw, th = THUMB_DIMENSIONS[item_kind]
        li_html = ''.join(
            f'<li><a href="{prefix}/{kind}/{slug}/">'
            f'<img src="{thumb_url(_thumb(item_kind, first[slug]))}" alt="{_esc(zh if is_zh else en)}" width="{tw}" height="{th}" loading="lazy" decoding="async">'
            f'<span>{_esc(zh if is_zh else en)} · {cnt}</span></a></li>'
            for slug, zh, en, cnt in entries
        )
        extra = '' if kind != 'costume' else f'<p><a href="{prefix}/tag/">{"按单品和颜色浏览 →" if is_zh else "Browse by garment and colour →"}</a></p>'
        body = f'<div class="wrap">{crumbs_html(crumbs)}<h1>{_esc(name)}</h1><p class="lead">{_esc(desc)}</p><ul class="cg">{li_html}</ul>{extra}</div>'
        ld = [
            {'@type': 'CollectionPage', 'url': page_url(lang, path), 'name': name, 'description': desc, 'inLanguage': 'zh-CN' if is_zh else 'en'},
            crumbs_ld(crumbs),
        ]
        write_page(prefix + path, shell(lang, path, f'{name} | 衣姿 PoseWear' if is_zh else f'{name} | PoseWear', desc, body, ld))
        if is_zh:
            add_sitemap('pages', path, today)

    for lang in ('zh', 'en'):
        for kind in HUB_NAMES:
            hub_page(lang, kind)

    # 3. English home page
    cat_links_en = ''.join(
        f'<li><a href="/en/{k}/{s}/">{_esc(en)}</a></li>'
        for k in ('pose', 'costume')
        for s, _, en, _ in cats[k]
    )
    en_desc = f'PoseWear: {len(safe_poses)} pose sets ({na_pub} angle images), {len(safe_costumes):,} outfits, {len(safe_anime):,} anime outfits and {len(safe_portraits):,} CC0 portraits, all with English and Chinese prompts — plus online AI try-on.'
    en_ld = [
        {
            '@type': 'WebSite',
            '@id': site + '/en/#website',
            'url': site + '/en/',
            'name': 'PoseWear',
            'alternateName': '衣姿 PoseWear',
            'inLanguage': 'en',
            'description': en_desc,
            'potentialAction': {
                '@type': 'SearchAction',
                'target': {'@type': 'EntryPoint', 'urlTemplate': site + '/?t=costume&q={search_term_string}'},
                'query-input': 'required name=search_term_string',
            },
        },
        {
            '@type': 'WebApplication',
            'name': 'PoseWear',
            'url': site + '/en/',
            'applicationCategory': 'DesignApplication',
            'operatingSystem': 'Any (web browser)',
            'browserRequirements': 'Requires JavaScript',
            'inLanguage': ['zh-CN', 'en', 'ja', 'vi'],
            'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
            'description': en_desc,
        },
    ]
    en_body = (
        f'<div class="wrap"><h1>Pose, outfit and portrait references with prompts</h1>'
        f'<p class="lead">{_esc(en_desc)} Favourite and combine references, copy prompts for Stable Diffusion or Midjourney, or upload your own photo to try an outfit on.</p>'
        f'<p><a class="go" href="/#costume">Open the gallery</a><a class="go secondary" href="/#studio">Try on online</a></p>'
        f'<section class="sec"><h2>Browse by category</h2><ul class="tg">{cat_links_en}<li><a href="/en/portrait/">Portraits</a></li><li><a href="/en/anime/">Anime outfits</a></li><li><a href="/en/tag/">Outfit tags</a></li></ul></section>'
        f'<section class="sec"><h2>Outfits</h2><ul class="cg">{"".join(card_li("en", "costume", c) for c in safe_costumes[:12])}</ul></section>'
        f'<section class="sec"><h2>Poses</h2><ul class="cg">{"".join(card_li("en", "pose", p) for p in safe_poses[:12])}</ul></section>'
        f'</div>'
    )
    en_credit = (
        'The code is open source (MIT, <a href="https://github.com/atuizz/posewear">GitHub</a>). '
        'Pose and outfit images come from AI Pose Gallery / AI Costume Gallery by <a href="https://x.com/giaaibusi">@giaaibusi</a> — '
        'no license is stated, so ask the author before reuse. Portraits come from AI Portrait Gallery by '
        f'<a href="https://x.com/agi_aibusi">@agi_aibusi</a> under <a href="{CC0_URL}" rel="license">CC0 1.0</a>.'
    )
    write_page('/en/', shell('en', '/', 'PoseWear – Pose & Outfit Reference Library with AI Prompts and Online Try-On', en_desc, en_body, en_ld, credit=en_credit))
    add_sitemap('pages', '/', today)

    # 4. Chinese home page: meta, JSON-LD, live stats, SSR first 12 poses, footer category index
    home_pub = {'pose': len(safe_poses), 'ang': na_pub, 'cos': len(safe_costumes), 'ani': anime_pub, 'por': len(safe_portraits)}
    home_all = {'pose': len(poses), 'ang': na_total, 'cos': len(costumes), 'ani': len(anime), 'por': len(portraits)}
    for stat_key, filename in EXTRA_CATALOG_STATS:
        raw_payload = catalogs[filename]
        parsed = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
        items = parsed['items'] if isinstance(parsed, dict) else parsed
        home_pub[stat_key] = sum(1 for item in items if not item.get('a'))
        home_all[stat_key] = len(items)

    zh_desc = f"衣姿 PoseWear：{home_pub['pose']} 组姿势（{home_pub['ang']:,} 张角度图）、{home_pub['cos']:,} 套服装、{home_pub['ani']:,} 套动画服装、{home_pub['por']:,} 张人像参考图，附中英文提示词，可上传照片在线 AI 试穿。免费，无需注册。"
    zh_title = '衣姿 PoseWear · 姿势、服装、人像参考图库 | 中英文提示词 + 在线 AI 试穿'

    index_path = os.path.join(dist_dir, 'index.html')
    with open(index_path) as fh:
        idx = fh.read()
    idx = re.sub(r'<title>.*?</title>', f'<title>{zh_title}</title>', idx, count=1)
    idx = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{_esc(zh_desc)}">', idx, count=1)
    idx = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="衣姿 PoseWear：姿势、服装、人像参考图库">', idx, count=1)
    idx = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{_esc(zh_desc)}">', idx, count=1)
    idx = idx.replace('<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:description" content="{_esc(zh_desc)}">', 1)
    idx = idx.replace('https://posewear.pages.dev/', site + '/')
    idx = idx.replace(f'<link rel="canonical" href="{site}/">', f'<link rel="canonical" href="{site}/">' + hreflang_tags('/'))
    home_ld = [
        {
            '@type': 'WebSite',
            '@id': site + '/#website',
            'url': site + '/',
            'name': '衣姿 PoseWear',
            'alternateName': ['PoseWear', '衣姿'],
            'inLanguage': 'zh-CN',
            'description': zh_desc,
            'potentialAction': {
                '@type': 'SearchAction',
                'target': {'@type': 'EntryPoint', 'urlTemplate': site + '/?t=costume&q={search_term_string}'},
                'query-input': 'required name=search_term_string',
            },
        },
        {
            '@type': 'WebApplication',
            'name': '衣姿 PoseWear',
            'url': site + '/',
            'applicationCategory': 'DesignApplication',
            'operatingSystem': 'Any (web browser)',
            'browserRequirements': 'Requires JavaScript',
            'inLanguage': ['zh-CN', 'en', 'ja', 'vi'],
            'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'CNY'},
            'description': zh_desc,
            'image': site + '/og.png',
            'isAccessibleForFree': True,
            'featureList': ['姿势参考图（多角度）', '服装穿搭参考图', '人像脸模参考（CC0）', '中英文提示词', '在线 AI 试穿'],
        },
    ]
    home_ld_json = json.dumps({'@context': 'https://schema.org', '@graph': home_ld}, ensure_ascii=False, separators=(',', ':'))
    idx = idx.replace('</head>', f'<script type="application/ld+json">{home_ld_json}</script></head>', 1)

    for key in home_pub:
        idx = re.sub(
            r'<b (?=[^>]*data-stat="' + key + r'")[^>]*>[^<]*</b>',
            f'<b data-stat="{key}" data-n="{home_pub[key]}" data-na="{home_all[key]}">{home_pub[key]:,}</b>',
            idx,
            count=1,
        )

    def ssr_pose(pos_idx, pose):
        loading = '' if pos_idx < 4 else ' loading="lazy"'
        title = pose['zh']
        angles = pose['angles']
        return (
            f'<article class="card ssr"><div class="ph pose done">'
            f'<a href="/pose/{pose["id"]}/" class="ssl">'
            f'<img class="ld" src="{thumb_url(angles[0]["t"])}" alt="{_esc(title)}" width="300" height="400" decoding="async"{loading}></a>'
            f'<span class="badge">{pose["no"]}</span></div>'
            f'<div class="info"><h3><a href="/pose/{pose["id"]}/">{_esc(title)}</a></h3>'
            f'<div class="sub">{_esc(pose["cat"])} · {len(angles)} 个角度</div>'
            f'<div class="tags"><span class="tag">{_esc(pose["line"])}</span><span class="tag c">{_esc(pose["cat"])}</span></div></div></article>'
        )

    grid_match = re.search(r'(<main id="grid"[^>]*>)(.*?)(</main>)', idx, re.S)
    idx = idx[:grid_match.start(2)] + ''.join(ssr_pose(i, p) for i, p in enumerate(safe_poses[:12])) + idx[grid_match.end(2):]
    cat_nav = (
        '<nav class="seoc" aria-label="分类浏览">'
        '<div><h4>姿势分类</h4>' + ''.join(f'<a href="/pose/{s}/">{z}</a>' for s, z, _, _ in cats['pose']) + '</div>'
        '<div><h4>服装分类</h4>' + ''.join(f'<a href="/costume/{s}/">{z}</a>' for s, z, _, _ in cats['costume']) + '<a href="/tag/">按单品和颜色</a></div>'
        '<div><h4>人像</h4>' + ''.join(f'<a href="/portrait/{s}/">{z}</a>' for s, z, _, _ in cats['portrait']) + '</div>'
        '<div><h4>其他</h4><a href="/pose/">姿势图库</a><a href="/costume/">服装图库</a><a href="/anime/">动画服装图库</a><a href="/portrait/">人像图库</a><a href="/en/" hreflang="en" lang="en">English</a></div>'
        '</nav>'
    )
    idx = idx.replace('<!-- category-index -->', '<details class="footer-index"><summary>分类索引</summary>' + cat_nav + '</details>')
    with open(index_path, 'w') as fh:
        fh.write(idx)

    # 5. Sitemaps, robots.txt, URL list and extra cache headers
    def sitemap_xml(entries):
        out = ['<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n']
        for loc, lm, imgs in entries:
            img_tags = ''.join(f'<image:image><image:loc>{_esc(u)}</image:loc></image:image>' for u, _ in imgs)
            out.append(f'<url><loc>{loc}</loc><lastmod>{lm}</lastmod>{img_tags}</url>\n')
        return ''.join(out) + '</urlset>\n'

    sitemaps['pages'].insert(0, (site + '/', today, [(site + '/og.png', '')]))
    for sm_key, entries in sitemaps.items():
        with open(os.path.join(dist_dir, f'sitemap-{sm_key}.xml'), 'w') as fh:
            fh.write(sitemap_xml(entries))

    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(
            f'<sitemap><loc>{site}/sitemap-{sm_key}.xml</loc><lastmod>{max((x[1] for x in entries), default=today)}</lastmod></sitemap>\n'
            for sm_key, entries in sitemaps.items()
        )
        + '</sitemapindex>\n'
    )
    for name in ('sitemap_index.xml', 'sitemap.xml'):
        with open(os.path.join(dist_dir, name), 'w') as fh:
            fh.write(sitemap_index)

    with open(os.path.join(dist_dir, 'robots.txt'), 'w') as fh:
        fh.write(f'User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /o/\n\nSitemap: {site}/sitemap_index.xml\n')

    with open(urls_path, 'w') as fh:
        fh.write('\n'.join(loc for entries in sitemaps.values() for loc, _, _ in entries) + '\n')

    with open(os.path.join(dist_dir, '_headers'), 'a') as fh:
        fh.write('/en/*\n  Cache-Control: public, max-age=600\n/tag/*\n  Cache-Control: public, max-age=600\n/sitemap*\n  Cache-Control: public, max-age=3600\n')

    summary = {'na_pub': na_pub, 'sitemaps': {k: len(v) for k, v in sitemaps.items()}, 'tags': len(tags_map)}
    print('NA_PUB', na_pub)
    print('seo', summary['sitemaps'], 'tags', summary['tags'])
    return summary
