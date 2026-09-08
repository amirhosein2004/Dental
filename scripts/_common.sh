#!/usr/bin/env sh
#
# Shared setup for every script in this folder. Sourced, never run directly.
#
# The job here is to answer one question: how do I run `manage.py` on this
# machine? On a server the app lives inside a container; on a laptop it is a
# virtualenv. Every script needs the same answer, so it is worked out once.
#
set -eu

# Repo root, however the script was invoked — `./scripts/backup.sh`,
# `/srv/dental/scripts/backup.sh`, or from cron with no working directory at
# all. cron in particular starts in `/`, which is why nothing here may assume
# a relative path.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Which environment's stack to act on. Set it in the crontab or export it.
DENTAL_ENV="${DENTAL_ENV:-production}"

case "$DENTAL_ENV" in
    develop|stage|production) ;;
    *)
        echo "DENTAL_ENV must be develop, stage or production (got: $DENTAL_ENV)" >&2
        exit 2
        ;;
esac

ENV_FILE="deploy/env/.env.$DENTAL_ENV"
COMPOSE_FILES="-f deploy/base.yml -f deploy/$DENTAL_ENV.yml"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
die() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; exit 1; }

# --- How to reach Django ----------------------------------------------------
# Docker if the stack is configured and reachable, otherwise a local Python.
# Explicit override: DENTAL_USE_DOCKER=0 or 1.
detect_runner() {
    if [ "${DENTAL_USE_DOCKER:-auto}" = "0" ]; then
        RUNNER="local"
    elif [ "${DENTAL_USE_DOCKER:-auto}" = "1" ]; then
        RUNNER="docker"
    elif [ -f "$ENV_FILE" ] && command -v docker >/dev/null 2>&1; then
        RUNNER="docker"
    else
        RUNNER="local"
    fi
}

# Variables that have to survive the jump into the container.
#
# `docker compose exec` starts the process with the *container's* environment,
# so exporting something in this shell does not reach it. That is how
# `create-superuser.sh` came to export DJANGO_SUPERUSER_PASSWORD and get
# "CommandError: missing: username, email, password" back from inside — the
# script looked correct and the account was never created.
#
# `-e NAME` with no `=value` tells compose to take the value from this
# environment, which keeps the password out of the argument list and so out of
# `ps` for anyone else on the host.
FORWARDED_VARS="DJANGO_SUPERUSER_USERNAME DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_PASSWORD DJANGO_SUPERUSER_FIRST_NAME DJANGO_SUPERUSER_LAST_NAME"

forwarded_env_flags() {
    _flags=""
    for _name in $FORWARDED_VARS; do
        eval "_value=\${$_name:-}"
        [ -z "$_value" ] || _flags="$_flags -e $_name"
    done
    printf '%s' "$_flags"
}

# Run a manage.py command wherever the app actually lives.
#
# `exec -T` rather than `run`: `run` starts a *new* container, which for a
# backup means a second process connecting to the database and, on some
# setups, a second set of volumes. `exec` uses the container already serving
# the site, so it sees exactly the configuration production is running.
manage() {
    detect_runner

    if [ "$RUNNER" = "docker" ]; then
        [ -f "$ENV_FILE" ] || die "missing $ENV_FILE — copy it from $ENV_FILE.example"
        # shellcheck disable=SC2086
        docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T \
            $(forwarded_env_flags) web python manage.py "$@"
    else
        PY="python"
        [ -x "venv/bin/python" ] && PY="venv/bin/python"
        [ -x "venv/Scripts/python.exe" ] && PY="venv/Scripts/python.exe"
        # `src/manage.py`, not `manage.py`: the application lives under src/
        # while these scripts run from the repository root. Inside the
        # container /app *is* src/, which is why the docker branch above needs
        # no equivalent.
        DJANGO_ENV="$DENTAL_ENV" "$PY" src/manage.py "$@"
    fi
}

# Same, but for a command that needs a terminal (createsuperuser prompting).
manage_interactive() {
    detect_runner

    if [ "$RUNNER" = "docker" ]; then
        [ -f "$ENV_FILE" ] || die "missing $ENV_FILE — copy it from $ENV_FILE.example"
        # shellcheck disable=SC2086
        docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec \
            $(forwarded_env_flags) web python manage.py "$@"
    else
        PY="python"
        [ -x "venv/bin/python" ] && PY="venv/bin/python"
        [ -x "venv/Scripts/python.exe" ] && PY="venv/Scripts/python.exe"
        DJANGO_ENV="$DENTAL_ENV" "$PY" src/manage.py "$@"
    fi
}
