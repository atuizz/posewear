"""Offline regression test for the build/post/seo/CSP pipeline (stdlib-only, no Pillow or raw archives required)."""

import json
import os
from pathlib import Path
import py_compile
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

import check_csp
import post


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


def _check_static_invariants():
    # 1. Compile all build pipeline modules (catches syntax errors even without Pillow installed)
    for name in ('build.py', 'post.py', 'seo.py', 'tests/check_csp.py'):
        py_compile.compile(str(ROOT / name), doraise=True)

    # 2. Ensure exec() glue has been eliminated from build.py / post.py / seo.py
    for name in ('build.py', 'post.py', 'seo.py'):
        text = (ROOT / name).read_text(encoding="utf-8")
        _assert('exec(' not in text, f'{name} must not use exec() glue')

    # 3. Every local script/stylesheet referenced by src/index.html must be in post.CLIENT_FILES and src/sw.js
    index_html = (ROOT / 'src/index.html').read_text(encoding="utf-8")
    referenced = set(re.findall(r'<script\b[^>]*\bsrc="([^":/]+\.js)"', index_html))
    referenced |= set(re.findall(r'<link\b[^>]*\brel="stylesheet"[^>]*\bhref="([^":/]+\.css)"', index_html))
    client_set = set(post.CLIENT_FILES)
    _assert(referenced == client_set, f'CLIENT_FILES mismatch with src/index.html: missing={referenced - client_set}, extra={client_set - referenced}')

    sw_text = (ROOT / 'src/sw.js').read_text(encoding="utf-8")
    sw_precache = set(re.findall(r"'([^']+\.(?:js|css))'", sw_text))
    _assert(client_set <= sw_precache, f'src/sw.js PRECACHE missing client files: {client_set - sw_precache}')


