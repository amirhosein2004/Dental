"""
The project's own Django applications.

Grouped under one package so the repository root holds infrastructure —
Dockerfile, deploy, docs, scripts — rather than thirteen app directories
mixed in with it.

Each app's `AppConfig.name` is the dotted path (`apps.blog`), but Django
derives the *label* from the last component, so every app label, migration
and string reference such as `AUTH_USER_MODEL = 'users.CustomUser'` is
unchanged by the move.
"""
