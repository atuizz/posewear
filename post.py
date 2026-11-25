"""Build post-processor: asset fingerprinting, index.html/sw.js assembly, 404, _headers/CSP, and SEO."""

import base64
import hashlib
import json
import os
import re
import shutil

import seo


CLIENT_FILES = [
    'theme.js',
    'style.css',
    'i18n.js',
    'catalog.js',
    'references.js',
    'palette.js',
    'app.js',
    'sketch.js',
    'command-palette.js',
    'zip.js',
    'extras.js',
    'image-providers.js',
    'board-export.js',
    'studio.js',
    'history.js',
]

CATALOG_FILES = (
    'poses.json',
    'costumes.json',
    'anime.json',
    'portraits.json',
    'depths.json',
    'expressions.json',
    'hair.json',
    'dynasties.json',
    'scenes.json',
    'lights.json',
    'props.json',
    'furniture.json',
)

DARK_TOKENS = 'color-scheme:dark;--paper:#111;--ink:#eee;--muted:#aaa;--surface:#1d1d1d;--surface-hover:#292929;--edge:#333'

BASE_CSS = (
    ':root{color-scheme:light;--paper:#fff;--ink:#111;--muted:#606060;--surface:#f5f5f5;--surface-hover:#ececec;--edge:#ededed}'
    ':root[data-theme="dark"]{' + DARK_TOKENS + '}'
    '@media(prefers-color-scheme:dark){:root:not([data-theme]){' + DARK_TOKENS + '}}'
    'body{margin:0;font:15px/1.7 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--paper)}a{color:inherit}\n'
    'header{display:flex;align-items:center;gap:10px;padding:14px 20px;border-bottom:1px solid var(--edge)}header a{text-decoration:none;font-weight:700;display:flex;align-items:center;gap:8px}\n'
    '.mk{width:26px;height:26px;color:#ff2442;display:grid;place-items:center}.mk svg{width:26px;height:26px}\n'
    'main{max-width:1040px;margin:0 auto;padding:24px 20px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:32px}\n'
    '@media(max-width:760px){main{grid-template-columns:1fr}}\n'
    '.im img{width:100%;height:auto;border-radius:16px;background:var(--surface);display:block}\n'
    'h1{font-size:24px;margin:0 0 6px}.mu{color:var(--muted);font-size:13px}.bc{font-size:13px;color:var(--muted);margin-bottom:12px}\n'
    '.box{background:var(--surface);border-radius:14px;padding:14px 16px;margin:14px 0}.box small{color:var(--muted)}\n'
    '.go{display:inline-block;background:#d81b3a;color:white;border-radius:999px;padding:10px 22px;text-decoration:none;font-weight:600;margin:6px 8px 6px 0}\n'
    '.rel{grid-column:1/-1}.rel ul{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:12px}.rel img{width:100%;height:auto;border-radius:10px;background:var(--surface);display:block}.rel a{text-decoration:none;font-size:13px}\n'
    'footer{text-align:center;color:var(--muted);font-size:12px;padding:30px 20px;border-top:1px solid var(--edge)}\n'
    'h1{overflow-wrap:anywhere}\n'
    '.go.secondary{background:var(--ink);color:var(--paper)}'
)

LOGO = (
    '<span class="mk"><svg viewBox="0 0 32 32" aria-hidden="true">'
    '<circle cx="16" cy="6.6" r="4" fill="currentColor"/>'
    '<path d="M16 13.4 3.4 25.6h25.2z" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linejoin="round"/>'
    '</svg></span>'
)

IMMUTABLE_PATHS = ('/assets/*', '/p/*', '/c/*', '/a/*', '/r/*', '/e/*', '/y/*', '/s/*', '/l/*', '/t/*', '/f/*', '/o/*')


def _hash10(data):
    raw = data if isinstance(data, bytes) else data.encode()
    return hashlib.sha256(raw).hexdigest()[:10]