def _synthetic_dataset():
    poses_list = [
        {
            'id': 'p_001',
            'no': 'P001',
            'line': '全身·标准',
            'cat': '站姿',
            'ja': '立ちポーズ1',
            'zh': '自然站姿',
            'en': 'standing pose',
            'lineEn': 'full body, solo',
            'angles': [
                {'zh': '正面', 'en': 'front view', 't': 'p/t/p_001_f.webp', 'i': 'p/i/p_001_f.webp', 'o': 'o/p/p_001_f.png'},
                {'zh': '侧面', 'en': 'side view', 't': 'p/t/p_001_s.webp', 'i': 'p/i/p_001_s.webp', 'o': 'o/p/p_001_s.png'},
            ],
        },
        {
            'id': 'p_002',
            'no': 'P002',
            'line': '全身·性感',
            'cat': '性感·大胆',
            'ja': 'セクシー1',
            'zh': '性感站姿',
            'en': 'sexy standing pose',
            'lineEn': 'full body, solo, sexy',
            'a': 1,
            'angles': [
                {'zh': '正面', 'en': 'front view', 't': 'p/t/p_002_f.webp', 'i': 'p/i/p_002_f.webp', 'o': 'o/p/p_002_f.png'},
            ],
        },
    ]
    poses = {p['id']: p for p in poses_list}

    # 4 costumes with "dress" and "black" so tag threshold (>=4) triggers /tag/dress/ and /tag/black/
    costumes = [
        {
            'id': f'c_00{i}',
            'cat': '春季',
            'catEn': 'spring',
            'kw': 'black dress boots',
            'zh': f'黑色连衣裙搭配短靴穿搭 {i}。',
            'en': 'spring outfit, black dress, short boots',
            'ti': f'黑色连衣裙 {i}',
            't': f'c/t/c_00{i}.webp',
            'm': f'c/m/c_00{i}.webp',
            'i': f'c/i/c_00{i}.webp',
            'o': f'o/c/c_00{i}.png',
        }
        for i in range(1, 5)
    ]

    anime = [
        {
            'id': 'a_001',
            'cat': '夏季',
            'catEn': 'summer',
            'kw': 'white dress',
            'zh': '白色连衣裙动画穿搭。',
            'en': 'summer anime outfit, white dress',
            'ti': '白色连衣裙',
            't': 'a/t/a_001.webp',
            'm': 'a/m/a_001.webp',
            'i': 'a/i/a_001.webp',
            'o': 'o/a/a_001.png',
        },
        {
            'id': 'cdb_001',
            'cat': '夏季',
            'catEn': 'summer',
            'kw': 'sailor uniform',
            'zh': '水手服。',
            'en': 'sailor uniform',
            'ti': '水手服',
            't': 'https://charadb-2fi.pages.dev/t/cdb_001.webp',
            'm': 'https://charadb-2fi.pages.dev/m/cdb_001.webp',
            'i': 'https://charadb-2fi.pages.dev/i/cdb_001.webp',
            'o': '',
            'ext': 1,
        },
    ]

    portraits = [
        {
            'id': 'r_001',
            'no': 'F001',
            'sec': '正脸',
            'len': '短发',
            'st': '自然清透',
            'ti': '自然清透',
            'zh': '一位亚洲年轻女性，短发，正脸参考。',
            'en': 'young Asian woman, short hair, front portrait',
            'ja': 'ショート',
            't': 'r/t/r_001.webp',
            'm': 'r/m/r_001.webp',
            'i': 'r/m/r_001.webp',
            'o': 'o/r/r_001.png',
            'w': 800,
            'h': 1000,
        },
    ]

    depths = {
        'packs': [{'id': 'base', 'name': 'AI Pose Depth Gallery'}],
        'items': [
            {
                'id': 'd_001',
                'no': 'D001',
                'line': '全身·标准',
                'cat': '站姿',
                'zh': '深度站姿',
                'en': 'depth standing pose',
                'lineEn': 'full body, solo',
                'angles': [
                    {
                        'zh': '正面',
                        'en': 'front view',
                        't': 'https://pwimg.0vo.pro/d/thumbs/d_001.webp',
                        'i': 'https://pwimg.0vo.pro/d/img/d_001.webp',
                    }
                ],
            }
        ],
    }

    def view_item(prefix, item_id, title):
        return {
            'id': item_id,
            'cat': '默认',
            'ti': title,
            'zh': title,
            'en': title,
            'ja': '',
            'line': '标准',
            'lineEn': 'standard',
            'no': item_id,
            'angles': [
                {'zh': '正面', 'en': 'front view', 't': f'{prefix}/t/{item_id}_front.webp', 'i': f'{prefix}/i/{item_id}_front.webp', 'o': f'o/{prefix}/{item_id}_front.webp'}
            ],
        }

    hair = [
        {
            'id': 'h_001',
            'cat': '长发',
            'ti': '黑长直',
            'zh': '黑长直发型',
            'en': 'long straight black hair',
            't': 'https://charadb-2fi.pages.dev/hair/h_001.webp',
            'm': 'https://charadb-2fi.pages.dev/hair/h_001.webp',
            'i': 'https://charadb-2fi.pages.dev/hair/h_001.webp',
            'o': '',
            'ext': 1,
        }
    ]

    dump = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    catalogs = {
        'poses.json': dump(poses_list),
        'costumes.json': dump(costumes),
        'anime.json': dump(anime),
        'portraits.json': dump(portraits),
        'depths.json': dump(depths),
        'expressions.json': dump([view_item('e', 'E01', '微笑')]),
        'hair.json': dump(hair),
        'dynasties.json': dump([view_item('y', 'Y01', '唐代襦裙')]),
        'scenes.json': dump([view_item('s', 'S01', '咖啡馆')]),
        'lights.json': dump([view_item('l', 'L01', '逆光')]),
        'props.json': dump([view_item('t', 'T01', '雨伞')]),
        'furniture.json': dump([view_item('f', 'F01', '木椅')]),
    }
    data = {
        'poses': poses,
        'poses_list': poses_list,
        'costumes': costumes,
        'anime': anime,
        'portraits': portraits,
    }
    return catalogs, data


