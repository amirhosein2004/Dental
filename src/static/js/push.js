/* Staff-side "turn on notifications" control.

   Drives any element carrying `data-push-toggle`, and reports state into a
   sibling `[data-push-status]`. The button is only rendered for staff, but the
   endpoints it calls check permissions themselves — this file is a
   convenience, never the access control. */
(function () {
    'use strict';

    var SW_URL = '/sw.js';

    function urlBase64ToUint8Array(base64String) {
        // VAPID keys travel as URL-safe base64 without padding; subscribe()
        // wants raw bytes.
        var padding = new Array((4 - (base64String.length % 4)) % 4 + 1).join('=');
        var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        var raw = window.atob(base64);
        var output = new Uint8Array(raw.length);
        for (var i = 0; i < raw.length; ++i) output[i] = raw.charCodeAt(i);
        return output;
    }

    /* The CSRF token, from the page rather than from `document.cookie`.

       `CSRF_COOKIE_HTTPONLY = True` in production settings — and stage
       inherits it — so `document.cookie` cannot see `csrftoken` at all there.
       Reading it from the cookie returned an empty string, and every
       subscribe / unsubscribe POST came back 403: the button said
       "فعال‌سازی ناموفق بود", no row was ever written, and every later push
       reported "0 sent, 0 failed" because there was nothing to send to.
       Development has HTTPONLY off, which is why this only ever broke on the
       deployed site.

       The template renders `data-csrf` from `{{ csrf_token }}`; the cookie
       stays as a fallback for a cached page served before that attribute
       existed. */
    function csrf(button) {
        var attr = button && button.getAttribute('data-csrf');
        if (attr) return attr;
        var hidden = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (hidden && hidden.value) return hidden.value;
        var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }

    function init() {
        var button = document.querySelector('[data-push-toggle]');
        if (!button) return;

        var card = document.querySelector('[data-push-card]');
        var status = document.querySelector('[data-push-status]');
        var label = button.querySelector('[data-push-label]');
        var icon = button.querySelector('[data-push-icon]');
        var stateLabel = document.querySelector('[data-push-state-label]');
        var publicKey = button.getAttribute('data-vapid-key') || '';

        function say(text, tone) {
            if (!status) return;
            status.textContent = text;
            status.dataset.tone = tone || '';
        }

        /* One place decides how the card looks. The card's `data-state` drives
           the tint, the bell, the pill and the button styling from CSS, so the
           visual state can never drift from the button's label. */
        function setState(state) {
            if (card) card.dataset.state = state;

            var on = state === 'on';
            if (label) label.textContent = on ? 'خاموش کردن اعلان' : 'فعال‌سازی اعلان';
            if (icon) icon.className = on ? 'fas fa-bell-slash' : 'fas fa-bell';
            if (stateLabel) {
                stateLabel.textContent =
                    state === 'on' ? 'روشن' :
                    state === 'blocked' ? 'مسدود' : 'خاموش';
            }
            button.dataset.subscribed = on ? '1' : '';
        }

        function isIOS() {
            // iPadOS reports itself as a Mac, so the touch-point count is what
            // separates an iPad from a desktop Safari.
            return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
                (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
        }

        function isStandalone() {
            return window.matchMedia('(display-mode: standalone)').matches ||
                window.navigator.standalone === true;
        }

        function unsupportedReason() {
            if (!window.isSecureContext) return 'اعلان فقط روی HTTPS کار می‌کند';
            if (!publicKey) return 'کلید اعلان روی سرور تنظیم نشده است';

            // Safari hides the Push API from a normal tab entirely; it appears
            // only once the site has been added to the Home Screen and is
            // launched from there. Saying "your browser does not support this"
            // would be both wrong and a dead end, so name the one step that
            // actually turns it on.
            if (isIOS() && !isStandalone()) {
                return 'برای فعال کردن اعلان روی آیفون: دکمه‌ی اشتراک‌گذاری ' +
                    '(مربع با فلش) را بزنید، «Add to Home Screen» را انتخاب کنید، ' +
                    'سپس سایت را از همان آیکون باز کنید و دوباره اینجا برگردید.';
            }

            if (!('serviceWorker' in navigator)) return 'مرورگر شما از این قابلیت پشتیبانی نمی‌کند';
            if (!('PushManager' in window)) return 'مرورگر شما از اعلان وب پشتیبانی نمی‌کند';
            return null;
        }

        var blocked = unsupportedReason();
        if (blocked) {
            button.disabled = true;
            setState('blocked');
            say(blocked, 'muted');
            return;
        }

        if (Notification.permission === 'denied') {
            button.disabled = true;
            setState('blocked');
            say('اعلان‌ها در تنظیمات مرورگر مسدود شده‌اند — از تنظیمات سایت در مرورگر دوباره اجازه دهید', 'muted');
            return;
        }

        setState('off');

        // Reflect the state this browser is already in, so the button does not
        // invite someone to enable what is already on.
        navigator.serviceWorker.getRegistration(SW_URL).then(function (registration) {
            if (!registration) return;
            registration.pushManager.getSubscription().then(function (existing) {
                if (existing) {
                    setState('on');
                    say('این دستگاه اعلان دریافت می‌کند', 'ok');
                }
            });
        });

        button.addEventListener('click', function () {
            if (button.dataset.subscribed === '1') unsubscribe();
            else subscribe();
        });

        function subscribe() {
            button.disabled = true;
            say('در حال فعال‌سازی…', '');

            Notification.requestPermission().then(function (permission) {
                if (permission !== 'granted') {
                    say('اجازه‌ی نمایش اعلان داده نشد', 'muted');
                    return null;
                }

                // `scope: '/'` is the whole reason the worker is served from
                // the site root rather than from /static/.
                return navigator.serviceWorker.register(SW_URL, { scope: '/' })
                    .then(function (registration) {
                        return navigator.serviceWorker.ready.then(function () {
                            return registration.pushManager.subscribe({
                                // Chrome refuses a subscription that could be
                                // used to wake the device silently.
                                userVisibleOnly: true,
                                applicationServerKey: urlBase64ToUint8Array(publicKey)
                            });
                        });
                    })
                    .then(function (subscription) {
                        var raw = subscription.toJSON();
                        return fetch(button.getAttribute('data-subscribe-url'), {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrf(button)
                            },
                            body: JSON.stringify({
                                endpoint: raw.endpoint,
                                p256dh: raw.keys.p256dh,
                                auth: raw.keys.auth
                            })
                        });
                    })
                    .then(function (response) {
                        if (!response.ok) throw new Error('HTTP ' + response.status);
                        setState('on');
                        say('این دستگاه اعلان دریافت می‌کند', 'ok');
                    });
            }).catch(function (error) {
                console.error('push subscribe failed:', error);
                say('فعال‌سازی اعلان ناموفق بود', 'error');
            }).then(function () {
                button.disabled = false;
            });
        }

        function unsubscribe() {
            button.disabled = true;

            navigator.serviceWorker.getRegistration(SW_URL).then(function (registration) {
                return registration ? registration.pushManager.getSubscription() : null;
            }).then(function (subscription) {
                if (!subscription) return null;
                var endpoint = subscription.endpoint;
                return subscription.unsubscribe().then(function () {
                    // Tell the server too, or it keeps pushing to an endpoint
                    // the browser has already forgotten.
                    return fetch(button.getAttribute('data-unsubscribe-url'), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrf(button)
                        },
                        body: JSON.stringify({ endpoint: endpoint })
                    });
                });
            }).then(function () {
                setState('off');
                say('اعلان روی این دستگاه خاموش شد', 'muted');
            }).catch(function (error) {
                console.error('push unsubscribe failed:', error);
                say('خاموش کردن اعلان ناموفق بود', 'error');
            }).then(function () {
                button.disabled = false;
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
