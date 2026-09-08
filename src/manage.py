#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# The repository root, one level above `src/`. Resolved from this file rather
# than from the working directory, because `python src/manage.py` from the
# root and `python manage.py` from inside `src` are both normal — and a bare
# `load_dotenv()` searches the working directory, so one of the two would
# silently start with no environment at all.
REPO_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(REPO_ROOT / '.env')


def main():
    """Run administrative tasks."""
    # Which settings module to load. `develop` rather than `dev`: the module
    # is `config/settings/develop.py`, and a default naming a file that does
    # not exist fails as an unhelpful ModuleNotFoundError.
    env = os.environ.get('DJANGO_ENV', 'develop')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'config.settings.{env}')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
