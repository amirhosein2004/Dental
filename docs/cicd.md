# CI/CD

GitLab. The pipeline lives in [`../.gitlab-ci.yml`](../.gitlab-ci.yml).

| Push to | What happens |
|---|---|
| any branch, or a merge request | tests + dependency audit |
| `develop` | tests, build — no deploy |
| `master` | tests, build, then a **button** for production |

---

## Why production is a button

Production is the only environment the pipeline deploys at all, and it waits
for a person. The reason is `deploy/entrypoint.sh`: it runs `migrate` on the
way up.

That is the right behaviour — it means a deploy cannot forget the migration —
but it also means an automatic production deploy runs an unreviewed schema
change against the real patient database, possibly at 2am, possibly while the
author has already closed their laptop. Code rolls back in seconds. A
migration that dropped a column does not roll back at all.

So: merging to `master` builds and tests the image and stops. Someone opens the
pipeline and presses **deploy:production** when they are ready to watch it.

If you later decide the risk is acceptable, delete the `when: manual` line on
that job. Do that as a deliberate decision, not by accident.

---

## The image is built on the server

The production server is in Iran. It reaches neither GitHub nor GitLab, so it
cannot clone this repository; it reaches Docker Hub only through a mirror, and
GitLab's container registry not at all. A pipeline that built an image and
expected the server to `docker pull` it had nothing on the far end able to do
the pulling.

So the code travels over SSH and the build happens there:

```
laptop/runner                          server
  git archive HEAD ──── ssh ────▶ tar -xzf - -C /srv/dental
                                  docker compose build
                                  docker compose up -d
```

That is [`scripts/ship.sh`](../scripts/ship.sh), and it is what both `make
ship` and the `deploy:production` job run. Neither is a separate deploy path —
a procedure that only exists inside CI is one nobody can run on the day CI is
the thing that is broken.

The cost is real and worth naming: **the bytes production runs were compiled
on production**, at a different time from the test run, possibly resolving a
dependency to a different version than the pipeline saw. The `build` job still
runs on every push to `develop` and `master`, but it is now a check that the
Dockerfile builds — not the artefact that ships. Pinning in `requirements.txt`
is what keeps the drift small; it matters more here than it would with a
registry.

`APP_IMAGE` is left unset on the server, so the compose files fall back to:

```yaml
image: ${APP_IMAGE:-dental-app:local}
```

which is the tag `compose build` writes. All three app services (`web`,
`worker`, `backup`) share it, which matters: a worker running last week's code
against this week's schema fails in ways that are hard to read.

### The mirrors the build needs

`docker compose build` on that machine fetches from Debian's archive, from
`apt.postgresql.org` and from PyPI, and reaches none of them. Each is a build
argument, empty by default and filled in on the server only —
`APT_MIRROR`, `PYPI_INDEX_URL`, `PYPI_TRUSTED_HOST`, plus `USE_PGDG`,
`PGDG_URL` and `PGDG_ASC_URL`, all set in `deploy/env/.env.production`. The four images
the stack does not build (`postgres`, `redis`, `nginx`, `certbot`) come from
the daemon's own Hub mirror in `/etc/docker/daemon.json`.

Which mirrors work is not a fact that stays true — Iranian mirrors appear and
close on a timescale of months — so ask the machine rather than a list:

```bash
ssh server 'cd /srv/dental && sh scripts/check-mirrors.sh'
```

Two traps in that set. `python:3.12-slim` is Debian **trixie** — not Ubuntu,
and not bookworm either since the base image moved — so an Ubuntu mirror, or
one that stops at the previous suite, answers 404 on every index file and apt
reports it as a missing release.

The second is worth turning into a saving rather than a warning: **trixie
ships `postgresql-client-17` in its own archive**, so with `PG_MAJOR=17` the
PostgreSQL apt repository is not needed at all. Set `USE_PGDG=0` in
`deploy/env/.env.production` and the build stops touching
`apt.postgresql.org` and `www.postgresql.org` — two more hosts the server
cannot reach and neither of which has an Iranian mirror. What is left needing
one is Debian's archive and PyPI, and that is the whole list.

Leave it at `1` the day `PG_MAJOR` moves ahead of what Debian ships. The
client version has to match the server's Postgres, and a mismatch is not
loud: an older `pg_dump` against a newer server refuses outright, while a
newer one writes a dump the older server rejects on restore with
`ERROR: unrecognized configuration parameter "transaction_timeout"` — a file
that exists, looks the right size, and cannot be used.

---

## Rolling back

A rollback is a deploy of an older commit. There is no registry holding a
known-good tag to point at, so the server rebuilds and it takes as long as a
deploy does:

1. Pipelines → the `rollback:production` job
2. Set `ROLLBACK_SHA` to the commit to go back to
3. Run it

When minutes matter, skip the runner — from a checkout of the old commit,
`SHIP_REF=<sha> sh scripts/ship.sh` does exactly the same thing.

