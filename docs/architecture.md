# Architecture

A Django monolith. One database, one deployable, fourteen apps split by what
they are *about* rather than by technical layer.

```
request ──▶ nginx ──▶ gunicorn ──▶ Django ──┬──▶ Postgres
                                            ├──▶ Redis   (cache, throttle, queue)
                                            └──▶ Celery  (SMS, email, push, cleanup)
```

## The apps

| App | Owns | Public? |
|---|---|---|
| `home` | landing page, pulls previews from five other apps | yes |
| `about` | clinic profile, working hours — singleton rows | yes |
| `service` | treatments offered | yes |
| `pricing` | tariffs, grouped by category | yes |
| `blog` | articles, rich text | yes |
| `gallery` | before/after sets, one gallery holds many images | yes |
| `appointments` | weekly recurring slots, patient booking | yes |
| `contact` | the public form and the staff inbox | both |
| `accounts` | login, OTP, password reset | staff |
| `dashboard` | a doctor's own panel; `Doctor` profile model | staff |
| `doctors` | the public CV page per doctor, and the roster | yes |
| `users` | `CustomUser` — the model only, no screens | — |
| `core` | shared `Category`, the staff landing panel, cache signals | staff |
| `notifications` | SMS console, web push, contact groups | staff |
| `utils` | cross-app helpers (not a Django app) | — |

## Repository layout

Two layers, and the split is the point: `src/` is what runs, everything
beside it is how it is built, shipped and explained.

```
src/                   the application — nothing else
  apps/                the fourteen applications below
  config/              settings, urls, wsgi, asgi, celery
  utils/               cross-app helpers (not a Django app)
  static/  templates/
  manage.py

deploy/                compose overlays, nginx, entrypoint, env examples
scripts/               backup, restore, superuser, cron
docs/                  this
Dockerfile  requirements.txt  README.md  LICENSE
```

`src/` here is not the packaging convention of the same name — this is an
application, not a library, so that problem does not arise. It is drawn for
one reason: `utils/` and `templates/` sitting at the root next to `Dockerfile`
and `deploy/` gave no line between the code and the machinery around it.

Two consequences worth knowing:

* **The image contains only `src/`.** `COPY src/ /app/` — so `deploy/`,
  `docs/` and `scripts/` are not inside the running container. The entrypoint
  is copied separately to `/usr/local/bin/`, outside `/app`, because the
  develop overlay mounts the source over `/app` and anything the image put
  there would disappear behind that mount.
* **`/app` inside the container *is* `src/`.** So `manage.py` is still at
  `/app/manage.py`, and every command that runs inside a container is
  unchanged by the move.

`apps/` exists so the root holds infrastructure rather than fourteen app
directories mixed in with it. It is a plain package, not a Django concept.

Each app's `AppConfig.name` is its dotted path (`apps.blog`), but Django takes
the *label* from the last component — so the label stays `blog`, and every
migration, `AUTH_USER_MODEL = 'users.CustomUser'` and `to='dashboard.doctor'`
reference is unaffected by the grouping.

A new app goes in the same place:

```bash
mkdir src/apps/newthing
python src/manage.py startapp newthing src/apps/newthing
# then set `name = 'apps.newthing'` in its apps.py, and add
# 'apps.newthing' to INSTALLED_APPS
```

The `name` line is the step that is easy to miss: `startapp` writes the bare
label, and Django then fails to import the app from a path that no longer
matches.

`config/` rather than the project name: it says what the directory is for, and
it does not have to be renamed if the project ever is.

## Shape of an app

Every app follows the same layout. Where a real public/staff boundary exists,
the split follows it — that is the line that matters when reading, because one
side is reachable by anyone and the other is behind a permission gate.

```
src/apps/contact/
  models.py
  forms.py
  urls.py
  views/
    __init__.py
    contact_view.py       public: the form, captcha, honeypot, rate limit
    messages_view.py      staff: inbox, filters, cleanup
  tests/
    test_form.py
    test_messages_view.py
  templates/  static/
```

Small apps keep one module inside the package rather than pretending to a
split. The rule: **over ~300 lines, split; under, one file.** A package with
one file inside is still the right shape — the next file added is a new file,
not a refactor.

## `utils/`, grouped by why you would open it

```
utils/
  security/   login throttle, auth backend, signed OTP tokens,
              HTML sanitiser, math captcha
  http/       view mixins (permissions, rate limit), response caching
  data/       field validators, social handle conversion
  mail/       email helper and its Celery task
  test_runner.py
```

## Two roles, no permission system

`is_doctor` and `is_superuser` on `CustomUser`. `has_perm` is overridden to
return `is_superuser` and ignore Django's permission tables entirely — do not
assume groups or per-object permissions work, because they do not.

Ownership is one function, `utils.http.mixins.user_owns`:

- superusers may act on anything
- a doctor may act only on their own content
- orphaned content (owner deleted) is superuser-only

Staff routes answer **404, not 403**, to anyone who should not be there. A 403
confirms the route exists and, worse, that the object id is real.

## Things that will surprise you

**No `/admin/`.** The admin lives at whatever `SECURE_ADMIN_PANEL` says.

**The `Doctor` model lives in `dashboard`, not in `doctors`.** `doctors` is
only the public half — the roster and one CV page per doctor. The split is
along the line that matters for search: `/dashboard/` is staff-only and
noindexed, while these pages are the ones most meant to be found. Moving the
model would rewrite every `to='dashboard.doctor'` reference for no gain.

**Bookings are a weekly template, not a calendar.** A slot is "Saturday 20:00",
and a booking is stamped with the Saturday that opens its week — so the
schedule empties itself with no cron job. See
[appointments.md](appointments.md).

**Blog content is rendered with `|safe`** and sanitised on the way *in*, in
`BlogPost.save()`. The CKEditor config's `disallow` list is editor
configuration, not a server-side check.

**Everything is self-hosted** — fonts, Font Awesome, Leaflet, Swiper. No CDN
is reachable enough from Iran to depend on. A test enforces this
(`apps/core/tests/test_hygiene.py`).

**The site is an installable PWA.** `/sw.js` and `/manifest.webmanifest` are
served from the root, not `/static/`, because both are scope-limited to the
directory they come from. On iOS, installing is the *precondition* for
notifications — Safari hides the Push API from a normal tab.

**Bootstrap is gone.** `.form-control` and friends are defined in
`static/css/design-system.css`; the class names stayed so 47 Django widgets
did not have to change.
