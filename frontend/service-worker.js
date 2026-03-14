const CACHE_NAME = 'vitin-v1';
const urlsToCache = [
    '/',
    '/aluno',
    '/styles.css',
    '/app.js',
    '/muscle-icons.js',
    '/manifest.json'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Network first, fallback to cache
                return fetch(event.request)
                    .then(networkResponse => {
                        // Update cache with fresh response
                        if (networkResponse && networkResponse.status === 200) {
                            const responseToCache = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => cache.put(event.request, responseToCache));
                        }
                        return networkResponse;
                    })
                    .catch(() => response); // Offline: use cache
            })
    );
});
