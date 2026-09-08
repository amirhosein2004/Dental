#!/usr/bin/env sh
#
# Prepare the production server to build this project. Run once, from the
# laptop, before the first `make ship`:
#
#   make provision
#
# It installs Docker and Compose v2, points the daemon at an Iranian registry
# mirror, and creates /srv/dental owned by the deploy user. After it, `make
# ship` has everything it needs.
#
# PRODUCTION ONLY, and there is no develop equivalent on purpose: a develop
# stack runs on the laptop, where Docker is already installed and Docker Hub
# is reachable. The entire subject of this script is a machine that cannot
# reach Docker Hub.
#
# Idempotent. Every step checks whether it is already done, so re-running it
# after a server rebuild, or to pick up a changed mirror, costs one check per
# step and changes nothing else.
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# The same four variables ship.sh reads, so one export configures both and a
# second server needs no commit.
SHIP_HOST="${SHIP_HOST:-87.248.131.223}"
SHIP_PORT="${SHIP_PORT:-9011}"
SHIP_USER="${SHIP_USER:-amiiiriii}"
SHIP_PATH="${SHIP_PATH:-/srv/dental}"

# The registry mirror the daemon uses for python:3.12-slim, postgres:17,
# redis:7-alpine, nginx:1.27-alpine and certbot.
#
# Deliberately NOT in deploy/env/.env.production with the other mirrors: those
# are build arguments, consumed by apt and pip inside the build. These images
# are pulled by dockerd itself, which never reads that file. Putting it there
# is the mistake that looks like it worked and then times out on the first
# pull with nothing saying why.
DOCKER_REGISTRY_MIRROR="${DOCKER_REGISTRY_MIRROR:-https://docker.arvancloud.ir}"

# The hosting provider's own apt mirror setup. Without it `apt-get update`
# fails outright — deb.debian.org is not reachable from this machine — and
# nothing below can install. Skipped automatically once apt works.
APT_MIRROR_SETUP_URL="${APT_MIRROR_SETUP_URL:-https://mirror.parsvds.com/scripts/parsvds-mirror-setup.sh}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

command -v ssh >/dev/null 2>&1 || die "ssh is not on PATH"

# --- The remote half --------------------------------------------------------
# Written to a file and sent, rather than piped into `ssh "bash -s"`. The
# remote side needs sudo, sudo needs a TTY to prompt for a password, and
# `ssh -t` refuses to allocate one when stdin is a heredoc — `ssh -tt` does
# allocate it and then hangs at the end, because a pty never delivers the EOF
# that ends `bash -s`. Sending the script first leaves stdin free for the
# prompt.
#
# It also means the whole thing runs under one `sudo`, so nothing inside needs
# to guess which individual commands are privileged.
REMOTE_SCRIPT="$(mktemp)"
trap 'rm -f "$REMOTE_SCRIPT"' EXIT INT TERM

cat > "$REMOTE_SCRIPT" <<'REMOTE'
#!/usr/bin/env bash
# Runs as root on the production server. Arguments, in order:
#   $1 deploy user   $2 install path   $3 registry mirror
#   $4 apt mirror setup URL            $5 skip apt mirror (0|1)
set -euo pipefail

DEPLOY_USER="$1"
INSTALL_PATH="$2"
REGISTRY_MIRROR="$3"
APT_SETUP_URL="$4"
SKIP_APT_MIRROR="$5"

say() { echo; echo "== $* =="; }

id "$DEPLOY_USER" >/dev/null 2>&1 || {
  echo "no such user: $DEPLOY_USER"; exit 1; }

# --- 1. apt ---------------------------------------------------------------
# `--error-on=any` for the same reason the Dockerfile uses it: without it apt
# treats an index it could not fetch as a warning and exits 0, so a dead
# mirror is reported three lines later as a missing package.
say "apt"
if [ "$SKIP_APT_MIRROR" = "1" ]; then
  echo "mirror setup skipped (PROVISION_SKIP_APT_MIRROR=1)"
  apt-get update --error-on=any
elif apt-get update --error-on=any >/dev/null 2>&1; then
  echo "apt already reaches its archive — sources left alone"
else
  echo "configuring mirrors from $APT_SETUP_URL"
  # Fetched to a file and hashed before it runs, rather than piped straight
  # into a root shell. This is still a remote script executing as root; the
  # hash makes it reviewable and makes a changed script visible on the next
  # run. It is not a substitute for trusting the provider, and it is only
  # here because without a working apt this machine cannot install anything.
  tmp="$(mktemp)"
  curl -fsSL "$APT_SETUP_URL" -o "$tmp"
  echo "sha256: $(sha256sum "$tmp" | cut -d' ' -f1)"
  bash "$tmp"
  rm -f "$tmp"
  apt-get update --error-on=any
fi

# --- 2. Docker engine -----------------------------------------------------
say "docker engine"
if command -v docker >/dev/null 2>&1; then
  echo "already installed — $(docker --version)"
else
  apt-get install -y --no-install-recommends docker.io
fi
systemctl enable --now docker >/dev/null 2>&1 || true

# --- 3. Compose v2 --------------------------------------------------------
# v2, the plugin, invoked as `docker compose`. NOT the `docker-compose`
# package, which is the Python v1 tool that most Iranian install guides still
# name: this project's overlays use `depends_on.condition: service_healthy`
# and a YAML anchor for the shared build block, and v1 reads neither. It gets
# you a stack whose web container starts before Postgres is ready and two
# images built from one tag, with no error saying so.
say "docker compose v2"
if docker compose version >/dev/null 2>&1; then
  echo "already present — $(docker compose version)"
