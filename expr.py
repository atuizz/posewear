# 表情素材：字段映射、校验、缩略图、expressions.json。
# manifest 字段名只在 FIELDS / VIEWS / ANGLES 出现一次。前端只读构建结果。
import json, os, shutil
from PIL import Image

ROOT = os.environ.get('POSEWEAR_EXPR', 'expressions/packs')
SKIP = {'manifest.json', 'about.json', 'README.md', 'README.txt', 'contact_sheet.png', '.DS_Store'}
ID_RE = __import__('re').compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$')
KEY_RE = __import__('re').compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

# manifest 字段 -> 站内字段。新增素材字段只改这里。
FIELDS = {
    'id': 'id', 'name_zh': 'zh', 'name_en': 'en', 'tags': 'tags', 'angle': 'angle',
    'group': 'group', 'prompt_zh': 'zhPrompt', 'prompt_en': 'enPrompt', 'w': 'w', 'h': 'h',
    'pack': 'pack', 'blendshape_weights': 'weights',
}
REQ = ['id', 'name_zh', 'tags', 'angle', 'source', 'depth', 'landmarks', 'w', 'h', 'pack']
VIEWS = [
    {'id': 'source', 'field': 'source', 'zh': '原图', 'en': 'Color', 'role': 'color'},
    {'id': 'depth', 'field': 'depth', 'zh': '深度图', 'en': 'Depth', 'role': 'depth'},
    {'id': 'landmarks', 'field': 'landmarks', 'zh': '线稿', 'en': 'Landmarks', 'role': 'line'},
]
# 已知角度的显示名。manifest.angles 可覆盖或追加，未列出的角度原样显示，不必改代码。
ANGLES = {
    'front': {'zh': '正面', 'en': 'front view', 'pose': '正面', 'aliases': ['正面']},
    'three_quarter': {'zh': '斜侧', 'en': 'three-quarter view', 'pose': '斜侧', 'aliases': ['3/4 侧', '3/4侧', '斜侧', '四分之三侧']},
    'side': {'zh': '侧面', 'en': 'side view', 'pose': '侧面', 'aliases': ['侧面']},
    'high': {'zh': '俯拍', 'en': 'high angle, from above', 'pose': '俯拍', 'aliases': ['俯拍']},
    'low': {'zh': '仰拍', 'en': 'low angle, from below', 'pose': '仰拍', 'aliases': ['仰拍']},
}
ANGLE_ORDER = ['front', 'three_quarter', 'side', 'high', 'low']
# 姿势角度对不上时，先试同名，再按这里退回。键是姿势库的中文角度。
FALLBACK = {'俯拍': ['正面'], '仰拍': ['正面'], '侧面': ['斜侧']}
TEMPLATES = {
    'zh': '{poseZh}，{lineZh}，{poseAngZh}。面部表情：{exprZh}（{tags}），{exprAngZh}。请参考所附表情原图、深度图（白色为近）和面部关键点线稿。',
    'en': '{poseEn}, {lineEn}, {poseAngEn}. Facial expression: {exprEn} ({tags}), {exprAngEn}. Follow the attached expression render, depth map (white is near) and facial-landmark line art.',
}
FACEKIT_REPO = 'https://github.com/ICT-VGL/ICT-FaceKit'
FACEKIT_VARIANT = 'Light'
# 默认分支 master 在 2026-10-31 的最新提交（Merge pull request #15）
FACEKIT_COMMIT = 'da5f95a607f5e6b37755b38d3385d7f2853732e5'
FACEKIT_UPSTREAM = {'repo': FACEKIT_REPO, 'variant': FACEKIT_VARIANT, 'commit': FACEKIT_COMMIT}
THIRD_PARTY = 'THIRD_PARTY_LICENSES.txt'
FACEKIT_LICENSE = (
    'MIT. Face model: ICT-FaceKit Light only, Copyright (c) 2020 USC Institute for Creative Technologies. '
    + FACEKIT_REPO + ' @ ' + FACEKIT_COMMIT + '. Full text: ' + THIRD_PARTY + '.'
)


