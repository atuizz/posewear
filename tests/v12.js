const {chromium}=require('playwright');const path=require('path'),FX=path.join(__dirname,'fixtures')+'/',SS=path.join(__dirname,'screenshots')+'/';require('fs').mkdirSync(SS,{recursive:true});(async()=>{const U=process.env.U||'http://localhost:8787';const b=await chromium.launch({executablePath:process.env.CHROME_PATH});const errs=[],R=[];const S=SS+'v12-';const T=15000;
const ok=(n,v)=>{R.push((v?'PASS ':'FAIL ')+n)};
const W=(pg,f,a)=>pg.waitForFunction(f,a,{timeout:T}).then(()=>true).catch(()=>false);
const ctx=await b.newContext({viewport:{width:1440,height:900}});const pg=await ctx.newPage();pg.on('pageerror',e=>errs.push(''+e));pg.on('console',m=>m.type()=='error'&&!/404/.test(m.text())&&errs.push(m.text()));
await pg.goto(U+'/');ok('home grid',await W(pg,()=>document.querySelectorAll('#grid .card img.ld').length>=5));ok('intro visible',await pg.isVisible('#intro'));await pg.screenshot({path:S+'d-home.png'});
// tab switch timing
const tt=await pg.evaluate(async()=>{const o=[];for(const t of ['costume','portrait','pose']){const t0=performance.now();document.querySelector(`[data-tab=${t}]`).click();await new Promise(r=>{const f=()=>APP.st.tab==t&&document.querySelector('#grid .card')&&!document.querySelector('#grid .skel')?r():requestAnimationFrame(f);f()});o.push(Math.round(performance.now()-t0))}return o});ok('tab switch ms '+tt,Math.max(...tt)<400);
// back behaviour
await pg.click('[data-tab=costume]');await W(pg,()=>APP.st.tab=='costume'&&document.querySelector('#grid .card'));
await pg.evaluate(()=>document.querySelector('#grid .card .phk').click());ok('lb open',await W(pg,()=>!document.querySelector('#lb').hidden&&location.hash.includes('/')));
await pg.waitForTimeout(600);await pg.screenshot({path:S+'d-lb.png'});
await pg.goBack();ok('back closes lb',await W(pg,()=>document.querySelector('#lb').hidden&&location.hash=='#costume'));
await pg.goBack();ok('back to previous tab',await W(pg,()=>APP.st.tab=='pose'));
await pg.goForward();ok('forward',await W(pg,()=>APP.st.tab=='costume'));
// fav in lightbox updates fav grid
await pg.evaluate(()=>{APP.st.list.slice(0,3).forEach(i=>APP.st.fav.has(i.k)||APP.toggleFav(i.k,1))});
await pg.click('[data-tab=fav]');ok('fav grid',await W(pg,()=>APP.st.tab=='fav'&&document.querySelectorAll('#grid .card').length>=3));const nf=await pg.$$eval('#grid .card',x=>x.length);
await pg.evaluate(()=>document.querySelector('#grid .card .phk').click());await W(pg,()=>!document.querySelector('#lb').hidden);await pg.waitForTimeout(400);await pg.keyboard.press('f');await pg.waitForTimeout(200);await pg.keyboard.press('Escape');
ok('unfav in lb removes card',await W(pg,n=>document.querySelector('#lb').hidden&&document.querySelectorAll('#grid .card').length==n-1,nf));
// refresh restore
await pg.goto(U+'/#portrait');ok('refresh restore portrait',await W(pg,()=>APP.st.tab=='portrait'&&document.querySelector('#grid .card img')));
// intro dismiss
await pg.click('#introX');await pg.waitForTimeout(400);await pg.reload();await W(pg,()=>document.querySelector('#grid .card'));ok('intro dismissed persists',!(await pg.isVisible('#intro')));
// studio + settings
await pg.click('[data-tab=studio]');await W(pg,()=>APP.st.tab=='studio');await pg.waitForTimeout(800);await pg.screenshot({path:S+'d-studio.png'});ok('studio fits',(await pg.evaluate(()=>document.documentElement.scrollHeight))<=900);
// dark lb
await pg.evaluate(()=>{document.documentElement.dataset.theme='dark'});await pg.goto(U+'/#costume');await W(pg,()=>APP.st.tab=='costume'&&document.querySelectorAll('#grid .card .phk').length>3);await pg.evaluate(()=>document.querySelectorAll('#grid .card .phk')[2].click());await pg.waitForTimeout(900);await pg.screenshot({path:S+'d-dark-lb.png'});await pg.keyboard.press('Escape');
await pg.evaluate(()=>{localStorage.theme='light'});
// mobile
const m=await (await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true})).newPage();m.on('pageerror',e=>errs.push('m '+e));
await m.goto(U+'/');await W(m,()=>document.querySelectorAll('#grid .card img.ld').length>=2);await m.waitForTimeout(400);await m.screenshot({path:S+'m-home.png'});
let small=await m.evaluate(()=>[...document.querySelectorAll('.tabs button,.cbtns button,#adultSw,#theme')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height<34}).map(e=>e.id||e.className||e.textContent));console.log(small);small=small.length;ok('mobile small targets '+small,small==0);
await m.evaluate(()=>document.querySelector('#grid .card .phk').click());await W(m,()=>!document.querySelector('#lb').hidden);await m.waitForTimeout(900);ok('mobile sticky actions',await m.isVisible('.mact'));await m.screenshot({path:S+'m-lb.png'});
await m.goto(U+'/#studio');await W(m,()=>APP.st.tab=='studio');await m.waitForTimeout(700);await m.screenshot({path:S+'m-studio.png'});
await m.goto(U+'/#fav');await W(m,()=>APP.st.tab=='fav');await m.waitForTimeout(800);await m.screenshot({path:S+'m-fav.png'});
if(process.env.LIVE){for(const p of ['/pose/full_single_P001/','/costume/SPR-0001/','/nope-x']){await pg.goto(U+p);await pg.waitForTimeout(600);await pg.screenshot({path:S+'d'+p.replace(/\W+/g,'-')+'.png'})}}
console.log(R.join('\n'));console.log('errs',errs);await b.close()})()
