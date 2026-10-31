#!/usr/bin/env python3
"""把表情素材导入 expressions/packs/<包 id>/。

用法：
  python3 scripts/import-expressions.py <目录或 zip>
  python3 scripts/import-expressions.py /path/to/posewear-expressions-v2

接受三种布局（zip 或目录都可以）：

1. 一个包：目录里有 manifest.json，条目的 pack 与 manifest.id 相同。
2. 多个包：子目录各自有 manifest.json，例如 general/ 与 adult/。
3. 一份合并清单：根上一个 manifest.json，条目用 pack 区分。
   可用 packConfig.<id> 写这个包的 gated、ageGate、license 等。
   导入时会拆成 expressions/packs/<id>/。

README.md、contact_sheet.png 以及清单没有引用的文件不会复制，也不会进站点。
图片按原样复制，不改像素。校验失败则不会替换已有的包。
"""
import argparse, json, os, shutil, sys, tempfile, zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import expr

DROP = {'README.md', 'README.txt', 'contact_sheet.png', '.DS_Store'}


def _extract(path):
    if not path.lower().endswith('.zip'):
        return path, None
    tmp = tempfile.mkdtemp(prefix='expr-zip-')
    with zipfile.ZipFile(path) as z:
        z.extractall(tmp)
    names = [n for n in os.listdir(tmp) if not n.startswith('.')]
    if len(names) == 1 and os.path.isdir(os.path.join(tmp, names[0])):
        return os.path.join(tmp, names[0]), tmp
    return tmp, tmp


def _rels(manifest, it):
    out = []
    for view in expr.pack_views(manifest):
        field = view.get('field') or view['id']
        if it.get(field):
            out.append(os.path.normpath(str(it[field])))
    return out


def _write_pack(dest, manifest, src_root):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    keep = []
    for it in manifest.get('items') or []:
        for rel in _rels(manifest, it):
            full = os.path.join(src_root, rel)
            if os.path.isfile(full):
                target = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(full, target)
                keep.append(rel)
    about = os.path.join(src_root, 'about.json')
    if os.path.isfile(about):
        shutil.copy2(about, os.path.join(dest, 'about.json'))
    src_lic = os.path.join(src_root, expr.THIRD_PARTY)
    dest_lic = os.path.join(dest, expr.THIRD_PARTY)
    if os.path.isfile(src_lic):
        shutil.copy2(src_lic, dest_lic)
    else:
        up = manifest.get('upstream') if isinstance(manifest.get('upstream'), dict) else {}
        open(dest_lic, 'w', encoding='utf-8').write(expr.third_party_text(
            up.get('repo') or expr.FACEKIT_REPO, up.get('variant') or expr.FACEKIT_VARIANT, up.get('commit') or ''))
    with open(os.path.join(dest, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return keep


def _sources(path):
    """返回 [(manifest, 文件所在目录)]。"""
    manifest_path = os.path.join(path, 'manifest.json')
    if os.path.isfile(manifest_path):
        manifest = json.load(open(manifest_path, encoding='utf-8'))
        items = manifest.get('items') or []
        ids = []
        for it in items:
            if isinstance(it, dict) and it.get('pack') and it['pack'] not in ids:
                ids.append(it['pack'])
        if len(ids) <= 1:
            if not manifest.get('id'):
                manifest['id'] = ids[0] if ids else os.path.basename(os.path.abspath(path))
            return [(manifest, path)]
        cfg = manifest.get('packConfig') or {}
        out = []
        for pid in ids:
            sub = {k: v for k, v in manifest.items() if k not in ('items', 'packConfig', 'id')}
            if isinstance(cfg.get(pid), dict):
                sub.update(cfg[pid])
            sub['id'] = pid
            sub['items'] = [it for it in items if it.get('pack') == pid]
            out.append((sub, path))
        return out
    found = []
    for name in sorted(os.listdir(path)):
        sub = os.path.join(path, name)
        mp = os.path.join(sub, 'manifest.json')
        if os.path.isdir(sub) and os.path.isfile(mp):
            manifest = json.load(open(mp, encoding='utf-8'))
            if not manifest.get('id'):
                manifest['id'] = name
            found.append((manifest, sub))
    if not found:
        raise SystemExit('没有找到 manifest.json：%s' % path)
    return found


def import_path(src, dest_root=expr.ROOT):
    path, tmp = _extract(os.path.abspath(src))
    try:
        sources = _sources(path)
        staging = tempfile.mkdtemp(prefix='expr-stage-')
        ids = []
        try:
            for manifest, root in sources:
                pid = manifest['id']
                _write_pack(os.path.join(staging, pid), manifest, root)
                ids.append(pid)
            _, errors = expr.validate(staging)
            if errors:
                expr.abort(errors)
            os.makedirs(dest_root, exist_ok=True)
            for pid in ids:
                final = os.path.join(dest_root, pid)
                if os.path.isdir(final):
                    shutil.rmtree(final)
                shutil.copytree(os.path.join(staging, pid), final)
        finally:
            shutil.rmtree(staging, ignore_errors=True)
        return ids
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description='导入表情素材包')
    p.add_argument('src', help='包目录、多包父目录，或 zip')
    p.add_argument('--dest', default=expr.ROOT, help='导入到此目录（默认 expressions/packs）')
    a = p.parse_args()
    ids = import_path(a.src, a.dest)
    print('已导入', ', '.join(ids), '→', a.dest)


if __name__ == '__main__':
    main()
