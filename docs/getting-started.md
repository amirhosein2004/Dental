# Getting started

## Requirements

Python 3.12. Nothing else is needed for the default setup — no Postgres, no
Redis, no message broker. `develop` settings fall back to SQLite and
in-memory everything precisely so that a fresh clone runs.

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # macOS / Linux

pip install -r requirements.txt

cp .env.example .env             # then edit — see below
python src/manage.py migrate
python src/manage.py createsuperuser
python src/manage.py runserver
```

`DJANGO_ENV` in `.env` decides which settings module loads. It defaults to
`develop`, so `runserver` and `manage.py test` need no `--settings` flag.

### The `.env` in the root is for this — running Django directly

It is read by `src/manage.py` and by nothing else. **Docker does not use it.**
Each container environment has its own file under `deploy/env/`, handed to
Compose with `--env-file`.

| Running | Reads |
|---|---|
| `python src/manage.py runserver` | `.env` |
| the develop stack in Docker | `deploy/env/.env.develop` |
| stage / production | `deploy/env/.env.stage` / `.env.production` |

They are not copies of each other. `.env` describes a machine with no
Postgres, no Redis and no Celery worker: `develop.py` sees
`USE_CONTAINER_SERVICES` unset and substitutes SQLite, a local-memory cache
and inline Celery, so a fresh clone runs with nothing installed. The develop
stack sets that variable to `1`, which is what makes the same settings module
talk to the containers.

Editing one and restarting the other explains nothing changing — see
[environments.md](environments.md#env-files).

### What you must set in `.env`

Three values have no safe default and the app refuses to start without them:

| | Why it cannot be random per restart |
|---|---|
| `SECRET_KEY` | signs sessions — a new one logs everyone out |
| `OTP_SECRET_KEY` | signs the half-finished login token |
| `SECURE_ADMIN_PANEL` | the admin URL, which is deliberately not `/admin/` |

`develop.py` fills these with fixed insecure values, so a local run works
without touching them. Any real host must set its own.

## Demo data

```bash
python src/manage.py seed_demo          # realistic Persian content
python src/manage.py seed_demo --keep   # add to what is there instead of replacing
```

Gives you doctors, services, articles, galleries, tariffs and contact messages
— enough that the pages look like a real site rather than empty shells.

## Day-to-day

```bash
python src/manage.py test                    # 500+ tests, ~7s
python src/manage.py test apps.contact       # one app
python src/manage.py check --deploy          # security audit
python src/manage.py backup_db               # dump, keeping the newest 3
```

## Reading email and OTP codes locally

`develop` writes mail to `sent_emails/` instead of sending it. Logging in as a
doctor needs the one-time code from that folder — open the newest file.

This is not only convenience: the console backend cannot print Persian on a
Windows terminal (cp1256 raises `UnicodeEncodeError`), which used to surface
as a 500 on the login step.

## Running against real Postgres and Redis

When you need to test something the SQLite fallback cannot show — a migration
against Postgres, or Celery actually queuing:

```bash
cp deploy/env/.env.develop.example deploy/env/.env.develop
docker compose --env-file deploy/env/.env.develop \
  -f deploy/base.yml -f deploy/develop.yml up
```

See [environments.md](environments.md).

## If something is wrong

**Pages show old content.** The public pages cache for 24 hours. A write
should invalidate them automatically — if it does not, that is a bug worth
reporting, not a cache to clear by hand. See [caching.md](caching.md).

**Styles look broken after pulling.** Your browser is holding the old CSS.
Ctrl+Shift+R. In production this cannot happen: filenames are content-hashed.

**A staff page 404s.** That is the correct answer for someone who is not
signed in as staff — the routes do not confirm they exist. Check you are
logged in.

**Login says "too many attempts".** Five wrong passwords from one IP for one
username locks that pair for fifteen minutes. Clear it with:
`python src/manage.py shell -c "from django.core.cache import cache; cache.clear()"`