**This rolls back code, not the database.** If the bad deploy included a
migration that changed data, restoring is the fix — see
[`../scripts/README.md`](../scripts/README.md#restoring). The deploy takes a
backup *before* it migrates, precisely so that file exists.

---

## Setting it up

### 1. Variables

Settings → CI/CD → Variables. Everything below must be **Protected** — that
restricts it to protected branches, so a merge request from a fork cannot read
the production SSH key. `SSH_PRIVATE_KEY` must also be **File** type, or its
newlines are mangled and `ssh-add` fails with an unhelpful error.

| Variable | Type | What |
|---|---|---|
| `SSH_PRIVATE_KEY` | File, Protected, Masked | deploy key's private half |
| `SSH_KNOWN_HOSTS` | Variable, Protected | output of `ssh-keyscan -p 9011 -H your.server` |

Where the code goes — `SHIP_HOST`, `SHIP_PORT`, `SHIP_USER`, `SHIP_PATH` — is
in `.gitlab-ci.yml` already, because none of it is a secret. Override any of
them here for a second server. No registry variables are used at all now; the
server builds its own image.

`SSH_KNOWN_HOSTS` is not optional and not paperwork. Without it the job needs
`StrictHostKeyChecking=no`, which means the first connection trusts whatever
answers on that address — and handing your deploy key to whatever answers is
the entire attack.

### 2. A deploy key on the server

On your machine, a key used for nothing else:

```bash
ssh-keygen -t ed25519 -C "gitlab-deploy" -f ~/.ssh/dental_deploy
ssh-copy-id -i ~/.ssh/dental_deploy.pub deploy@your.server
ssh-keyscan -H your.server        # this output goes in SSH_KNOWN_HOSTS
```

Upload `~/.ssh/dental_deploy` (the private half, no `.pub`) as the
`SSH_PRIVATE_KEY` file variable.

The server user needs to be in the `docker` group. Note that this is
equivalent to root on that machine — docker group membership always is — so
use an account that exists for this and nothing else.

### 3. A runner that can reach the server

GitLab's shared runners are outside Iran; the deploy job is tagged `iran-vpn`
so it lands on one you control instead — in practice a `gitlab-runner` on the
laptop. It polls gitlab.com outbound, so it needs no public address, no open
port and no static IP, and it is already on the connection that reaches both
gitlab.com and the server.

```bash
docker run -d --name gitlab-runner --restart always   -v /var/run/docker.sock:/var/run/docker.sock   -v gitlab-runner-config:/etc/gitlab-runner   gitlab/gitlab-runner:latest

docker exec -it gitlab-runner gitlab-runner register   --url https://gitlab.com/ --executor docker   --docker-image docker:27-cli --docker-privileged   --tag-list iran-vpn
```

`--docker-privileged` is not optional: the `build` job runs `docker:27-dind`,
and without it every build stops on "Cannot connect to the Docker daemon".

The token comes from Settings → CI/CD → Runners. Until a runner carries that
tag, the deploy job sits pending with "no runner matching" and no other
explanation. And the laptop has to be on — that is the whole trade for not
needing a machine that can reach both networks.

### 4. The server side

The server cannot clone the repository, so the first copy arrives the same way
every later one does:

```bash
make ship                    # from the laptop, into /srv/dental
```

Then, on the server, before anything will build:

```bash
cd /srv/dental
cp deploy/env/.env.production.example deploy/env/.env.production
# fill in every CHANGE-ME, and the mirror block at the bottom
sh scripts/check-mirrors.sh  # says which mirrors this machine can reach
```

`ship.sh` stops with a readable message if that env file is missing, rather
than building against defaults. Then the first deploy by hand, following
[deploying.md](deploying.md). CI takes over from the second one.

### 5. Protect the branches

Settings → Repository → Protected branches: protect `master` and `develop`.
Without this the Protected variables are never exposed and every deploy job
fails on a missing `SSH_PRIVATE_KEY`.

---

## What the test job checks

```
cd src
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The middle one earns its place: it fails when a model was edited without
generating the migration. Without it, that lands on the server, the entrypoint
runs `migrate`, finds nothing to apply, and the schema silently disagrees with
the code — which surfaces later as a column-does-not-exist error on a page
nobody touched.

The suite needs no Postgres or Redis service. `utils/test_runner.py` swaps in
SQLite, a local-memory cache and inline Celery, so the ~500 tests run in about
seven seconds.

The `security` job runs `pip-audit` and is `allow_failure: true` — a CVE
published overnight should be visible, but it should not block a deploy that
fixes something else.

---

## What is deliberately not here

**No auto-deploy on a tag.** Tags and branches doing different things is one
mechanism too many for a project this size.

**No blue/green or zero-downtime.** `up -d` restarts the containers, which is
a few seconds of downtime. For a clinic site that is cheaper than the
complexity of running two stacks.

**No CD to develop.** Develop runs on your laptop.
