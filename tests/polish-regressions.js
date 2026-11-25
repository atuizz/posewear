const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const root = path.join(__dirname, '..', 'src');
const mkImg = (name) => ({ t: name, m: name, i: name, o: name });
const angles = [
  { zh: '正面', en: 'front view', ...mkImg('icon-192.png') },
  { zh: '侧面', en: 'side view', ...mkImg('icon-512.png') },
];

const data = {
  'poses.json': [
    { id: '001', ti: '站姿一', zh: '站姿一', en: 'standing one', no: '1', cat: '站姿', line: '全身', lineEn: 'full body', angles },
    { id: '002', ti: '坐姿二', zh: '坐姿二', en: 'sitting two', no: '2', cat: '坐姿', line: '全身', lineEn: 'full body', angles },
  ],
  'depths.json': [
    { id: '001', pack: 'gia-depth', ti: '站姿一', zh: '站姿一', en: 'standing one', no: '1', cat: '站姿', line: '全身', lineEn: 'full body', angles },
  ],
  'costumes.json': [
    { id: 'c1', ti: '红色连衣裙', zh: '红色连衣裙', en: 'red dress', kw: 'red dress', no: '1', cat: '连衣裙', ...mkImg('swatch-demo.svg') },
    { id: 'c2', ti: '蓝色制服', zh: '蓝色制服', en: 'blue jacket', kw: 'blue jacket', no: '2', cat: '制服', ...mkImg('icon-512.png') },
  ],
  'portraits.json': [
    { id: 'p1', ti: '室内人像一', zh: '室内人像一', en: 'indoor portrait one', no: '1', cat: '室内', sec: '默认', st: '自然', ...mkImg('icon-192.png') },
    { id: 'p2', ti: '户外人像二', zh: '户外人像二', en: 'outdoor portrait two', no: '2', cat: '户外', sec: '默认', st: '自然', ...mkImg('icon-512.png') },
  ],
  'props.json': [
    { id: 'pr1', ti: '木吉他', zh: '木吉他', en: 'wooden guitar', no: '1', cat: '乐器', angles },
  ],
};

