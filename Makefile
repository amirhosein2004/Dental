# One entry point for both environments.
#
# Every compose command in this project carries the same three arguments — an
# env file and two overlays — and getting one wrong is not obvious. Leaving
# out --env-file drops COMPOSE_PROJECT_NAME, and a production `up` then
# attaches to develop's database volume with nothing anywhere saying so. This
# file builds that line once.
#
#   make up                  # develop, the default
#   make ENV=production up
#   make ENV=production logs
#
# Needs GNU make and a POSIX sh. On Windows both come with Git:
# `winget install ezwinports.make`, and make picks up Git's sh.exe from PATH.
#
# Nothing here reimplements a script in scripts/ — the targets that need one
# call it, so the safety checks inside (restore's confirmation prompt, the
# superuser env forwarding) still apply.

# On Windows, make runs its recipes through cmd.exe unless it finds a POSIX
# sh on PATH — and Git only puts its `cmd` directory there, not `usr/bin`. The
# recipes below are ordinary shell (test, pipes, quoting), all of which cmd
# reads differently, so point make at Git's sh explicitly. PROGRA~1 rather
# than "Program Files" because make splits variables on spaces and there is no
# quoting that survives it.
#
# Git's usr/bin joins PATH for the same reason: make short-circuits simple
# recipe lines and runs them without a shell at all, so `echo`, `grep`, `test`
# and `awk` have to exist as real programs rather than as cmd builtins.
ifeq ($(OS),Windows_NT)
  GIT_USR := C:/PROGRA~1/Git/usr/bin
  ifneq ($(wildcard $(GIT_USR)/sh.exe),)
    SHELL := $(GIT_USR)/sh.exe
    .SHELLFLAGS := -c
    export PATH := $(GIT_USR);$(PATH)
  endif
endif

ENV ?= develop

VALID_ENVS := develop production
ifeq ($(filter $(ENV),$(VALID_ENVS)),)
$(error ENV must be one of: $(VALID_ENVS) - got '$(ENV)')
endif

ENV_FILE := deploy/env/.env.$(ENV)
COMPOSE  := docker compose --env-file $(ENV_FILE) \
              -f deploy/base.yml -f deploy/$(ENV).yml


.DEFAULT_GOAL := help
.PHONY: help env-check up up-build build down down-volumes restart ps logs \
        logs-web shell dbshell manage migrate makemigrations collectstatic \
        test check seed superuser backup restore

help:  ## Show this help
	@echo 'usage: make [ENV=develop|production] <target>'
	@echo ''
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'
	@echo ''
	@echo "current ENV: $(ENV)"

# Fail early and in one place. Every target that talks to Docker depends on
# this, so a missing env file reports itself rather than surfacing as compose
# quietly using an empty project name.
env-check:
	@test -f $(ENV_FILE) || { \
	  echo "missing $(ENV_FILE) - copy it from $(ENV_FILE).example"; exit 1; }
	@# Docker creates a missing bind-mount source itself, but as root - and
	@# the image runs as uid 1000, so the first backup would fail on
	@# permissions. Made here instead, owned by whoever ran make.
	@mkdir -p backups/$(ENV)
	@# A `$$` in a value compose interpolates is a silent data corruption.
	@# --env-file values are expanded before compose substitutes them, so a
	@# DB_PASSWORD of `a$$b` reaches Postgres as `a` while Django, which reads
	@# the same file literally through env_file, keeps `a$$b` - and the app then
	@# cannot authenticate against its own database. SECRET_KEY and the rest are
	@# not checked because nothing interpolates them.
	@! grep -qE '^(DB_PASSWORD|DB_NAME|DB_USER|COMPOSE_PROJECT_NAME)=.*[$$]' $(ENV_FILE) || { 	  echo "$(ENV_FILE): a database value contains '$$', which compose expands."; 	  echo "Generate one without that character."; exit 1; }

# --- Lifecycle --------------------------------------------------------------

up: env-check  ## Start the stack in the background
	$(COMPOSE) up -d

up-build: env-check  ## Rebuild the image, then start
	$(COMPOSE) up -d --build

build: env-check  ## Rebuild web and worker only
	$(COMPOSE) build web worker

down: env-check  ## Stop the stack, keep the database
	$(COMPOSE) down

# Separate target and a required CONFIRM, because `down -v` deletes the
# database volume and there is no undo. Mistyping this on production is the
# kind of thing a one-character difference should not be able to do.
down-volumes: env-check  ## Stop AND delete all data (needs CONFIRM=yes)
	@test "$(CONFIRM)" = "yes" || { \
	  echo "this deletes the $(ENV) database permanently."; \
	  echo "re-run as: make ENV=$(ENV) down-volumes CONFIRM=yes"; exit 1; }
	$(COMPOSE) down -v

restart: env-check  ## Recreate the containers
	$(COMPOSE) up -d --force-recreate

# --- Looking at it ----------------------------------------------------------

ps: env-check  ## Show container status
	$(COMPOSE) ps

logs: env-check  ## Follow logs for every service
	$(COMPOSE) logs -f

logs-web: env-check  ## Follow the web container's logs
	$(COMPOSE) logs -f web

shell: env-check  ## Open a shell inside the web container
	$(COMPOSE) exec web sh

# The name and user come from the container's own POSTGRES_* variables rather
# than from anything written here: the database is called dental_develop or
# dental_production depending on the env file, so a hardcoded `-d dental`
# fails with `database "dental" does not exist` in every environment there is.
dbshell: env-check  ## Open psql on the stack's database
	$(COMPOSE) exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

# --- Django -----------------------------------------------------------------

# Escape hatch for anything without its own target:
#   make ENV=production manage ARGS="changepassword amir"
manage: env-check  ## Run manage.py ARGS="..."
	$(COMPOSE) exec -T web python manage.py $(ARGS)

migrate: env-check  ## Apply migrations by hand (the entrypoint already does this on boot)
	$(COMPOSE) exec -T web python manage.py migrate --noinput

makemigrations: env-check  ## Generate new migrations
	$(COMPOSE) exec -T web python manage.py makemigrations

collectstatic: env-check  ## Re-collect static files
	$(COMPOSE) exec -T web python manage.py collectstatic --noinput --clear

test: env-check  ## Run the test suite inside the container
	$(COMPOSE) exec -T web python manage.py test

check: env-check  ## Run Django's deployment checks
	$(COMPOSE) exec -T web python manage.py check --deploy

seed: env-check  ## Load demo content
	$(COMPOSE) exec -T web python manage.py seed_demo

# --- Scripts ----------------------------------------------------------------
# These need a terminal or their own confirmation prompts, so they go through
# the scripts rather than through `exec -T`.

superuser:  ## Create an admin account (prompts)
	DENTAL_ENV=$(ENV) sh scripts/create-superuser.sh

backup:  ## Take a database dump now
	DENTAL_ENV=$(ENV) sh scripts/backup.sh

restore:  ## Restore a dump: make restore FILE=backups/<env>/dental-<stamp>.sql
	@test -n "$(FILE)" || { echo "usage: make ENV=$(ENV) restore FILE=backups/$(ENV)/dental-<stamp>.sql"; exit 1; }
	DENTAL_ENV=$(ENV) sh scripts/restore.sh $(FILE)
