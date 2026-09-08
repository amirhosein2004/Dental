#!/usr/bin/env sh
#
# Install the backup schedule into the current user's crontab.
#
#   scripts/install-cron.sh                  # every 3 days, 03:00
#   DENTAL_ENV=develop scripts/install-cron.sh
#   BACKUP_EVERY_DAYS=1 scripts/install-cron.sh
#
# Idempotent: run it twice and you still have one entry. It matches on a
# marker comment rather than on the command text, so changing the schedule
# replaces the old line instead of adding a second one that also fires.
#
set -eu
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

EVERY_DAYS="${BACKUP_EVERY_DAYS:-3}"
HOUR="${BACKUP_HOUR:-3}"
MARKER="# dental-backup ($DENTAL_ENV)"

command -v crontab >/dev/null 2>&1 || die "crontab not found — this script is for Linux servers"

ENTRY="0 $HOUR */$EVERY_DAYS * * DENTAL_ENV=$DENTAL_ENV BACKUP_KEEP=${BACKUP_KEEP:-3} $PROJECT_ROOT/scripts/backup.sh $MARKER"

# Read the existing crontab, drop any line carrying our marker, add ours back.
# `|| true` because `crontab -l` exits non-zero when there is no crontab yet,
# which is the normal state on a fresh server.
EXISTING="$(crontab -l 2>/dev/null || true)"
FILTERED="$(printf '%s\n' "$EXISTING" | grep -vF "$MARKER" || true)"

printf '%s\n%s\n' "$FILTERED" "$ENTRY" | grep -v '^$' | crontab -

log "installed: backup every $EVERY_DAYS day(s) at ${HOUR}:00, keeping ${BACKUP_KEEP:-3}"
log "environment: $DENTAL_ENV"
echo
echo "Current schedule:"
crontab -l | grep -F "$MARKER" | sed 's/^/  /'
echo
echo "Remove it again with:"
echo "  crontab -l | grep -vF '$MARKER' | crontab -"
