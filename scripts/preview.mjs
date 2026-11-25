import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Readable } from 'node:stream';
import { catalogIndex, catalogNames, publishedSite, readCatalog } from './catalog-source.mjs';
import { onRequest } from '../functions/api/proxy.js';
import { localEngine, localRequest } from './local-engine.mjs';
const engine = localEngine(process.env);

const root = fileURLToPath(new URL('../src/', import.meta.url));
const stagedPages = process.env.POSEWEAR_STAGING || fileURLToPath(new URL('../dist/', import.meta.url));
const release = new URL(publishedSite).origin;
const media = 'https://pwimg.0vo.pro';
const port = Number(process.env.PORT || 8787);
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.svg':'image/svg+xml',
  '.png':'image/png','.webmanifest':'application/manifest+json','.json':'application/json'};
const catalogs = catalogNames;
let snapshot;
const statNames = {poses:'pose',depths:'depth',costumes:'cos',anime:'ani',portraits:'por',expressions:'exp',
  hair:'hair',dynasties:'dyn',scenes:'scene',lights:'light',props:'prop',furniture:'furn'};
async function discover() {
  const index = await catalogIndex(process.env.POSEWEAR_CATALOG_URL || publishedSite);
  const data = new Map(), counts = {};
  for (let i = 0; i < catalogs.length; i += 4) {
    await Promise.all(catalogs.slice(i,i+4).map(async name => {
      const {text,items} = await readCatalog(index,name);
      if (!items.length) throw new Error('Empty catalog: '+name);
      const publicItems = items.filter(item => !item.a);
      const key = statNames[name];
      if (key) counts[key] = [publicItems.length, items.length];
      data.set(name,text);
    }));
  }
  return {data,counts};
}
function publishedSnapshot() {
  snapshot ??= discover().catch(error => { snapshot = undefined; throw error; });
  return snapshot;
}
function streamOut(res, body) {
  const s = Readable.fromWeb(body);
  // 上游中途断开（如 content-length 不符）只丢弃本次响应，不能让预览进程退出
  s.on('error', () => { if (!res.writableEnded) res.destroy(); });
  res.on('error', () => {});
  s.pipe(res);
}
async function remote(res, url, method, successStatus) {
  const r = await fetch(url, { method });
  const headers = {};
  for (const key of ['content-type','cache-control']) if (r.headers.has(key)) headers[key] = r.headers.get(key);
  res.writeHead(r.ok && successStatus ? successStatus : r.status, headers);
  if (r.body) streamOut(res, r.body); else res.end();
  return r.status;
}
const server = http.createServer(async (req,res) => {
  try {
    const currentPort = server.address().port;
    if (!['127.0.0.1:'+currentPort,'localhost:'+currentPort].includes(req.headers.host)) return res.writeHead(400).end();
    const u = new URL(req.url, 'http://'+req.headers.host);
    if (u.pathname.startsWith('/api/local/')) {
      const controller = new AbortController();
      res.once('close',()=>{ if(!res.writableEnded) controller.abort(); });
      const request = new Request(u,{method:req.method,headers:req.headers,signal:controller.signal,
        ...(req.method==='POST'?{body:Readable.toWeb(req),duplex:'half'}:{})});
      const reply = await localRequest(engine,request);
      res.writeHead(reply.status,Object.fromEntries(reply.headers));
      if(reply.body) streamOut(res, reply.body); else res.end();
      return;
    }
    if (u.pathname === '/api/proxy') {
      const request = new Request(u,{method:req.method,headers:req.headers,
        ...(req.method === 'POST' ? {body:Readable.toWeb(req),duplex:'half'} : {})});
      const response = await onRequest({request,env:process.env});
      res.writeHead(response.status,Object.fromEntries(response.headers));
      if (response.body) streamOut(res, response.body); else res.end();
      return;
    }
    if (!['GET','HEAD'].includes(req.method)) return res.writeHead(405).end();
    const name = u.pathname.slice(1).replace(/\.json$/,'');
    if (u.pathname === '/'+name+'.json' && catalogs.includes(name)) {
      const {data} = await publishedSnapshot();
      res.writeHead(200,{'content-type':mime['.json'],'cache-control':'no-cache'}).end(data.get(name));
      return;
    }
    const rel = u.pathname === '/' ? 'index.html' : u.pathname.slice(1);
    if (/^[a-zA-Z0-9.-]+$/.test(rel) && rel !== '.' && rel !== '..') {
      try {
        let content = await fs.readFile(path.join(root,rel));
        if (rel === 'index.html') {
          const {counts} = await publishedSnapshot();
          content = content.toString().replace(/<b data-stat="(\w+)"[^>]*>[^<]*<\/b>/g, (_,key) => {
            const [visible,total] = counts[key];
            return `<b data-stat="${key}" data-n="${visible}" data-na="${total}">${visible.toLocaleString('en-US')}</b>`;
          });
        }
        if (rel === 'index.html' && engine) {
          const preset = engine.preset ? ' data-local-preset="1"' : '';
          content = content.toString().replace('<html ',`<html data-local-engine="${engine.name}"${preset} `);
        }
        if (rel === 'app.js') content = content.toString().replace("const AH='';","const AH='"+media+"/';");
        res.writeHead(200,{'content-type':mime[path.extname(rel)] || 'application/octet-stream','cache-control':'no-store'}).end(content);
        return;
      } catch (e) { if (e.code !== 'ENOENT') throw e; }
    }
    // Static pages use the theme asset from the same build as their HTML.
    if (/^\/assets\/theme\.[0-9a-f]{10}\.js$/.test(u.pathname)) {
      try {
        const script = await fs.readFile(path.join(stagedPages,u.pathname));
        return res.writeHead(200,{'content-type':mime['.js']}).end(script);
      } catch (error) {
        if (error.code !== 'ENOENT') throw error;
      }
      await remote(res,release+u.pathname,req.method);
      return;
    }
    const seoRoute = /^\/(?:en|pose|costume|anime|portrait|tag)\/[\w/-]*$/.test(u.pathname);
    if (seoRoute) {
      try {
        const html = await fs.readFile(path.join(stagedPages,u.pathname,'index.html'));
        return res.writeHead(200,{'content-type':mime['.html'],'cache-control':'no-cache'}).end(html);
      } catch (error) {
        if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
      }
    }
    if (seoRoute || /^\/[pcareysltf]\/(?:m|i)\/[\w.%-]+\.webp$/.test(u.pathname)) {
      await remote(res,release+u.pathname,req.method);
      return;
    }
    if ((req.headers.accept || '').includes('text/html')) {
      try {
        const html = await fs.readFile(path.join(stagedPages,'404.html'));
        return res.writeHead(404,{'content-type':mime['.html']}).end(html);
      } catch (error) {
        if (error.code !== 'ENOENT') throw error;
      }
      // The published 404 document itself returns 200. Keep the unknown route a 404.
      await remote(res,release+'/404.html',req.method,404);
      return;
    }
    res.writeHead(404).end();
  } catch (error) {
    if (!res.headersSent) res.writeHead(502,{'content-type':'text/plain; charset=utf-8'});
    res.end('Preview unavailable: '+error.message);
  }
});
server.listen(port,'127.0.0.1',() => console.log('PoseWear: http://127.0.0.1:'+server.address().port+'/'));
