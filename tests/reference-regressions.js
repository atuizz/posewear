const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

const source = path.resolve(__dirname,'../src');
const photo = path.join(__dirname,'fixtures/mk1.png');
const site = 'https://posewear.pages.dev/';
const outfit = {id:'coat',ti:'大衣',zh:'灰色大衣',en:'grey coat',cat:'外套',m:'c/m/coat.webp',i:'c/i/coat.webp',t:'c/t/coat.webp'};
const pose = {id:'turn',zh:'转身',en:'turning',line:'全身',lineEn:'full body',angles:[
  {zh:'正面',en:'front view',t:'p/t/front.webp',i:'p/i/front.webp',o:'p/o/front.webp'},
  {zh:'侧面',en:'side view',t:'p/t/side.webp',i:'p/i/side.webp',o:'p/o/side.webp'}
]};
const guitar={...outfit,id:'T001',ti:'木吉他',zh:'木吉他',en:'wooden guitar',cat:'乐器',
  angles:pose.angles.map(a=>({...a,t:a.t.replace('p/','t/'),i:a.i.replace('p/','t/')}))};
const room={...outfit,id:'room',ti:'客厅',zh:'客厅',en:'living room',cat:'室内',m:'s/m/room.webp'};
const catalogs = {'poses.json':[pose],'costumes.json':[outfit],'props.json':[guitar],'scenes.json':[room]};

