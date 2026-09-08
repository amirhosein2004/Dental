#!/usr/bin/env sh
#
# Obtain the first Let's Encrypt certificate for production. Run once, on the
# server, after the DNS for the domain points at it.
#
#   scripts/init-letsencrypt.sh sbdental.ir www.sbdental.ir you@example.com
#
# Why a script and not a documented `certbot certonly`:
#
# nginx refuses to start when `ssl_certificate` names a file that is not there
# — not just the TLS server block, the whole config is rejected. So on a fresh
# server nginx is down, which means nothing answers on port 80, which means
# Let's Encrypt cannot reach the ACME challenge, which means no certificate
# can be issued, which means nginx will not start. The documented "bring the
# stack up, then issue the certificate" cannot work.
#
# The way out is a throwaway self-signed certificate. nginx starts with that,
# serves the challenge over port 80, certbot replaces the placeholder with a
# real certificate, and nginx reloads.
#
set -eu

# Certificates are a production concern only; develop serves plain HTTP on 8000.
# Set before sourcing, because _common.sh validates DENTAL_ENV.
DENTAL_ENV="${DENTAL_ENV:-production}"
. "$(cd "$(dirname "$0")" && pwd)/_common.sh"

DOMAIN="${1:-}"
WWW_DOMAIN="${2:-}"
EMAIL="${3:-}"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    cat >&2 <<USAGE
usage: scripts/init-letsencrypt.sh <domain> [www-domain] <email>

  scripts/init-letsencrypt.sh sbdental.ir www.sbdental.ir admin@sbdental.ir

The email is where Let's Encrypt sends expiry warnings. It is the only notice
you get if renewal has been quietly failing.
USAGE
    exit 2
fi

[ -f "$ENV_FILE" ] || die "missing $ENV_FILE — copy it from $ENV_FILE.example"

# shellcheck disable=SC2086
COMPOSE="docker compose --env-file $ENV_FILE $COMPOSE_FILES"

# `staging` mode first is worth knowing about: Let's Encrypt allows 5 failed
# attempts per hostname per hour, and a typo in the domain burns them fast.
STAGING="${STAGING:-0}"
STAGING_FLAG=""
if [ "$STAGING" = "1" ]; then
    STAGING_FLAG="--staging"
    echo "STAGING MODE — the certificate issued will not be trusted by browsers."
fi

CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

echo
echo "  Domain : $DOMAIN${WWW_DOMAIN:+, $WWW_DOMAIN}"
echo "  Email  : $EMAIL"
echo

# ---------------------------------------------------------------------------
# 1. Refuse to clobber a real certificate
# ---------------------------------------------------------------------------
if $COMPOSE run --rm --entrypoint "test -f $CERT_PATH/fullchain.pem" certbot 2>/dev/null; then
    echo "A certificate for $DOMAIN already exists."
    echo "Renewal is automatic; there is nothing to do. To replace it anyway,"
    echo "delete the certbot_certs volume first — which also loses the account"
    echo "registration, so only do that deliberately."
    exit 0
fi

# ---------------------------------------------------------------------------
# 2. A placeholder certificate, so nginx can start at all
# ---------------------------------------------------------------------------
log "[1/4] writing a temporary self-signed certificate"
$COMPOSE run --rm --entrypoint "sh -c" certbot "
    mkdir -p '$CERT_PATH'
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -subj '/CN=$DOMAIN' \
        -keyout '$CERT_PATH/privkey.pem' \
        -out '$CERT_PATH/fullchain.pem' 2>/dev/null
    cp '$CERT_PATH/fullchain.pem' '$CERT_PATH/chain.pem'
"

# ---------------------------------------------------------------------------
# 3. Start nginx on that placeholder and prove port 80 answers
# ---------------------------------------------------------------------------
log "[2/4] starting the stack"
$COMPOSE up -d

log "[3/4] waiting for nginx to answer on port 80"
attempt=0
until curl -fsS "http://localhost/healthz" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 30 ]; then
        echo "nginx is not answering. Check: $COMPOSE logs nginx" >&2
        exit 1
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# 4. Replace the placeholder with a real certificate
# ---------------------------------------------------------------------------
log "[4/4] requesting the certificate from Let's Encrypt"

DOMAIN_ARGS="-d $DOMAIN"
[ -n "$WWW_DOMAIN" ] && DOMAIN_ARGS="$DOMAIN_ARGS -d $WWW_DOMAIN"

# `--force-renewal` because the placeholder is technically a valid
# certificate for this name, and certbot would otherwise decline as "not yet
# due for renewal".
if ! $COMPOSE run --rm --entrypoint "certbot certonly --webroot -w /var/www/certbot \
        $STAGING_FLAG $DOMAIN_ARGS \
        --email $EMAIL --agree-tos --no-eff-email \
        --force-renewal --non-interactive" certbot; then
    echo >&2
    echo "Certificate request failed. The placeholder is still in place, so the" >&2
    echo "site is up but untrusted. Most common causes:" >&2
    echo "  * DNS for $DOMAIN does not point at this server yet" >&2
    echo "  * port 80 is not reachable from the internet (firewall, or a" >&2
    echo "    provider that blocks it)" >&2
    echo "  * the rate limit was hit — retry with STAGING=1 to test freely" >&2
    exit 1
fi

log "reloading nginx onto the real certificate"
$COMPOSE exec nginx nginx -s reload

echo
echo "Done. https://$DOMAIN should now be trusted."
echo "Renewal is handled by the certbot service; nothing further to schedule."
