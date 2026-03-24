const CACHE_NAME = 'vitin-cache-v4';
const urlsToCache = [
    '/',
    '/aluno',
    '/styles.css',
    '/app.js',
    '/aluno.js',
    '/muscle-icons.js',
    '/manifest.json'
];

self.addEventListener('install', event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(keys.map(key => {
                if (key !== CACHE_NAME) return caches.delete(key);
            }));
        })
    );
});

self.addEventListener('fetch', event => {
    // Não interceptar navegação para /aluno/ se não estiver no cache
    if (event.request.mode === 'navigate' && event.request.url.includes('/aluno/')) {
        return; // Deixa o navegador ir direto para o servidor
    }

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                if (cachedResponse) return cachedResponse;
                
                return fetch(event.request).then(response => {
                    // Cache fresh responses for static assets only
                    const url = event.request.url;
                    const isStatic = url.includes('.css') || url.includes('.js') || url.includes('.png') || url.includes('.webp');
                    
                    if (response.status === 200 && isStatic) {
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseToCache));
                    }
                    return response;
                });
            })
            .catch(() => {
                // Removemos o fallback para '/' que causava o erro do professor
                return fetch(event.request);
            })
    );
});
