// Service worker — mise en cache de l'agenda pour un accès hors connexion.
// À placer dans le même dossier que index.html sur GitHub (ex: /agenda/sw.js)

const CACHE_NAME = 'synalojik-agenda-v1'; // change ce numéro (v2, v3...) à chaque grosse mise à jour pour forcer le rafraîchissement
const URLS_TO_CACHE = [
  '/agenda/',
  '/agenda/index.html',
  '/agenda/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  // Ne jamais intercepter les appels vers Google (auth / Drive / fonts) — on les laisse échouer
  // normalement hors connexion, l'app gère déjà ce cas côté JS.
  if (req.url.includes('google') || req.url.includes('gstatic')) return;

  event.respondWith(
    caches.match(req).then((cached) => {
      const fetchPromise = fetch(req)
        .then((networkResp) => {
          if (networkResp && networkResp.status === 200) {
            const respClone = networkResp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, respClone));
          }
          return networkResp;
        })
        .catch(() => cached); // hors ligne → on sert la version en cache
      // Sert le cache immédiatement si dispo, tout en revalidant en tâche de fond
      return cached || fetchPromise;
    })
  );
});
