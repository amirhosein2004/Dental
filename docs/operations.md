# Operations

## Backups

```bash
python src/manage.py backup_db                 # dump, keep the newest 3
python src/manage.py backup_db --keep 7
python src/manage.py backup_db --dry-run       # show what would happen
```

Postgres goes through `pg_dump`; SQLite is copied. Not `dumpdata`: a JSON
fixture cannot restore into a database whose shape has since changed, loses
sequence positions, and is slow.

**Rotation is why this is a command and not a cron one-liner.** A backup job
with no retention fills the disk, and a full disk takes the site down in a way
that also stops the next backup from running.

Files are named `dental-<UTC timestamp>` and rotated by name, not mtime — a
file's mtime changes if it is copied or restored, and that must not reorder
the history. Anything not matching `dental-*` is never touched, so a manual
dump left in the folder is safe.

Two ways it runs automatically, and you only need one:

* the `backup` service in the stage and production stacks — nightly in
  production keeping seven, every third day in stage keeping three
* `scripts/install-cron.sh`, which schedules the same thing from the host's
  cron — use this if you want backups to continue while the stack is down

Dumps land in `backups/<environment>/` on the host — `backups/production/`,
`backups/stage/`, `backups/develop/` — one directory each. They shared a single
folder once: rotation counts by age across everything it finds, so a stage
backup deleted production's dumps, and a filename carried nothing to say which
database it came from.

The in-stack service tracks its interval with a marker file beside the dumps,
not with a `sleep` in the container. The container is recreated on every
deploy, so a plain `sleep 3d` restarted its count each time — deploying more
often than the interval meant the backup never fired at all.

**The `pg_dump` client version is pinned to the server's** (`PG_MAJOR=17` in
the Dockerfile, `postgres:17` in `deploy/base.yml`). Change one and you must
change the other: a newer pg_dump writes settings an older server rejects, and
the result is a dump file of the right size that cannot be restored.

Seven nightly copies in production: at most a day's appointments are ever at
risk, and a week is long enough to notice corruption that a three-deep
rotation would already have overwritten — the usual failure is not "the disk
died", it is "something has been quietly wrong since Tuesday".

### Off-site is still missing

`backups/` lives on the same disk as the database it is dumping.
That protects against the common failures — a bad migration, a row deleted by
mistake, corruption noticed a week later. It protects against none of the
failures that take the disk with them: the server dying, the provider closing
the account, or an intruder with root.

Until a copy leaves the machine, this is a local snapshot rather than a
backup. Any of these closes it, in rising order of effort:

```bash
# 1. Pull to your own machine. Nothing to install on the server.
rsync -avz --delete server:/srv/dental/backups/production/ ~/dental-backups/

# 2. Push to object storage from the server (Arvan S3, Liara buckets, S3).
aws s3 sync backups/production/ s3://dental-backups/ --endpoint-url https://s3.ir-thr-at1.arvanstorage.ir
```

Whichever you pick, the copy must be **pull-based or write-only**. A server
that can delete its own off-site backups offers no protection against the
intruder case, which is the main reason the second copy exists.

Restore:

```bash
make ENV=production restore FILE=backups/production/dental-20260824-030000.sql
```

That asks for confirmation and takes a safety backup first — the usual reason
to restore is that something already went wrong.

Backups are gitignored. A dump in the repository is the whole database handed
to anyone who clones it.

## Deploying

```bash
git pull
make ENV=production up-build
```

The entrypoint waits for Postgres, migrates, and collects static before
anything serves. Nothing to remember by hand.

Check before and after:

```bash
make ENV=production check
make ENV=production logs-web
```

## Common problems

**Pages show old content.** A write should invalidate its cache group
automatically. If it does not, that is a bug — find the model in
`apps/core/signals.py` and add a test to `apps/core/tests/test_cache_invalidation.py`.
Clearing by hand hides it.

**Styles broken after a deploy.** Should be impossible in stage and
production: filenames are content-hashed, so a changed file has a changed URL.
If it happens, `collectstatic` did not run — check the entrypoint log.

**`collectstatic` fails with "could not be found".** Something references a
file that is not there — usually a `.map` a minified library points at.
`ManifestStaticFilesStorage` follows every reference and refuses to collect a
missing target.

**502 on every page, but `web` looks healthy.** nginx is dialling an address
nothing is listening on. `web` was recreated, Docker gave it a new IP, and
nginx had the old one cached. Both nginx configs address the app through a
variable with `resolver 127.0.0.11 valid=10s` precisely so this heals itself
within ten seconds — if you see it anyway, check for an `upstream` block that
crept back in, and unblock the site with:

```bash
make ENV=production restart
```

`docker compose up -d` reports success through all of this, and the web
container's own log shows a healthy gunicorn, so nginx's error log is the only
place that says what is wrong:

```bash
make ENV=production logs     # "connect() failed (111: Connection refused)"
```

**Login 500s.** Check the mail path first: a login sends an OTP, and in an
environment with eager Celery an SMTP failure propagates into the request.

**Staff locked out.** Five wrong passwords for one (IP, username) pair locks
it 15 minutes. Clear early:

```bash
make ENV=production manage ARGS="shell -c \"from django.core.cache import cache; cache.clear()\""
```

That also drops the response cache — harmless, just cold for a while.

**Notifications stopped on someone's phone.** Either they deleted the Home
Screen icon (iOS drops the subscription), or their `is_doctor` flag was
cleared, which stops delivery by design.

**A patient reports the contact form rejects them.** Check the phone format —
11 digits starting with 0, mobile or landline. Then the rate limit: 20/min per
IP, which a shared clinic wifi can reach.

## Health

Both proxies expose `/healthz`, which returns 200 without touching the
database — so a failing query shows up as 500s rather than as an unhealthy
container being restarted in a loop.

```bash
make ENV=production ps          # container health
docker compose --env-file deploy/env/.env.production   -f deploy/base.yml -f deploy/production.yml exec db pg_isready -U dental
```

## Logs

JSON-file driver, 10MB × 5 files per service in production.

```bash
make ENV=production logs-web
make ENV=production logs
```

The login throttle logs once when it engages, on the attempt that crosses the
line — not on every subsequent refusal, which would let an attacker fill the
log.
