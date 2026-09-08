#!/usr/bin/env sh
#
# Restore the database from a backup file.
#
#   scripts/restore.sh backups/dental-20260824-030000.sql
#
# DESTRUCTIVE. This replaces the current database. It asks for confirmation
# and takes a safety backup first, because the usual reason to restore is that
# something already went wrong — and a restore of the wrong file at that point
# turns a recoverable morning into an unrecoverable one.
#
set -eu
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

DUMP="${1:-}"
[ -n "$DUMP" ] || die "usage: scripts/restore.sh <path-to-dump>"
[ -f "$DUMP" ] || die "no such file: $DUMP"

echo
echo "  Restore into: $DENTAL_ENV"
echo "  From:         $DUMP ($(du -h "$DUMP" | cut -f1))"
echo
echo "  This REPLACES the current database. Everything written since that"
echo "  dump was taken is lost."
echo
printf 'Type the environment name to confirm: '
read -r CONFIRM

[ "$CONFIRM" = "$DENTAL_ENV" ] || die "cancelled"

# A backup of what is about to be overwritten. If the dump turns out to be the
# wrong one, this is the only way back.
log "taking a safety backup of the current state first"
manage backup_db --keep 10 || die "safety backup failed — refusing to restore"

detect_runner

if [ "$RUNNER" = "docker" ]; then
    DB_NAME="$(grep '^DB_NAME=' "$ENV_FILE" | cut -d= -f2-)"
    DB_USER="$(grep '^DB_USER=' "$ENV_FILE" | cut -d= -f2-)"

    # Clear the schema first rather than trusting the dump to do it. Dumps
    # taken before `--clean` was added carry no DROP statements at all, and
    # applying one of those over a live database merges into it: the tables
    # already exist, every CREATE fails, and rows written after the dump stay
    # behind. Starting from an empty schema makes the outcome identical
    # whatever vintage the file is.
    log "clearing the current schema in $DB_NAME"
    # shellcheck disable=SC2086
    docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
        psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 -q \
        -c "DROP SCHEMA IF EXISTS public CASCADE;" \
        -c "CREATE SCHEMA public;" \
        -c "GRANT ALL ON SCHEMA public TO \"$DB_USER\";" \
        -c "GRANT ALL ON SCHEMA public TO public;" \
        || die "could not clear the schema — nothing was changed"

    log "restoring into $DB_NAME"
    # ON_ERROR_STOP: psql's default is to report each failure and carry on to
    # the end, then exit 0. That is how a restore can print pages of ERROR and
    # still be called a success.
    #
    # --single-transaction: the schema is already dropped by this point, so a
    # failure halfway through would otherwise leave a half-populated database
    # and no way back except the safety backup.
    # shellcheck disable=SC2086
    docker compose --env-file "$ENV_FILE" $COMPOSE_FILES exec -T db \
        psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 --single-transaction -q < "$DUMP" \
        || die "restore failed and was rolled back — the safety backup is in backups/"
else
    die "local restore is not automated: run psql or copy the sqlite file by hand"
fi

log "restore finished"
log "restart the app so it drops any cached rows: docker compose ... restart web worker"