def third_party_text(repo, variant, commit):
    """包内 THIRD_PARTY_LICENSES.txt：锁定信息 + ICT-FaceKit MIT 全文。"""
    lic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LICENSES', 'ICT-FaceKit.txt')
    body = open(lic_path, encoding='utf-8').read().strip() + '\n'
    return (
        '第三方许可 / Third-party notice\n'
        '上游仓库 / Upstream: %s\n'
        '版本 / Variant: %s\n'
        '锁定提交 / Commit: %s\n'
        '\n'
        '本包只使用上述提交里的 ICT Face Model Light。\n'
        '不包含 Full ICT Face Model（完整模型另行授权，未使用）。\n'
        'This pack uses only the ICT Face Model Light at the commit above.\n'
        'The Full ICT Face Model is not included.\n'
        '\n'
        '%s' % (repo, variant, commit, body)
    )


def abort(errors):
    raise SystemExit('表情素材校验失败（%d 项）：\n%s' % (len(errors), '\n'.join('- ' + e for e in errors)))


def _inside(root, rel):
    rel = os.path.normpath(rel)
    if rel.startswith('..') or os.path.isabs(rel):
        return None
    full = os.path.normpath(os.path.join(root, rel))
    if os.path.commonpath([os.path.abspath(root), os.path.abspath(full)]) != os.path.abspath(root):
        return None
    return full


def pack_views(manifest):
    views = [dict(v) for v in VIEWS]
    by = {v['id']: v for v in views}
    for v in manifest.get('views') or []:
        if not isinstance(v, dict) or not v.get('id'):
            continue
        if v['id'] in by:
            by[v['id']].update(v)
        else:
            views.append(dict(v))
            by[v['id']] = views[-1]
    return views


def angle_table(manifests):
    table = {k: dict(v) for k, v in ANGLES.items()}
    for m in manifests:
        for k, v in (m.get('angles') or {}).items():
            if isinstance(v, dict):
                table[k] = {**table.get(k, {}), **v}
    return table


def hide_set(table, manifests):
    hide = set()
    for a in table.values():
        for k in ('zh', 'en', 'pose'):
            if a.get(k):
                hide.add(a[k])
        hide.update(a.get('aliases') or [])
    hide.update(table.keys())
    for m in manifests:
        hide.update(m.get('hideTags') or [])
    return {x for x in hide if isinstance(x, str) and x}


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_image(path, role, w, h):
    err = []
    try:
        im = Image.open(path)
        im.load()
    except Exception as e:
        return ['%s: 无法打开（%s）' % (path, e)]
    if im.size != (int(w), int(h)):
        err.append('%s: 尺寸 %d×%d，manifest 为 %s×%s' % (path, im.size[0], im.size[1], w, h))
    if role == 'color' and im.mode not in ('RGB', 'RGBA'):
        err.append('%s: 原图通道 %s，需要 RGB' % (path, im.mode))
    elif role == 'depth' and im.mode != 'L':
        err.append('%s: 深度图通道 %s，需要 8 位单通道 L（白为近）' % (path, im.mode))
    elif role == 'line':
        if im.mode not in ('L', 'RGB', 'RGBA'):
            err.append('%s: 线稿通道 %s' % (path, im.mode))
        elif im.mode in ('RGB', 'RGBA'):
            r, g, b = im.convert('RGB').split()
            if r.tobytes() != g.tobytes() or g.tobytes() != b.tobytes():
                err.append('%s: 线稿不是纯灰度' % path)
    elif role == 'image' and im.mode not in ('L', 'RGB', 'RGBA'):
        err.append('%s: 通道 %s' % (path, im.mode))
    elif role not in ('color', 'depth', 'line', 'image'):
        err.append('%s: 未知视图 role %s' % (path, role))
    return err


