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

## The image is built once

CI builds one image, tags it with the commit SHA, pushes it to GitLab's
registry. Production pulls that tag — the same bytes the tests ran against.

The alternative — the server running `docker compose build` for itself — means
the bytes on production were compiled from source at a different time, on a
different machine, possibly resolving a dependency to a different version. The
thing you tested and the thing you shipped are then not the same thing.

`APP_IMAGE` is how the compose files pick it up:

```yaml
image: ${APP_IMAGE:-dental-app:local}
```

Unset — on your laptop — it falls back to a locally built image and everything
works as before. Set by CI, all three app services (`web`, `worker`, `backup`)
move together, which matters: a worker running last week's code against this
week's schema fails in ways that are hard to read.

---

## Rolling back

The tag is the commit SHA, so a rollback is "point at the older tag":

1. Pipelines → the `rollback:production` job
2. Set `ROLLBACK_SHA` to the short SHA you want
3. Run it

**This rolls back code, not the database.** If the bad deploy included a
migration that changed data, restoring is the fix — see
[`../scripts/README.md`](../scripts/README.md#restoring). The production deploy
job takes a backup *before* it migrates, precisely so that file exists.

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
| `SSH_KNOWN_HOSTS` | Variable, Protected | output of `ssh-keyscan -H your.server` |
| `DEPLOY_USER` | Variable, Protected | the SSH user on the server |
| `DEPLOY_HOST` | Variable, Protected | the server's hostname or IP |
| `DEPLOY_PATH` | Variable, Protected | where the repo is, e.g. `/srv/dental` |

`CI_REGISTRY*` are provided by GitLab; you do not set them.

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

### 3. The server side

The server needs the repository present (for the compose files and nginx
config) but never builds from it:

```bash
git clone <repo> /srv/dental
cd /srv/dental
cp deploy/env/.env.production.example deploy/env/.env.production
# fill in every CHANGE-ME
```

Then the first deploy by hand, following [deploying.md](deploying.md). CI takes
over from the second one.

### 4. Protect the branches

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
