/* Mobile drawer + active-link highlighting for site-nav.

   The drawer is a fixed sheet over the page, so opening it has to do three
   things beyond flipping a class: show the backdrop that a tap-outside lands
   on, stop the page behind from scrolling (otherwise a swipe over the dim
   area moves the article underneath), and hide the backdrop from assistive
   tech and the tab order while it is closed. */
(function () {
    'use strict';

    function init() {
        const toggle = document.querySelector('[data-nav-toggle]');
        const menu = document.querySelector('[data-nav-menu]');
        const backdrop = document.querySelector('[data-nav-backdrop]');

        if (toggle && menu) {
            let scrollY = 0;

            function open() {
                // Remember the offset before the page is pinned: `position:
                // fixed` on <body> otherwise jumps the visitor to the top and
                // leaves them there when the drawer closes.
                scrollY = window.scrollY;
                menu.classList.add('is-open');
                toggle.setAttribute('aria-expanded', 'true');
                toggle.setAttribute('aria-label', 'بستن منو');

                if (backdrop) {
                    backdrop.hidden = false;
                    // Next frame, so the element is painted at opacity 0 first
                    // and the transition actually runs.
                    requestAnimationFrame(function () {
                        backdrop.classList.add('is-visible');
                    });
                }

                document.body.style.position = 'fixed';
                document.body.style.top = '-' + scrollY + 'px';
                document.body.style.width = '100%';
            }

            function close(returnFocus) {
                if (!menu.classList.contains('is-open')) return;

                menu.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.setAttribute('aria-label', 'باز کردن منو');

                if (backdrop) {
                    backdrop.classList.remove('is-visible');
                    // Kept in the DOM until the fade finishes, then taken out
                    // of the tab order — a transparent backdrop still swallows
                    // taps and still gets focused.
                    setTimeout(function () {
                        if (!menu.classList.contains('is-open')) backdrop.hidden = true;
                    }, 250);
                }

                document.body.style.position = '';
                document.body.style.top = '';
                document.body.style.width = '';

                // `html { scroll-behavior: smooth }` applies to this too, so
                // restoring the offset animated the whole page from the top
                // back down to where the reader had been — a long scroll they
                // never asked for. Put it back in one frame instead.
                const root = document.documentElement;
                const previousBehavior = root.style.scrollBehavior;
                root.style.scrollBehavior = 'auto';
                window.scrollTo(0, scrollY);
                root.style.scrollBehavior = previousBehavior;

                if (returnFocus) toggle.focus();
            }

            toggle.addEventListener('click', function () {
                if (menu.classList.contains('is-open')) close(false);
                else open();
            });

            if (backdrop) backdrop.addEventListener('click', function () { close(false); });

            const closeButton = menu.querySelector('[data-nav-close]');
            if (closeButton) {
                closeButton.addEventListener('click', function () { close(true); });
            }

            // Following a link inside the drawer navigates away; leaving the
            // sheet open means the next page paints behind a locked body.
            menu.querySelectorAll('a[href]').forEach(function (link) {
                link.addEventListener('click', function () { close(false); });
            });

            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') close(true);
            });

            // Rotating to landscape can cross the breakpoint, at which point
            // the sheet is no longer fixed but the body is still pinned.
            window.addEventListener('resize', function () {
                if (window.innerWidth >= 992) close(false);
            });
        }

        // Highlight the link matching the current path.
        const here = window.location.pathname.replace(/\/+$/, '') || '/';
        document.querySelectorAll('.site-nav__link').forEach(function (link) {
            const href = (link.getAttribute('href') || '').replace(/\/+$/, '') || '/';
            if (href === here) link.classList.add('is-active');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