def _pack_meta(manifest, folder):
    pid = manifest.get('id') or folder
    return {
        'id': pid,
        'version': str(manifest.get('version') or ''),
        'nameZh': manifest.get('name_zh') or manifest.get('name') or pid,
        'nameEn': manifest.get('name_en') or '',
        'license': manifest.get('license') or '',
        'source': manifest.get('source') or manifest.get('credit') or '',
        'author': manifest.get('author') or '',
        'url': manifest.get('url') or '',
        'note': manifest.get('note') or '',
        'placeholder': bool(manifest.get('placeholder')),
        'model': manifest.get('model') or '',
        'gated': bool(manifest.get('gated')),
        'ageGate': manifest.get('ageGate') or '',
        'badge': manifest.get('badge') or (manifest.get('ageGate') if manifest.get('gated') else '') or '',
        'switch': manifest.get('switch') or manifest.get('badge') or manifest.get('ageGate') or '',
        'gateTitle': manifest.get('gateTitle') or '',
        'gateBody': manifest.get('gateBody') or '',
        'confirm': manifest.get('confirm') or '',
        'cancel': manifest.get('cancel') or '',
        'noticeZh': manifest.get('noticeZh') or '',
        'noticeEn': manifest.get('noticeEn') or '',
        'upstream': manifest.get('upstream') if isinstance(manifest.get('upstream'), dict) else {},
    }


