# Deploying — step by step

The runbook for all three environments. Follow it top to bottom the first
time; after that only [Every deploy after the first](#every-deploy-after-the-first)
applies.

Reference material lives elsewhere and is linked where it becomes relevant:
[environments.md](environments.md) for what differs between the three,
[`../deploy/README.md`](../deploy/README.md) for the compose layout,
[`../scripts/README.md`](../scripts/README.md) for the helper scripts,
[operations.md](operations.md) for what to do when something breaks.

---

## The one thing to know first

Every command is `make <target>`, and the environment is a variable:

```bash
make ENV=stage up
make ENV=production logs
make up                  # ENV defaults to develop
make                     # lists every target
```

`ENV` picks both the env file and the compose overlay together — they must
always change as a pair. Getting that wrong is not obvious: without the right
`--env-file` there is no `COMPOSE_PROJECT_NAME`, and a stage `up` then
attaches to develop's database volume with nothing anywhere saying so. The
[`Makefile`](../Makefile) builds that line once so it cannot be typed wrong.

An invalid `ENV` stops before anything runs. A missing env file reports itself
by name rather than surfacing later as strange behaviour.

**On Windows**, run `make` from either PowerShell or Git Bash — the Makefile
points itself at Git's `sh.exe`. The `scripts/*.sh` files, if you call them
directly, need Git Bash.

<details>
<summary>Without make</summary>

```bash
C="docker compose --env-file deploy/env/.env.stage \
     -f deploy/base.yml -f deploy/stage.yml"
$C up -d
```

Same three arguments, typed every time. `make ENV=stage up` is this.
</details>

---

# develop

Your own machine. Never faces the internet.

### 1. The env file

```bash
cp deploy/env/.env.develop.example deploy/env/.env.develop
```

That is the whole step. `develop.py` pins its own secret key, admin path and
VAPID pair, so there is nothing to fill in.

### 2. Start it

```bash
make up-build
make logs-web
```

You do not run `migrate`. The entrypoint goes through this order on every
boot:

```
[entrypoint] waiting for postgres      ← depends_on waits for the container, not for Postgres
[entrypoint] applying migrations       ← web only, so two containers cannot race the same tables
[entrypoint] collecting static files
[entrypoint] starting: runserver
```

Those are in `deploy/entrypoint.sh` precisely so a deploy cannot skip one.
They used to be instructions in a README, and a deploy that forgot them
produced a site with an out-of-date schema and no stylesheets, with nothing
anywhere saying so.

### 3. Demo content

```bash
make seed
```

### 4. An admin account

```bash
make superuser
```

Prompts for username, email, name and password, with the password hidden.

Do **not** use `createsuperuser --noinput` in a deploy script. It sets an
unusable password: the account is created, the script exits 0, and it looks
like it worked right up until someone tries to sign in.

A superuser without `is_doctor` can only reach the admin panel — the doctor
login on the site itself checks that flag:

```bash
make manage ARGS="shell -c \"from apps.users.models import CustomUser as U; U.objects.filter(username='amir').update(is_doctor=True)\""
```

### 5. Tests

```bash
make test
```

### 6. Open it

`http://127.0.0.1:8000` — no nginx here, runserver answers directly.

> **Never expose develop.** `DEBUG=True` is forced, not defaulted, and its
> `SECRET_KEY` is published in this repository. To show the site to someone,
> use stage, which was built for exactly that.

---

# stage

Production's settings with production's teeth pulled: real gunicorn, real
nginx, hashed static — but SMS to the console, email to a file, and
`X-Robots-Tag: noindex` on every response.

### 1. The env file

```bash
cp deploy/env/.env.stage.example deploy/env/.env.stage
```

Three values are generated, not invented:

```bash
# SECRET_KEY and OTP_SECRET_KEY — run it twice, they must differ
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

# VAPID keys for web push — both values
python src/manage.py generate_vapid_keys
```

Set `DB_PASSWORD` to something random too, and `SECURE_ADMIN_PANEL` to a
random path — that is the admin URL, and a random one is not found by the
scanners that walk the internet trying `/admin/`.

`ALLOWED_HOSTS` must name the hostname you will actually use:

```
ALLOWED_HOSTS=stage.sbdental.ir,.trycloudflare.com,localhost,127.0.0.1
```

Then check it before anything runs against it:

```bash
DJANGO_ENV=stage python src/manage.py check --deploy
```

Cheapest step in the whole list, and it catches a wrong `ALLOWED_HOSTS` or a
`DEBUG` left on — which are otherwise found by a user.

### 2. Start it

```bash
make ENV=stage up-build
make ENV=stage ps
```

Six services: `db`, `redis`, `web`, `worker`, `nginx`, `backup`.

### 3. Confirm it works

```bash
curl -I http://127.0.0.1:8080/healthz
make ENV=stage check
```

`curl http://127.0.0.1:8080/` answers **301**, and that is correct rather than
broken: stage inherits `SECURE_SSL_REDIRECT` from production and this
container is only ever spoken to over plain HTTP. To see a real page, send
the headers the proxy in front would send:

```bash
curl -I -H 'X-Forwarded-Proto: https' -H 'Host: stage.sbdental.ir' \
     http://127.0.0.1:8080/
```

### 4. An admin account

```bash
make ENV=stage superuser
```

### 5. Publish it

```bash
make tunnel
```

See [Showing stage to someone](#showing-stage-to-someone-from-a-machine-with-no-public-address).

### 6. Prove the backup works

The backup service takes its first dump about 90 seconds after `up`:

```bash
make ENV=stage manage ARGS="shell -c \"import os; print(os.listdir('/app/backups'))\""
```

**Then restore it before you need to.** An untested backup is a file, not a
recovery plan — the first real restore of this project reported success while
silently leaving post-backup rows in place and dropping a whole table, and
only a rehearsal found it.

```bash
make ENV=stage restore FILE=backups/stage/dental-<stamp>.sql
```

---

# production

Everything in stage, plus TLS, real SMS and email, S3 media, and no `noindex`.

### 1. The env file

```bash
cp deploy/env/.env.production.example deploy/env/.env.production
```

Fill in **every** `CHANGE-ME` — Kavenegar, SMTP, the S3 bucket, and the same
generated values as stage. This file is gitignored and never leaves the
server. Its `SECURE_ADMIN_PANEL` must be its own value, not stage's.

```bash
DJANGO_ENV=production python src/manage.py check --deploy
```

### 2. Start it, and get the first certificate

On a plain VPS these are one step, and the script brings the stack up itself:

```bash
scripts/init-letsencrypt.sh sbdental.ir www.sbdental.ir you@example.com
```

It exists because the obvious sequence cannot work. nginx refuses to start
when `ssl_certificate` names a file that is not there, and it rejects the
*whole* config, not just the TLS block — so the port-80 server that answers
Let's Encrypt's challenge never starts either. No certificate, no nginx; no
nginx, no certificate. The script breaks the loop with a throwaway
self-signed certificate: nginx starts on that, serves the challenge, certbot
replaces it with a real one, nginx reloads.

Test the plumbing first if the domain is new — Let's Encrypt allows five
failed attempts per hostname per hour, and a typo spends them quickly:

```bash
STAGING=1 scripts/init-letsencrypt.sh sbdental.ir www.sbdental.ir you@example.com
```

Renewal needs nothing scheduled: the `certbot` service checks twice a day, and
nginx reloads every six hours so a renewed certificate is actually served.
Without that reload nginx keeps the old certificate in memory and goes on
serving it until it expires — 90 days after a renewal that looked like it
worked.

**Skip this entire step if something else terminates TLS** — a managed
platform, or Cloudflare. See [Who owns the certificate](#who-owns-the-certificate).

### 3. Admin account, then confirm

```bash
make ENV=production superuser
make ENV=production ps
curl -I https://sbdental.ir/healthz
```

Then in a browser: load a page, sign in, submit the contact form, and check
that the push notification arrives. That last one exercises Redis, Celery and
the VAPID keys in a single click — the three things most likely to be
misconfigured on a fresh server.

### 4. Backups

The in-stack service runs on its own. Its two knobs live in
`deploy/production.yml`:

```yaml
BACKUP_KEEP: "3"
BACKUP_INTERVAL_DAYS: "3"
```

Three copies three days apart span nine days, which is long enough to notice
corruption that a nightly rotation would already have overwritten. The
trade-off is that up to three days of work is at risk. **For a site taking
real appointments, set `BACKUP_INTERVAL_DAYS: "1"` and `BACKUP_KEEP: "7"`** —
same nine-day-ish window, one day of exposure instead of three, and a dump of
this size costs almost nothing.

Rehearse the restore here too, and read
[operations.md](operations.md#off-site-is-still-missing): the backups sit on
the same disk as the database they are dumping, so until a copy leaves the
machine this is a local snapshot rather than a backup.

---

## Every deploy after the first

```bash
git pull
make ENV=production up-build
make ENV=production logs-web
```

`up-build` rather than `up`: a container keeps the code baked into its image,
so changing a file on the server changes nothing until the image is rebuilt.
An env-only change needs just `make ENV=production up`.

The entrypoint migrates and re-collects static on the way up. Nothing else to
remember.

If it looks wrong afterwards:

```bash
make ENV=production logs
make ENV=production check
```

## When it breaks

**Every page 502s but `web` looks healthy.** nginx is dialling an address
nothing is listening on. Both configs address the app through a variable with
`resolver 127.0.0.11 valid=10s`, so this heals itself within ten seconds; if
it does not, `make ENV=production restart`. The cause only ever appears in
one place:

```bash
make ENV=production logs        # "connect() failed (111: Connection refused)"
```

More in [operations.md](operations.md#common-problems).

## Shutting down

```bash
make ENV=stage down                             # containers go, database stays
make ENV=stage down-volumes CONFIRM=yes         # database deleted, no undo
```

`down-volumes` is a separate target and demands `CONFIRM=yes` on purpose:
`-v` destroys the database and one character should not be able to do that.

## Rolling back

Code and database roll back separately, and in that order.

```bash
git checkout <previous-tag>
make ENV=production up-build
```

If the bad deploy included a migration that lost data, restore instead — but
read [`../scripts/README.md`](../scripts/README.md#restoring) first. A restore
discards everything written since the dump, so it is the right move for a
corrupted database and the wrong one for a cosmetic bug.

---

## One-off: the deploy that moves apps into `apps/`

Celery task names are module paths, so they changed with the package move —
`contact.tasks.delete_old_messages` became
`apps.contact.tasks.delete_old_messages`.

A task already sitting in the queue when the new worker starts carries the old
name, and the worker answers `NotRegistered` and drops it. In this project
that is harmless: Redis runs with `--save ""`, so the queue does not survive a
restart anyway, and the tasks in it are SMS, email, push and a cleanup job —
all safe to lose one of.

Worth knowing rather than worth working around. If it ever stops being safe to
lose one, drain the queue before deploying:

```bash
make ENV=production manage ARGS="shell -c \"pass\""   # or:
docker compose --env-file deploy/env/.env.production \
  -f deploy/base.yml -f deploy/production.yml exec worker celery -A config inspect active
```

---

## Who owns the certificate

Whoever terminates TLS owns the certificate. That single rule decides whether
any of step 2 above applies.

| In front of the app | Certificate | Run certbot? |
|---|---|---|
| Nothing — a bare VPS | yours, from Let's Encrypt | **yes**, `init-letsencrypt.sh` |
| A managed platform (Liara and similar) | theirs, automatic | no |
| Cloudflare proxy or tunnel | theirs at the edge, free | no |

**Do not run two of these at once.** It is not that two certificates for one
domain are forbidden — a CA will issue them — it is that certbot's HTTP-01
challenge needs port 80 on your machine to be what the domain resolves to. If
DNS points at Liara or at Cloudflare's proxy, the challenge is answered by
them, certbot fails, and it fails *repeatedly*: five failures per hostname per
hour is the rate limit, and a renewal loop reaches it and then keeps trying
against a wall. The failure is silent — nothing serves an error, the old
certificate just quietly stops being renewed.

So pick one. Behind Cloudflare or on a managed platform, delete the `certbot`
service from your overlay and skip `init-letsencrypt.sh` entirely.

**A certificate from one platform cannot usually be moved to another.** A
managed host issues certificates for domains pointed at *it* and keeps the
private key; there is no export. If you want your own certificate on your own
VPS while Cloudflare sits in front, use a **Cloudflare Origin Certificate** —
free, valid 15 years, downloadable, and it needs no port 80 because
Cloudflare already knows you own the zone.

---

## Showing stage to someone, from a machine with no public address

A laptop or a desktop at home has no reachable address: the IP is dynamic,
the connection is behind NAT, and Iranian home lines generally refuse inbound
80 and 443. So stage does not get a certificate of its own — something in
front of it terminates TLS and reaches back over an outbound connection.

A Cloudflare quick tunnel touches no DNS record at all:

```bash
make ENV=stage up
cloudflared tunnel --url http://127.0.0.1:8080
```

It prints an `https://<random>.trycloudflare.com` and holds it open until
Ctrl-C.

For a name of your own the domain has to be on Cloudflare, and then it is a
named tunnel — created once:

```bash
cloudflared tunnel login
cloudflared tunnel create dental-stage
cloudflared tunnel route dns dental-stage stage.sbdental.ir
```

That last line writes the DNS record itself (a CNAME to
`<uuid>.cfargotunnel.com`); do not create one by hand. Point `config.yml` at
`http://127.0.0.1:8080`, and from then on:

```bash
make tunnel
```

Three things this needs, all already in place:

* **`.trycloudflare.com` in `ALLOWED_HOSTS`.** The leading dot matches any
  subdomain, which a quick tunnel needs because the name changes every run.
* **`X-Forwarded-Proto` honoured, not overwritten.** `stage.conf` maps the
  incoming header through rather than passing `$scheme`. Pass `$scheme` and
  Django redirects to HTTPS, the tunnel hands the same request back, and the
  browser loops forever.
* **Cloudflare's encryption mode on `Full`.** `Flexible` sends
  `X-Forwarded-Proto: http` and produces the same loop.

`127.0.0.1`, not `localhost`: `localhost` can resolve to `::1` first, and the
published port is IPv4 only, so the tunnel answers 502 with nothing in its own
log.

`--protocol quic` is the default and worth keeping. On a connection that
inspects TLS, cloudflared's http2 transport fails its handshake with the edge
outright (`TLS handshake with edge error: EOF`) while QUIC rides over UDP and
is left alone.

Worth knowing before moving a domain to Cloudflare: the live site's DNS moves
with it, and **records are not always imported**. Check every one before the
nameserver change takes effect — apex, `www`, `MX`, any verification `TXT`.
Keep the production records on **grey cloud**: proxying an Iran-hosted site
through a European edge makes it slower for the audience it has.

---

## If production is on Liara

Then `deploy/production.yml` and `deploy/nginx/production.conf` are unused —
Liara terminates TLS, runs the proxy, and serves static files itself. The
build, certificate and backup steps above are replaced by Liara's own
features.

What still applies unchanged: `config/settings/production.py`, every variable
in `.env.production.example` (set in Liara's panel instead of a file), and the
env-file and admin-account steps.

You would add a `liara.json` naming the platform, the Python version, and
`DJANGO_ENV=production`.

---

## The order matters, and why

| | Depends on |
|---|---|
| 1 env file | nothing — but everything below reads it |
| 2 build & up | the env file, for `COMPOSE_PROJECT_NAME` and the database credentials |
| 3 certificate | the stack being up and answering on port 80 |
| 4 admin account | migrations having run, which happened in step 2 |
| 5 verify | all of the above |
| 6 backup rehearsal | there being a schema to dump |

The two that are easy to get wrong: issuing a certificate before nginx can
answer the challenge, and creating a superuser before `migrate` has made the
table.
