/* Service worker: staff push notifications, and the offline fallback that
   makes the site installable.

   Served from `/sw.js`, not from `/static/js/`. A worker's scope is capped by
   the directory it is served from, so one under `/static/` could only control
   `/static/…` — it would never receive a push, and Chrome would not count the
   site as installable. See `notifications.push_views.service_worker`.

   Deliberately does almost no caching. A service worker sits between every
   request and the network for its whole scope, and a caching mistake here is
   the hardest kind to undo: the thing serving stale pages is the same thing
   that would have to update itself. The public pages already carry a 24-hour
   server-side response cache, so a second layer in front of it would make
   "why is the site showing yesterday's article" close to undiagnosable.

   So: exactly one HTML page is cached — the offline fallback — and it is only
   ever served when a navigation fails outright. Every other request is passed
   straight through, untouched. */

var CACHE = 'clinic-shell-v1';
var OFFLINE_URL = '/offline/';

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE).then(function (cache) {
            // `reload` bypasses the HTTP cache so the precache never captures
            // a copy the browser happened to be holding from before a deploy.
            return cache.add(new Request(OFFLINE_URL, { cache: 'reload' }));
        }).catch(function () {
            // A failed precache must not abort installation: without the
            // worker there is no push either, and push is the more important
            // half of this file.
        })
    );
    // Take over without waiting for existing tabs to close, so a staff member
    // who just granted permission does not have to close every tab first.
    self.skipWaiting();
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys().then(function (names) {
            // Drop caches from older versions of this worker, so bumping
            // CACHE is all it takes to retire the previous shell.
            return Promise.all(names.map(function (name) {
                return name === CACHE ? null : caches.delete(name);
            }));
        }).then(function () {
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', function (event) {
    var request = event.request;

    // Only page navigations, and only GET. Leaving everything else alone means
    // form posts, the AJAX "load more" endpoints and every static asset behave
    // exactly as they would with no worker installed.
    if (request.mode !== 'navigate' || request.method !== 'GET') return;

    event.respondWith(
        fetch(request).catch(function () {
            // Network-first, with the cached page as a last resort. A 404 or a
            // 500 still reaches the visitor as itself — only a genuine network
            // failure lands here.
            return caches.match(OFFLINE_URL).then(function (cached) {
                return cached || new Response(
                    'اتصال اینترنت برقرار نیست',
                    { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }
                );
            });
        })
    );
});

self.addEventListener('push', function (event) {
    var payload = { title: 'مطب', body: '', url: '/', tag: 'clinic' };

    if (event.data) {
        try {
            payload = Object.assign(payload, event.data.json());
        } catch (e) {
            // A push service can wake the worker with no body at all (and some
            // send a plain string). Showing *something* beats a silent wake —
            // browsers revoke permission from workers that receive a push and
            // display nothing.
            payload.body = event.data.text() || 'اعلان جدید';
        }
    }

    event.waitUntil(
        self.registration.showNotification(payload.title, {
            body: payload.body,
            icon: '/static/img/site-logo.png',
            badge: '/static/img/site-logo.png',
            // Same tag replaces rather than stacks: a busy morning should not
            // bury the phone under identical banners.
            tag: payload.tag,
            renotify: true,
            dir: 'rtl',
            lang: 'fa',
            data: { url: payload.url }
        })
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    var target = (event.notification.data && event.notification.data.url) || '/';

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(function (list) {
                // Reuse a tab that is already on the site rather than opening a
                // third copy of the messages page.
                for (var i = 0; i < list.length; i++) {
                    var client = list[i];
                    if (client.url.indexOf(self.location.origin) === 0 && 'focus' in client) {
                        client.navigate(target);
                        return client.focus();
                    }
                }
                if (self.clients.openWindow) return self.clients.openWindow(target);
            })
    );
});