def validate(root=ROOT):
    """返回 (packs, errors)。packs 为规范化后的包，含条目和绝对路径。"""
    errors = []
    if not os.path.isdir(root):
        return [], ['找不到表情包目录 %s' % root]
    folders = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith('.'))
    raw = []
    for folder in folders:
        base = os.path.join(root, folder)
        mp = os.path.join(base, 'manifest.json')
        if not os.path.isfile(mp):
            errors.append('%s: 缺少 manifest.json' % folder)
            continue
        try:
            manifest = json.load(open(mp, encoding='utf-8'))
        except Exception as e:
            errors.append('%s: manifest 无法解析（%s）' % (folder, e))
            continue
        if not isinstance(manifest, dict) or not isinstance(manifest.get('items'), list):
            errors.append('%s: manifest.items 必须是数组' % folder)
            continue
        raw.append((folder, base, manifest))
    table = angle_table([m for _, _, m in raw])
    hide = hide_set(table, [m for _, _, m in raw])
    seen = {}
    ga = set()
    packs = []
    for folder, base, manifest in raw:
        meta = _pack_meta(manifest, folder)
        pid = meta['id']
        if not ID_RE.match(str(pid)):
            errors.append('%s: 包 id 非法 %r' % (folder, pid))
        if pid != folder:
            errors.append('%s: 目录名必须与 manifest.id 一致（现在是 %s）' % (folder, pid))
        if not meta['version']:
            errors.append('%s: 缺少 version' % pid)
        if not isinstance(meta['license'], str) or not meta['license'].strip():
            errors.append('%s: 缺少 license' % pid)
        elif meta['model'] == 'ICT-FaceKit' and ('ICT-FaceKit' not in meta['license'] or 'MIT' not in meta['license']):
            errors.append('%s: model 为 ICT-FaceKit 时，license 须注明 ICT-FaceKit 与 MIT' % pid)
        up = meta['upstream']
        commit = str(up.get('commit') or '').strip()
        variant = str(up.get('variant') or '').strip()
        repo = str(up.get('repo') or '').strip()
        if not commit:
            errors.append('%s: upstream.commit 不能为空，须锁定 ICT-FaceKit 的完整提交号' % pid)
        if meta['model'] == 'ICT-FaceKit':
            if variant != 'Light':
                errors.append('%s: 只使用 ICT-FaceKit Light，upstream.variant 必须是 "Light"' % pid)
            if not repo:
                errors.append('%s: upstream.repo 不能为空' % pid)
            if commit and not __import__('re').fullmatch(r'[0-9a-fA-F]{40}', commit):
                errors.append('%s: upstream.commit 必须是 40 位完整 SHA' % pid)
        notice = os.path.join(base, THIRD_PARTY)
        if not os.path.isfile(notice):
            errors.append('%s: 缺少 %s' % (pid, THIRD_PARTY))
        else:
            text = open(notice, encoding='utf-8').read()
            if 'MIT License' not in text or 'Copyright' not in text:
                errors.append('%s: %s 须包含 MIT 许可全文和版权声明' % (pid, THIRD_PARTY))
            if commit and commit not in text:
                errors.append('%s: %s 须写明锁定的 commit' % (pid, THIRD_PARTY))
            if repo and repo not in text:
                errors.append('%s: %s 须写明上游仓库 URL' % (pid, THIRD_PARTY))
        meta['upstream'] = {'repo': repo, 'variant': variant, 'commit': commit}
        meta['thirdParty'] = 'licenses/packs/%s/%s' % (pid, THIRD_PARTY)
        if meta['gated']:
            if not meta['ageGate']:
                errors.append('%s: gated 包必须声明 ageGate' % pid)
            if not meta['gateTitle'] or not meta['gateBody']:
                errors.append('%s: gated 包必须声明 gateTitle 与 gateBody，供年龄确认弹窗使用' % pid)
        views = pack_views(manifest)
        roles = {v.get('role') for v in views}
        for need in ('color', 'depth', 'line'):
            if need not in roles:
                errors.append('%s: 视图缺少 role=%s' % (pid, need))
        items = []
        for it in manifest['items']:
            if not isinstance(it, dict):
                errors.append('%s: 条目不是对象' % pid)
                continue
            miss = [k for k in REQ if it.get(k) in (None, '', [])]
            if miss:
                errors.append('%s/%s: 缺少必填字段 %s' % (pid, it.get('id'), ', '.join(miss)))
                continue
            iid = str(it['id'])
            if not ID_RE.match(iid):
                errors.append('%s: id 非法 %r' % (pid, iid))
            if iid in seen:
                errors.append('id 重复：%s（%s 与 %s）' % (iid, seen[iid], pid))
            seen[iid] = pid
            if it.get('pack') != pid:
                errors.append('%s/%s: pack 必须等于包 id %s' % (pid, iid, pid))
            if not isinstance(it.get('tags'), list) or not all(isinstance(t, str) and t for t in it['tags']):
                errors.append('%s/%s: tags 必须是非空字符串数组' % (pid, iid))
                tags = []
            else:
                tags = [t for t in it['tags'] if t not in hide]
            ang = str(it['angle'])
            if not ang:
                errors.append('%s/%s: angle 为空' % (pid, iid))
            if iid == ang:
                errors.append('%s/%s: id 不能和 angle 相同，否则会盖住角度列表页' % (pid, iid))
            info = table.get(ang) or {}
            group = str(it.get('group') or iid)
            gkey = (pid, group, ang)
            if gkey in ga:
                errors.append('%s: 同一表情同一角度重复 %s/%s' % (pid, group, ang))
            ga.add(gkey)
            if not _num(it.get('w')) or not _num(it.get('h')) or int(it['w']) < 1 or int(it['h']) < 1:
                errors.append('%s/%s: w/h 必须是正数' % (pid, iid))
                continue
            w, h = int(it['w']), int(it['h'])
            weights = it.get('blendshape_weights', None)
            if weights is not None:
                if not isinstance(weights, dict):
                    errors.append('%s/%s: blendshape_weights 必须是对象' % (pid, iid))
                else:
                    for k, v in weights.items():
                        if not isinstance(k, str) or not KEY_RE.match(k):
                            errors.append('%s/%s: blendshape 名称非法 %r' % (pid, iid, k))
                        elif not _num(v) or v < 0 or v > 1:
                            errors.append('%s/%s: blendshape %s 的权重必须在 0 到 1' % (pid, iid, k))
            files = {}
            for view in views:
                field = view.get('field') or view['id']
                rel = it.get(field)
                if not rel:
                    errors.append('%s/%s: 缺少视图 %s' % (pid, iid, field))
                    continue
                full = _inside(base, str(rel))
                if not full:
                    errors.append('%s/%s: 路径越界 %s' % (pid, iid, rel))
                    continue
                if not os.path.isfile(full):
                    errors.append('%s/%s: 文件不存在 %s' % (pid, iid, rel))
                    continue
                errors.extend(check_image(full, view.get('role') or 'image', w, h))
                files[view['id']] = full
            items.append({
                'id': iid, 'group': group, 'zh': it['name_zh'], 'en': it.get('name_en') or iid,
                'tags': tags, 'angle': ang,
                'angleZh': info.get('zh') or ang, 'angleEn': info.get('en') or ang,
                'poseAngle': info.get('pose') or info.get('zh') or ang,
                'zhPrompt': it.get('prompt_zh') or '', 'enPrompt': it.get('prompt_en') or '',
                'w': w, 'h': h, 'pack': pid, 'weights': weights, 'files': files,
                'gate': meta['ageGate'] if meta['gated'] else '',
                'badge': meta['badge'] if meta['gated'] else '',
            })
        meta['views'] = views
        meta['items'] = items
        meta['root'] = base
        packs.append(meta)
    return packs, errors


