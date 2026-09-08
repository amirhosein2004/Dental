# Documentation

Written for the next developer on this project — including you in six months.

| | |
|---|---|
| [getting-started.md](getting-started.md) | Clone to running site |
| [architecture.md](architecture.md) | What the apps are and how they fit |
| [environments.md](environments.md) | develop / production |
| [deploying.md](deploying.md) | **step by step, first deploy to rollback** |
| [cicd.md](cicd.md) | GitLab pipeline: what deploys itself, what waits |
| [caching.md](caching.md) | What is cached, and what invalidates it |
| [security.md](security.md) | The controls, and why each one exists |
| [appointments.md](appointments.md) | The booking system: weekly slots, double-booking |
| [notifications.md](notifications.md) | SMS and web push |
| [frontend.md](frontend.md) | Design system, themes, RTL, the PWA |
| [seo.md](seo.md) | Structured data, sitemaps, what search sees |
| [testing.md](testing.md) | Running and writing tests |
| [operations.md](operations.md) | Backups, deploys, common problems |

Two runbooks live beside the files they describe:

* [`../deploy/README.md`](../deploy/README.md) — bringing a stack up
* [`../scripts/README.md`](../scripts/README.md) — backups, superusers, restores

## A note on the comments in this codebase

Comments here explain *why*, not *what* — often by naming the bug that made
the line necessary. When something looks redundant or over-careful, the
comment above it usually says which incident it came from. Read that before
simplifying it away.
