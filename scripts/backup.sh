#!/usr/bin/env sh
#
# Take a database backup, keeping only the newest few.
#
# Built to be run from cron, which means two things it does not look like it
# needs: it resolves its own paths (cron starts in `/`), and it logs with
# timestamps to a file, because cron's own mail is rarely read.
#
# Install the schedule with `scripts/install-cron.sh`, or by hand:
#
#   0 3 */3 * *  DENTAL_ENV=production /srv/dental/scripts/backup.sh
#
#   ^ 03:00 every third day. Not midnight: that is when every other cron on
#     the box runs, and a dump competing with log rotation is slower and more
#     likely to be interrupted.
#
set -eu
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

KEEP="${BACKUP_KEEP:-3}"
LOG_FILE="${BACKUP_LOG:-$PROJECT_ROOT/backups/$DENTAL_ENV/backup.log}"

mkdir -p "$(dirname "$LOG_FILE")"

# Everything from here goes to the log as well as the terminal, so a cron run
# leaves a record and a manual run still shows you what happened.
exec 3>&1
log_both() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE" >&3; }

log_both "backup starting (env=$DENTAL_ENV, keep=$KEEP)"

if manage backup_db --keep "$KEEP" >>"$LOG_FILE" 2>&1; then
    # The command prints what it wrote and what it rotated; echo the tail so a
    # human running this sees the result without opening the log.
    tail -n 3 "$LOG_FILE" >&3
    log_both "backup finished"
else
    log_both "backup FAILED — see $LOG_FILE"
    exit 1
fi

# Keep the log itself from growing without limit. It is a few lines per run,
# but "a few lines per run, forever" is how a disk fills.
if [ -f "$LOG_FILE" ]; then
    tail -n 500 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