async function run() {
  const browser=await chromium.launch({executablePath:process.env.CHROME_PATH});
  try {
    const context=await browser.newContext({permissions:['clipboard-read','clipboard-write'],serviceWorkers:'block',reducedMotion:'reduce',locale:'zh-CN'});
    await context.addInitScript(()=>{localStorage.lang=JSON.stringify('en')});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.route('**/*',route=>{
      const url=new URL(route.request().url());
      if(url.hostname!=='posewear.test')return route.abort();
      const name=url.pathname.slice(1)||'index.html';
      if(name.endsWith('.json'))return route.fulfill({json:catalogs[name]||[]});
      if(name.endsWith('.webp'))return route.fulfill({path:photo,contentType:'image/png'});
      const local=path.join(source,name);
      return fs.existsSync(local)?route.fulfill({path:local}):route.fulfill({status:404});
    });
    await page.goto('https://posewear.test/#pose');
    const card=page.locator('#grid .card').first();
    const clipboard=()=>page.evaluate(async()=>(await navigator.clipboard.readText()).replace(/\r\n/g,'\n'));
    async function copied(button) {
      await page.evaluate(()=>navigator.clipboard.writeText(''));
      await button.click();
      await page.waitForFunction(async()=>!!(await navigator.clipboard.readText()));
      return clipboard();
    }
    const side=site+'p/i/side.webp';
    await card.locator('[data-a=ang][data-i="1"]').click();
    assert.match(await copied(card.locator('[data-a=copy]')),/turning, full body, side view/);
    assert.ok((await clipboard()).includes(side));
    await card.locator('.phk').click();
    await page.keyboard.press('c');
    await page.waitForFunction(async()=> (await navigator.clipboard.readText()).includes('侧面'));
    assert.ok((await clipboard()).includes(side));
    await page.keyboard.press('Escape');
    await card.locator('[data-a=sel]').click();
    await page.locator('#libraryMenu summary').click();
    await page.locator('#libraryMenu [data-tab=costume]').click();
    await card.locator('[data-a=sel]').click();
    await page.locator('#trayFab').click();
    await page.locator('#trayComboBox summary').click();
    const mixed=await copied(page.locator('#trayCopyEn'));
    assert.deepEqual(mixed.match(/https:\/\/\S+/g),[side,site+outfit.m]);
    await page.locator('#tgPrompt').fill('Keep this exact wording.');
    await page.locator('#tgN').selectOption('3');
    await page.locator('#tgAR').selectOption('16:9');
    await page.reload();
    await page.locator('#trayFab').click();
    assert.equal(await page.locator('#tgN').inputValue(),'3');
    assert.equal(await page.locator('#tgAR').inputValue(),'16:9');
    const edited=await copied(page.locator('#tgCopyDraft'));
    assert.ok(edited.startsWith('Keep this exact wording.\n\n'));
    assert.deepEqual(edited.match(/https:\/\/\S+/g),[site+outfit.m,side]);
    await page.locator('#trayMin').click();
    await page.locator('#batchBtn').click();
    await card.locator('.phk').click();
    assert.ok((await copied(page.locator('[data-b=cp]'))).includes(site+outfit.m));
    await page.locator('[data-b=x]').click();
    await card.locator('[data-a=try]').click();
    await page.locator('#wbFile').setInputFiles(photo);
    await page.waitForFunction(()=>WB._W.persons.length===1);
    await page.locator('.adv summary').click();
    await page.locator('#wbPrompt').fill('keep my edit');
    const studio=await copied(page.locator('#wbCopyP'));
    assert.ok(studio.startsWith('keep my edit\n\n'));
    assert.match(studio,/(Image|图) 1 · (Attach|请另附)/);
    assert.match(studio,/(Image|图) 2 · /);
    assert.ok(studio.includes(site+outfit.m));
    assert.doesNotMatch(studio,/blob:|data:image|mk1\.png/);
    await page.locator('#wbExtra').fill('Side lighting');
    await page.locator('#wbN').selectOption('2');
    await page.locator('#wbAR').selectOption('3:4');
    await page.reload();
    await page.locator('#wbG .pick').waitFor();
    assert.equal(await page.locator('#wbPrompt').inputValue(),'keep my edit');
    assert.equal(await page.locator('#wbN').inputValue(),'2');
    assert.equal(await page.locator('#wbAR').inputValue(),'3:4');
    assert.equal(await page.locator('#wbExtra').inputValue(),'Side lighting');
    await page.locator('#wbReP').click();
    await page.reload();
    await page.locator('#wbG .pick').waitFor();
    assert.match(await page.locator('#wbPrompt').inputValue(),/Side lighting/);
    assert.doesNotMatch(await page.locator('#wbPrompt').inputValue(),/keep my edit/);
    await page.evaluate(async()=>{
      const after=await (await fetch('icon-192.png')).blob();
      await WB.db.put({t:1234,after,mode:'gen',prov:'openai',prompt:'saved draft',orig:'original draft',
        inputs:{persons:[],garments:[],poses:[{k:'p:turn',ai:1}],exprs:[],lang:'en'}});
    });
    await page.goto('https://posewear.test/#history');
    await page.reload();
    await page.locator('.hist-card .hopen').click();
    const saved=await copied(page.locator('[data-hlb=cp]'));
    assert.ok(saved.startsWith('saved draft\n\n'));
    assert.ok(saved.includes(side));
    await page.locator('#lbSide .raw summary').click();
    const original=await copied(page.locator('[data-hlb=cporig]'));
    assert.ok(original.startsWith('original draft\n\n'));
    assert.ok(original.includes(side));
    await page.keyboard.press('Escape');
    await page.locator('#languageMenu summary').click();
    await page.locator('#copyRefs').uncheck();
    await page.reload();
    await page.goto('https://posewear.test/#costume');
    assert.equal(await copied(card.locator('[data-a=copy]')),'grey coat');

    // Earlier versions could save a prop in the garment slot.
    await page.evaluate(()=>{
      localStorage.wbSel=JSON.stringify({g:['t:T001'],p:[],e:[]});
      localStorage.copyRefs='true';localStorage.sel='[]';
      history.replaceState(null,'','#studio');
    });
    await page.reload();
    const other=page.locator('#wbOther');
    await page.locator('#wbOtherCount').filter({hasText:'1'}).waitFor();
    assert.equal(await other.getAttribute('open'),null);
    assert.deepEqual(await page.locator('.primary-materials .sh b').allTextContents(),['人物','服装','姿势']);
    assert.equal(await page.locator('#wbG .pick').count(),0);
    assert.ok(await page.locator('#wbPrompt').isVisible());
    assert.ok(await page.locator('#wbGo').isEnabled());
    await other.locator('summary').click();
    await other.locator('[data-type=prop] select').selectOption('1');
    assert.ok((await copied(page.locator('#wbCopyP'))).includes(site+'t/i/side.webp'));
    await other.locator('[data-pick=scene]').click();
    await page.locator('#pkG [data-k="s:room"]').click();
    await page.locator('#pkDone').click();
    assert.deepEqual(await page.locator('#wbBoardCards .board-card').evaluateAll(els=>els.map(el=>el.dataset.type)),['prop','scene']);
    await page.reload();
    await other.locator('summary').click();
    await other.locator('.pick[data-type=scene] [data-rm]').click();
    assert.ok((await copied(page.locator('#wbCopyP'))).includes(site+'t/i/side.webp'));
    assert.doesNotMatch(await clipboard(),/s\/m\/room\.webp/);

    await page.locator('#trayFab').click();
    assert.deepEqual(await page.locator('#tgAddRow > [data-add]').evaluateAll(els=>els.map(el=>el.dataset.add)),['portrait','costume','pose']);
    await page.locator('#tgMore summary').click();
    await page.locator('#tgMore [data-add=scene]').click();
    await page.locator('#pkG [data-k="s:room"]').click();
    await page.locator('#pkDone').click();
    await page.locator('#tgStudio').click();
    await page.locator('#wbBoardCards [data-pk-key="s:room"]').waitFor();
    assert.ok((await copied(page.locator('#wbCopyP'))).includes(site+room.m));
    assert.ok(await page.locator('#wbGo').isEnabled());
    assert.deepEqual(errors,[]);
    console.log('PASS real clipboard: card, angle, lightbox, batch, mixed and edited workspaces, private upload positions, saved history and text-only preference');
  } finally {await browser.close()}
}
run().catch(error=>{console.error(error);process.exitCode=1});