else
  apt-get install -y --no-install-recommends docker-compose-v2 \
    || apt-get install -y --no-install-recommends docker-compose-plugin \
    || {
      echo "Neither docker-compose-v2 (Debian's name) nor docker-compose-plugin"
      echo "(Docker's own) is available from the configured mirrors."
      echo
      echo "Do NOT fall back to 'apt install docker-compose'. That is v1 and"
      echo "this project's compose files do not work with it."
      exit 1
    }
  docker compose version
fi

# --- 4. Registry mirror ---------------------------------------------------
# Merged into daemon.json, never written over it. That file may already carry
# a storage driver, log rotation or an insecure registry, and replacing all of
# it would take those away silently — with the damage only visible after the
# restart two lines below.
say "registry mirror: $REGISTRY_MIRROR"
if [ -f /etc/docker/daemon.json ] && grep -q -- "$REGISTRY_MIRROR" /etc/docker/daemon.json; then
  echo "already configured"
else
  install -d -m 755 /etc/docker
  if [ -f /etc/docker/daemon.json ]; then
    stamp="$(date +%Y%m%d-%H%M%S)"
    cp /etc/docker/daemon.json "/etc/docker/daemon.json.bak-$stamp"
    echo "existing config backed up to /etc/docker/daemon.json.bak-$stamp"
    if command -v python3 >/dev/null 2>&1; then
      python3 - "$REGISTRY_MIRROR" <<'PY'
import json, sys

path = "/etc/docker/daemon.json"
with open(path) as fh:
    cfg = json.load(fh)

mirrors = cfg.setdefault("registry-mirrors", [])
if sys.argv[1] not in mirrors:
    mirrors.insert(0, sys.argv[1])

with open(path, "w") as fh:
    json.dump(cfg, fh, indent=2)
    fh.write("\n")
PY
      echo "merged"
    else
      echo "python3 is not installed, so the existing daemon.json cannot be"
      echo "merged without risking the keys already in it. Add this by hand:"
      echo "    \"registry-mirrors\": [\"$REGISTRY_MIRROR\"]"
      echo "then re-run."
      exit 1
    fi
  else
    printf '{\n  "registry-mirrors": ["%s"]\n}\n' "$REGISTRY_MIRROR" \
      > /etc/docker/daemon.json
    echo "written"
  fi
  systemctl restart docker
fi

# --- 5. The deploy user ---------------------------------------------------
say "deploy user: $DEPLOY_USER"
if id -nG "$DEPLOY_USER" | tr ' ' '\n' | grep -qx docker; then
  echo "already in the docker group"
else
  # Worth being explicit about: membership of the docker group is root on this
  # host by any measure — it can bind-mount / into a container. It is granted
  # so ship.sh needs no sudo at the far end, and it is acceptable here only
  # because the deploy user and the administrator are the same person on this
  # machine. On one where they are not, this is the line to reconsider.
  usermod -aG docker "$DEPLOY_USER"
  echo "added to the docker group — the next login picks it up"
fi

# --- 6. Where the code lands ----------------------------------------------
say "install path: $INSTALL_PATH"
install -d -m 755 "$INSTALL_PATH"
# `user:` rather than `user:group`: the primary group is not always named
# after the account, and a wrong group name makes chown fail outright.
chown "$DEPLOY_USER:" "$INSTALL_PATH"
ls -ld "$INSTALL_PATH"

# --- 7. Prove it ----------------------------------------------------------
# A pull that works is the one thing that cannot be checked from the laptop:
# it is the only test of whether this machine's route to the registry mirror
# is open, as opposed to the mirror merely existing.
say "verifying"
docker compose version
docker pull hello-world >/dev/null && echo "registry mirror reachable"
docker run --rm hello-world >/dev/null && echo "containers run"
docker rmi hello-world >/dev/null 2>&1 || true

echo
echo "server ready."
REMOTE

log "provisioning $SHIP_USER@$SHIP_HOST:$SHIP_PORT"
log "registry mirror: $DOCKER_REGISTRY_MIRROR"

REMOTE_PATH="/tmp/dental-provision.$$.sh"

# shellcheck disable=SC2086
ssh -p "$SHIP_PORT" "$SHIP_USER@$SHIP_HOST" "cat > '$REMOTE_PATH'" < "$REMOTE_SCRIPT" \
    || die "could not copy the provisioning script to the server"

# -t so sudo has a terminal to ask for a password on. The remote file is
# removed whether the script succeeded or not, so a failed run leaves nothing
# executable lying in /tmp.
ssh -t -p "$SHIP_PORT" "$SHIP_USER@$SHIP_HOST" \
    "sudo bash '$REMOTE_PATH' '$SHIP_USER' '$SHIP_PATH' '$DOCKER_REGISTRY_MIRROR' '$APT_MIRROR_SETUP_URL' '${PROVISION_SKIP_APT_MIRROR:-0}'; rc=\$?; rm -f '$REMOTE_PATH'; exit \$rc" \
    || die "provisioning failed — nothing was left running on the server"

log "provisioned"
echo
echo "Next:"
echo "  1. make ship          # scaffolds deploy/env/.env.production, then stops"
echo "  2. fill that file in on the server (mirrors at the bottom;"
echo "     'sh scripts/check-mirrors.sh' there says which ones work today)"
echo "  3. make ship          # this one builds and starts the stack"
