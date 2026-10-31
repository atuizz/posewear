# 深度姿势：按素材包生成前端数据。图片地址只在这里解析一次。
# hotlink 包只写 URL，不下载、不复制图片。local 包才把自有文件复制进 dist。
import json, os, re
from urllib.parse import urlsplit

ROOT = os.environ.get('POSEWEAR_DEPTH', 'depth/packs')
IMG_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'}
# 与 build.py 的 LINE / CAT / ANG 一致，保证和姿势库用同一套译名。
LINE = {'全身1人・セクシー系': ('全身·性感', 'full body, solo, sexy'), '全身1人・標準系': ('全身·标准', 'full body, solo'), '上半身1人': ('上半身', 'upper body, solo'), '2人絡み': ('双人互动', 'two people, couple')}
CAT = {'寝そべり': '躺卧', 'セクシー・露骨寄り系': '性感·大胆', '立ち': '站姿', '座り': '坐姿', 'かわいい系': '可爱', '胸寄せ・谷間強調系': '挤胸·乳沟', '膝立ち・四つん這い': '跪立·趴姿', '特殊': '特殊', '正常位': '正面位', '膝立ち': '跪立', '横座り・女の子座り': '侧坐·鸭子坐', '後背位': '后入位', '背面座位': '背面坐位', 'しゃがみ': '蹲姿', '前かがみ': '前倾', '顔寄せ系': '贴脸', '騎乗位': '骑乘位', '立位': '立位', '立位密着': '立位贴身', 'のけぞり・反り': '后仰', 'ひねり': '扭身', '側位': '侧位', '座位': '坐位', '対面座位': '对面坐位', '座位密着': '坐位贴身', '密着': '贴身'}
ANG = {'正面': ('正面', 'front view'), '上から': ('俯拍', 'high angle, from above'), '下から': ('仰拍', 'low angle, from below'), '横': ('侧面', 'side view'), '斜め': ('斜侧', 'three-quarter view')}
ANG_ORDER = ['正面', '斜め', '横', '上から', '下から']
FIELDS = {'id': 'id', 'line': '系統', 'no': 'ポーズ番号', 'cat': '分類', 'name': 'ポーズ名', 'angle': 'アングル', 'thumb': 'サムネ', 'full': '原寸'}
REFERRERS = {'no-referrer', 'origin', 'strict-origin', 'strict-origin-when-cross-origin', ''}


def abort(errors):
    raise SystemExit('深度姿势素材校验失败（%d 项）：\n%s' % (len(errors), '\n'.join('- ' + e for e in errors)))


def _tr():
    out = {}
    for line in open('tr_pose.txt', encoding='utf-8'):
        p = line.rstrip('\n').split('|')
        if len(p) >= 3 and p[0]:
            out[p[0]] = (p[1], p[2])
    return out


def _rel(path, label):
    if not isinstance(path, str) or not path or path.startswith(('/', '\\')) or '://' in path or '\\' in path:
        return None, '%s：路径必须是站内相对路径' % label
    norm = os.path.normpath(path)
    if norm.startswith('..') or os.path.isabs(norm):
        return None, '%s：路径越界' % label
    return norm.replace('\\', '/'), None


def _origin(url):
    u = urlsplit(url)
    if u.scheme != 'https' or not u.netloc:
        return None
    return 'https://' + u.netloc


def _inside(root, rel):
    full = os.path.normpath(os.path.join(root, rel))
    if os.path.commonpath([os.path.abspath(root), os.path.abspath(full)]) != os.path.abspath(root):
        return None
    return full


