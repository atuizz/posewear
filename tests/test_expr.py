#!/usr/bin/env python3
"""表情包校验、年龄门槛拆分、导入。不依赖姿势/服装素材。"""
import json, os, shutil, tempfile, unittest
from PIL import Image
import expr
import importlib.util
spec = importlib.util.spec_from_file_location('import_expressions', os.path.join(os.path.dirname(__file__), '..', 'scripts', 'import-expressions.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def tiny(path, mode, size=(8, 8), color=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if mode == 'L':
        im = Image.new('L', size, 0 if color is None else color)
    elif mode == 'RGB':
        im = Image.new('RGB', size, (0, 0, 0) if color is None else color)
    else:
        im = Image.new(mode, size, color or 0)
    im.save(path)


def pack(root, pid, items, **meta):
    base = os.path.join(root, pid)
    os.makedirs(base, exist_ok=True)
    manifest = {'version': '0.2.0', 'id': pid, 'license': expr.FACEKIT_LICENSE, 'model': 'ICT-FaceKit',
                'upstream': dict(expr.FACEKIT_UPSTREAM), 'items': items}
    manifest.update(meta)
    up = manifest['upstream']
    open(os.path.join(base, expr.THIRD_PARTY), 'w', encoding='utf-8').write(
        expr.third_party_text(up.get('repo') or '', up.get('variant') or '', up.get('commit') or ''))
    for it in items:
        it.setdefault('pack', pid)
        it.setdefault('w', 8)
        it.setdefault('h', 8)
        for field, mode in (('source', 'RGB'), ('depth', 'L'), ('landmarks', 'RGB')):
            rel = it[field]
            tiny(os.path.join(base, rel), mode, (it['w'], it['h']), (255, 255, 255) if mode == 'RGB' else 200)
    json.dump(manifest, open(os.path.join(base, 'manifest.json'), 'w'), ensure_ascii=False)
    return base


def item(iid, ang='front', pack='general', **kw):
    d = {'id': iid, 'name_zh': '测试', 'tags': ['正面情绪', '正面'], 'angle': ang, 'pack': pack,
         'source': 'source/%s.png' % iid, 'depth': 'depth/%s.png' % iid, 'landmarks': 'landmarks/%s.png' % iid}
    d.update(kw)
    return d


class ExprTests(unittest.TestCase):
    def test_repo_packs(self):
        packs = expr.load_packs()
        ids = {p['id']: p for p in packs}
        self.assertIn('general', ids)
        self.assertIn('adult', ids)
        self.assertFalse(ids['general']['gated'])
        self.assertTrue(ids['adult']['gated'])
        self.assertEqual(ids['adult']['ageGate'], '18+')
        self.assertEqual(ids['general']['upstream']['variant'], 'Light')
        self.assertEqual(ids['general']['upstream']['commit'], expr.FACEKIT_COMMIT)
        self.assertTrue(os.path.isfile('expressions/packs/general/THIRD_PARTY_LICENSES.txt'))
        self.assertTrue(os.path.isfile('expressions/packs/adult/THIRD_PARTY_LICENSES.txt'))
        text = open('expressions/packs/general/THIRD_PARTY_LICENSES.txt', encoding='utf-8').read()
        self.assertIn(expr.FACEKIT_COMMIT, text)
        self.assertIn(expr.FACEKIT_REPO, text)
        self.assertIn('MIT License', text)
        for p in packs:
            self.assertIn('ICT-FaceKit', p['license'])
            self.assertIn('MIT', p['license'])
            for it in p['items']:
                self.assertNotIn('正面', it['tags'])
                self.assertNotIn('3/4 侧', it['tags'])
                self.assertTrue(it['weights'])

    def test_build_splits_gated(self):
        dist = tempfile.mkdtemp()
        try:
            doc = expr.build(dist)
            pub = doc['public']
            self.assertTrue(all(not it.get('gate') for it in pub['items']))
            self.assertTrue(all('e/gated/' not in json.dumps(it) for it in pub['items']))
            self.assertIn('smirk_front', pub['gatedIndex'])
            self.assertTrue(doc['gated']['items'])
            self.assertTrue(all(it.get('gate') == '18+' for it in doc['gated']['items']))
            self.assertTrue(os.path.isfile(os.path.join(dist, 'licenses', 'packs', 'general', 'THIRD_PARTY_LICENSES.txt')))
            self.assertTrue(os.path.isfile(os.path.join(dist, 'licenses', 'ICT-FaceKit.txt')))
            self.assertFalse(os.path.exists(os.path.join(dist, 'e', 't', 'smirk_front_source.webp')))
            self.assertTrue(os.path.isfile(os.path.join(dist, 'e', 'gated', 'adult', 't', 'smirk_front_source.webp')))
        finally:
            shutil.rmtree(dist)

    def test_new_angle_needs_no_code_change(self):
        root = tempfile.mkdtemp()
        try:
            pack(root, 'general', [item('bird_view', ang='bird', blendshape_weights={'jawOpen': 0.2})],
                 angles={'bird': {'zh': '鸟瞰', 'en': 'bird view', 'pose': '俯拍'}})
            packs, errors = expr.validate(root)
            self.assertEqual(errors, [], errors)
            self.assertEqual(packs[0]['items'][0]['angleZh'], '鸟瞰')
            self.assertEqual(packs[0]['items'][0]['poseAngle'], '俯拍')
        finally:
            shutil.rmtree(root)

    def test_failures(self):
        root = tempfile.mkdtemp()
        try:
            pack(root, 'general', [item('a_front'), item('a_front')])
            _, errors = expr.validate(root)
            self.assertTrue(any('重复' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            pack(root, 'general', [item('a_front', blendshape_weights={'mouthSmile_L': 1.2})])
            _, errors = expr.validate(root)
            self.assertTrue(any('0 到 1' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            pack(root, 'general', [item('a_front', pack='other')])
            _, errors = expr.validate(root)
            self.assertTrue(any('pack 必须' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            pack(root, 'general', [item('a_front')])
            # 深度图改成 RGB
            Image.new('RGB', (8, 8), (1, 2, 3)).save(os.path.join(root, 'general', 'depth', 'a_front.png'))
            _, errors = expr.validate(root)
            self.assertTrue(any('深度图' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            it = item('a_front')
            del it['pack']
            base = pack(root, 'general', [it])
            m = json.load(open(os.path.join(base, 'manifest.json')))
            del m['items'][0]['pack']
            json.dump(m, open(os.path.join(base, 'manifest.json'), 'w'))
            _, errors = expr.validate(root)
            self.assertTrue(any('缺少必填字段' in e and 'pack' in e for e in errors))
            os.remove(os.path.join(root, 'general', expr.THIRD_PARTY))
            _, errors = expr.validate(root)
            self.assertTrue(any('THIRD_PARTY_LICENSES' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            pack(root, 'general', [item('a_front')], upstream={'repo': expr.FACEKIT_REPO, 'variant': 'Light', 'commit': ''})
            _, errors = expr.validate(root)
            self.assertTrue(any('commit' in e for e in errors))
            shutil.rmtree(os.path.join(root, 'general'))
            pack(root, 'general', [item('a_front')], upstream={'repo': expr.FACEKIT_REPO, 'variant': 'Full', 'commit': expr.FACEKIT_COMMIT})
            _, errors = expr.validate(root)
            self.assertTrue(any('Light' in e for e in errors))
        finally:
            shutil.rmtree(root)

    def test_import_skips_readme_and_contact_sheet(self):
        src = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()
        try:
            pack(src, 'general', [item('a_front', blendshape_weights={'jawOpen': 0})])
            open(os.path.join(src, 'general', 'README.md'), 'w').write('nope')
            open(os.path.join(src, 'general', 'contact_sheet.png'), 'wb').write(b'not a png')
            ids = mod.import_path(os.path.join(src, 'general'), dest)
            self.assertEqual(ids, ['general'])
            self.assertFalse(os.path.exists(os.path.join(dest, 'general', 'README.md')))
            self.assertFalse(os.path.exists(os.path.join(dest, 'general', 'contact_sheet.png')))
            self.assertTrue(os.path.isfile(os.path.join(dest, 'general', 'source', 'a_front.png')))
            self.assertTrue(os.path.isfile(os.path.join(dest, 'general', 'THIRD_PARTY_LICENSES.txt')))
            expr.load_packs(dest)
        finally:
            shutil.rmtree(src)
            shutil.rmtree(dest)

    def test_sw_does_not_precache_gated(self):
        sw = open('src/sw.js', encoding='utf-8').read()
        self.assertIn('expressions-gated', sw)
        self.assertIn('gated', sw)


if __name__ == '__main__':
    unittest.main()
