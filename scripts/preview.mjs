import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Readable } from 'node:stream';
import { onRequest } from '../functions/api/proxy.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '../src');

const nativeFetch = globalThis.fetch;
globalThis.fetch = async (url, init = {}) =>
  nativeFetch(
    url,
    init.body instanceof ReadableStream
      ? { ...init, body: await new Response(init.body).arrayBuffer() }
      : init
  );

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.json': 'application/json',
  '.webmanifest': 'application/manifest+json',
  '.ico': 'image/x-icon'
};

const JSON_MAP = {
  '/poses.json': 'https://posewear.pages.dev/assets/poses.2383bf449f.json',
  '/depths.json': 'https://posewear.pages.dev/assets/depths.264ea86381.json',
  '/costumes.json': 'https://posewear.pages.dev/assets/costumes.2cee954fb7.json',
  '/anime.json': 'https://posewear.pages.dev/assets/anime.5b38cbc858.json',
  '/portraits.json': 'https://posewear.pages.dev/assets/portraits.0b8834f90f.json'
};

const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, 'http://127.0.0.1:8787');

    // 1. API proxy route
    if (u.pathname === '/api/proxy') {
      const h = new Headers();
      for (const [k, v] of Object.entries(req.headers)) {
        if (v) h.set(k, Array.isArray(v) ? v.join(', ') : v);
      }
      const request = new Request(u, {
        method: req.method,
        headers: h,
        ...(req.method === 'POST' ? { body: Readable.toWeb(req), duplex: 'half' } : {})
      });
      const result = await onRequest({ request });
      res.writeHead(result.status, Object.fromEntries(result.headers));
      if (result.body) Readable.fromWeb(result.body).pipe(res);
      else res.end();
      return;
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405).end();
      return;
    }

    // 2. Map known data JSON endpoints
    if (JSON_MAP[u.pathname]) {
      const remote = await fetch(JSON_MAP[u.pathname]);
      res.writeHead(remote.status, {
        'content-type': 'application/json; charset=utf-8',
        'cache-control': 'no-cache'
      });
      if (remote.body) Readable.fromWeb(remote.body).pipe(res);
      else res.end();
      return;
    }

    // 3. Check local files in src/
    let relPath = u.pathname.replace(/^\/+/, '');
    if (!relPath || relPath === 'index.html') relPath = 'index.html';

    // Map hashed /assets/* requests to unhashed local files if needed
    if (relPath.startsWith('assets/')) {
      const base = path.basename(relPath);
      if (/^studio(\.[a-f0-9]+)?\.js$/.test(base)) relPath = 'studio.js';
      else if (/^history(\.[a-f0-9]+)?\.js$/.test(base)) relPath = 'history.js';
      else if (/^app(\.[a-f0-9]+)?\.js$/.test(base)) relPath = 'app.js';
      else if (/^extras(\.[a-f0-9]+)?\.js$/.test(base)) relPath = 'extras.js';
      else if (/^zip(\.[a-f0-9]+)?\.js$/.test(base)) relPath = 'zip.js';
      else if (/^style(\.[a-f0-9]+)?\.css$/.test(base)) relPath = 'style.css';
    }

    const localFile = path.resolve(root, relPath);
    if (localFile.startsWith(root + '/')) {
      try {
        const data = await fs.readFile(localFile);
        res.writeHead(200, {
          'content-type': mime[path.extname(localFile)] || 'application/octet-stream',
          'cache-control': 'no-cache'
        });
        res.end(data);
        return;
      } catch (err) {
        // Not found locally, proceed to remote proxy
      }
    }

    // 4. Remote asset proxy (fallback to asset host or main host)
    let remoteUrl = 'https://posewear.pages.dev' + u.pathname + u.search;
    if (/^\/(p|c|a|o|r)\//.test(u.pathname)) {
      remoteUrl = 'https://posewear-assets-96b.pages.dev' + u.pathname + u.search;
    }

    let remote = await fetch(remoteUrl);
    if (!remote.ok && remoteUrl.includes('posewear-assets-96b')) {
      // Try fallback to main site
      const fallback = await fetch('https://posewear.pages.dev' + u.pathname + u.search);
      if (fallback.ok) remote = fallback;
    }

    const h = {};
    for (const key of ['content-type', 'cache-control']) {
      if (remote.headers.has(key)) h[key] = remote.headers.get(key);
    }
    res.writeHead(remote.status, h);
    if (remote.body) Readable.fromWeb(remote.body).pipe(res);
    else res.end();
  } catch (e) {
    res.writeHead(502, { 'content-type': 'text/plain' }).end('Local preview error: ' + e.message);
  }
});

server.listen(8787, '127.0.0.1', () => {
  console.log('PoseWear local preview running at http://127.0.0.1:8787/');
});