def load_packs(root=ROOT):
    packs, errors = validate(root)
    if errors:
        abort(errors)
    return packs


def _webp(src, dest, size):
    im = Image.open(src).convert('RGB')
    im.thumbnail(size)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    im.save(dest, 'WEBP', quality=80, method=4)


def _public_pack(p):
    return {k: p[k] for k in (
        'id', 'version', 'nameZh', 'nameEn', 'license', 'source', 'author', 'url', 'note',
        'placeholder', 'model', 'gated', 'ageGate', 'badge', 'switch', 'gateTitle', 'gateBody',
        'confirm', 'cancel', 'noticeZh', 'noticeEn', 'upstream', 'thirdParty') if k in p}


def _item_out(it, views):
    o = {
        'id': it['id'], 'group': it['group'], 'zh': it['zh'], 'en': it['en'], 'tags': it['tags'],
        'angle': it['angle'], 'angleZh': it['angleZh'], 'angleEn': it['angleEn'], 'poseAngle': it['poseAngle'],
        'zhPrompt': it['zhPrompt'], 'enPrompt': it['enPrompt'], 'w': it['w'], 'h': it['h'], 'pack': it['pack'],
        'views': views,
    }
    if it.get('gate'):
        o['gate'] = it['gate']
        o['badge'] = it.get('badge') or it['gate']
    if it.get('weights'):
        o['weights'] = it['weights']
    return o


def _paths(it, view_id):
    stem = '%s_%s' % (it['id'], view_id)
    if it.get('gate'):
        return (
            'e/gated/%s/t/%s.webp' % (it['pack'], stem),
            'e/gated/%s/i/%s.webp' % (it['pack'], stem),
            'o/e/gated/%s/%s/%s.png' % (it['pack'], view_id, it['id']),
        )
    return (
        'e/t/%s.webp' % stem,
        'e/i/%s.webp' % stem,
        'o/e/%s/%s/%s.png' % (it['pack'], view_id, it['id']),
    )


def build(dist, root=ROOT):
    packs, errors = validate(root)
    if errors:
        abort(errors)
    expect = set()
    public_items, gated_items = [], []
    view_ids = []
    for p in packs:
        for v in p['views']:
            if v['id'] not in view_ids:
                view_ids.append(v['id'])
        for it in p['items']:
            rels = {}
            for vid, src in it['files'].items():
                t, i, o = _paths(it, vid)
                for rel, size in ((t, (360, 480)), (i, (1200, 1600))):
                    dest = os.path.join(dist, rel)
                    _webp(src, dest, size)
                    expect.add(rel)
                odst = os.path.join(dist, o)
                os.makedirs(os.path.dirname(odst), exist_ok=True)
                shutil.copy2(src, odst)
                expect.add(o)
                rels[vid] = {'t': t, 'i': i, 'o': o}
            out = _item_out(it, rels)
            (gated_items if it.get('gate') else public_items).append(out)
    # 清掉已删除条目留下的缩略图和原图，避免 dist 里混进不该预缓存的旧文件
    for prefix in ('e/t', 'e/i', 'e/gated', 'o/e'):
        base = os.path.join(dist, prefix)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for f in files:
                rel = os.path.relpath(os.path.join(dirpath, f), dist).replace(os.sep, '/')
                if rel not in expect:
                    os.remove(os.path.join(dirpath, f))
    used = []
    seen_a = set()
    for it in public_items + gated_items:
        if it['angle'] not in seen_a:
            seen_a.add(it['angle'])
            used.append(it['angle'])
    order = {a: i for i, a in enumerate(ANGLE_ORDER)}
    used.sort(key=lambda a: (order.get(a, 1000), a))
    table = angle_table([json.load(open(os.path.join(p['root'], 'manifest.json'), encoding='utf-8')) for p in packs])
    angles = [{'id': a, 'zh': (table.get(a) or {}).get('zh') or a, 'en': (table.get(a) or {}).get('en') or a,
               'pose': (table.get(a) or {}).get('pose') or (table.get(a) or {}).get('zh') or a} for a in used]
    views = []
    seen_v = set()
    for p in packs:
        for v in p['views']:
            if v['id'] not in seen_v:
                seen_v.add(v['id'])
                views.append({'id': v['id'], 'zh': v.get('zh') or v['id'], 'en': v.get('en') or v['id']})
    pub_packs = [_public_pack(p) for p in packs]
    doc = {
        'version': 1,
        'packs': pub_packs,
        'angles': angles,
        'views': views,
        'fallback': FALLBACK,
        'templates': TEMPLATES,
        'items': public_items,
        'gatedIds': [it['id'] for it in gated_items],
        'gatedIndex': {it['id']: it['gate'] for it in gated_items},
        'gated': '__EXPR_GATED__' if gated_items else '',
    }
    gated = {'items': gated_items} if gated_items else None
    lic = os.path.join('LICENSES', 'ICT-FaceKit.txt')
    if os.path.isfile(lic):
        os.makedirs(os.path.join(dist, 'licenses'), exist_ok=True)
        shutil.copy2(lic, os.path.join(dist, 'licenses', 'ICT-FaceKit.txt'))
    for p in packs:
        src = os.path.join(p['root'], THIRD_PARTY)
        if os.path.isfile(src):
            dest = os.path.join(dist, 'licenses', 'packs', p['id'], THIRD_PARTY)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
    print('expr', len(public_items), 'public', len(gated_items), 'gated', len(packs), 'packs')
    return {'public': doc, 'gated': gated, 'public_items': public_items, 'gated_items': gated_items, 'packs': pub_packs}


