'use strict';
(()=>{
  const A = window.APP;
  if (!A) return;
  const $ = s => document.querySelector(s), $$ = s => document.querySelectorAll(s), esc = A.esc, toast = A.toast;
  const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const p2 = n => String(n).padStart(2, '0');
  const stamp = d => `${d.getFullYear()}${p2(d.getMonth() + 1)}${p2(d.getDate())}-${p2(d.getHours())}${p2(d.getMinutes())}`;
  const PROV_NAME = { openai: 'OpenAI', gemini: 'Gemini', seedream: '豆包', custom: '自定义' };

  let L = [];
  const sel = new Set();
  let curIndex = -1;
  let blobUrls = [];
  let lbUrls = [];

  const U = b => {
    if (!b) return '';
    const u = URL.createObjectURL(b);
    blobUrls.push(u);
    return u;
  };
  const cleanupUrls = () => {
    blobUrls.forEach(u => URL.revokeObjectURL(u));
    blobUrls = [];
  };
  const cleanupLbUrls = () => {
    lbUrls.forEach(u => URL.revokeObjectURL(u));
    lbUrls = [];
  };

  // Database access
  let dbp;
  const getDB = () => dbp || (dbp = new Promise((res, rej) => {
    const q = indexedDB.open('lk-studio', 1);
    q.onupgradeneeded = () => q.result.createObjectStore('h', { keyPath: 't' });
    q.onsuccess = () => res(q.result);
    q.onerror = () => rej(q.error);
  }));

  const tx = async (mode, fn) => {
    if (window.WB?.db?.tx) return window.WB.db.tx(mode, fn);
    const d = await getDB();
    return new Promise((res, rej) => {
      const t = d.transaction('h', mode), s = t.objectStore('h'), q = fn(s);
      t.oncomplete = () => res(q && q.result);
      t.onerror = () => rej(t.error);
    });
  };

  const getRecords = async () => {
    try {
      const all = await tx('readonly', s => s.getAll());
      return (all || []).sort((a, b) => b.t - a.t);
    } catch (e) {
      return [];
    }
  };

  const delRecord = async t => {
    if (window.WB?.db?.del) {
      await window.WB.db.del(t);
      if (window.WB.db.refreshHist) window.WB.db.refreshHist();
    } else {
      await tx('readwrite', s => s.delete(t));
    }
  };

  const putRecord = async rec => {
    if (window.WB?.db?.put) {
      await window.WB.db.put(rec);
      if (window.WB.db.refreshHist) window.WB.db.refreshHist();
    } else {
      await tx('readwrite', s => s.put(rec));
    }
  };

  const clearAll = async () => {
    if (window.WB?.db?.clear) {
      await window.WB.db.clear();
      if (window.WB.db.refreshHist) window.WB.db.refreshHist();
    } else {
      await tx('readwrite', s => s.clear());
    }
  };

  function updateToolbar() {
    const total = L.length;
    const cntEl = $('#histCount');
    if (cntEl) cntEl.innerHTML = total ? `<b>${total}</b> 条记录` : '';

    const selN = sel.size;
    const selNEl = $('#histSelN');
    if (selNEl) {
      selNEl.hidden = selN === 0;
      if (selN > 0) selNEl.innerHTML = `已选 <b>${selN}</b> 张`;
    }

    const selAllBox = $('#histSelAll');
    if (selAllBox) {
      selAllBox.checked = total > 0 && selN === total;
      selAllBox.indeterminate = selN > 0 && selN < total;
      selAllBox.disabled = total === 0;
    }

    const zipBtn = $('#histZip');
    if (zipBtn) zipBtn.disabled = selN === 0;
    const expBtn = $('#histExp');
    if (expBtn) expBtn.disabled = selN === 0;
    const clrBtn = $('#histClr');
    if (clrBtn) clrBtn.disabled = total === 0;

    const nHist = $('#nHist');
    if (nHist) nHist.textContent = total || '';
  }

  function renderStats() {
    const el = $('#histStats');
    if (!el) return;
    if (!L.length) {
      el.innerHTML = '';
      return;
    }
    const tryon = L.filter(r => r.mode != 'gen').length;
    const gen = L.filter(r => r.mode == 'gen').length;
    const provCount = {};
    L.forEach(r => {
      const p = PROV_NAME[r.prov] || r.prov || '其他';
      provCount[p] = (provCount[p] || 0) + 1;
    });
    const provStr = Object.entries(provCount).map(([k, v]) => `${esc(k)} ${v}`).join(' / ');
    el.innerHTML = `共 <b>${L.length}</b> 张 · 试穿 <b>${tryon}</b> / 生图 <b>${gen}</b>${provStr ? ' · ' + provStr : ''}`;
  }

  function renderGrid() {
    cleanupUrls();
    const grid = $('#histGrid');
    const empty = $('#histEmpty');
    const bar = $('#histBar');
    const stats = $('#histStats');
    if (!grid) return;

    if (!L.length) {
      grid.innerHTML = '';
      if (empty) empty.hidden = false;
      if (bar) bar.hidden = true;
      if (stats) stats.hidden = true;
      updateToolbar();
      return;
    }

    if (empty) empty.hidden = true;
    if (bar) bar.hidden = false;
    if (stats) stats.hidden = false;

    grid.innerHTML = L.map((r, i) => {
      const u = U(r.after);
      const isSel = sel.has(r.t);
      const d = new Date(r.t);
      const timeStr = `${d.getMonth() + 1}/${d.getDate()} ${p2(d.getHours())}:${p2(d.getMinutes())}`;
      const prov = PROV_NAME[r.prov] || r.prov || 'AI';
      const label = r.label || (r.prompt ? r.prompt.slice(0, 40) : (r.mode == 'gen' ? '自由生图' : '虚拟试穿'));
      const sub = `${timeStr} · ${prov} · ${r.model || ''}`;

      return `<article class="hist-card${isSel ? ' selected' : ''}" data-t="${r.t}" data-i="${i}">
        <div class="hph" role="button" tabindex="0" aria-label="查看大图：${esc(label)}">
          <img src="${u}" alt="${esc(label)}" loading="lazy">
          <input type="checkbox" class="hsel" data-t="${r.t}" aria-label="选择此记录" ${isSel ? 'checked' : ''}>
          <div class="hcbtns">
            <button class="icon" data-act="dl" title="下载图片" aria-label="下载图片">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            </button>
            <button class="icon" data-act="regen" title="用相同设置重新生成" aria-label="重新生成">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.19"/></svg>
            </button>
            <button class="icon" data-act="del" title="删除记录" aria-label="删除记录">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            </button>
          </div>
          <span class="hmode">${r.mode == 'gen' ? '生图' : '试穿'}</span>
        </div>
        <div class="hinfo">
          <h3 title="${esc(label)}">${esc(label)}</h3>
          <div class="sub" title="${esc(sub)}">${esc(sub)}</div>
        </div>
      </article>`;
    }).join('');

    renderStats();
    updateToolbar();
  }

  function dlOne(r) {
    if (!r?.after) return;
    const ts = stamp(new Date(r.t));
    const name = `posewear-${r.mode == 'gen' ? 'gen' : 'tryon'}-${ts}.png`;
    window.X.dl(r.after, name);
    toast('已开始下载图片');
  }

  async function delOne(r) {
    if (!r) return;
    await delRecord(r.t);
    sel.delete(r.t);
    toast('已删除 1 条记录', async () => {
      await putRecord(r);
      await refresh();
    });
    await refresh();
  }

  async function regen(r) {
    if (!r) return;
    if (window.WB) {
      await WB.show();
      const W = WB._W;
      if (W) {
        W.mode = r.mode || 'tryon';
        if (r.before) {
          W.persons = [{
            blob: r.before,
            url: URL.createObjectURL(r.before),
            w: 1024,
            h: 1024
          }];
        }
        if (r.prompt) {
          const ex = $('#wbExtra');
          if (ex) ex.value = r.orig || r.prompt;
        }
        if (r.neutral != null && $('#wbNeutral')) {
          $('#wbNeutral').checked = !!r.neutral;
        }
        if (r.prov && WB._cfg) {
          WB._cfg.prov = r.prov;
          if (r.model) WB._cfg.model = r.model;
        }
      }
      A.setTab('studio');
      toast('已载入生成设置，可在工作台调整或直接生成');
    }
  }

  async function asPerson(r) {
    if (!r?.after || !window.WB) return;
    await WB.show();
    const W = WB._W;
    if (W) {
      W.mode = 'tryon';
      W.persons = [{
        blob: r.after,
        url: URL.createObjectURL(r.after),
        w: 1024,
        h: 1024
      }];
    }
    A.lbClose();
    A.setTab('studio');
    toast('已将结果设为新的人物照片');
  }

  function openLb(index, srcCard) {
    if (index < 0 || index >= L.length) return;
    curIndex = index;
    const r = L[curIndex];
    if (!r) return;

    const lb = $('#lb');
    if (!lb) return;
    lb.hidden = false;
    document.body.style.overflow = 'hidden';

    drawLb();

    if (!RM && srcCard) {
      const ph = srcCard.querySelector('.hph');
      if (ph) {
        const rect = ph.getBoundingClientRect();
        $('.lb-bg').animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300 });
        const el = $('.lb-box');
        const dx = rect.left + rect.width / 2 - innerWidth / 2;
        const dy = rect.top + rect.height / 2 - innerHeight / 2;
        const s = Math.max(rect.width / el.offsetWidth, 0.08);
        el.animate([
          { transform: `translate(${dx}px,${dy}px) scale(${s})`, opacity: 0.2, borderRadius: '40px' },
          { transform: 'none', opacity: 1, borderRadius: '20px' }
        ], { duration: 520, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'both' });
      }
    }
    setTimeout(() => $('.lb-x')?.focus({ preventScroll: true }), 60);
  }

  function drawLb() {
    const r = L[curIndex];
    if (!r) return;
    cleanupLbUrls();

    const img = $('#lbImg');
    const box = $('.lb-img');
    if (box) box.classList.remove('loading', 'ext', 'fail');
    const afterUrl = URL.createObjectURL(r.after);
    lbUrls.push(afterUrl);

    if (img) {
      img.removeAttribute('srcset');
      img.src = afterUrl;
      img.alt = r.label || (r.mode == 'gen' ? '自由生图' : '虚拟试穿');
    }

    let cmpHtml = '';
    if (r.before && r.mode != 'gen') {
      const beforeUrl = URL.createObjectURL(r.before);
      lbUrls.push(beforeUrl);
      cmpHtml = `
      <div class="hlb-cmp" style="--x:50%">
        <img src="${afterUrl}" alt="生成后">
        <div class="hlb-bef"><img src="${beforeUrl}" alt="原图"></div>
        <div class="hlb-hdl"><span></span></div>
        <input type="range" min="0" max="100" value="50" aria-label="前后对比">
        <em class="l">原图</em><em class="r">生成后</em>
      </div>`;
    }

    const d = new Date(r.t);
    const dateStr = `${d.getFullYear()}/${p2(d.getMonth() + 1)}/${p2(d.getDate())} ${p2(d.getHours())}:${p2(d.getMinutes())}`;
    const prov = PROV_NAME[r.prov] || r.prov || 'AI 服务商';

    const side = $('#lbSide');
    if (!side) return;
    side.innerHTML = `
      <div class="mu">生成记录 · 第 ${curIndex + 1} / ${L.length} 项</div>
      <h2>${r.mode == 'gen' ? '自由生图' : '虚拟试穿'} · ${esc(prov)}</h2>
      <div class="mu">${dateStr} · 模型 ${esc(r.model || '默认')}${r.label ? ' · ' + esc(r.label) : ''}</div>
      ${cmpHtml}
      <div class="pbox" style="margin-top:14px">
        <small>提示词 · PROMPT${r.neutral ? '（已减少误拦截）' : ''}</small>
        <p>${esc(r.prompt || '（无提示词）')}</p>
        ${r.prompt ? '<button class="sm pri" data-hlb="cp">复制提示词</button>' : ''}
      </div>
      ${r.orig ? `<details class="raw" style="margin-top:10px"><summary>原始提示词</summary><pre>${esc(r.orig)}</pre><button class="sm ghost" data-hlb="cporig">复制</button></details>` : ''}
      <div class="acts" style="margin-top:16px">
        <button class="pri" data-hlb="dl">下载图片</button>
        <button data-hlb="regen">用此设置重新生成</button>
        ${r.mode != 'gen' && r.after ? '<button data-hlb="person">用作人物照片</button>' : ''}
        <button data-hlb="del" class="ghost" style="color:var(--err,#e53e3e)">删除此记录</button>
      </div>
      <p class="mu" style="margin-top:22px;line-height:2.1"><kbd>←</kbd><kbd>→</kbd>切换记录　<kbd>Esc</kbd>关闭</p>
    `;

    const slider = side.querySelector('.hlb-cmp input[type=range]');
    if (slider) {
      slider.oninput = e => {
        const wrap = e.target.closest('.hlb-cmp');
        if (wrap) wrap.style.setProperty('--x', e.target.value + '%');
      };
    }
  }

  function stepLb(delta) {
    if (!L.length) return;
    curIndex = (curIndex + delta + L.length) % L.length;
    drawLb();
    if (!RM) {
      const img = $('#lbImg');
      if (img) {
        img.animate([
          { opacity: 0.3, transform: `translateX(${delta * 30}px)` },
          { opacity: 1, transform: 'none' }
        ], { duration: 320, easing: 'cubic-bezier(.16,1,.3,1)' });
      }
    }
  }

  // Intercept prev / next buttons when in history view
  $('.prev')?.addEventListener('click', e => {
    if (A.st.tab == 'history' && !$('#lb')?.hidden) {
      e.stopImmediatePropagation();
      stepLb(-1);
    }
  }, true);

  $('.next')?.addEventListener('click', e => {
    if (A.st.tab == 'history' && !$('#lb')?.hidden) {
      e.stopImmediatePropagation();
      stepLb(1);
    }
  }, true);

  // Intercept keyboard arrow keys when in history view
  addEventListener('keydown', e => {
    if (A.st.tab == 'history' && !$('#lb')?.hidden) {
      if (e.key == 'ArrowLeft') {
        e.stopImmediatePropagation();
        stepLb(-1);
      } else if (e.key == 'ArrowRight') {
        e.stopImmediatePropagation();
        stepLb(1);
      }
    }
  }, true);

  // Hook side actions
  $('#lbSide')?.addEventListener('click', async e => {
    if (A.st.tab != 'history') return;
    const b = e.target.closest('[data-hlb]');
    if (!b) return;
    const act = b.dataset.hlb;
    const r = L[curIndex];
    if (!r) return;

    if (act == 'cp') A.copy(r.prompt, '提示词');
    if (act == 'cporig') A.copy(r.orig, '原始提示词');
    if (act == 'dl') dlOne(r);
    if (act == 'regen') {
      A.lbClose();
      await regen(r);
    }
    if (act == 'person') {
      await asPerson(r);
    }
    if (act == 'del') {
      A.lbClose();
      await delOne(r);
    }
  });

  // Grid click interactions
  $('#histGrid')?.addEventListener('click', async e => {
    const card = e.target.closest('.hist-card');
    if (!card) return;
    const t = +card.dataset.t;
    const i = +card.dataset.i;
    const r = L.find(x => x.t == t) || L[i];
    if (!r) return;

    if (e.target.classList.contains('hsel')) {
      if (e.target.checked) {
        sel.add(t);
        card.classList.add('selected');
      } else {
        sel.delete(t);
        card.classList.remove('selected');
      }
      updateToolbar();
      return;
    }

    const btn = e.target.closest('button[data-act]');
    if (btn) {
      e.stopPropagation();
      const act = btn.dataset.act;
      if (act == 'dl') dlOne(r);
      if (act == 'del') await delOne(r);
      if (act == 'regen') await regen(r);
      return;
    }

    const ph = e.target.closest('.hph');
    if (ph) {
      openLb(i, card);
    }
  });

  $('#histGrid')?.addEventListener('keydown', e => {
    if (e.key == 'Enter' || e.key == ' ') {
      const ph = e.target.closest('.hph');
      if (ph && !e.target.classList.contains('hsel')) {
        e.preventDefault();
        const card = ph.closest('.hist-card');
        const i = +card?.dataset.i;
        if (i >= 0) openLb(i, card);
      }
    }
  });

  // Toolbar events
  $('#histSelAll')?.addEventListener('change', e => {
    if (e.target.checked) {
      L.forEach(r => sel.add(r.t));
    } else {
      sel.clear();
    }
    $$('#histGrid .hist-card').forEach(c => {
      const isSel = sel.has(+c.dataset.t);
      c.classList.toggle('selected', isSel);
      const cb = c.querySelector('.hsel');
      if (cb) cb.checked = isSel;
    });
    updateToolbar();
  });

  $('#histZip')?.addEventListener('click', async () => {
    const selected = L.filter(r => sel.has(r.t));
    if (!selected.length) return toast('请先勾选要下载的记录');
    if (!window.makeZip) return toast('未加载打包组件');
    const btn = $('#histZip');
    btn.disabled = true;
    btn.textContent = '打包中…';
    try {
      const ts = stamp(new Date());
      const files = selected.map((r, i) => ({
        name: `posewear-${r.mode == 'gen' ? 'gen' : 'tryon'}-${stamp(new Date(r.t))}-${String(i + 1).padStart(2, '0')}.png`,
        blob: r.after
      }));
      const zipBlob = await window.makeZip(files);
      window.X.dl(zipBlob, `posewear-history-${ts}.zip`);
      toast(`已打包下载 ${files.length} 张图片`);
    } catch (err) {
      toast('打包失败，请重试');
    } finally {
      btn.disabled = false;
      btn.textContent = '打包下载';
    }
  });

  $('#histExp')?.addEventListener('click', async () => {
    const selected = L.filter(r => sel.has(r.t));
    if (!selected.length) return toast('请先勾选要导出的记录');
    if (!window.makeZip) return toast('未加载打包组件');
    const btn = $('#histExp');
    btn.disabled = true;
    btn.textContent = '导出中…';
    try {
      const ts = stamp(new Date());
      const metaList = [];
      const files = [];
      selected.forEach((r, i) => {
        const fileName = `posewear-${r.mode == 'gen' ? 'gen' : 'tryon'}-${stamp(new Date(r.t))}-${String(i + 1).padStart(2, '0')}.png`;
        files.push({ name: fileName, blob: r.after });
        metaList.push({
          time: new Date(r.t).toISOString(),
          timestamp: r.t,
          mode: r.mode || 'tryon',
          provider: r.prov,
          model: r.model,
          prompt: r.prompt,
          originalPrompt: r.orig || null,
          neutral: !!r.neutral,
          label: r.label || '',
          fileName
        });
      });
      const metaBlob = new Blob([JSON.stringify({
        app: '衣姿 PoseWear',
        type: 'generation-history',
        exportTime: new Date().toISOString(),
        totalCount: selected.length,
        records: metaList
      }, null, 2)], { type: 'application/json' });
      files.push({ name: 'metadata.json', blob: metaBlob });

      const zipBlob = await window.makeZip(files);
      window.X.dl(zipBlob, `posewear-export-${ts}.zip`);
      toast(`已导出 ${selected.length} 条记录（含元数据）`);
    } catch (err) {
      toast('导出失败，请重试');
    } finally {
      btn.disabled = false;
      btn.textContent = '导出 ZIP';
    }
  });

  $('#histClr')?.addEventListener('click', async () => {
    if (!L.length) return toast('还没有生成记录');
    const oldList = L.slice();
    await clearAll();
    sel.clear();
    await refresh();
    toast(`已清空 ${oldList.length} 条记录`, async () => {
      for (const r of oldList) await putRecord(r);
      await refresh();
    });
  });

  $('#histEmpty button[data-go="studio"]')?.addEventListener('click', () => {
    A.setTab('studio');
  });

  async function refresh() {
    L = await getRecords();
    const currentKeys = new Set(L.map(r => r.t));
    for (const k of sel) {
      if (!currentKeys.has(k)) sel.delete(k);
    }
    renderGrid();
  }

  async function show() {
    await refresh();
  }

  window.HIS = { show, refresh, getList: () => L };

  // Init badge count on load
  getRecords().then(list => {
    L = list;
    const nHist = $('#nHist');
    if (nHist) nHist.textContent = L.length || '';
    if (document.body.classList.contains('histview') || location.hash == '#history') {
      show();
    }
  }).catch(() => {});
})();
