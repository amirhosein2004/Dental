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
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl ca-certificates gnupg \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc]" \
        "https://apt.postgresql.org/pub/repos/apt $(. /etc/os-release && echo $VERSION_CODENAME)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install --no-install-recommends -y "postgresql-client-${PG_MAJOR}" \
    && apt-get purge -y gnupg && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements first, and alone. Docker caches this layer on the file's
# checksum, so editing application code does not reinstall Django.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
