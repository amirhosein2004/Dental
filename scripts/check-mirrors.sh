#!/usr/bin/env sh
#
# Run this ON THE SERVER, before the first build there.
#
# The production host is in Iran and reaches almost nothing the build needs.
# Which of the mirrors is currently working is not a fact that stays true —
# Iranian Docker Hub mirrors in particular appear, get overloaded and shut
# down on a timescale of months — so this asks the machine rather than
# trusting a list written six months ago.
#
#   sh scripts/check-mirrors.sh
#
# Every OK line is a host the build can use. Every FAIL line is one that has
# to be replaced in deploy/env/.env.production before `make ENV=production
# up-build` will get past it.
set -eu

# 10s: long enough for a slow Iranian mirror, short enough that a blocked host
# fails now rather than in three minutes. A blocked address usually hangs
# until the timeout rather than refusing the connection outright, which is why
# this is a timeout and not a retry count.
TIMEOUT=10

# Which Debian suite to ask about. The image is built FROM python:3.12-slim,
# and that tracks Debian's releases — it was bookworm, it is trixie now — so a
# hardcoded suite here quietly checks the wrong paths after a base image bump.
# Asked of the image itself when docker can reach it, with the current answer
# as the fallback for a host where it cannot.
SUITE="$(docker run --rm python:3.12-slim sh -c '. /etc/os-release; echo $VERSION_CODENAME' 2>/dev/null || true)"
SUITE="${SUITE:-trixie}"
echo "Debian suite: $SUITE"

probe() {
    _label="$1"
    _url="$2"
    if curl -fsS --max-time "$TIMEOUT" -o /dev/null "$_url" 2>/dev/null; then
        printf '  OK    %-22s %s\n' "$_label" "$_url"
        return 0
    fi
    printf '  FAIL  %-22s %s\n' "$_label" "$_url"
    return 1
}

echo
echo "What the image build fetches, upstream:"
probe "debian archive"   "https://deb.debian.org/debian/dists/$SUITE/Release" || true
probe "debian security"  "https://security.debian.org/debian-security/dists/$SUITE-security/Release" || true
probe "pgdg repo"        "https://apt.postgresql.org/pub/repos/apt/dists/$SUITE-pgdg/Release" || true
probe "pgdg key"         "https://www.postgresql.org/media/keys/ACCC4CF8.asc" || true
probe "pypi"             "https://pypi.org/simple/django/" || true

# What is configured, if anything is. Sourcing the env file rather than asking
# for the values again: the point is to test what the build will actually use,
# not what someone remembers setting.
if [ -f deploy/env/.env.production ]; then
    # shellcheck disable=SC1091
    APT_MIRROR="$(sed -n 's/^APT_MIRROR=//p' deploy/env/.env.production)"
    PYPI_INDEX_URL="$(sed -n 's/^PYPI_INDEX_URL=//p' deploy/env/.env.production)"
    PGDG_URL="$(sed -n 's/^PGDG_URL=//p' deploy/env/.env.production)"
fi

echo
echo "What deploy/env/.env.production currently points at:"
if [ -n "${APT_MIRROR:-}" ]; then
    # Both derived paths, because APT_MIRROR replaces only the host: apt asks
    # for $APT_MIRROR/debian and $APT_MIRROR/debian-security, and a mirror
    # carrying the first but not the second fails halfway through `apt-get
    # update` with a 404 that names a path nobody configured.
    probe "APT_MIRROR debian"   "$APT_MIRROR/debian/dists/$SUITE/Release" || true
    probe "APT_MIRROR security" "$APT_MIRROR/debian-security/dists/$SUITE-security/Release" || true
else
    echo "  ----  APT_MIRROR             unset (build will use deb.debian.org)"
fi
if [ -n "${PYPI_INDEX_URL:-}" ]; then
    probe "PYPI_INDEX_URL"      "$PYPI_INDEX_URL/django/" || true
else
    echo "  ----  PYPI_INDEX_URL        unset (build will use pypi.org)"
fi
[ -n "${PGDG_URL:-}" ] && { probe "PGDG_URL" "$PGDG_URL/dists/$SUITE-pgdg/Release" || true; }

echo
echo "Candidates, if the above came back FAIL. Not a recommendation — Iranian"
echo "mirrors move and close, and this is what asking beats guessing:"
probe "arvan (debian)"   "https://mirror.arvancloud.ir/repo/debian/dists/$SUITE/Release" || true
probe "arvan (security)" "https://mirror.arvancloud.ir/repo/debian-security/dists/$SUITE-security/Release" || true
probe "runflare pypi"    "https://mirror-pypi.runflare.com/simple/django/" || true

echo
echo "Docker Hub. The daemon does the pulling, so this asks the daemon:"
if command -v docker >/dev/null 2>&1; then
    # `python:3.12-slim` and not `hello-world`: it is the base image this
    # project actually needs, and some mirrors carry the small official images
    # while timing out on anything with real layers.
    if docker pull python:3.12-slim >/dev/null 2>&1; then
        echo "  OK    docker pull            python:3.12-slim"
    else
        echo "  FAIL  docker pull            python:3.12-slim"
        echo
        echo "  Configure a mirror in /etc/docker/daemon.json:"
        echo '      { "registry-mirrors": ["https://<mirror-host>"] }'
        echo "  then: sudo systemctl restart docker"
        echo
        echo "  Current registry mirrors:"
        docker info --format '{{range .RegistryConfig.Mirrors}}      {{.}}{{"\n"}}{{end}}' 2>/dev/null \
            || echo "      (none)"
    fi
else
    echo "  SKIP  docker is not installed on this host"
fi

echo
echo "The four base images the stack pulls without building them:"
for image in postgres:17 redis:7-alpine nginx:1.27-alpine certbot/certbot:latest; do
    if command -v docker >/dev/null 2>&1 && docker pull "$image" >/dev/null 2>&1; then
        printf '  OK    %s\n' "$image"
    else
        printf '  FAIL  %s\n' "$image"
    fi
done

echo
echo "Anything FAIL above is a mirror to set in deploy/env/.env.production"
echo "(APT_MIRROR, PYPI_INDEX_URL, PYPI_TRUSTED_HOST) or, for the images, a"
echo "registry-mirrors entry in /etc/docker/daemon.json."
echo
echo "If the pgdg lines failed: they do not have to work. Debian trixie ships"
echo "postgresql-client-17 itself, so USE_PGDG=0 drops that repository and"
echo "leaves the build needing only Debian and PyPI. Keep USE_PGDG=1 only if"
echo "PG_MAJOR has moved past what Debian carries."
echo
