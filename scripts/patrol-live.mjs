#!/usr/bin/env node
/**
 * Live site health patrol for PoseWear (used by scheduled GitHub Actions & manual checks).
 * Verifies home page + CSP, /api/proxy CORS preflight, all 12 fingerprinted catalogs,
 * and sample R2 / same-origin / hotlink image availability.
 */

import { catalogIndex, catalogNames, publishedSite, readCatalog } from './catalog-source.mjs';

const SITE = (process.env.POSEWEAR_SITE || publishedSite).replace(/\/?$/, '/');

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

async function headOk(url, label) {
  const res = await fetch(url, { method: 'HEAD', signal: AbortSignal.timeout(15000) });
  assert(res.ok, `${label} failed (${res.status}): ${url}`);
  return res.status;
}

async function main() {
  const checks = [];

  // 1. Home page & CSP header
  const homeRes = await fetch(SITE, { signal: AbortSignal.timeout(20000) });
  assert(homeRes.status === 200, `Home returned HTTP ${homeRes.status}`);
  const csp = homeRes.headers.get('content-security-policy') || '';
  assert(csp.includes("img-src") && csp.includes("connect-src"), 'Home response missing CSP img-src/connect-src');
  checks.push(`Home 200 OK (CSP present)`);

  // 2. /api/proxy CORS preflight
  const proxyRes = await fetch(new URL('/api/proxy', SITE), {
    method: 'OPTIONS',
    headers: { Origin: new URL(SITE).origin },
    signal: AbortSignal.timeout(15000),
  });
  assert(proxyRes.status === 204, `/api/proxy OPTIONS returned HTTP ${proxyRes.status} (expected 204)`);
  checks.push(`/api/proxy OPTIONS 204 OK`);

  // 3. Discover and verify all 12 fingerprinted catalogs
  const index = await catalogIndex(SITE);
  const counts = {};
  let samplePoseThumb = null;
  let samplePoseMid = null;
  let sampleHotlink = null;

  for (let i = 0; i < catalogNames.length; i += 4) {
    await Promise.all(catalogNames.slice(i, i + 4).map(async name => {
      const { items } = await readCatalog(index, name);
      assert(items.length > 0, `Catalog ${name} is empty`);
      counts[name] = items.length;
      if (name === 'poses' && items[0]?.angles?.[0]) {
        samplePoseThumb = new URL(items[0].angles[0].t, index.assetHost).href;
        samplePoseMid = new URL(items[0].angles[0].i, index.site).href;
      }
      if (name === 'hair') {
        const ext = items.find(it => typeof it.t === 'string' && it.t.startsWith('https://'));
        if (ext) sampleHotlink = ext.t;
      }
    }));
  }
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  checks.push(`12 catalogs verified (${total.toLocaleString('en-US')} total entries)`);

  // 4. Sample image delivery across R2, same-origin, and hotlink
  if (samplePoseThumb) {
    await headOk(samplePoseThumb, 'R2 thumbnail');
    checks.push(`R2 thumb 200 OK`);
  }
  if (samplePoseMid) {
    await headOk(samplePoseMid, 'Same-origin mid image');
    checks.push(`Same-origin mid 200 OK`);
  }
  if (sampleHotlink) {
    await headOk(sampleHotlink, 'Hotlink image');
    checks.push(`Hotlink image 200 OK`);
  }

  console.log('PATROL_PASS');
  for (const line of checks) console.log(' -', line);
}

main().catch(err => {
  console.error('PATROL_FAIL:', err.message);
  process.exit(1);
});
