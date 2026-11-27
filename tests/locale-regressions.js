const assert = require('node:assert/strict');
const {serveSite} = require('./fixtures/site');
const { chromium } = require('playwright');

const sample = {
  id:'test', ti:'收藏', zh:'收藏', en:'The original English prompt',
  cat:'春季', t:'icon-192.png', m:'icon-192.png', i:'icon-192.png', o:'icon-192.png',
};
const pose = {...sample, line:'全身', no:'1', angles:[{...sample, zh:'正面', en:'front view'}]};

const serve = serveSite({'poses.json':[pose], 'costumes.json':[sample]});

// A Locator click may scroll clipped controls into view. Test the touch target at its original coordinates.
async function tapVisible(page, selector) {
  const button = page.locator(selector);
  await button.waitFor();
  const rect = await button.boundingBox();
  const {width, height} = page.viewportSize();
  assert.ok(rect && rect.x >= 0 && rect.y >= 0 && rect.x+rect.width <= width+1 && rect.y+rect.height <= height+1,
    selector+' outside viewport: '+JSON.stringify(rect));
  const x = rect.x+rect.width/2, y = rect.y+rect.height/2;
  assert.ok(await button.evaluate((el, [x,y]) => el.contains(document.elementFromPoint(x,y)), [x,y]), selector+' is covered');
  await page.touchscreen.tap(x,y);
}

async function chooseLocale(page, value) {
  await page.locator('#languageMenu summary').tap();
  await page.locator('#uiLocale').selectOption(value);
  await page.locator('#languageMenu summary').tap();
}

async function run() {
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH});
  try {
    for (const [width,height] of [[320,568],[390,844]]) {
      const ctx = await browser.newContext({viewport:{width,height}, isMobile:true, hasTouch:true,
        reducedMotion:'reduce', serviceWorkers:'block'});
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.route('**/*',serve);
      await page.goto('http://posewear.test/#costume');
      const description = page.locator('.card .sub').first();
      await description.waitFor();
      assert.equal(await description.textContent(),sample.zh);
      assert.equal(await page.locator('#libraryMenu section').count(),4);
      assert.equal(await page.locator('#libraryMenu button[data-tab]').count(),12);
      await tapVisible(page,'#libraryMenu summary');
      await tapVisible(page,'#libraryMenu [data-tab=furn]');
      assert.equal(await page.evaluate(() => location.hash),'#furn');
      assert.equal(await page.locator('#libraryLabel').textContent(),'家具库');
      await tapVisible(page,'#libraryMenu summary');
      await tapVisible(page,'#libraryMenu [data-tab=costume]');
      await description.waitFor();
      await tapVisible(page,'#q');
      assert.ok((await page.locator('.top .search').boundingBox()).width >= width - 24);
      await tapVisible(page,'#qDone');
      // Switch directly between the library and notifications.
      await page.locator('#libraryMenu summary').tap();
      await tapVisible(page,'#noticeMenu summary');
      assert.ok(await page.locator('#releaseNotice').isVisible());
      assert.ok(await page.locator('#libraryMenu [data-tab=pose]').isHidden());
      await tapVisible(page,'#noticeMenu summary');
      assert.ok(await page.locator('#releaseNotice').isHidden());
      assert.equal(await page.locator('footer #credits').count(),1);
      assert.ok(await page.locator('.credit-list').isHidden());
      const nav = page.locator('.tabs [data-tab=studio]');
      for (const [locale,lang,label] of [['en','en','Studio'],['ja','ja','スタジオ'],['vi','vi','Studio'],['tr','tr','Stüdyo'],['zh','zh-CN','工作台']]) {
        await chooseLocale(page,locale);
        assert.equal(await nav.innerText(),label);
        assert.equal(await description.textContent(),sample.zh);
        await page.reload();
        await description.waitFor();
        assert.equal(await page.locator('html').getAttribute('lang'),lang);
        assert.equal(await nav.innerText(),label);
        assert.equal(await description.textContent(),sample.zh);
      }
      await page.locator('#languageMenu summary').tap();
      await page.locator('[data-lang=en]').tap();
      await page.locator('#languageMenu summary').tap();
      await chooseLocale(page,'ja');
      assert.equal(await description.textContent(),sample.en);
      assert.equal(await page.locator('.card h3').first().textContent(),sample.ti);
      assert.equal(await page.locator('.card h3').first().getAttribute('title'),sample.ti);

      await chooseLocale(page,'en');
      await page.locator('#trayFab').tap();
      await page.locator('#tgPrompt').fill('保存 / 自分のプロンプト');
      await page.locator('#tgCfg').tap();
      await tapVisible(page,'#cfSave');
      await page.locator('#cfg').waitFor({state:'hidden'});
      await page.locator('#tray [data-add=pose]').tap();
      await page.locator('#pkG button').first().waitFor();
      await tapVisible(page,'#pkDone');
      await page.locator('#pk').waitFor({state:'hidden'});
      assert.equal(await page.locator('#tgPrompt').inputValue(),'保存 / 自分のプロンプト');
      await page.locator('#trayMin').tap();
      await nav.tap();
      await page.locator('details.adv > summary').tap();
      await page.locator('#wbExtra').fill('衣装 / 保持原文');
      await chooseLocale(page,'ja');
      assert.equal(await page.locator('#wbExtra').inputValue(),'衣装 / 保持原文');
      assert.deepEqual(errors, []);
      await ctx.close();
      console.log('PASS '+width+'px touch targets, locale persistence and independent prompts');
    }
  } finally { await browser.close(); }
}
run().catch(error => {console.error(error);process.exitCode=1;});
