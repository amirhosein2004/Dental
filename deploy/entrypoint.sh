#!/usr/bin/env sh
#
# Runs before every process in the image — web, worker, or a one-off shell.
#
# Lives in deploy/ and not scripts/ on purpose. Everything in scripts/ is
# something a person runs on a server; this is baked into the image (the
# Dockerfile copies it to /usr/local/bin/) and is executed by the container
# itself, every start, with no one watching. Same file extension, different
# category.
#
# The point is that a deploy cannot forget a step. Previously `migrate` and
# `collectstatic` lived in the README as instructions for a human, which meant
# a deploy that skipped them produced a site with an out-of-date schema and no
# stylesheets, and nothing anywhere said so.
#
set -eu

# Steps that touch shared state must run once, not once per container. The
# worker and the web container start together, and two simultaneous `migrate`
# runs race on the same tables.
RUN_MIGRATIONS="${RUN_MIGRATIONS:-0}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-0}"

log() { echo "[entrypoint] $*"; }

# --- Wait for Postgres ------------------------------------------------------
# `depends_on` only waits for the container to start, not for Postgres to
# accept connections — so without this the first boot after `compose up` dies
# on "connection refused" and restarts until the database happens to be ready.
if [ -n "${DB_HOST:-}" ]; then
    log "waiting for postgres at ${DB_HOST}:${DB_PORT:-5432}"
    attempt=0
    until pg_isready --host="$DB_HOST" --port="${DB_PORT:-5432}" --quiet; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 60 ]; then
            log "postgres did not become ready after 60s; giving up"
            exit 1
        fi
        sleep 1
    done
    log "postgres is ready"
fi

# --- Schema -----------------------------------------------------------------
if [ "$RUN_MIGRATIONS" = "1" ]; then
    log "applying migrations"
    python manage.py migrate --noinput
fi

# --- Static assets ----------------------------------------------------------
# Must run in the same image that serves the pages: production hashes filenames
# into a manifest, and a template rendering `{% static %}` raises outright if
# the manifest is missing an entry.
if [ "$RUN_COLLECTSTATIC" = "1" ]; then
    log "collecting static files"
    python manage.py collectstatic --noinput --clear
fi

log "starting: $*"
exec "$@"
