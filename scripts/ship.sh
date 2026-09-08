#!/usr/bin/env sh
#
# Ship the repository to the production server over SSH and build it there.
#
#   sh scripts/ship.sh
#   SHIP_REF=HEAD~1 sh scripts/ship.sh      # ship an older commit
#   SHIP_DIRTY=1 sh scripts/ship.sh         # ship the working tree, warts and all
#
# Why this exists rather than a registry: the server reaches neither GitHub
# nor GitLab nor Docker Hub, so it can neither `git pull` nor `docker pull`
# the application image. It can, however, accept an SSH connection and build
# from Iranian mirrors at its own bandwidth — which is a great deal more than
# the laptop's upstream. So the code travels over SSH and the build happens at
# the far end.
#
# Nothing is written to disk on either side: `git archive` streams into ssh,
# which streams into tar. A failure anywhere in the pipe leaves the server
# exactly as it was, because the build only starts after the transfer returns.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# --- Where it goes ----------------------------------------------------------
# Overridable so this file carries no secret and works for a second server.
# The defaults are the real ones; the port is not 22 because the server moved
# sshd off it.
SHIP_HOST="${SHIP_HOST:-87.248.131.223}"
SHIP_PORT="${SHIP_PORT:-9011}"
SHIP_USER="${SHIP_USER:-amiiiriii}"
SHIP_PATH="${SHIP_PATH:-/srv/dental}"
SHIP_REF="${SHIP_REF:-HEAD}"

SSH="ssh -p $SHIP_PORT $SHIP_USER@$SHIP_HOST"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is not on PATH"
git rev-parse --git-dir >/dev/null 2>&1 || die "not a git repository"

REV="$(git rev-parse --short "$SHIP_REF")" || die "no such ref: $SHIP_REF"

# --- What travels -----------------------------------------------------------
# `git archive` rather than `tar` of the directory, and this is the whole
# reason the script is worth having. tar of the working tree ships whatever
# happens to be lying around: venv/, __pycache__/, node_modules/, a 4GB
# backups/ directory, and — the one that matters — deploy/env/.env.production
# if a copy was ever pulled down to the laptop for reference. git archive ships
# tracked files at a named commit and nothing else, so the transfer is
# reproducible and cannot leak a local file that was never meant to leave.
#
# The escape hatch is SHIP_DIRTY=1, for trying an uncommitted change against
# the server. It uses the same exclude list the .dockerignore does, but it is
# still the blunt instrument — commit the change instead, when it works.
if [ "${SHIP_DIRTY:-0}" = "1" ]; then
    log "shipping the WORKING TREE (uncommitted changes included)"
    PACK="tar -czf - --exclude=.git --exclude=venv --exclude=node_modules \
          --exclude=__pycache__ --exclude=backups --exclude=deploy/env/.env.* ."
else
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log "note: uncommitted changes are NOT being shipped (SHIP_DIRTY=1 to include them)"
    fi
    log "shipping $SHIP_REF ($REV)"
    PACK="git archive --format=tar $SHIP_REF | gzip"
fi

# --- Transfer ---------------------------------------------------------------
# `tar -xzf -` extracts over what is there without deleting anything, which is
# deliberate: deploy/env/.env.production and backups/ live on the server and
# are not in the repository. It also means a file deleted from the repository
# stays behind on the server until someone removes it — worth knowing the day
# an old compose overlay keeps being picked up.
log "transferring to $SHIP_USER@$SHIP_HOST:$SHIP_PATH"
# shellcheck disable=SC2086
eval "$PACK" | $SSH "mkdir -p '$SHIP_PATH' && tar -xzf - -C '$SHIP_PATH'" \
    || die "transfer failed"

# --- Build and start, on the server ----------------------------------------
# The full compose invocation, not a bare `docker compose build`: without
# --env-file and both overlays, compose reads no COMPOSE_PROJECT_NAME and
# builds against a different project than the one that is running — a stack
# that comes up beside production instead of replacing it, on develop's
# volumes.
#
# The backup runs before the build for the same reason the CI job takes one:
# the entrypoint migrates on the way up, and a migration is the one deploy
# step that cannot be undone by starting the old image again.
log "building on the server"
$SSH "bash -s" <<REMOTE || die "remote build failed"
set -euo pipefail
cd '$SHIP_PATH'

test -f deploy/env/.env.production || {
  echo "deploy/env/.env.production is missing on the server."
  echo "Copy deploy/env/.env.production.example to it and fill it in — the"
  echo "mirror settings at the bottom are what makes the build work here."
  exit 1
}

COMPOSE="docker compose --env-file deploy/env/.env.production -f deploy/base.yml -f deploy/production.yml"

if \$COMPOSE ps --status running --quiet web | grep -q .; then
  \$COMPOSE exec -T web python manage.py backup_db --keep 5
else
  echo "web is not running — skipping the pre-deploy backup"
fi

# APP_IMAGE stays unset on purpose. base.yml then falls back to
# dental-app:local, which is what \`build\` tags, so the server runs the image
# it just built rather than looking for one in a registry it cannot reach.
\$COMPOSE build
\$COMPOSE up -d
docker image prune -f
REMOTE

log "deployed $REV"
log "checking the site"
# From the laptop, not the server: this is the path a visitor takes, so it
# also catches an nginx or a certificate that is broken from outside while
# the container itself looks healthy.
sleep 15
curl -fsS --retry 5 --retry-delay 5 https://sbdental.ir/healthz \
    && log "healthz OK" \
    || die "the site did not come back — check: $SSH 'cd $SHIP_PATH && docker compose logs --tail 50 web'"
