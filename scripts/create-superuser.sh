#!/usr/bin/env sh
#
# Create the first admin account on a server.
#
#   scripts/create-superuser.sh                   # asks for the details
#   DENTAL_ENV=develop scripts/create-superuser.sh
#
# Non-interactive, for a deploy pipeline:
#
#   DJANGO_SUPERUSER_USERNAME=amir \
#   DJANGO_SUPERUSER_EMAIL=a@example.com \
#   DJANGO_SUPERUSER_PASSWORD='...' \
#   scripts/create-superuser.sh
#
# Wraps `manage.py ensure_superuser`, not Django's `createsuperuser`: that one
# with `--noinput` creates the account with an *unusable* password, so it looks
# like it worked until someone tries to sign in.
#
set -eu
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

log "target environment: $DENTAL_ENV"

# Non-interactive path: everything already in the environment.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] \
   && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] \
   && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    log "using DJANGO_SUPERUSER_* from the environment"
    manage ensure_superuser
    exit 0
fi

# Interactive path.
printf 'Username: '
read -r SU_USERNAME
[ -n "$SU_USERNAME" ] || die "username cannot be empty"

printf 'Email: '
read -r SU_EMAIL
[ -n "$SU_EMAIL" ] || die "email cannot be empty"

printf 'First name [مدیر]: '
read -r SU_FIRST
printf 'Last name [سیستم]: '
read -r SU_LAST

# `stty -echo` so the password does not appear on screen or in the scrollback
# of whatever terminal this was run from.
printf 'Password: '
stty -echo 2>/dev/null || true
read -r SU_PASSWORD
stty echo 2>/dev/null || true
printf '\n'

printf 'Password (again): '
stty -echo 2>/dev/null || true
read -r SU_PASSWORD_CONFIRM
stty echo 2>/dev/null || true
printf '\n'

[ -n "$SU_PASSWORD" ] || die "password cannot be empty"
[ "$SU_PASSWORD" = "$SU_PASSWORD_CONFIRM" ] || die "passwords do not match"

# Passed through the environment rather than as arguments: command-line
# arguments are visible to anyone who can run `ps` on this machine.
export DJANGO_SUPERUSER_USERNAME="$SU_USERNAME"
export DJANGO_SUPERUSER_EMAIL="$SU_EMAIL"
export DJANGO_SUPERUSER_PASSWORD="$SU_PASSWORD"
[ -n "$SU_FIRST" ] && export DJANGO_SUPERUSER_FIRST_NAME="$SU_FIRST"
[ -n "$SU_LAST" ] && export DJANGO_SUPERUSER_LAST_NAME="$SU_LAST"

manage ensure_superuser

log "done — sign in at the path your SECURE_ADMIN_PANEL setting names"