async function run() {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
  try {
    const ctx = await browser.newContext({
      viewport: { width: 1366, height: 860 },
      reducedMotion: 'reduce',
      serviceWorkers: 'block',
      locale: 'zh-CN',
    });
    const page = await ctx.newPage();
    const errors = [];
    const requested = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.hostname !== 'posewear.test') return route.abort();
      const file = url.pathname.slice(1) || 'index.html';
      requested.push(file);
      if (file === 'swatch-demo.svg') {
        const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="90" height="120"><rect width="90" height="40" fill="#C8233C"/><rect y="40" width="90" height="40" fill="#2B5B84"/><rect y="80" width="90" height="40" fill="#2E8B57"/></svg>';
        return route.fulfill({ contentType: 'image/svg+xml', body: svg });
      }
      if (file.endsWith('.json')) return route.fulfill({ json: data[file] || [] });
      const source = path.join(root, file);
      if (fs.existsSync(source)) return route.fulfill({ path: source });
      return route.fulfill({ status: 404, body: '' });
    });

    // 1. Gallery: color swatch dots, angle switch in-place, filter drawer hide on single-row tabs, recent .rgrp headers
    await page.goto('http://posewear.test/#costume');
    await page.locator('#grid .card').first().waitFor();
    await page.locator('#fBtn').click();
    assert.ok(await page.locator('#filters .chip .csw').count() >= 2, 'Color chips should render swatch dots');

    // Lightbox on costume: grayscale value check (B) + auto extracted color palette (#lbPal)
    await page.locator('#grid .card').first().locator('.phk').click();
    await page.locator('#lbTools [data-lt=gray]').waitFor({ state: 'visible' });
    await page.locator('#lbPal .pal-sw').first().waitFor({ state: 'visible' });
    const swCount = await page.locator('#lbPal .pal-sw').count();
    assert.ok(swCount >= 3, 'Color costume lightbox should extract >= 3 dominant swatches');
    const firstHex = await page.locator('#lbPal .pal-sw').first().getAttribute('data-hex');
    assert.match(firstHex || '', /^#[0-9A-F]{6}$/);
    await page.locator('#lbPal .pal-sw').first().click();
    assert.ok(await page.locator('#lbPal .pal-sw').first().evaluate(el => el.classList.contains('copied')));
    await page.keyboard.press('b');
    assert.ok(await page.locator('#lbStage').evaluate(el => el.classList.contains('gray')), 'B shortcut should toggle grayscale value check');
    await page.keyboard.press('Escape');

    // Favorite first costume so we can test picker fav filter later
    await page.locator('#grid .card').first().locator('[data-a=fav]').click();

    // Switch to prop (single filter row) -> #fBtn hidden
    await page.locator('#libraryMenu summary').click();
    await page.locator('.tabs [data-tab=prop]').click();
    await page.locator('#grid .card').first().waitFor();
    assert.ok(await page.locator('#fBtn').isHidden(), '#fBtn should hide when tab has <= 1 filter row');

    // Switch to pose -> test in-place angle switch (same card DOM element preserved)
    await page.locator('#libraryMenu summary').click();
    await page.locator('.tabs [data-tab=pose]').click();
    await page.locator('#grid .card').first().waitFor();
    await page.evaluate(() => { window.__cardRef = document.querySelector('#grid .card'); });
    await page.locator('#grid .card').first().locator('[data-a=ang][data-i="1"]').click();
    const sameNodeAndImg = await page.evaluate(() => {
      const c = document.querySelector('#grid .card');
      return c === window.__cardRef && c.querySelector('img').getAttribute('src').includes('icon-512.png');
    });
    assert.ok(sameNodeAndImg, 'Switching angle should update card image in place without rebuilding card DOM');

    // Gesture Drawing Studio (#sketchBtn -> #sketch): pause, mirror, grid, advance to recap, close
    await page.locator('#sketchBtn').waitFor({ state: 'visible' });
    await page.locator('#sketchBtn').click();
    await page.locator('#sketch').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#skStep').textContent(), '1 / 2');
    await page.keyboard.press('Space');
    assert.equal(await page.locator('#skPause').textContent(), '继续');
    await page.keyboard.press('h');
    assert.ok(await page.locator('#skFrame').evaluate(el => el.classList.contains('flipped')));
    await page.keyboard.press('g');
    assert.equal(await page.locator('#skGrid').getAttribute('data-mode'), 'thirds');
    await page.keyboard.press('ArrowRight');
    assert.equal(await page.locator('#skStep').textContent(), '2 / 2');
    await page.keyboard.press('ArrowRight'); // 2 poses in fixture -> completes session with recap sheet
    await page.locator('#skDone').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#skRecap button').count(), 2, 'Recap sheet should display all practiced references');
    await page.keyboard.press('Escape');
    assert.ok(await page.locator('#sketch').isHidden());

    // Global Command Palette (Ctrl+K): fuzzy search across ZH / EN / JA
    await page.keyboard.press('Control+k');
    await page.locator('#cmdPal').waitFor({ state: 'visible' });
    await page.fill('#cmdQ', '服装');
    assert.ok(await page.locator('#cmdList .cmd-it').count() >= 1);
    await page.fill('#cmdQ', 'クロッキー');
    assert.ok(await page.locator('#cmdList .cmd-it').count() >= 1);
    await page.keyboard.press('Escape');
    assert.ok(await page.locator('#cmdPal').isHidden());

    // 2. Lightbox Artist Inspection Studio (zoom, flip, grid, paired split compare, reset on close)
    const beforeCmpReqs = requested.length;
    await page.locator('#grid .card').first().locator('.phk').click();
    await page.locator('#lbTools').waitFor({ state: 'visible' });
    await page.locator('#lbTools [data-lt=cmp]').waitFor({ state: 'visible' });
    assert.ok(await page.locator('#lbTools [data-lt=gray]').isHidden(), 'Grayscale tool should stay hidden on monochrome pose sketches');
    assert.ok(await page.locator('#lbPairCmp').isHidden(), 'Split compare should start off');
    assert.equal(await page.locator('#lbPairImg').getAttribute('src'), null, 'Depth counterpart should stay lazy before activating compare');

    await page.keyboard.press('z');
    assert.ok(await page.locator('#lbStage').evaluate(el => el.classList.contains('zoomed') && el.style.getPropertyValue('--lb-z') === '2'));
    await page.keyboard.press('h');
    assert.ok(await page.locator('#lbStage').evaluate(el => el.classList.contains('flipped')));
    await page.keyboard.press('g');
    assert.equal(await page.locator('#lbGrid').getAttribute('data-mode'), 'thirds');
    await page.keyboard.press('g');
    assert.equal(await page.locator('#lbGrid').getAttribute('data-mode'), 'cross');
    await page.keyboard.press('g');
    assert.equal(await page.locator('#lbGrid').getAttribute('data-mode'), '');

    await page.keyboard.press('v');
    assert.ok(await page.locator('#lbPairCmp').isVisible(), 'V shortcut should reveal split compare curtain');
    assert.ok((await page.locator('#lbPairImg').getAttribute('src') || '').includes('icon-512.png'), 'Split compare should load matching angle depth image');
    await page.locator('#lbPairRange').evaluate(el => { el.value = '30'; el.dispatchEvent(new Event('input', { bubbles: true })); });
    assert.equal(await page.locator('#lbStage').evaluate(el => el.style.getPropertyValue('--x')), '30%');

    // Header copy button pulse
    await page.locator('#lbSide .pbox-cp').first().click();
    assert.ok(await page.locator('#lbSide .pbox-cp').first().evaluate(el => el.classList.contains('copied')));

    await page.keyboard.press('Escape');
    assert.ok(await page.locator('#lb').isHidden());
    assert.equal(await page.locator('#lbPairImg').getAttribute('src'), null, 'Closing lightbox should clear compare image src');
    assert.ok(!(await page.locator('#lbStage').evaluate(el => el.classList.contains('zoomed') || el.classList.contains('flipped'))));

    // Recent tab should render .rgrp heading and clean it up on card removal
    await page.locator('#personalMenu summary').click();
    await page.locator('.tabs [data-tab=recent]').click();
    await page.locator('#grid .rgrp').first().waitFor({ state: 'visible' });
    assert.equal(await page.locator('#grid .rgrp').count(), 1);
    assert.equal(await page.locator('#grid .grp').count(), 0, 'Recent headers must use .rgrp, not .grp');
    await page.locator('#grid .card .unrec').first().click();
    await page.locator('#grid .card .unrec').first().click();
    await page.waitForFunction(() => document.querySelectorAll('#grid .rgrp').length === 0);

    // 3. Floating dock prompt reset
    await page.locator('#libraryMenu summary').click();
    await page.locator('.tabs [data-tab=pose]').click();
    await page.locator('#grid .card').first().locator('[data-a=sel]').click();
    await page.locator('#trayFab').click();
    const autoPrompt = await page.locator('#tgPrompt').inputValue();
    assert.ok(autoPrompt.length > 0);
    assert.ok(await page.locator('#tgResetPrompt').isHidden());
    await page.locator('#tgPrompt').fill('自定义测试提示词');
    assert.ok(await page.locator('#tgResetPrompt').isVisible());
    await page.locator('#tgResetPrompt').click();
    assert.equal(await page.locator('#tgPrompt').inputValue(), autoPrompt);
    assert.ok(await page.locator('#tgResetPrompt').isHidden());
    await page.locator('#trayMin').click();

    // 4. Studio: Custom http:// URL validation + official https:// enforcement, shuffle, board badges, board PNG export, clear-all + undo, board/result toggle, picker filters
    await page.locator('.tabs [data-tab=studio]').click();
    await page.waitForFunction(() => window.WB && APP.st.tab === 'studio');
    assert.ok(await page.locator('#wbExportBoard').isHidden(), 'Export PNG button should stay hidden on sample board');

    await page.locator('#wbCfg').click();
    await page.locator('[name=prov][value=custom]').check();
    await page.fill('#cfBase', 'http://127.0.0.1:8188/v1');
    await page.fill('#cfKey', 'local-relay-key');
    await page.click('#cfSave');
    await page.waitForSelector('#cfg', { state: 'hidden' });
    assert.equal(await page.evaluate(() => WB._cfg.base), 'http://127.0.0.1:8188/v1');

    // Official gemini still requires HTTPS
    await page.locator('#wbCfg').click();
    await page.locator('[name=prov][value=gemini]').check();
    await page.fill('#cfBase', 'http://example.test');
    await page.click('#cfSave');
    assert.match(await page.locator('#cfMsg').textContent(), /HTTPS/);
    await page.click('#cfgX');

    // Shuffle + apply example -> numbered .board-idx badges + export PNG -> Clear all + Undo
    await page.locator('#wbShuffle').click();
    await page.locator('#wbExample').click();
    await page.waitForFunction(() => document.querySelectorAll('#wbBoardCards .board-idx').length >= 2);
    assert.equal(await page.locator('#wbBoardCards .board-idx').first().textContent(), '1');
    assert.ok(await page.locator('#wbExportBoard').isVisible(), 'Export PNG button should appear once board has user references');
    const pngInfo = await page.evaluate(async () => {
      const b = await WB.exportBoardPng({ download: false });
      const head = [...new Uint8Array(await b.slice(0, 4).arrayBuffer())];
      return { type: b.type, size: b.size, head };
    });
    assert.equal(pngInfo.type, 'image/png');
    assert.ok(pngInfo.size > 4000, 'Exported board PNG should be non-trivial');
    assert.deepEqual(pngInfo.head, [137, 80, 78, 71], 'Exported board blob should start with PNG magic bytes');

    assert.ok(await page.locator('#wbClearAll').isVisible());
    await page.locator('#wbClearAll').click();
    await page.waitForFunction(() => WB._W.garments.length === 0 && WB._W.poses.length === 0);
    assert.ok(await page.locator('#wbClearAll').isHidden());
    assert.ok(await page.locator('#wbExportBoard').isHidden());
    await page.locator('#toast button').click(); // Undo clear all
    await page.waitForFunction(() => WB._W.garments.length >= 1 && WB._W.poses.length >= 1);

    // Picker category & favorites filter
    await page.locator('.garment-step [data-pick=costume]').click();
    await page.locator('#pkBar').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#pkG button').count(), 2);
    await page.locator('#pkCats [data-pk-cat="制服"]').click();
    assert.equal(await page.locator('#pkG button').count(), 1);
    await page.locator('#pkCats [data-pk-cat=""]').click();
    assert.equal(await page.locator('#pkG button').count(), 2);
    await page.locator('#pkFavOnly').click();
    assert.equal(await page.locator('#pkG button').count(), 1, 'Favorites filter should show only favorited costume');
    await page.click('#pkX');

    // Board / Result view toggle when result exists
    await page.evaluate(async () => {
      const pic = await (await fetch('icon-192.png')).blob();
      const rec = { t: Date.now(), mode: 'tryon', prov: 'custom', model: 'flux-dev', prompt: 'red silk dress in studio', after: pic, before: pic, inputs: { garments: [{ k: 'c:c1' }], poses: [{ k: 'p:001', ai: 0 }] } };
      const rec2 = { t: Date.now() + 1, mode: 'gen', prov: 'openai', model: 'gpt-image-1', prompt: 'cyberpunk portrait rain', after: pic, before: null, inputs: { poses: [{ k: 'p:001', ai: 0 }] } };
      await WB.db.put(rec);
      await WB.db.put(rec2);
      await WB.db.refreshHist();
    });
    await page.locator('#wbHist button').first().click();
    assert.ok(await page.locator('#wbCanvasSwitch').isVisible());
    assert.ok(await page.locator('#wbCmp').isVisible());
    assert.ok(await page.locator('#wbPh0').isHidden());
    assert.ok(await page.locator('#wbExportBoard').isHidden(), 'Export PNG button should hide while viewing generated result');
    await page.locator('#wbCanvasSwitch [data-cv=board]').click();
    assert.ok(await page.locator('#wbPh0').isVisible());
    assert.ok(await page.locator('#wbCmp').isHidden());
    assert.ok(await page.locator('#wbExportBoard').isVisible());

    // 5. History mode filter, search, empty-match reset, and lightbox reference strip + hidden artist tools
    await page.locator('#personalMenu summary').click();
    await page.locator('.tabs [data-tab=history]').click();
    await page.waitForFunction(() => document.querySelectorAll('#histGrid .hist-card').length === 2);

    await page.locator('#histFilter [data-hf=tryon]').click();
    assert.equal(await page.locator('#histGrid .hist-card').count(), 1);
    assert.match(await page.locator('#histCount').textContent(), /1 \/ 2 条记录/);

    await page.locator('#histFilter [data-hf=all]').click();
    await page.fill('#histQ', 'cyberpunk');
    await page.waitForFunction(() => document.querySelectorAll('#histGrid .hist-card').length === 1);

    await page.fill('#histQ', 'no-such-prompt-xyz');
    await page.waitForSelector('#histResetFilter');
    await page.click('#histResetFilter');
    await page.waitForFunction(() => document.querySelectorAll('#histGrid .hist-card').length === 2);

    // Open History Lightbox: verify #lbTools hidden and #hlbRefs renders used reference thumbnail
    await page.locator('#histGrid .hist-card .hopen').first().click();
    await page.locator('#hlbRefs .hlb-ref').first().waitFor({ state: 'visible' });
    assert.ok(await page.locator('#lbTools').isHidden(), 'Gallery inspection toolbar must stay hidden in history lightbox');
    await page.keyboard.press('Escape');

    // 6. Trilingual UI parity check (en / ja) on new controls
    await page.locator('#languageMenu summary').click();
    await page.selectOption('#uiLocale', 'en');
    await page.waitForFunction(() => document.documentElement.lang === 'en');
    assert.equal(await page.locator('#histFilter [data-hf=all]').textContent(), 'All');
    await page.keyboard.press('Control+k');
    await page.locator('#cmdPal').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#cmdQ').getAttribute('placeholder'), 'Jump to a library, search, or run a command…');
    await page.keyboard.press('Escape');
    await page.selectOption('#uiLocale', 'ja');
    await page.waitForFunction(() => document.documentElement.lang === 'ja');
    assert.equal(await page.locator('#histFilter [data-hf=all]').textContent(), 'すべて');
    assert.equal(await page.locator('#histQ').getAttribute('placeholder'), 'プロンプトやモデルを検索…');
    assert.equal(await page.locator('#sketchBtn span').textContent(), 'クロッキー');

    assert.deepEqual(errors, []);
    assert.ok(beforeCmpReqs > 0);
    console.log('polish-regressions PASS');
  } finally {
    await browser.close();
  }
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
