# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# One image for both environments. What changes between develop and
# production is the command and the environment file, never the image — so
# what develop proved is the thing production runs.
#
# `-slim` rather than the full image: the default python image carries a
# compiler toolchain and ~700MB of headers this project never uses at runtime.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# --- Mirrors ----------------------------------------------------------------
# Empty means upstream, which is what a laptop with a working connection
# wants. They exist because the production server builds this image itself and
# reaches none of the originals: deb.debian.org, apt.postgresql.org and
# pypi.org are all blocked from it, while Iranian mirrors of each are not.
#
# Values come from deploy/env/.env.<environment> through the compose `args`
# block, so nothing here is baked in and the same Dockerfile builds on both
# sides. Set them wrong and the failure is loud — apt and pip both stop on an
# unreachable index rather than carrying on with a stale one.
#
# APT_MIRROR replaces the *host part* of Debian's URLs and nothing else, so
# what apt then fetches is `$APT_MIRROR/debian` and
# `$APT_MIRROR/debian-security` — both of those paths have to exist on the
# mirror. Pointing it straight at a mirror's Debian directory yields
# `.../debian/debian` and a 404 on every index file. No trailing slash.
#
# It also has to be a *Debian* mirror carrying the suite this image is built
# on. That is **trixie** as of writing, and it moves with Debian's releases —
# a mirror that only goes back to bookworm will 404 after the next base image
# bump. Check rather than assume:
#
#   docker run --rm python:3.12-slim sh -c '. /etc/os-release; echo $VERSION_CODENAME'
#
# An Ubuntu mirror serves none of these paths at all, and apt reports that as
# a missing release — which reads like a broken mirror rather than a wrong one.
ARG APT_MIRROR=
ARG PGDG_URL=https://apt.postgresql.org/pub/repos/apt
ARG PGDG_ASC_URL=https://www.postgresql.org/media/keys/ACCC4CF8.asc
ARG PYPI_INDEX_URL=
ARG PYPI_TRUSTED_HOST=

# Debian 12 images carry deb822 `/etc/apt/sources.list.d/debian.sources`, older
# ones a one-line `/etc/apt/sources.list`. Rewrite whichever is there; a base
# image that changes format between rebuilds must not silently keep using the
# unreachable original.
RUN if [ -n "$APT_MIRROR" ]; then \
      for f in /etc/apt/sources.list /etc/apt/sources.list.d/debian.sources; do \
        [ -f "$f" ] || continue; \
        sed -i "s|https\?://deb.debian.org|$APT_MIRROR|g; \
                s|https\?://security.debian.org|$APT_MIRROR|g" "$f"; \
      done; \
      echo "apt mirror in use:"; \
      grep -hE '^(URIs:|deb )' /etc/apt/sources.list \
           /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
    fi

# postgresql-client is not for the app — psycopg2-binary ships its own driver.
# It is here for `pg_isready`, which the entrypoint uses to wait for the
# database, and for `pg_dump`, which the backup command shells out to.
#
# The version is pinned to the server's, and must be changed with it: Debian
# ships whatever client is current, and a newer pg_dump writes settings the
# older server rejects. That produced a dump which restored with
# `ERROR: unrecognized configuration parameter "transaction_timeout"` —
# a backup file that existed, looked the right size, and could not be used.
ARG PG_MAJOR=17

# Whether to add PostgreSQL's own apt repository for it.
#
# Debian trixie carries postgresql-client-17 in its own archive, so with
# PG_MAJOR=17 this can be 0 — and on the production server it should be, since
# apt.postgresql.org and www.postgresql.org are two more hosts it cannot reach
# and neither has an Iranian mirror. Turning it off makes the whole build need
# exactly two mirrors: Debian's and PyPI's.
#
# Keep it at 1 when PG_MAJOR moves ahead of what Debian ships — the version
# has to match the server's Postgres, and that constraint outranks the
# convenience of one fewer repository. It stays the default so a bump to 18
# does not silently install a 17 client.
ARG USE_PGDG=1

