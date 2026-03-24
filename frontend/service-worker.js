const CACHE_NAME = 'vitin-cache-v3';
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
            .then(cachedResponse => {
                if (cachedResponse) return cachedResponse;
                
                return fetch(event.request).then(response => {
                    // Cache fresh responses for static assets
                    if (response.status === 200 && (event.request.url.includes('.css') || event.request.url.includes('.js') || event.request.url.includes('.png'))) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
                    }
                    return response;
                });
            })
            .catch(() => {
                // Return index.html for navigation requests (SPA) if offline
                if (event.request.mode === 'navigate') {
                    return caches.match('/');
                }
            })
    );
});
