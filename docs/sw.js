/* 임베디드기사 CBT — 서비스 워커
 * 핵심: HTML/version.json은 network-first + {cache:'no-store'} 로 가져와
 *       브라우저 HTTP 캐시(GitHub Pages max-age=600)까지 우회 → 재배포 즉시 반영.
 *       오프라인일 때만 캐시 폴백. 이미지 등은 stale-while-revalidate.
 * 이 파일(VERSION)을 바꿔 배포하면 기존 탭은 새 워커 활성화 시 자동 새로고침.
 */
const VERSION = 'v16';
const CACHE = 'cbt-' + VERSION;
const SHELL = ['index.html', 'embedded.html', 'electric.html', 'gconsafety.html', 'version.json'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE);
      await cache.addAll(SHELL.map((u) => new Request(u, { cache: 'reload' })));
    } catch (_) { /* offline install — ignore */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

function isHtmlNav(req) {
  if (req.mode === 'navigate') return true;
  const a = req.headers.get('accept') || '';
  return req.method === 'GET' && a.includes('text/html');
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // HTML 문서 / version.json → 네트워크 우선, HTTP 캐시 우회
  if (isHtmlNav(req) || url.pathname.endsWith('/version.json') || url.pathname.endsWith('/index.html')) {
    e.respondWith((async () => {
      try {
        const fresh = await fetch(url.pathname + url.search, { cache: 'no-store' });
        const cache = await caches.open(CACHE);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (err) {
        return (await caches.match(req)) ||
               (await caches.match('index.html')) ||
               (await caches.match('./')) ||
               Response.error();
      }
    })());
    return;
  }

  // 그 외 동일 출처 GET(이미지 등) → stale-while-revalidate
  if (url.origin === self.location.origin) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(req);
      const network = fetch(req)
        .then((res) => { if (res && res.status === 200) cache.put(req, res.clone()); return res; })
        .catch(() => null);
      return cached || (await network) || Response.error();
    })());
  }
});
