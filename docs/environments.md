# Environments

Three, and no more. `DJANGO_ENV` names the settings module, so the value and
the filename are the same word.

| | Runs on | Settings | Database | Reaches patients? |
|---|---|---|---|---|
| **develop** | your machine | `config.settings.develop` | SQLite, or a container | no |
| **stage** | a test host | `config.settings.stage` | its own Postgres | **no** |
| **production** | the live server | `config.settings.production` | the real one | yes |

There is no separate "local" and no "test" environment. Test-time
configuration lives in `utils/test_runner.py` — those are properties of
running tests, not of a place to deploy.

## develop

Two ways to run it, and they need different infrastructure.

**On the laptop** — the default. SQLite, in-memory cache, Celery inline, mail
to `sent_emails/`. A fresh clone works with nothing installed.

```bash
python src/manage.py runserver
```

**In Docker** — when you need the real thing: a migration against Postgres, or
Celery actually queuing through Redis.

```bash
cp deploy/env/.env.develop.example deploy/env/.env.develop
docker compose --env-file deploy/env/.env.develop \
  -f deploy/base.yml -f deploy/develop.yml up
```

The switch between them is `USE_CONTAINER_SERVICES=1`, set only by the compose
env file. It is explicit rather than inferred from `DB_HOST` because the root
`.env` carries production values for exactly those variables.

## stage

Production's shape, none of its reach. Same gunicorn, same nginx, same
`DEBUG = False`, same hashed static files — so the bugs that only appear with
real infrastructure appear here first.

What `stage.py` forces, regardless of what the environment file says:

- **SMS to the console.** A staging run against a copied production database
  would otherwise text every real patient in it.
- **Email to a file.**
- **Media on local disk**, not the shared bucket — a test upload cannot
  overwrite a live one.
- **`X-Robots-Tag: noindex`** on every response, via middleware rather than a
  template, so it also covers JSON and error pages.
- **HSTS off.** A year-long header from a staging host pins that name to HTTPS
  in every tester's browser, including after the certificate is gone.

## production

The only environment that can spend money or reach a patient.

Three values cannot be rotated without consequences worth knowing first:

| Rotating it | Costs |
|---|---|
| `SECRET_KEY` | everyone is logged out |
| `OTP_SECRET_KEY` | in-flight login codes stop working |
| `VAPID_PRIVATE_KEY` | every staff device is silently unsubscribed |

## Env files

There are **four**, and which one applies depends on *how you start Django*,
not on which environment you think you are in. This is the thing that catches
people, so it is worth reading once:

| File | Read by | When |
|---|---|---|
| `.env` | `src/manage.py` | `python src/manage.py runserver` on your own machine |
| `deploy/env/.env.develop` | Docker Compose | the develop stack, in containers |
| `deploy/env/.env.stage` | Docker Compose | the stage host |
| `deploy/env/.env.production` | Docker Compose | the live server |

**Docker never reads the root `.env`.** Compose is given its file explicitly
with `--env-file`, and the containers get their values from `env_file:` in the
overlay. So editing `.env` and restarting a container changes nothing, and the
reverse is equally true.

The two are not duplicates of each other. They describe two different ways of
running the same code:

* `.env` — no Postgres, no Redis, no Celery worker. `develop.py` sees
  `USE_CONTAINER_SERVICES` unset and swaps in SQLite, a local-memory cache and
  inline Celery, so `runserver` works on a fresh clone with nothing installed.
* `deploy/env/.env.develop` — sets `USE_CONTAINER_SERVICES=1`, which is what
  makes the same settings module use the real containers.

Templates are committed; the filled-in versions never are.

```
.env.example
deploy/env/.env.develop.example
deploy/env/.env.stage.example
deploy/env/.env.production.example
```

The deploy ones live under `deploy/` rather than a top-level `env/` because
that name is already ignored as a virtualenv — and git does not descend into
an ignored directory, so no negation inside it can rescue a file.

### Empty is not the same as unset

Every example file lists keys with no value, so the shape of the file is
visible. That means settings routinely receive variables that are *present but
empty*, and neither `os.getenv(name, default)` nor `os.environ.setdefault`
handles that: both treat `''` as a real value and skip the default.

`base.py` has `_env()` and `develop.py` has `_setdefault()` for this. Use them
rather than the standard library calls when adding a setting with a default.

It is not a theoretical concern. `EMAIL_PORT=` in a file was enough to raise
`ValueError: invalid literal for int()` at import time and stop the project
booting, and a blank `VAPID_PUBLIC_KEY=` made five push tests fail on one
machine and pass on another.

## Adding a setting

1. Read it in `base.py` with `os.getenv`, and give it a safe default.
2. If it has no safe default, use `_required_env` — the app then refuses to
   start rather than running misconfigured.
3. Add it to all three `.example` files, with a comment saying what breaks if
   it is wrong.