def _run_pipeline_regression():
    catalogs, data = _synthetic_dataset()
    with tempfile.TemporaryDirectory(prefix='posewear-post-test-') as tmp:
        tmp_path = Path(tmp)
        dist = tmp_path / 'dist'
        dist.mkdir()
        for entry in (ROOT / 'src').iterdir():
            shutil.copy(entry, dist / entry.name)

        ctx = {
            'raw_dir': str(tmp_path / 'raw-empty'),
            'dist_dir': str(dist),
            'src_dir': str(ROOT / 'src'),
            'functions_dir': str(ROOT / 'functions'),
            'site': 'https://posewear.pages.dev',
            'asset_host': 'https://pwimg.0vo.pro',
            'wa_token': 'test-wa-token-123',
            'urls_path': str(tmp_path / 'urls.txt'),
            'indexnow_key_path': str(tmp_path / 'indexnow.key'),
            'catalogs': catalogs,
            'data': data,
            'depth_origins': ['https://ai-pose-depth-gallery.pages.dev'],
            'hotlink_origins': ['https://charadb-2fi.pages.dev'],
        }
        result = post.run(ctx)

        # 1. Official CSP & catalog check must pass with 0 issues
        issues = check_csp.check(dist)
        _assert(not issues, 'check_csp.check failed:\n' + '\n'.join(issues))

        # 2. All 15 client files hashed into dist/assets/ and unhashed removed from dist/
        assets = result['assets']
        for name in post.CLIENT_FILES:
            _assert(name in assets, f'Missing asset mapping for {name}')
            _assert((dist / assets[name]).is_file(), f'Hashed file missing: {assets[name]}')
            _assert(not (dist / name).exists(), f'Unhashed file was not removed: {name}')

        # 3. Compiled app.js matches catalog-source.mjs discovery contracts
        app_js = (dist / assets['app.js']).read_text(encoding="utf-8")
        _assert("const AH='https://pwimg.0vo.pro/';" in app_js, 'AH asset host injection failed')
        discovered = set(re.findall(r'["\'](?:/assets/)?([a-z]+)\.[a-f0-9]{10}\.json["\']', app_js))
        expected_catalogs = {f.removesuffix('.json') for f in post.CATALOG_FILES}
        _assert(discovered == expected_catalogs, f'app.js catalog discovery mismatch: {expected_catalogs - discovered}')

        # 4. index.html references all hashed client files, stats, SSR cards, footer index, WA beacon
        idx = (dist / 'index.html').read_text(encoding="utf-8")
        for name in post.CLIENT_FILES:
            _assert(f'"/{assets[name]}"' in idx, f'index.html missing hashed reference for {name}')
        _assert('data-stat="pose" data-n="1" data-na="2"' in idx, 'pose stat counter mismatch')
        _assert('data-stat="cos" data-n="4" data-na="4"' in idx, 'costume stat counter mismatch')
        _assert('data-stat="ani" data-n="2" data-na="2"' in idx, 'anime stat counter mismatch')
        _assert('class="card ssr"' in idx, 'SSR pose cards missing in index.html')
        _assert('data-cf-beacon=\'{"token": "test-wa-token-123"}\'' in idx, 'Web Analytics beacon missing')

        # 5. Service Worker precache updated with hashed files
        sw = (dist / 'sw.js').read_text(encoding="utf-8")
        _assert("'posewear-development'" not in sw, 'sw.js version was not fingerprinted')
        for name in post.CLIENT_FILES + ['poses.json', 'depths.json']:
            _assert(f'"/{assets[name]}"' in sw, f'sw.js PRECACHE missing {name}')

        # 6. _headers CSP allows WA beacon, hotlinks, asset host, and loopback http
        headers = (dist / '_headers').read_text(encoding="utf-8")
        for token in (
            'https://static.cloudflareinsights.com',
            'https://pwimg.0vo.pro',
            'https://charadb-2fi.pages.dev',
            'https://ai-pose-depth-gallery.pages.dev',
            'http://localhost:*',
            'http://127.0.0.1:*',
            "'sha256-",
            '/en/*',
            '/sitemap*',
        ):
            _assert(token in headers, f'_headers missing expected token: {token}')

        # 7. Pages Functions copied into dist/functions/
        _assert((dist / 'functions/api/proxy.js').is_file(), 'functions/api/proxy.js not copied into dist/')

        # 8. Static SEO pages, sitemaps, robots.txt and IndexNow key generated
        for rel in (
            '404.html',
            'en/index.html',
            'pose/index.html',
            'en/pose/index.html',
            'pose/p_001/index.html',
            'en/pose/p_001/index.html',
            'costume/c_001/index.html',
            'en/costume/c_001/index.html',
            'anime/a_001/index.html',
            'portrait/r_001/index.html',
            'tag/dress/index.html',
            'en/tag/dress/index.html',
            'sitemap_index.xml',
            'sitemap.xml',
            'sitemap-pose.xml',
            'sitemap-pages.xml',
            'robots.txt',
        ):
            _assert((dist / rel).is_file(), f'Expected SEO output missing: {rel}')

        # Adult pose must NOT leak into public static SEO detail pages
        _assert(not (dist / 'pose/p_002/index.html').exists(), 'Adult pose leaked into public SEO page')
        # CharaDB hotlink anime outfit must NOT generate static detail page
        _assert(not (dist / 'anime/cdb_001/index.html').exists(), 'External hotlink anime item leaked into static detail page')

        key = (tmp_path / 'indexnow.key').read_text(encoding="utf-8").strip()
        _assert((dist / f'{key}.txt').read_text(encoding="utf-8").strip() == key, 'IndexNow key file mismatch')
        _assert((tmp_path / 'urls.txt').read_text(encoding="utf-8").strip().splitlines(), 'urls.txt is empty')


if __name__ == '__main__':
    _check_static_invariants()
    _run_pipeline_regression()
    print('PASS build/post/seo/CSP module pipeline regressions')