def catalog(root=ROOT):
    """返回 {payload, origins, copies}。copies 只有 local 包才有，热链包为空。"""
    errors = []
    if not os.path.isdir(root):
        abort(['找不到深度姿势包目录 %s' % root])
    tr = _tr()
    folders = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith('.'))
    if not folders:
        abort(['%s 下没有素材包' % root])
    items, origins, copies = [], [], []
    seen = set()
    for folder in folders:
        base = os.path.join(root, folder)
        mp = os.path.join(base, 'manifest.json')
        if not os.path.isfile(mp):
            errors.append('%s：缺少 manifest.json' % folder)
            continue
        try:
            manifest = json.load(open(mp, encoding='utf-8'))
        except Exception as e:
            errors.append('%s：manifest 无法解析（%s）' % (folder, e))
            continue
        pid = manifest.get('id') or folder
        source = manifest.get('source') or 'hotlink'
        if source not in ('hotlink', 'local'):
            errors.append('%s：source 只能是 hotlink 或 local' % pid)
            continue
        fields = dict(FIELDS)
        fields.update(manifest.get('fields') or {})
        site = (manifest.get('site') or '').strip()
        origin = _origin(manifest.get('base') or site)
        if source == 'hotlink':
            if not origin:
                errors.append('%s：热链 base 必须是 https 地址' % pid)
                continue
            if origin not in origins:
                origins.append(origin)
            for dirpath, _, files in os.walk(base):
                for name in files:
                    if os.path.splitext(name)[1].lower() in IMG_EXT:
                        errors.append('%s：热链包不能包含图片 %s' % (pid, os.path.relpath(os.path.join(dirpath, name), base)))
        if not site:
            errors.append('%s：缺少 site（原站地址）' % pid)
        ref = manifest.get('referrerPolicy', 'no-referrer')
        if ref not in REFERRERS:
            errors.append('%s：不认识的 referrerPolicy %s' % (pid, ref))
            ref = 'no-referrer'
        ip = os.path.join(base, manifest.get('items') or 'items.json')
        try:
            doc = json.load(open(ip, encoding='utf-8'))
        except Exception as e:
            errors.append('%s：条目文件无法解析（%s）' % (pid, e))
            continue
        raw = doc.get('items') if isinstance(doc, dict) else doc
        if not isinstance(raw, list) or not raw:
            errors.append('%s：条目为空' % pid)
            continue
        lines = []
        if isinstance(doc, dict) and isinstance((doc.get('meta') or {}).get('lines'), list):
            lines = doc['meta']['lines']
        gated = set(manifest.get('gatedLines') or [])
        unknown = sorted(gated - set(lines) - set(LINE))
        if unknown:
            errors.append('%s：gatedLines 不在数据里 %s' % (pid, '、'.join(unknown)))
        groups = {}
        order = []
        for n, row in enumerate(raw, 1):
            if not isinstance(row, dict):
                errors.append('%s：第 %d 条不是对象' % (pid, n))
                continue
            try:
                iid, line, no, cat, name, ang = (row[fields[k]] for k in ('id', 'line', 'no', 'cat', 'name', 'angle'))
                thumb, full = row[fields['thumb']], row[fields['full']]
            except KeyError as e:
                errors.append('%s：第 %d 条缺少 %s' % (pid, n, e))
                continue
            gid = str(iid).rsplit('_', 1)[0]
            if not re.match(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,80}$', gid):
                errors.append('%s：编号不合法 %s' % (pid, iid))
                continue
            thumb, err = _rel(thumb, '%s %s 缩略图' % (pid, iid))
            full, err2 = _rel(full, '%s %s 原图' % (pid, iid))
            if err or err2:
                errors.append(err or err2)
                continue
            if line not in LINE:
                errors.append('%s：未知系列 %s' % (pid, line))
                continue
            if cat not in CAT:
                errors.append('%s：未知分类 %s' % (pid, cat))
                continue
            if ang not in ANG:
                errors.append('%s：未知角度 %s' % (pid, ang))
                continue
            if name not in tr:
                errors.append('%s：没有中文译名 %s' % (pid, name))
                continue
            if source == 'hotlink':
                turl, iurl = origin + '/' + thumb, origin + '/' + full
            else:
                for rel in (thumb, full):
                    src = _inside(base, rel)
                    if not src or not os.path.isfile(src):
                        errors.append('%s：找不到本地图片 %s' % (pid, rel))
                        continue
                    copies.append((src, 'd/%s/%s' % (pid, rel)))
                turl, iurl = '/d/%s/%s' % (pid, thumb), '/d/%s/%s' % (pid, full)
            g = groups.get(gid)
            if g is None:
                zh, en = tr[name]
                lz, le = LINE[line]
                g = {'id': gid, 'no': str(no), 'line': lz, 'lineEn': le, 'lineJa': line, 'cat': CAT[cat], 'catJa': cat, 'ja': name, 'zh': zh, 'en': en, 'pack': pid, 'site': site, 'credit': manifest.get('credit') or '', 'unofficial': manifest.get('unofficial') or '非官方汉化', 'angles': []}
                if source == 'hotlink':
                    g['ext'] = 1
                    g['ref'] = ref or 'no-referrer'
                if line in gated:
                    g['a'] = 1
                groups[gid] = g
                order.append(gid)
            else:
                if g['ja'] != name or g['lineJa'] != line or g['catJa'] != cat or g['no'] != str(no):
                    errors.append('%s：同一姿势的名称或分类不一致 %s' % (pid, gid))
            if any(a['ja'] == ang for a in g['angles']):
                errors.append('%s：角度重复 %s %s' % (pid, gid, ang))
                continue
            g['angles'].append({'zh': ANG[ang][0], 'en': ANG[ang][1], 'ja': ang, 't': turl, 'i': iurl})
        got_lines = {g['lineJa'] for g in groups.values()}
        miss = sorted(x for x in gated if x not in got_lines)
        if miss:
            errors.append('%s：gatedLines 没有对应条目 %s' % (pid, '、'.join(miss)))
        line_index = {x: i for i, x in enumerate(lines)}

        def sort_key(gid, line_index=line_index, groups=groups):
            g = groups[gid]
            m = re.search(r'(\d+)', g['no'])
            return (g.get('a', 0), line_index.get(g['lineJa'], 99), int(m.group(1)) if m else 0, gid)

        for gid in sorted(order, key=sort_key):
            g = groups[gid]
            if gid in seen:
                errors.append('姿势编号在多个包里重复 %s' % gid)
                continue
            seen.add(gid)
            g['angles'].sort(key=lambda a: ANG_ORDER.index(a['ja']) if a['ja'] in ANG_ORDER else 99)
            if not g['angles']:
                errors.append('%s：没有角度' % gid)
                continue
            items.append(g)
    if errors:
        abort(errors)
    payload = {'pack': _public_pack(folders, root), 'items': items}
    # 单包时把该包的署名放到顶层，前端横幅直接用。多包时保留第一包，条目各自带 site。
    return {'payload': payload, 'origins': origins, 'copies': copies}