def _build_csp(inline_hashes, img_origins, wa_token):
    script_src = "'self' " + inline_hashes + (' https://static.cloudflareinsights.com' if wa_token else '')
    img_src = ' '.join(img_origins)
    # Local loopback http is allowed so custom/local engines (e.g. ComfyUI, sd.cpp, OpenAI-compatible
    # gateways on 127.0.0.1/localhost) can be fetched directly from the browser without CSP blocking.
    return (
        f"default-src 'self'; script-src {script_src}; style-src 'self' 'unsafe-inline'; "
        f"img-src {img_src}; font-src 'self' data:; "
        "connect-src 'self' data: blob: https: http://localhost:* http://127.0.0.1:*; "
        "worker-src 'self'; manifest-src 'self'; media-src 'self' blob:; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
        "upgrade-insecure-requests"
    )


def run(ctx):
    """Fingerprint assets, rewrite index.html & sw.js, emit 404/_headers/functions, then run seo.run."""
    dist_dir = ctx['dist_dir']
    src_dir = ctx.get('src_dir', 'src')
    functions_dir = ctx.get('functions_dir', 'functions')
    site = ctx.get('site', os.environ.get('POSEWEAR_SITE', 'https://posewear.pages.dev')).rstrip('/')
    asset_host = ctx.get('asset_host', os.environ.get('POSEWEAR_ASSET_HOST', '')).rstrip('/')
    wa_token = ctx.get('wa_token', os.environ.get('POSEWEAR_WA_TOKEN', '')).strip()
    catalogs = ctx['catalogs']
    depth_origins = list(ctx.get('depth_origins', ()))
    hotlink_origins = list(ctx.get('hotlink_origins', ()))

    assets_dir = os.path.join(dist_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    for name in os.listdir(assets_dir):
        os.remove(os.path.join(assets_dir, name))

    assets = {}

    def put(name, data):
        blob = data.encode() if isinstance(data, str) else data
        base, ext = name.rsplit('.', 1)
        rel = f'assets/{base}.{_hash10(blob)}.{ext}'
        with open(os.path.join(dist_dir, rel), 'wb') as fh:
            fh.write(blob)
        assets[name] = rel
        return rel

    # 1. Write all 12 fingerprinted catalog JSON manifests
    for filename in CATALOG_FILES:
        payload = catalogs[filename]
        if not isinstance(payload, (str, bytes)):
            payload = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
        put(filename, payload)

    # 2. Fingerprint client scripts & styles (inject asset host & manifest hashes into app.js)
    for filename in CLIENT_FILES:
        if filename != 'app.js':
            with open(os.path.join(src_dir, filename), 'rb') as fh:
                put(filename, fh.read())

    with open(os.path.join(src_dir, 'app.js')) as fh:
        app_js = fh.read()
    if asset_host:
        app_js = app_js.replace("const AH='';", f"const AH={repr(asset_host + '/')};")
    for name, rel in assets.items():
        if name.endswith('.json'):
            app_js = app_js.replace(repr(name), repr('/' + rel))
    put('app.js', app_js)

    # 3. Assemble index.html with hashed assets and remove unhashed duplicates from dist/
    with open(os.path.join(src_dir, 'index.html')) as fh:
        idx = fh.read()
    for filename in CLIENT_FILES:
        idx = idx.replace(f'"{filename}"', f'"/{assets[filename]}"')
    idx = idx.replace('href="poses.json"', f'href="/{assets["poses.json"]}"')
    if wa_token:
        idx = idx.replace(
            '</body>',
            f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token": "{wa_token}"}}\'></script></body>',
        )
    with open(os.path.join(dist_dir, 'index.html'), 'w') as fh:
        fh.write(idx)

    for filename in CLIENT_FILES:
        unhashed = os.path.join(dist_dir, filename)
        if os.path.exists(unhashed):
            os.remove(unhashed)

    # 4. Assemble Service Worker with version hash and fingerprinted precache list
    with open(os.path.join(src_dir, 'sw.js')) as fh:
        sw = fh.read()
    version = 'posewear-' + _hash10(sw + idx + ''.join(assets.values()))
    sw = sw.replace("'posewear-development'", repr(version))
    precache = ['/', '/favicon.svg'] + ['/' + assets[f] for f in CLIENT_FILES + ['poses.json', 'depths.json']]
    sw = re.sub(r'const PRECACHE = .*?;', 'const PRECACHE = ' + json.dumps(precache) + ';', sw, count=1)
    with open(os.path.join(dist_dir, 'sw.js'), 'w') as fh:
        fh.write(sw)

    # 5. Compute inline script SHA-256 CSP hashes, clean old static dirs, write 404.html
    inline_scripts = re.findall(r'<script>(.*?)</script>', idx, re.S)
    inline_hashes = ' '.join(
        "'sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() + "'"
        for script in inline_scripts
    )

    for sub in ('pose', 'costume', 'anime', 'portrait'):
        target = os.path.join(dist_dir, sub)
        if os.path.exists(target):
            shutil.rmtree(target)

    theme_head = f'<meta name="theme-color" content="#ffffff"><script src="/{assets["theme.js"]}"></script>'
    not_found_html = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>页面不存在 | 衣姿 PoseWear</title><meta name="robots" content="noindex">'
        f'<link rel="icon" href="/favicon.svg" type="image/svg+xml">{theme_head}<style>{BASE_CSS}\n'
        '.nf{max-width:480px;margin:12vh auto;text-align:center;padding:0 20px}'
        '.nf b{font-size:64px;color:#d81b3a;display:block;line-height:1}</style></head><body>'
        f'<header><a href="/">{LOGO}衣姿 PoseWear</a></header>'
        '<div class="nf"><b>404</b><h1>这个页面不存在</h1>'
        '<p class="mu">链接可能写错了，或者内容已经调整。</p>'
        '<a class="go" href="/">回到首页</a><a class="go secondary" href="/#costume">看看服装库</a></div></body></html>'
    )
    with open(os.path.join(dist_dir, '404.html'), 'w') as fh:
        fh.write(not_found_html)

    # 6. Copy Pages Functions into dist/ so wrangler pages deploy includes /api/proxy (issue #7)
    if functions_dir and os.path.isdir(functions_dir):
        dest_fn = os.path.join(dist_dir, 'functions')
        shutil.rmtree(dest_fn, ignore_errors=True)
        shutil.copytree(functions_dir, dest_fn)

    # 7. Write _headers (security headers + CSP + cache lifetimes)
    img_origins = ["'self'", 'data:', 'blob:'] + depth_origins + hotlink_origins + ([asset_host] if asset_host else [])
    csp = _build_csp(inline_hashes, img_origins, wa_token)
    imm_block = ''.join(f'{path}\n  Cache-Control: public, max-age=31536000, immutable\n' for path in IMMUTABLE_PATHS)
    headers = (
        f'/*\n'
        f'  Content-Security-Policy: {csp}\n'
        f'  X-Content-Type-Options: nosniff\n'
        f'  Referrer-Policy: strict-origin-when-cross-origin\n'
        f'  X-Frame-Options: DENY\n'
        f'  Strict-Transport-Security: max-age=31536000; includeSubDomains\n'
        f'  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()\n'
        f'  Cross-Origin-Opener-Policy: same-origin\n'
        f'{imm_block}'
        '/icon-*\n  Cache-Control: public, max-age=86400\n'
        '/og.png\n  Cache-Control: public, max-age=86400\n'
        '/sw.js\n  Cache-Control: no-cache\n'
        '/\n  Cache-Control: public, max-age=0, must-revalidate\n'
        '/index.html\n  Cache-Control: public, max-age=0, must-revalidate\n'
        '/pose/*\n  Cache-Control: public, max-age=600\n'
        '/costume/*\n  Cache-Control: public, max-age=600\n'
        '/anime/*\n  Cache-Control: public, max-age=600\n'
        '/portrait/*\n  Cache-Control: public, max-age=600\n'
    )
    with open(os.path.join(dist_dir, '_headers'), 'w') as fh:
        fh.write(headers)

    # 8. Delegate static SEO pages, sitemaps, robots.txt and SSR home fragment to seo.run
    seo_ctx = {
        **ctx,
        'site': site,
        'asset_host': asset_host,
        'assets': assets,
        'theme_head': theme_head,
        'base_css': BASE_CSS,
        'logo': LOGO,
    }
    seo_summary = seo.run(seo_ctx)
    return {'assets': assets, 'csp': csp, 'seo': seo_summary}
