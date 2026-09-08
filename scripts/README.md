# Scripts

Server-side helpers. All of them work out for themselves whether the app is in
Docker or a local virtualenv, so the same command works on your laptop and on
the server.

Everything here is something **a person runs**, by hand — on a server, with
two exceptions. `ship.sh` runs on the laptop and reaches the server over SSH,
because the server cannot fetch the code itself; `check-mirrors.sh` runs on
whichever machine you are asking about.

| | |
|---|---|
| `ship.sh` | send this commit to the server and build it there — run from the laptop |
| `check-mirrors.sh` | report which mirrors a host can reach — run on the server |
| `init-letsencrypt.sh` | obtain the first TLS certificate — once, per host |
| `backup.sh` | take a backup, keep the newest 3 |
| `install-cron.sh` | schedule that backup every 3 days |
| `create-superuser.sh` | create the first admin account |
| `restore.sh` | restore from a dump — destructive, confirms first |
| `_common.sh` | shared setup; sourced, never run directly |

`deploy/entrypoint.sh` is a shell script too and is deliberately **not** here:
it is baked into the image and run by the container on every start, with
nobody watching. Same file extension, different category — see
[`../deploy/README.md`](../deploy/README.md).

## Which environment

Every script reads `DENTAL_ENV`, defaulting to `production`:

```bash
DENTAL_ENV=develop scripts/backup.sh
```

It must be `develop` or `production` — anything else is refused
rather than guessed at.

## Backups

There are **two** ways backups happen, and you only need one.

### Inside the stack (nothing to install)

`production.yml` includes a `backup` service that runs nightly for as long as
the stack is up. This is the default and needs no setup.

### From the host's cron

Use this if you want backups to keep running while the stack is down, or you
prefer them alongside the machine's other scheduled jobs:

```bash
scripts/install-cron.sh                     # every 3 days at 03:00
BACKUP_EVERY_DAYS=1 scripts/install-cron.sh # nightly
DENTAL_ENV=develop scripts/install-cron.sh
```

Idempotent — run it again and you still have one entry, because it matches on
a marker comment rather than on the command text.

If you use cron, comment out the `backup` service in the compose overlay.
Both running means two dumps on different clocks competing for the same
retention slots.

### Why three, and why three days

Three copies over nine days. Corruption that a nightly rotation would already
have overwritten is still recoverable here — the usual failure is not "the
disk died", it is "something has been quietly wrong since Tuesday".

Retention exists because a backup job without it fills the disk, and a full
disk takes the site down *and* stops the next backup from running.

```bash
scripts/backup.sh                    # keep 3 (default)
BACKUP_KEEP=7 scripts/backup.sh
```

Output goes to `backups/<environment>/backup.log`, trimmed to the last 500 lines. cron's own
mail is rarely read on a server nobody logs into.

## First admin account

```bash
scripts/create-superuser.sh
```

Prompts for username, email, name and password (hidden). Non-interactively:

```bash
DJANGO_SUPERUSER_USERNAME=amir \
DJANGO_SUPERUSER_EMAIL=a@example.com \
DJANGO_SUPERUSER_PASSWORD='...' \
scripts/create-superuser.sh
```

This wraps `manage.py ensure_superuser`, **not** Django's `createsuperuser`.
That one with `--noinput` creates the account with an unusable password — it
looks like it worked right up until someone tries to sign in.

Safe to run twice: an existing account is left alone unless you pass
`--update-password`.

Note that a superuser without `is_doctor` can only use the admin panel, at
whatever path `SECURE_ADMIN_PANEL` names. The doctor login on the site itself
requires the doctor flag.

## Restoring

```bash
scripts/restore.sh backups/production/dental-20260824-030000.sql
```

Replaces the current database. It asks you to type the environment name, and
takes a safety backup first — the usual reason to restore is that something
already went wrong, and restoring the wrong file at that point turns a
recoverable morning into an unrecoverable one.

Afterwards, restart the app so it drops cached rows:

```bash
docker compose --env-file deploy/env/.env.production \
  -f deploy/base.yml -f deploy/production.yml restart web worker
```

## Running these on Windows

They are `sh` scripts for a Linux server. On Windows use Git Bash or WSL, or
call the underlying command directly:

```powershell
python src/manage.py backup_db --keep 3
python src/manage.py ensure_superuser --username amir --email a@example.com --password ...
```

## Deploying

The production server is in Iran: it reaches neither GitHub nor GitLab, so
`git pull` on it is not an option, and it reaches no container registry it is
allowed to use, so `docker pull` is not either. What it can do is accept an
SSH connection and build from Iranian mirrors at its own bandwidth.

```bash
make ship                          # the current commit
SHIP_REF=v1.0.0 sh scripts/ship.sh # a tag or an older commit
SHIP_DIRTY=1 sh scripts/ship.sh    # the working tree, uncommitted changes and all
```

`ship.sh` packs with `git archive`, not with `tar` of the directory, and that
is the point of it: `tar .` ships whatever is lying around — `venv/`,
`node_modules/`, a multi-gigabyte `backups/`, and a `deploy/env/.env.production`
if a copy was ever pulled down for reference. `git archive` ships tracked files
at a named commit and nothing else.

It extracts over what is on the server without deleting anything, which is
deliberate: the env file and `backups/` live there and are not in the
repository. The corollary is that a file deleted from the repository stays
behind on the server until someone removes it.

Before the first build there, `check-mirrors.sh` says which of the hosts the
build needs are actually reachable from that machine today — the answer moves,
so it asks rather than assuming.

Override `SHIP_HOST`, `SHIP_PORT`, `SHIP_USER` or `SHIP_PATH` for a second
server. The same script is what the `deploy:production` job runs, so pressing
the button and running it by hand are the same operation.
