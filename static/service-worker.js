self.addEventListener('install', function(event) {
    // Basic service worker install
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    // Basic service worker activation
});

self.addEventListener('fetch', function(event) {
    // Basic fetch passing through (currently no offline caching to avoid breaking things)
    event.respondWith(fetch(event.request));
});
