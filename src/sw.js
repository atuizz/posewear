const VERSION = 'posewear-development';
const PRECACHE = ['./','index.html','theme.js','style.css','i18n.js','catalog.js','references.js','palette.js','app.js','sketch.js','command-palette.js','zip.js','extras.js','image-providers.js','board-export.js','studio.js','history.js','favicon.svg'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(VERSION).then(cache => cache.addAll(PRECACHE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('posewear-') && key !== VERSION).map(key => caches.delete(key))
  )));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== location.origin || url.pathname.startsWith('/api/')) return;
  event.respondWith((async () => {
    const cache = await caches.open(VERSION);
    let response;
    try { response = await fetch(request); }
    catch (error) { return await cache.match(request) || Promise.reject(error); }
    if (response.ok && response.status === 200 && !response.redirected) {
      event.waitUntil(cache.put(request, response.clone()).catch(() => {}));
    }
    return response;
  })());
});