def _public_pack(folders, root):
    """横幅用的署名。多包时列出全部，当前只有一个热链包。"""
    packs = []
    for folder in folders:
        m = json.load(open(os.path.join(root, folder, 'manifest.json'), encoding='utf-8'))
        packs.append({k: m.get(k, '') for k in ('id', 'site', 'siteName', 'author', 'authorUrl', 'credit', 'unofficial', 'note', 'referrerPolicy', 'source')})
    one = dict(packs[0])
    one['packs'] = packs
    return one


if __name__ == '__main__':
    c = catalog()
    items = c['payload']['items']
    from collections import Counter
    lines = Counter(i['lineJa'] for i in items)
    gated = [i for i in items if i.get('a')]
    imgs = sum(len(i['angles']) for i in items)
    print('poses', len(items), 'images', imgs, 'series', dict(lines))
    print('gated', Counter(i['lineJa'] for i in gated), 'gated_images', sum(len(i['angles']) for i in gated))
    print('origins', c['origins'], 'copies', len(c['copies']))
    assert not c['copies']
    assert c['origins'] == ['https://ai-pose-depth-gallery.pages.dev']
    assert set(i['lineJa'] for i in gated) == {'2人絡み'}
    assert imgs == 1439 and len(items) == 288
    assert all(i['angles'][0]['t'].startswith('https://ai-pose-depth-gallery.pages.dev/thumbs/') for i in items)
    assert all(i['angles'][0]['i'].startswith('https://ai-pose-depth-gallery.pages.dev/img/') for i in items)
    print('ok')
