# 🦷 SB Dental — clinic website and booking system

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2_LTS-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.4-37B24D?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**The public site and staff panel for a two-practice dental clinic in Mashhad
and Quchan — Persian, RTL, installable as an app.**

[🌐 Live](https://sbdental.ir) • [📖 Docs](docs/) • [🚀 Quick start](#quick-start)

</div>

---

## What it does

**For patients** — a public site: the clinic and both practices, the doctors
and their CVs, treatments, tariffs, a before/after gallery, articles, a contact
form, and online booking with no account to create.

**For the clinic** — a staff panel behind a two-step login: each doctor edits
their own content and schedule, the front desk sees the week's bookings and the
message inbox, and a superuser sees everything. Alerts arrive by SMS and as
browser notifications.

Booking is a **weekly recurring template**, not a calendar: a doctor publishes
"Saturday 20:00", a patient claims it for the current week, and the schedule
empties itself when the week turns over — no cron job involved. See
[docs/appointments.md](docs/appointments.md).

Notable choices, each with its reasons written down in `docs/`:

- **Two roles, no permission tables** — `is_doctor` and `is_superuser`, one
  ownership rule, and staff routes that answer 404 rather than 403.
- **Two-step login** — password, then a six-digit emailed code, with a
  Redis-backed throttle keyed on (IP, username).
- **Self-hosted everything** — fonts, icons, Leaflet, Swiper, and a
  hand-rolled math captcha. No CDN is reliably reachable from Iran, and a test
  fails if a `https://` asset link reappears.
- **Day-long response caching** with group-versioned invalidation, so a write
  that changes a page busts it.
- **Installable PWA** — which on iOS is the precondition for web push, not a
  nicety.

## Stack

| | |
|---|---|
| Django 5.2 LTS · Python 3.12 · Gunicorn | PostgreSQL 17 |
| Celery 5.4 (SMS, email, push, cleanup) | Redis 7 — cache, throttle, broker |
| nginx · Docker Compose · GitLab CI | Kavenegar (SMS) · VAPID web push |

No frontend build step: plain CSS and JavaScript on a design-token system, so
there is no npm, no bundler and nothing to compile before a deploy.

## Quick start

Python 3.12 and nothing else — `develop` settings fall back to SQLite,
in-memory cache and inline Celery so a fresh clone runs.

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # DJANGO_ENV defaults to `develop`
python src/manage.py migrate
python src/manage.py seed_demo    # optional: realistic Persian demo content
python src/manage.py createsuperuser
python src/manage.py runserver
```

Then <http://127.0.0.1:8000>. Logging in as a doctor needs the emailed OTP —
in develop, mail is written to `sent_emails/`; open the newest file.

Real Postgres, Redis and a Celery worker, in containers:

```bash
cp deploy/env/.env.develop.example deploy/env/.env.develop
docker compose --env-file deploy/env/.env.develop \
  -f deploy/base.yml -f deploy/develop.yml up
```

## Day to day

```bash
python src/manage.py test                    # ~500 tests, ~7s
python src/manage.py test apps.contact       # one app
python src/manage.py check --deploy          # security audit
python src/manage.py backup_db               # dump, keeping the newest 3
```

## Layout

```
src/            the application — nothing else
  apps/         fourteen apps, split by subject rather than by layer
  config/       settings (develop / production), urls, celery
  utils/        cross-app helpers: security, http, data, mail
  static/  templates/  manage.py
deploy/         compose overlays, nginx, entrypoint, env templates
scripts/        backup, restore, superuser, TLS, cron
docs/           everything below
```

## Documentation

| | |
|---|---|
| [getting-started.md](docs/getting-started.md) | clone to running site |
| [architecture.md](docs/architecture.md) | the apps and how they fit |
| [environments.md](docs/environments.md) | develop / production |
| [deploying.md](docs/deploying.md) | **step by step, first deploy to rollback** |
| [cicd.md](docs/cicd.md) | the GitLab pipeline |
| [caching.md](docs/caching.md) | what is cached, what invalidates it |
| [security.md](docs/security.md) | the controls and why each exists |
| [appointments.md](docs/appointments.md) | the booking system |
| [notifications.md](docs/notifications.md) | SMS and web push |
| [frontend.md](docs/frontend.md) | design system, themes, RTL, the PWA |
| [seo.md](docs/seo.md) | ساختار داده، سایت‌مپ و دیده‌شدن در جست‌وجو |
| [testing.md](docs/testing.md) | running and writing tests |
| [operations.md](docs/operations.md) | backups, deploys, common problems |

Runbooks live beside what they describe: [`deploy/README.md`](deploy/README.md)
for bringing a stack up, [`scripts/README.md`](scripts/README.md) for backups
and restores.

## A note on the comments

Comments in this codebase explain *why*, not *what* — usually by naming the bug
that made the line necessary. When something looks over-careful, the comment
above it says which incident it came from. Read that before simplifying it
away.

## License

See [LICENSE](LICENSE).
