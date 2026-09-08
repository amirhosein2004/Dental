# Frontend

No build step. No npm, no bundler, no framework — plain CSS and plain
JavaScript served by Django, because a clinic site that renders on the server
has nothing to hydrate and every build step is one more thing that can be
broken on a Friday.

Two rules cover most of it:

* **Nothing is loaded from a CDN.** Fonts, Font Awesome, Leaflet and Swiper are
  vendored under `src/static/`. No CDN is reliably reachable from Iran, and a
  page that waits on one is a page that hangs. `test_no_external_assets` in
  `apps/core/tests/test_hygiene.py` fails if a `https://…` asset link
  reappears.
* **Colours come from tokens, never from literals.** `design-system.css` is the
  single source of truth, and everything else consumes it.

## Where things live

```
src/static/css/     design-system.css   tokens + primitives, loaded first
                    navbar.css  footer.css  message.css  error_pages.css
src/static/js/      theme.js  navbar.js  base.js  message.js
                    dialogs.js  pwa.js  push.js  push-sw.js  math_captcha.js
src/static/vendor/  leaflet, swiper — vendored, not linked
src/static/fonts/   Vazirmatn (SIL OFL) and Font Awesome, self-hosted

src/apps/<app>/static/<app>/css/<page>.css     one file per page
src/templates/      base.html, navbar, footer, messages, errors, offline
src/apps/<app>/templates/<app>/               that app's pages
```

`base.html` loads the design system, the navbar and the footer for every page;
a page adds its own stylesheet in `{% block extra_static %}` and its scripts in
`{% block extra_js %}`. Site-wide scripts are already there — do not re-include
`theme.js` or `dialogs.js` from a page.

## Naming

The design system owns the `ds-` prefix: `ds-container`, `ds-section`,
`ds-btn`, `ds-card`, `ds-heading`, `ds-cta-card`. Reuse these before writing
anything. Buttons in particular: `ds-btn ds-btn--primary ds-btn--lg`, never a
new button style.

Page CSS is BEM under a short page prefix — `blg-hero__title`,
`site-footer__links`, `hero__mini--top`. The prefix is what keeps two pages
from colliding in a project with no scoping and no bundler.

`.form-control` and friends survive from Bootstrap, which is gone. The class
names stayed because 47 Django widgets declare them; the rules now live in
`design-system.css`. Adding a widget? Keep using `.form-control`.

## Themes

Light is the default and lives on bare `:root`. Dark is defined twice:

```css
:root[data-theme="dark"] { … }              /* explicit choice, set by theme.js */
@media (prefers-color-scheme: dark) {
    :root:not([data-theme]) { … }           /* system preference, no choice made */
}
```

So a colour must never be defined *only* inside one of those blocks — a token
that exists in dark and not in light renders as nothing at all.

The toggle stores `dental-theme` in `localStorage`; an inline script in
`base.html`'s `<head>` applies it **before the first stylesheet paints**. That
inline script is the reason there is no CSP header yet (see
[security.md](security.md)) and the reason there is no flash of the wrong
theme. Do not move it into a file.

Where a component needs a different colour in dark mode, prefer redefining a
token. `:root[data-theme="dark"] .thing { … }` overrides exist, but each one is
a rule that a system-preference visitor never gets — check the media block too.

## RTL

The document is `lang="fa" dir="rtl"`. Use **logical properties** everywhere:
`inset-inline-start`, `margin-inline`, `padding-block` — not `left`, `right`,
`margin-left`. Physical properties are correct once and wrong the moment a
mirrored context or an LTR field appears.

Latin input (phone, national code, social handles) sets `dir="ltr"` on the
input itself, and those placeholders stay Latin-only: a mixed Persian/Latin
placeholder reorders confusingly in an LTR box.

Dates shown to a patient are Jalali. Numbers in body copy are Persian digits.

## Breakpoints

Max-width, mobile last, and `.98` so nothing falls between two rules:

| | Width | Means |
|---|---|---|
| tablet | `max-width: 1023.98px` | the grid drops to one column |
| mobile | `max-width: 639.98px` | stacked, full-width actions |
| small | `max-width: 479.98px` | last-resort tightening |

`(min-width: 640px) and (max-width: 1023.98px)` is the tablet-only band, used
where a two-column grid leaves an odd card alone in a row.

Older files (`navbar.css`, `footer.css`) still carry `767.98` / `991.98` /
`1199.98` from the Bootstrap era. Leave them where they are unless you are
reworking that component; a half-converted file is worse than a consistent old
one. New CSS uses the three above.

The hero's floating badges are the standing example of why tablet layout is
tested by looking at it: the badges are positioned against `.hero__visual`, so
that box has to be *wider than the card inside it* or they land on top of the
artwork instead of overhanging its corners.

## Dialogs and toggles

**Never `window.confirm()`.** It renders an OS alert — Latin font, LTR, nothing
to do with the page. Destructive forms use the shared dialog:

```html
<form method="post" action="…" data-confirm
      data-confirm-title="حذف زمان" data-confirm-text="این زمان حذف شود؟">
```

`dialogs.js` delegates from `document`, so markup injected by an AJAX "load
more" works with no re-binding. A hygiene test fails the build if an inline
`confirm(` reappears.

**Toggle visibility with the `hidden` attribute**, and `el.hidden = false` in
JS. `design-system.css` carries `[hidden] { display: none !important }` because
the browser's own rule has the weakest possible specificity — any class rule
that sets `display` beats it. Dropping Bootstrap (whose reboot carried the
`!important` version) is what once left the "you've seen everything" note
showing next to a still-working "load more" button.

## PWA

The site is installable, and on iOS installing is the *precondition* for web
push — Safari hides the Push API from a normal tab.

| | Served from | Why the root |
|---|---|---|
| `/sw.js` | `notifications.views.push_view` | a worker's scope is its own directory |
| `/manifest.webmanifest` | same | `scope` defaults to where it is served |
| `/offline/` | a plain template | the one page the worker precaches |

The service worker intercepts **only failed navigations** and answers them with
the offline page. Form posts, the AJAX endpoints and static assets pass
straight through, and exactly one thing is ever precached — the public pages
already sit behind a 24-hour server-side cache, and a second HTML cache inside
the worker would make "why am I seeing yesterday's page" close to
undiagnosable.

`pwa.js` reveals the install button for anyone not already running the
installed app, and falls back to a platform-specific instructions dialog when
the browser hands over no install prompt (Safari never does; Chrome stops after
a dismissal). The button is hidden from signed-in staff — the installed app is
the patient's route back to booking, and the staff bar is full already.

## Adding a page

1. Template extends `base.html`, fills `title`, `meta_tags`, `content`.
2. One stylesheet at `apps/<app>/static/<app>/css/<page>.css`, linked from
   `{% block extra_static %}`.
3. Layout from `ds-container` / `ds-section`; buttons from `ds-btn`; colours
   from tokens.
4. Closing call to action: `{% include '_cta_actions.html' %}` — the same two
   actions in the same order on every page, rather than a new pair of buttons
   with new wording.
5. Check it at 375, 768 and desktop, in both themes, before calling it done.
