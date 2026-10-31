// 表情：年龄门槛、三种视图的下载、姿势组合。门槛文案来自包配置，不写死包名。
(()=>{const A=window.APP,$=s=>document.querySelector(s),LS=k=>{try{return JSON.parse(localStorage[k]||'null')}catch(e){return null}},SV=(k,v)=>{try{localStorage[k]=JSON.stringify(v)}catch(e){}};
const gates=()=>LS('exprGates')||{};
const saveGates=g=>SV('exprGates',g);
const meta=()=>A.DATA.exprMeta||{};
const packs=()=>meta().packs||[];
const packOf=it=>packs().find(p=>p.id==it.pack)||{};
const views=()=>meta().views||[{id:'source',zh:'原图'}];
function want(){const g=gates();return packs().some(p=>p.gated&&p.ageGate&&g[p.ageGate])}
let gatedP=null;
function loadGated(){const url=meta().gated;if(!url)return Promise.resolve();if(gatedP)return gatedP;
 gatedP=fetch(url).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(j=>{const have=new Set((A.DATA.expression||[]).map(it=>it.id));
  (j.items||[]).forEach((it,i)=>{if(have.has(it.id))return;it.type='expression';it.k='e:'+it.id;it.ord=1000+i;A.ITEMS[it.k]=it;A.DATA.expression.push(it)});A.counts()}).catch(e=>{gatedP=null;throw e});
 return gatedP}
function dropGated(){if(!A.DATA.expression)return;A.DATA.expression=A.DATA.expression.filter(it=>!it.gate);Object.keys(A.ITEMS).forEach(k=>{if(k[0]=='e'&&A.ITEMS[k]&&A.ITEMS[k].gate)delete A.ITEMS[k]});gatedP=null;A.counts()}
function gatePack(id){return packs().find(p=>p.gated&&p.ageGate==id)||packs().find(p=>p.gated)||{}}
let pending=null;
function ask(id,done){const p=gatePack(id);pending=done||null;$('#exprAgeT').textContent=p.gateTitle||'显示受限制的表情？';$('#exprAgeP').textContent=p.gateBody||'';$('#exprAgeY').textContent=p.confirm||'我已满 18 岁，打开';$('#exprAgeN').textContent=p.cancel||'暂不';$('#exprAge').hidden=false;setTimeout(()=>$('#exprAgeY').focus(),30)}
function setGate(id,on){const g=gates();if(on)g[id]=true;else delete g[id];saveGates(g);renderSwitch()}
function openGate(id){setGate(id,true);const after=pending;pending=null;return loadGated().then(()=>{A.drawFilters();A.apply();renderCombo();A.toast('已显示'+((gatePack(id).switch)||'受限制表情'),()=>{setGate(id,false);dropGated();A.drawFilters();A.apply();renderCombo()});after&&after()}).catch(()=>A.toast('表情加载失败'))}
$('#exprAgeY').onclick=()=>{const id=$('#exprAge').dataset.gate||(packs().find(p=>p.gated)||{}).ageGate;$('#exprAge').hidden=true;openGate(id)};
$('#exprAgeN').onclick=$('#exprAge').onclick=e=>{if(e.target.id!='exprAgeN'&&e.target.id!='exprAge')return;$('#exprAge').hidden=true;pending=null;renderSwitch()};
function renderSwitch(){const slot=$('#exprGate');if(!slot)return;const gs=[...new Map(packs().filter(p=>p.gated&&p.ageGate).map(p=>[p.ageGate,p])).values()];
 slot.innerHTML=gs.map(p=>{const on=!!gates()[p.ageGate];return `<button type="button" class="asw" data-gate="${A.esc(p.ageGate)}" role="switch" aria-checked="${on}"><span class="trk" aria-hidden="true"><span class="kn"></span></span><b>${A.esc(p.switch||p.badge||p.ageGate)}</b></button>`}).join('');
 slot.querySelectorAll('[data-gate]').forEach(b=>b.onclick=()=>{const id=b.dataset.gate;if(gates()[id]){setGate(id,false);dropGated();A.drawFilters();A.apply();renderCombo();A.toast('已关闭'+((gatePack(id).switch)||''),()=>{setGate(id,true);loadGated().then(()=>{A.drawFilters();A.apply();renderCombo()})})}else{$('#exprAge').dataset.gate=id;ask(id)}})}
function renderPacks(){const el=$('#exprPacks');if(!el)return;const ph=packs().some(p=>p.placeholder)?'<p>当前图片是占位，正式的 ICT-FaceKit 渲染用导入命令替换。模型许可不变。</p>':'';
 el.innerHTML=ph+packs().map(p=>`<p><b>${A.esc(p.nameZh||p.id)}</b>${p.gated?` · <span class="tag c">${A.esc(p.badge||p.ageGate)}</span> 默认隐藏`:''}${p.version?' · v'+A.esc(p.version):''}<br>${A.esc(p.source||'')} ${p.url?`<a href="${A.esc(p.url)}" target="_blank" rel="noopener">${A.esc(p.url)}</a>`:''}<br>${A.esc(p.license||'')}${p.note?'<br>'+A.esc(p.note):''}</p>`).join('')+
  '<p>人脸模型：<a href="https://github.com/ICT-VGL/ICT-FaceKit" target="_blank" rel="noopener">ICT-FaceKit Light</a>，Copyright (c) 2020 USC Institute for Creative Technologies，MIT。每个包目录里有 THIRD_PARTY_LICENSES.txt，写明锁定的提交。<a href="/licenses/ICT-FaceKit.txt">许可全文</a>。本站是开源非商业项目，不收款。</p>'}
function noticeText(it){const p=packOf(it);const up=p.upstream||{};return ['NOTICE'+(p.badge?': '+p.badge:''),p.noticeZh,p.noticeEn,p.gateBody,'License: '+(p.license||''),up.repo&&('Upstream: '+up.repo),up.variant&&('Variant: '+up.variant),up.commit&&('Commit: '+up.commit),'ICT-FaceKit Light, Copyright (c) 2020 USC Institute for Creative Technologies, MIT.'].filter(Boolean).join('\n')+'\n'}
const ext=u=>(String(u).match(/\.\w+$/)||['.png'])[0];
const licCache=new Map();
function licenseBlob(it){const p=packOf(it);const url=p.thirdParty?'/'+p.thirdParty:'/licenses/ICT-FaceKit.txt';
 if(licCache.has(url))return Promise.resolve(licCache.get(url));
 return fetch(url).then(r=>{if(!r.ok)throw Error(url);return r.blob()}).then(b=>{licCache.set(url,b);return b})}
async function filesOf(it){const out=[];for(const v of views()){const f=it.views&&it.views[v.id];if(!f)continue;const r=await fetch('/'+f.o);if(!r.ok)throw Error(f.o);out.push({name:`${it.id}_${v.id}${ext(f.o)}`,blob:await r.blob(),view:v.id})};return out}
async function withLegal(items,files){const list=Array.isArray(items)?items:[items].filter(Boolean);const seen=new Set();const many=new Set(list.map(it=>it.pack)).size>1;
 for(const it of list){if(seen.has(it.pack))continue;seen.add(it.pack);const dir=many?it.pack+'/':'';
  files.push({name:dir+'THIRD_PARTY_LICENSES.txt',blob:await licenseBlob(it)});
  if(it.gate)files.push({name:dir+'NOTICE.txt',blob:new Blob([noticeText(it)])})}
 return files}
async function downloadOne(it){try{const v=A.st.xv&&it.views[A.st.xv]?A.st.xv:'source';const r=await fetch('/'+it.views[v].o);if(!r.ok)throw Error();
 const files=await withLegal(it,[{name:`${it.id}_${v}.png`,blob:await r.blob()}]);
 window.X.dl(await makeZip(files),`posewear-${it.id}-${v}${it.gate?'-18plus':''}.zip`);A.toast(it.gate?'已开始下载（含 18+ 说明和许可）':'已开始下载（含第三方许可）')}catch(e){A.toast('下载失败')}}
async function downloadSet(it){try{const files=await withLegal(it,await filesOf(it));window.X.dl(await makeZip(files),`posewear-${it.id}${it.gate?'-18plus':''}.zip`);A.toast(it.gate?'已打包这一套（含 18+ 说明和许可）':'已打包这一套（含第三方许可）')}catch(e){A.toast('打包失败')}}
function manifestOf(list){const by={};list.forEach(it=>{const p=packOf(it);(by[it.pack]||(by[it.pack]={...p,items:[]})).items.push({id:it.id,name_zh:it.zh,name_en:it.en,tags:it.tags,angle:it.angle,group:it.group,prompt_zh:it.zhPrompt,prompt_en:it.enPrompt,w:it.w,h:it.h,pack:it.pack,blendshape_weights:it.weights||undefined,gate:it.gate||undefined,badge:it.badge||undefined})});return{packs:Object.values(by)}}
async function zipList(){const L=A.st.list.filter(it=>it.type=='expression');if(!L.length)return A.toast('当前没有可打包的表情');const b=$('#exprZip');const old=b.textContent;b.disabled=true;const files=[];let bytes=0;const cap=180*1024*1024;
 try{let n=0;for(const it of L){for(const v of views()){const f=it.views[v.id];if(!f)continue;const r=await fetch('/'+f.o);if(!r.ok)throw Error(f.o);const blob=await r.blob();bytes+=blob.size;if(bytes>cap){A.toast('筛选结果超过 180MB，请缩小范围再打包');return}files.push({name:`${v.id}/${it.id}${ext(f.o)}`,blob})}b.textContent=`打包中 ${++n}/${L.length}`}
  files.push({name:'manifest.json',blob:new Blob([JSON.stringify(manifestOf(L),null,2)])});
  await withLegal(L,files);
  window.X.dl(await makeZip(files),`posewear-expr-${L.length}.zip`);A.toast(`已打包 ${L.length} 个表情`)}catch(e){A.toast('打包失败')}finally{b.disabled=false;b.textContent=old}}
const C={pose:'',ai:0,expr:'',lang:LS('xlang')||'zh'};
function fill(t,o){return t.replace(/\{(\w+)\}/g,(_,k)=>o[k]??'')}
function resolve(){const pose=A.ITEMS[C.pose],expr=A.ITEMS[C.expr];if(!pose||!expr)return null;const ang=pose.angles[Math.min(C.ai,pose.angles.length-1)]||pose.angles[0];
 const sibs=A.DATA.expression.filter(e=>e.group==expr.group&&e.pack==expr.pack&&A.ok(e));
 const prefs=[ang.zh,...((meta().fallback||{})[ang.zh]||[])];let used=null;for(const zh of prefs){used=sibs.find(e=>e.angleZh==zh||e.poseAngle==zh);if(used)break}
 if(!used)used=sibs[0]||expr;const fell=used.angleZh!=ang.zh&&used.poseAngle!=ang.zh;return{pose,ang,expr,used,fell}}
function promptOf(r,lang){const tpl=(meta().templates||{})[lang]||'';const tags=r.used.tags.join(lang=='en'?', ':'、');
 const body=fill(tpl,{poseZh:r.pose.zh,poseEn:r.pose.en,lineZh:r.pose.line,lineEn:r.pose.lineEn,poseAngZh:r.ang.zh,poseAngEn:r.ang.en,exprZh:r.used.zh,exprEn:r.used.en,exprAngZh:r.used.angleZh,exprAngEn:r.used.angleEn,tags});
 const note=r.used.gate?(lang=='en'?(packOf(r.used).noticeEn||'18+'):(packOf(r.used).noticeZh||r.used.badge||'')):'';
 const fb=r.fell?(lang=='en'?`Pose angle is ${r.ang.en}; expression reference falls back to ${r.used.angleEn}.`:`姿势角度是${r.ang.zh}，表情参考退回${r.used.angleZh}。`):'';
 return [body,note,fb].filter(Boolean).join(lang=='en'?' ':'')}
function renderCombo(){const box=$('#xcombo');if(!box||box.hidden)return;const r=resolve();const pose=A.ITEMS[C.pose];
 $('#xPose').innerHTML=pose?`<img src="${A.thumb(pose)}" alt=""><div><b>${A.esc(A.title(pose))}</b><div class="mu">${A.esc(pose.line||'')}</div></div>`:'<span class="mu">还没有选姿势</span>';
 $('#xAng').innerHTML=pose?pose.angles.map((a,i)=>`<button type="button" class="chip ${i==C.ai?'on':''}" data-pai="${i}">${A.esc(a.zh)}</button>`).join(''):'';
 const expr=A.ITEMS[C.expr];
 $('#xExpr').innerHTML=r?views().map(v=>r.used.views[v.id]?`<img src="${r.used.views[v.id].t}" alt="${A.esc(v.zh)}" title="${A.esc(v.zh)}">`:'').join('')+(r.used.badge?`<span class="badge gate">${A.esc(r.used.badge)}</span>`:''):(expr?`<span class="mu">${A.esc(expr.zh)}</span>`:'<span class="mu">在卡片上点「配姿势」</span>');
 const hint=$('#xHint');if(r){hint.textContent=r.fell?`${r.ang.zh}没有对应表情，已退回${r.used.angleZh}`:`角度一致：${r.used.angleZh}`;hint.classList.toggle('warn',r.fell)}else hint.textContent=pose?'再选一个表情':'选一个姿势角度，再配一个表情';
 $('#xLang').querySelectorAll('[data-xl]').forEach(b=>b.classList.toggle('on',b.dataset.xl==C.lang));
 $('#xPrompt').value=r?promptOf(r,C.lang):''}
function pair(it){C.expr=it.k;if(!$('#lb').hidden)A.lbClose();$('#xcombo').classList.remove('min');$('#xMin').textContent='收起';renderCombo();$('#xcombo').scrollIntoView({block:'nearest'});A.toast('已配上表情：'+it.zh+(it.badge?'（'+it.badge+'）':''))}
function drawPoses(q){const s=(q||'').trim().toLowerCase();const L=(A.DATA.pose||[]).filter(A.ok).filter(it=>!s||(it.zh+it.en+it.id).toLowerCase().includes(s)).slice(0,60);
 $('#xpkG').innerHTML=L.map(it=>`<button type="button" class="pose" data-k="${it.k}"><img src="${A.thumb(it)}" alt=""><span>${A.esc(it.zh)}</span></button>`).join('')||'<p class="mu">没有匹配的姿势</p>'}
$('#xPick').onclick=async()=>{await A.load('pose');$('#xpk').hidden=false;document.body.style.overflow='hidden';$('#xpkQ').value='';drawPoses('');setTimeout(()=>$('#xpkQ').focus(),30)};
$('#xpkX').onclick=()=>{$('#xpk').hidden=true;document.body.style.overflow=''};
$('#xpk').onclick=e=>{if(e.target.id=='xpk'){$('#xpk').hidden=true;document.body.style.overflow=''}};
$('#xpkQ').oninput=e=>drawPoses(e.target.value);
$('#xpkG').onclick=e=>{const b=e.target.closest('[data-k]');if(!b)return;C.pose=b.dataset.k;C.ai=0;$('#xpk').hidden=true;document.body.style.overflow='';renderCombo()};
$('#xAng').onclick=e=>{const b=e.target.closest('[data-pai]');if(!b)return;C.ai=+b.dataset.pai;renderCombo()};
$('#xLang').onclick=e=>{const b=e.target.closest('[data-xl]');if(!b)return;C.lang=b.dataset.xl;SV('xlang',C.lang);renderCombo()};
$('#xCopy').onclick=()=>{if(!$('#xPrompt').value)return A.toast('先选姿势和表情');A.copy($('#xPrompt').value,'组合提示词')};
$('#xZip').onclick=async()=>{const r=resolve();if(!r)return A.toast('先选姿势和表情');try{const text=['中文',promptOf(r,'zh'),'','English',promptOf(r,'en')].join('\n');
 const poseUrl=r.ang.o||r.ang.i;const pr=await fetch('/'+poseUrl);if(!pr.ok)throw Error('pose');
 const files=[{name:'prompt.txt',blob:new Blob([text])},{name:'pose/'+r.pose.id+'_'+r.ang.zh+ext(poseUrl),blob:await pr.blob()},...await filesOf(r.used)];
 window.X.dl(await makeZip(await withLegal(r.used,files)),`posewear-combo-${r.pose.id}-${r.used.id}${r.used.gate?'-18plus':''}.zip`);A.toast(r.used.gate?'参考包已开始下载（含 18+ 说明和许可）':'参考包已开始下载（含第三方许可）')}catch(e){A.toast('参考包下载失败')}};
$('#xMin').onclick=()=>{const m=$('#xcombo').classList.toggle('min');$('#xMin').textContent=m?'展开':'收起'};
$('#exprZip').onclick=()=>zipList();
function onTab(){A.load('expression').then(()=>{renderPacks();renderSwitch();const id=decodeURIComponent((location.hash.split('/')[1]||''));const gate=(meta().gatedIndex||{})[id];
 const job=want()?loadGated():Promise.resolve();return job.then(()=>{renderCombo();if(want()){A.drawFilters();A.apply()}if(gate&&!gates()[gate]){$('#exprAge').dataset.gate=gate;ask(gate,()=>{const i=A.st.list.findIndex(x=>x.id==id);if(i<0){A.st.f={};A.st.q='';A.drawFilters();A.apply()}const j=A.st.list.findIndex(x=>x.id==id);if(j>=0)A.lbOpen(j)})}})}).catch(()=>A.toast('表情加载失败'))}
const _set=A.setTab;A.setTab=(...a)=>{const r=_set.apply(A,a);return Promise.resolve(r).then(v=>{if(A.st.tab=='expression')onTab();return v})};
if(innerWidth<=760)$('#xcombo').classList.add('min');
if(A.st.tab=='expression')onTab();else renderSwitch();
window.EXPR={onTab,loadGated,want,downloadOne,downloadSet,zipList,pair,noticeText,packOf,withLegal}})();
