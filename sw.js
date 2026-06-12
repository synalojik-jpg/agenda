const CACHE_NAME = 'synalojik-v1';
const URLS_TO_CACHE = [
  '/agenda/',
  '/agenda/index.html',
  '/agenda/manifest.json',
  'https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap',
  'https://apis.google.com/js/api.js',
  'https://accounts.google.com/gsi/client'
];

// Installation : mise en cache
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(URLS_TO_CACHE).catch(err => console.log('Cache partiel:', err));
    })
  );
  self.skipWaiting();
});

// Activation : nettoyage anciens caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch : cache d'abord, réseau ensuite
self.addEventListener('fetch', event => {
  // Ne pas intercepter les requêtes Google API (Drive, Auth)
  if (event.request.url.includes('googleapis.com') ||
      event.request.url.includes('accounts.google.com')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});