def write_seo(g):
    """由 seo.py 在写 sitemap 之前调用。gated 条目不生成详情页、不进站点地图。"""
    doc = g.get('EXPR') or {}
    items = doc.get('public_items') or []
    if not items:
        return
    packs = {p['id']: p for p in doc.get('packs') or []}
    angles = {a['id']: a for a in doc['public'].get('angles') or []}
    E, W, add, SM = g['E'], g['W'], g['add'], g['SM']
    SITE, TODAY = g['SITE'], g['TODAY']
    shell = g['shell']
    SM['expression'] = []

    def thumb(it):
        return it['views']['source']['t']

    def big(it):
        return it['views']['source']['i']

    def card(lang, it):
        t = it['en'] if lang == 'en' else it['zh']
        href = ('/en' if lang == 'en' else '') + '/expression/' + it['id'] + '/'
        return '<li><a href="%s"><img src="/%s" alt="%s" width="300" height="400" loading="lazy" decoding="async"><span>%s</span></a></li>' % (
            href, thumb(it), E(t), E(t + ' · ' + (it['angleEn'] if lang == 'en' else it['angleZh'])))

    def page(lang, it, rel):
        zh = lang == 'zh'
        p = packs.get(it['pack'], {})
        t = it['zh'] if zh else it['en']
        ang = it['angleZh'] if zh else it['angleEn']
        ttl = '%s · %s表情参考 | 衣姿 PoseWear' % (it['zh'], it['angleZh']) if zh else '%s – %s expression reference | PoseWear' % (it['en'], it['angleEn'])
        desc = (it['zhPrompt'] or '%s，%s。' % (it['zh'], it['angleZh'])) if zh else (it['enPrompt'] or '%s, %s.' % (it['en'], it['angleEn']))
        path = '/expression/%s/' % it['id']
        P = '/en' if not zh else ''
        cr = [('首页' if zh else 'Home', P + '/'), ('表情' if zh else 'Expressions', P + '/expression/'),
              (it['angleZh'] if zh else it['angleEn'], P + '/expression/' + it['angle'] + '/'), (t, None)]
        lic = p.get('license') or ''
        note = p.get('note') or ''
        boxes = ('<div class="box"><small>中文描述</small><p>%s</p></div><div class="box"><small>英文提示词 · PROMPT</small><p>%s</p></div>' % (E(it['zhPrompt'] or it['zh']), E(it['enPrompt'] or it['en'])) if zh else
                 '<div class="box"><small>PROMPT</small><p>%s</p></div><div class="box" lang="zh-CN"><small>中文</small><p>%s</p></div>' % (E(it['enPrompt'] or it['en']), E(it['zhPrompt'] or it['zh'])))
        src = '<p class="mu">%s</p>' % E(p.get('source') or '')
        license_p = '<p class="mu">%s <a href="/licenses/ICT-FaceKit.txt">ICT-FaceKit MIT</a>（Copyright (c) 2020 USC Institute for Creative Technologies）。%s</p>' % (E(lic), E(note))
        rl = ''.join(card(lang, r) for r in rel)
        body = '<main><div class="im"><img src="/%s" alt="%s" width="%d" height="%d"></div><div>%s<h1>%s</h1><div class="mu">%s · %s</div>%s%s<a class="go" href="/#expression/%s">%s</a>%s</div><section class="rel"><h2>%s</h2><ul>%s</ul></section></main>' % (
            big(it), E(t), it['w'], it['h'], g['crumbs_html'](cr), E(t), E(ang), E(it['pack']),
            boxes, src, it['id'], '在衣姿中打开' if zh else 'Open in PoseWear', license_p,
            '其他表情' if zh else 'More expressions', rl)
        ld = [{"@type": "ImageObject", "name": t, "description": desc, "contentUrl": SITE + '/' + big(it), "url": g['url'](lang, path)}]
        return shell(lang, path, ttl, desc[:160], body, ld, en=True, og=big(it), ogt='article')

    by_ang = {}
    for it in items:
        by_ang.setdefault(it['angle'], []).append(it)
    for it in items:
        rel = [x for x in items if x['group'] == it['group'] and x['id'] != it['id']]
        rel += [x for x in by_ang.get(it['angle'], []) if x['id'] != it['id'] and x not in rel]
        for lang in ('zh', 'en'):
            W(('/en' if lang == 'en' else '') + '/expression/%s/' % it['id'], page(lang, it, rel[:8]))
        add('expression', '/expression/%s/' % it['id'], TODAY, [(SITE + '/' + big(it), it['zh'])], en=True)
    for ang, group in by_ang.items():
        info = angles.get(ang) or {'zh': ang, 'en': ang}
        for lang in ('zh', 'en'):
            zh = lang == 'zh'
            P = '/en' if not zh else ''
            path = '/expression/%s/' % ang
            title = '%s表情参考 | 衣姿 PoseWear' % info['zh'] if zh else '%s expression references | PoseWear' % info['en']
            desc = ('%s角度的表情参考，共 %d 个。同一表情的其他角度在别的分组里。' % (info['zh'], len(group))) if zh else ('%s expression references: %d.' % (info['en'], len(group)))
            body = '<div class="wrap"><h1>%s</h1><p class="lead">%s</p><ul class="cg">%s</ul></div>' % (
                E(info['zh'] if zh else info['en']), E(desc), ''.join(card(lang, it) for it in group))
            W(P + path, shell(lang, path, title, desc, body, [], en=True))
        add('expression', '/expression/%s/' % ang, TODAY, en=True)
    for lang in ('zh', 'en'):
        zh = lang == 'zh'
        P = '/en' if not zh else ''
        desc = '按角度浏览表情参考。每个角度一组，同一表情的正面和斜侧不会排在一起。' if zh else 'Expression references grouped by camera angle.'
        blocks = []
        for ang, group in by_ang.items():
            info = angles.get(ang) or {'zh': ang, 'en': ang}
            blocks.append('<h2>%s</h2><ul class="cg">%s</ul>' % (E(info['zh'] if zh else info['en']), ''.join(card(lang, it) for it in group[:12])))
        notes = ''.join('<p class="mu">%s · %s</p>' % (E(p.get('nameZh') or p['id']), E(p.get('license') or '')) for p in packs.values() if not p.get('gated'))
        notes += ''.join('<p class="mu">%s（%s，默认不公开列出）· %s</p>' % (E(p.get('nameZh') or p['id']), E(p.get('badge') or p.get('ageGate') or 'gated'), E(p.get('license') or '')) for p in packs.values() if p.get('gated'))
        body = '<div class="wrap"><h1>%s</h1><p class="lead">%s</p>%s%s</div>' % ('表情参考' if zh else 'Expressions', E(desc), ''.join(blocks), notes)
        W(P + '/expression/', shell(lang, '/expression/', '表情参考 | 衣姿 PoseWear' if zh else 'Expressions | PoseWear', desc, body, [], en=True))
    add('expression', '/expression/', TODAY, en=True)
