# Deploying — step by step

The runbook for both environments. Follow it top to bottom the first time;
after that only [Every deploy after the first](#every-deploy-after-the-first)
applies.

Reference material lives elsewhere and is linked where it becomes relevant:
[environments.md](environments.md) for what differs between the two,
[`../deploy/README.md`](../deploy/README.md) for the compose layout,
[`../scripts/README.md`](../scripts/README.md) for the helper scripts,
[operations.md](operations.md) for what to do when something breaks.

---

## The one thing to know first

Every command is `make <target>`, and the environment is a variable:

```bash
make ENV=production up
make ENV=production logs
make up                  # ENV defaults to develop
make                     # lists every target
```

`ENV` picks both the env file and the compose overlay together — they must
always change as a pair. Getting that wrong is not obvious: without the right
`--env-file` there is no `COMPOSE_PROJECT_NAME`, and a production `up` then
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
C="docker compose --env-file deploy/env/.env.production \
     -f deploy/base.yml -f deploy/production.yml"
$C up -d
```

Same three arguments, typed every time. `make ENV=production up` is this.
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
> put it in front of a tunnel only long enough for them to look — see
> [Showing the site to someone](#showing-the-site-to-someone-from-a-machine-with-no-public-address)
> — and never point a real domain at it.

---

# production

The live site: TLS, real SMS and email, media in the object-storage bucket.
Everything in it is reachable by a patient, which is the only real difference
from develop.

Nothing below is typed on the server by hand. The server is in Iran and
reaches neither GitHub, GitLab nor Docker Hub, so both of the things that
would normally get code onto it — `git pull` and `docker pull` — are closed.
Two commands from the laptop cover it instead: `make provision` sets the
machine up once, `make ship` sends each commit and builds it there.

### 1. Prepare the server

Once per machine, from the laptop:

```bash
make provision
```

It installs Docker and Compose v2 over SSH, points the daemon at an Iranian
registry mirror so the five base images can be pulled at all, puts the deploy
user in the `docker` group, and creates `/srv/dental`. Idempotent — run it
again after a server rebuild, or to move the registry mirror.

It needs `sudo` on the far side and will ask for the password in your
terminal. What it installs is `docker-compose-v2`, the plugin invoked as
`docker compose`; if you have already run `apt install docker-compose` from a
provider's guide, that is v1 and these overlays do not work with it —
`depends_on.condition` is ignored and the shared build anchor is unreadable,
so the web container starts before Postgres is ready and nothing says why.

### 2. The env file, on the server

```bash
make ship
```

The first one does not deploy. It sends the code, finds no
`deploy/env/.env.production`, copies the example into place with mode 600 and
stops. Then, on the server:

```bash
ssh -p 9011 amiiiriii@87.248.131.223
cd /srv/dental
sh scripts/check-mirrors.sh          # which mirrors answer today
nano deploy/env/.env.production
```

Fill in **every** `CHANGE-ME` — Kavenegar, SMTP, the S3 bucket, and the same
generated values as develop, generated again, never copied. This file is
gitignored, `git archive` cannot carry it, and `ship.sh` never overwrites it,
so it exists in exactly one place and every secret in it is its own: reusing a
value that has been on a laptop is the same as not having one.

The next `make ship` refuses to build while `SECRET_KEY`, `DB_PASSWORD`,
`OTP_SECRET_KEY` or `SECURE_ADMIN_PANEL` is still a placeholder. Those four
are not "unconfigured" — they are a site that works and is compromised, and
`CHANGE-ME-long-random-password` is a password Postgres accepts on first boot
and then keeps for the life of the volume. The rest only turn a feature off,
so they warn and let the deploy through.

Two of them have an order to them. `DB_PASSWORD` is written into the Postgres
volume the first time the stack comes up and cannot be changed by editing this
file afterwards — after that it takes an `ALTER USER` inside the database. And
the VAPID pair is generated by a command that lives inside the image, so it is
normal for those to stay placeholders until the stack has been up once:

```bash
make ENV=production manage ARGS=generate_vapid_keys
```

Keep a copy of the finished file somewhere off the machine and outside this
repository. It is the only one there is.

```bash
DJANGO_ENV=production python src/manage.py check --deploy
```

### 3. Start it, and get the first certificate

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

### 4. Admin account, then confirm

```bash
make ENV=production superuser
make ENV=production ps
curl -I https://sbdental.ir/healthz
```

Then in a browser: load a page, sign in, submit the contact form, and check
that the push notification arrives. That last one exercises Redis, Celery and
the VAPID keys in a single click — the three things most likely to be
misconfigured on a fresh server.

### 5. Backups

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

From the laptop, in a clean checkout of what you want live:

```bash
make ship
```

`git pull` is not an option on that server: it reaches neither GitHub nor
GitLab. `make ship` streams the current commit over SSH with `git archive`,
extracts it into `/srv/dental`, takes a database backup, and runs
`docker compose build && up -d` at the far end. Then it checks
`https://sbdental.ir/healthz` from *here*, which is the path a visitor takes —
so an nginx or a certificate that is broken from outside shows up even when
the container looks healthy.

Uncommitted changes are deliberately not shipped; `SHIP_DIRTY=1 make ship`
overrides that for a quick try, and `SHIP_REF=<sha> sh scripts/ship.sh` ships
an older commit.

Building on the server rather than shipping an image is the whole reason this
works at all — its 855Mb line to Iranian mirrors beats a home upstream, and it
is the only side of the connection that can reach a Docker registry it is
allowed to use. The trade is that production compiles its own bytes; see
[cicd.md](cicd.md#the-image-is-built-on-the-server).

If you are already on the server — for an env-file change, which needs no
rebuild:

```bash
make ENV=production up
make ENV=production logs-web
```

`up-build` rather than `up` when code changed: a container keeps the code
baked into its image, so a changed file changes nothing until the image is
rebuilt.

The entrypoint migrates and re-collects static on the way up. Nothing else to
remember.

### Which mirror goes where

Three different things fetch from the network during a deploy, and each reads
its mirror from a different place. Setting one in another's file is silent:
nothing complains, and the failure arrives later as a timeout.

| What is fetched | Who fetches it | Where the mirror is configured |
| --- | --- | --- |
| `python:3.12-slim`, `postgres:17`, `redis:7-alpine`, `nginx:1.27-alpine`, `certbot` | `dockerd` | `registry-mirrors` in `/etc/docker/daemon.json` — written by `make provision` |
| `postgresql-client-17` and its apt dependencies | apt, inside the build | `APT_MIRROR` in `deploy/env/.env.production` |
| Django and the rest of `requirements.txt` | pip, inside the build | `PYPI_INDEX_URL` in the same file |

`make provision` handles the first row. The other two are the FAIL lines from:

```bash
sh scripts/check-mirrors.sh    # on the server
```

Run it there and not here — the question it answers is what *that* machine can
reach, and the answer moves as Iranian mirrors come and go.

Two mistakes that cost an afternoon each. `python:3.12-slim` is Debian
**trixie** — an **Ubuntu** mirror in `APT_MIRROR`, or one that only carries
bookworm, answers 404 on every index file, and apt reports that as a missing
release rather than as a wrong host.
The second is a saving. `apt.postgresql.org` has no Iranian mirror either —
but trixie ships `postgresql-client-17` in its own archive, so at
`PG_MAJOR=17` that repository is not needed. Set `USE_PGDG=0` in
`deploy/env/.env.production` and the build needs exactly two mirrors: Debian's
and PyPI's.

Only while the versions line up. `pg_dump` has to match the server's Postgres,
and the day `PG_MAJOR` goes past what Debian ships, `USE_PGDG=1` comes back —
a mismatch is silent until a restore fails with
`ERROR: unrecognized configuration parameter "transaction_timeout"`.

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
make ENV=develop down                           # containers go, database stays
make ENV=develop down-volumes CONFIRM=yes       # database deleted, no undo
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
| ArvanCloud CDN, DNS only (grey) | yours, from Let's Encrypt | **yes** |
| ArvanCloud CDN, proxied | theirs at the edge — **and** still yours on the origin | **yes**, see below |

ArvanCloud proxied is the row that catches people out: it is two certificates,
not one. Theirs answers the visitor, ours answers ArvanCloud, and ours is still
required because the origin must be reachable over HTTPS (see
[Behind ArvanCloud](#behind-arvancloud)).

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

## Showing the site to someone, from a machine with no public address

**Everything in this section is Cloudflare-specific, and it is the one thing
here that still is.** `cloudflared`, `trycloudflare.com`, the `Full` encryption
mode — all of it is Cloudflare's tunnel product, and none of it has an
ArvanCloud equivalent. Production DNS is on ArvanCloud now (see
[Behind ArvanCloud](#behind-arvancloud)), so a *named* tunnel on a
`sbdental.ir` subdomain is no longer possible at all: those records live in
ArvanCloud's zone, and `cloudflared tunnel route dns` writes into Cloudflare's.

What still works is a **quick tunnel**, which touches no DNS record of ours and
hands back a throwaway `trycloudflare.com` name. That is now the way to show
work in progress to someone — there is no stage host to point them at. Other
outbound tunnels (`ngrok`, `tailscale funnel`) or an SSH reverse tunnel to the
production VPS do the same job if Cloudflare is out of the picture entirely.

A laptop or a desktop at home has no reachable address: the IP is dynamic, the
connection is behind NAT, and Iranian home lines generally refuse inbound 80
and 443. So nothing local gets a certificate of its own — something in front
terminates TLS and reaches back over an outbound connection.

```bash
make up                                     # develop, on 8000
cloudflared tunnel --url http://127.0.0.1:8000
```

It prints an `https://<random>.trycloudflare.com` and holds it open until
Ctrl-C. **Only for as long as you are watching it.** Develop forces
`DEBUG=True` and its `SECRET_KEY` is published in this repository, so anyone
with that URL sees tracebacks with settings in them and can forge a session
cookie. Close the tunnel when the person has finished looking.

Two things it needs, both already in place:

* **`.trycloudflare.com` in `ALLOWED_HOSTS`.** The leading dot matches any
  subdomain, which a quick tunnel needs because the name changes every run.
* **Develop does not force HTTPS.** `develop.py` leaves `SECURE_SSL_REDIRECT`
  off, so the tunnel terminating TLS and speaking plain HTTP inward is fine.
  Point a tunnel at a stack running production settings and every request
  redirects to HTTPS, the tunnel hands the same request back, and the browser
  loops forever — the failure that used to need `stage.conf` to map
  `X-Forwarded-Proto` through instead of passing `$scheme`. Cloudflare's
  `Flexible` encryption mode causes the same loop, for the same reason.

`127.0.0.1`, not `localhost`: `localhost` can resolve to `::1` first, and the
published port is IPv4 only, so the tunnel answers 502 with nothing in its own
log.

`--protocol quic` is the default and worth keeping. On a connection that
inspects TLS, cloudflared's http2 transport fails its handshake with the edge
outright (`TLS handshake with edge error: EOF`) while QUIC rides over UDP and
is left alone.

Worth knowing before moving a domain to *any* DNS provider, Cloudflare or
ArvanCloud: the live site's DNS moves with it, and **records are not always
imported**. Check every one before the nameserver change takes effect — apex,
`www`, `MX`, any verification `TXT`. Cloudflare specifically: keep the
production records on **grey cloud**, because proxying an Iran-hosted site
through a European edge makes it slower for the audience it has. That is the
reason the domain is on ArvanCloud now — an edge inside the country, in front
of an origin inside the country.

---

## Behind ArvanCloud

Production DNS is on ArvanCloud, not Cloudflare. Nothing above this line
changes — the stack, certbot and `production.conf` are the same — but four
things are specific to it, and three of them are silent failures.

**DNS only, or proxied.** Both work. "DNS only" (the cloud icon off) makes
ArvanCloud a nameserver and nothing more: visitors reach the VPS directly and
every note below about certificates and the origin firewall is moot. Proxied
puts their edge in front, which is the point of moving here — an Iranian edge
for an Iranian audience. The rest of this section is about proxied.

**The origin must speak HTTPS.** In the CDN settings the origin protocol has to
be `HTTPS`, matching what `production.conf` actually serves. Set it to `HTTP`
and the edge fetches over port 80, nginx answers `301 https://…`, the edge
follows it back to itself, and the visitor gets a redirect loop that shows up
nowhere in the application log. This is the same failure Cloudflare's
`Flexible` mode causes, for the same reason, and the fix is the same: never let
a proxy in front reach the origin over plaintext.

**Certificates: two, not one.** ArvanCloud issues the certificate the visitor
sees, at the edge. The origin still needs its own, because of the paragraph
above — so `certbot` stays in `deploy/production.yml` and
`scripts/init-letsencrypt.sh` still runs. The catch is renewal: HTTP-01 needs
`http://sbdental.ir/.well-known/acme-challenge/…` to reach *our* nginx, and
with the record proxied it reaches ArvanCloud first. Either

* issue and renew while the record is on DNS-only, then turn the proxy back
  on — workable but manual every 60 days, and easy to forget until the
  certificate has already expired; or
* add a cache/forwarding rule that passes `/.well-known/acme-challenge/*`
  straight to the origin uncached, and leave the proxy on permanently. This is
  the one to set up once and stop thinking about.

Do **not** run certbot against a hostname that ArvanCloud is also issuing for
without one of those in place: five failures per hostname per hour is Let's
Encrypt's rate limit, the renewal loop reaches it, and then keeps failing
against a wall with nothing serving an error.

**Lock the origin down, or the CDN is decoration.** The VPS's own IP still
answers on 80 and 443, so anyone who learns it can skip the edge entirely —
and with it the WAF, the rate limits at the edge, and the visitor's real
address. Restrict inbound 80/443 at the firewall to ArvanCloud's ranges
(`https://www.arvancloud.ir/fa/ips.txt`), leaving SSH on whatever it uses:

```bash
# One-time, on the VPS. Re-run when their ranges change.
for cidr in $(curl -fsS https://www.arvancloud.ir/fa/ips.txt); do
  ufw allow proto tcp from "$cidr" to any port 80,443
done
ufw deny 80/tcp
ufw deny 443/tcp
```

Note that this makes HTTP-01 renewal impossible from anywhere but the edge,
which is another reason to prefer the forwarding rule over the DNS-only dance.

**The visitor's IP is already handled.** ArvanCloud sends the real client
address in an `ar-real-ip` header, and `deploy/nginx/production.conf` lists
their ranges under `set_real_ip_from` and reads it. Without that, `$remote_addr`
would be the edge for every request — and since the login lockout, every
`django-ratelimit` bucket and the captcha limit are all keyed on the client
address, five failed logins by any one person would lock out the entire site.
The ranges are pinned in that file: re-check them against
`https://www.arvancloud.ir/fa/ips.txt` when ArvanCloud announces new ones.

**Uploads go to an ArvanCloud bucket.** `AWS_*` in
`deploy/env/.env.production.example` — endpoint `https://s3.ir-thr-at1.arvanstorage.ir`
for the Simin (Tehran) region, `ir-thr-at1` as the region name. The bucket has
to be set to **public** access: `AWS_QUERYSTRING_AUTH = False` in
`production.py` produces plain permanent URLs, and against a private bucket
every image on the site 403s. Leave the three credential variables blank and
uploads fall back to the `media/` volume on disk, which nginx serves — that is
still a valid way to run, just not a durable one.

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