# `--error-on=any` on both updates below, and it is not decoration. apt treats
# an index it could not fetch as a warning and still exits 0, so a mirror
# answering 503 gets you `E: Unable to locate package curl` three lines later —
# an error naming a package rather than the mirror that is down. With the flag
# the build stops at the fetch and says which URL failed and why.
RUN apt-get update --error-on=any \
    && apt-get install --no-install-recommends -y curl ca-certificates \
    && if [ "$USE_PGDG" = "1" ]; then \
         apt-get install --no-install-recommends -y gnupg; \
         install -d /usr/share/postgresql-common/pgdg; \
         curl -fsSL "$PGDG_ASC_URL" \
           -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc; \
         echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc]" \
           "$PGDG_URL $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" \
           > /etc/apt/sources.list.d/pgdg.list; \
         apt-get update --error-on=any; \
       else \
         echo "PGDG disabled — postgresql-client-${PG_MAJOR} comes from Debian"; \
       fi \
    && apt-get install --no-install-recommends -y "postgresql-client-${PG_MAJOR}" \
    && apt-get purge -y gnupg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && pg_dump --version

WORKDIR /app

# Requirements first, and alone. Docker caches this layer on the file's
# checksum, so editing application code does not reinstall Django.
COPY requirements.txt .
# The flags appear only when the arguments are set — `--index-url ""` is not
# the same as no flag, and pip fails on it with a URL parse error rather than
# falling back to PyPI. A mirror served over plain HTTP, or over HTTPS with a
# certificate pip does not trust, also needs PYPI_TRUSTED_HOST (bare hostname,
# no scheme), otherwise every download dies on an SSL verification error.
RUN pip install --no-cache-dir \
      ${PYPI_INDEX_URL:+--index-url "$PYPI_INDEX_URL"} \
      ${PYPI_TRUSTED_HOST:+--trusted-host "$PYPI_TRUSTED_HOST"} \
      -r requirements.txt

# The entrypoint goes outside /app, not into it. The develop overlay mounts
# the source over /app for live reload, and anything the image had put there
# would vanish behind that mount — including this script, which is what
# ENTRYPOINT names.
#
# `chmod +x` here rather than relying on the host: a Windows checkout does not
# carry the executable bit into the build context, so the ENTRYPOINT below
# would fail with "permission denied" on an image built from this machine.
# The CR strip is the same story one layer down. `.gitattributes` pins this
# file to LF, but that only applies to what git checks out — a file created or
# edited outside that path keeps its CRLF endings, and the container then
# answers `env: 'sh\r': No such file or directory` and restart-loops with no
# hint that line endings are the problem.
COPY deploy/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
 && chmod +x /usr/local/bin/entrypoint.sh

# Only `src/` — the application. deploy/, scripts/ and docs/ are how the thing
# is run and documented, not part of what runs, and copying them in would put
# the compose files and nginx configs inside the running container for no
# reason. `src/*` rather than `src/` so its contents land directly in /app,
# keeping `manage.py` at /app/manage.py.
COPY src/ /app/

# Non-root for the reason any service is: a container process running as root
# is root on every host path it has mounted, including the media volume, which
# is writable by design.
RUN useradd --create-home --uid 1000 dental \
    && mkdir -p /app/staticfiles /app/media /app/sent_emails /app/backups \
    && chown -R dental:dental /app

USER dental

# Ends in `exec "$@"`, so the CMD below (or whatever compose overrides it with)
# becomes PID 1 and receives SIGTERM directly. Without that, a stop signal
# reaches the shell instead and Docker falls back to SIGKILL after 10s —
# cutting off in-flight requests.
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

EXPOSE 8000

# `--access-logfile -` sends the access log to stdout, where `docker logs`
# and any log driver can see it.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
