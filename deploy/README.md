# Deployment

Two environments, one image. What changes between them is the environment
file and the compose overlay — never the image — so what develop proved is the
thing production runs.

| | Where | Settings | Database | Reaches patients? |
|---|---|---|---|---|
| **develop** | your machine | `config.settings.develop` | throwaway container | no — SMS and email are stubbed |
| **production** | the live server | `config.settings.production` | the real one | yes |

There is no separate "local": `python src/manage.py runserver` with
`DJANGO_ENV=develop` is still the fastest way to work, and nothing here
replaces it. Reach for the develop stack when you need real Postgres or a real
Celery worker.

---

## What is in here, and what is not

`deploy/` describes **how the stack is assembled**: the compose overlays, the
nginx configs, the env templates, and `entrypoint.sh` — which is copied into
the image and run by every container on start.

Anything a *person* runs on a server lives in
[`../scripts/`](../scripts/README.md) instead: backups, restores, the first
superuser, the first TLS certificate. The line is who invokes it, not what
language it is written in.

---

## First run

```bash
cp deploy/env/.env.develop.example deploy/env/.env.develop
# production: same, then fill in every CHANGE-ME
```

Compose is run **from the repo root**, so the build context includes the
project:

```bash
# develop
docker compose --env-file deploy/env/.env.develop \
  -f deploy/base.yml -f deploy/develop.yml up

# production
docker compose --env-file deploy/env/.env.production \
  -f deploy/base.yml -f deploy/production.yml up -d
```

`--env-file` is not optional: `COMPOSE_PROJECT_NAME` lives in it, and that is
what keeps each environment's containers and volumes separate. Without it,
bringing up production would reuse develop's database volume.

---

## What happens on `up`

`deploy/entrypoint.sh` runs before every process:

1. waits for Postgres to accept connections — `depends_on` only waits for the
   container to *start*
2. `migrate` (web container only, so two containers cannot race)
3. `collectstatic` (web container only)
4. hands off to gunicorn, runserver, or celery

Nothing to remember, nothing to forget.

---

## Production: first certificate

nginx will not start without one, so issue it while the stack is up on port 80:

```bash
docker compose --env-file deploy/env/.env.production \
  -f deploy/base.yml -f deploy/production.yml \
  run --rm --entrypoint "certbot certonly --webroot -w /var/www/certbot \
    -d sbdental.ir -d www.sbdental.ir \
    --email you@example.com --agree-tos --no-eff-email" certbot

docker compose ... restart nginx
```

The `certbot` service then renews on a loop. Let's Encrypt only acts inside
the last 30 days, so the twelve-hour wake-ups cost nothing.

---

## Common tasks

The [`Makefile`](../Makefile) at the repository root wraps every one of these
so the env file and the overlay cannot drift apart. `ENV` selects both:

```bash
make ENV=production superuser
make ENV=production logs-web
make ENV=production backup
make ENV=production manage ARGS="generate_vapid_keys"
```

Deploying a change, from the laptop:

```bash
make ship        # git archive | ssh | tar, then build on the server
```

The server is in Iran and reaches neither GitHub, GitLab nor Docker Hub, so it
can neither pull the code nor pull a prebuilt image — `scripts/ship.sh` pushes
the commit to it over SSH and builds it there, against the mirrors set in
`env/.env.production`.

Already on the server, for an env-only change:

```bash
make ENV=production up         # no rebuild needed
make ENV=production up-build   # after a code change: the code is baked into
                               # the image, so editing a file changes nothing
                               # until it is rebuilt
```

---

## If production is on Liara

Then `production.yml` and `nginx/production.conf` are unused — Liara
terminates TLS, runs the proxy and serves static itself. What still applies:

- `config/settings/production.py`, unchanged
- the variables in `deploy/env/.env.production.example`, set in Liara's panel
- `develop.yml`, which works the same either way

You would add a `liara.json` naming the platform, the Python version and the
`DJANGO_ENV=production` variable. Everything else here stays as-is.

---

## Notes

**Redis holds four things**: the response cache, rate-limit counters, the login
throttle and the Celery queue. It is configured `allkeys-lru` with no
persistence — a full instance evicts cold cache entries rather than refusing
writes, which would take the site down since the response cache sits on the
request path. Losing it on restart costs a cold cache and nothing else.

**`client_max_body_size 60M`** in both nginx configs is not arbitrary: the
gallery accepts 30 images of up to 5MB in one POST. nginx's 1MB default turns
that into a 413 the uploader cannot act on.

**`X-Forwarded-Proto`** is set by nginx on every proxied request, and
`production.py` reads it through `SECURE_PROXY_SSL_HEADER`. Both halves are
required: without the setting, Django never sees a request as secure and
`SECURE_SSL_REDIRECT` loops forever; without nginx overwriting the header, a
client could forge it.
