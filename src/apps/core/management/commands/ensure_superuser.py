"""
Create or update a superuser, without a prompt and without surprises.

Django's own `createsuperuser --noinput` exists, but it sets an *unusable*
password — the account is created and cannot be logged into, which on a fresh
server looks like the script worked right up until someone tries to sign in.
This one requires a real password and says so if it is missing.

Idempotent on purpose, so it is safe to call from a deploy: an existing
account is left alone unless `--update-password` is passed.

    python manage.py ensure_superuser \\
        --username amir --email a@example.com \\
        --first-name امیر --last-name بابایی

Or from the environment, which is what the deploy script uses:

    DJANGO_SUPERUSER_USERNAME=amir \\
    DJANGO_SUPERUSER_EMAIL=a@example.com \\
    DJANGO_SUPERUSER_PASSWORD=... \\
    python manage.py ensure_superuser
"""
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if it does not exist, or update its password.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=None)
        parser.add_argument('--email', default=None)
        parser.add_argument('--password', default=None)
        parser.add_argument('--first-name', dest='first_name', default=None)
        parser.add_argument('--last-name', dest='last_name', default=None)
        parser.add_argument(
            '--update-password', action='store_true',
            help='Reset the password if the account already exists.',
        )
        parser.add_argument(
            '--skip-password-validation', action='store_true',
            help='Accept a password Django would reject. For recovery only.',
        )

    def handle(self, *args, **options):
        # Respect -v0 so a test run or a quiet deploy stays quiet.
        self._quiet = options.get('verbosity', 1) == 0

        # Command line wins; the environment is the fallback so a deploy can
        # supply secrets without them appearing in a process list.
        username = options['username'] or os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = options['email'] or os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = options['password'] or os.getenv('DJANGO_SUPERUSER_PASSWORD')
        first_name = (
            options['first_name'] or os.getenv('DJANGO_SUPERUSER_FIRST_NAME') or 'مدیر'
        )
        last_name = (
            options['last_name'] or os.getenv('DJANGO_SUPERUSER_LAST_NAME') or 'سیستم'
        )

        missing = [
            name for name, value in (
                ('username', username), ('email', email), ('password', password),
            ) if not value
        ]
        if missing:
            raise CommandError(
                'missing: ' + ', '.join(missing) + '. Pass them as flags, or set '
                'DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD.'
            )

        existing = User.objects.filter(username=username).first()

        if existing:
            self._update(existing, password, options)
            return

        # A different account may already hold this email: the field is unique,
        # so creating would fail with an IntegrityError that says less than
        # this does.
        clash = User.objects.filter(email=email).exclude(username=username).first()
        if clash:
            raise CommandError(
                f'email {email} already belongs to user "{clash.username}"'
            )

        self._validate_password(password, username, options)

        user = User.objects.create_superuser(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        self._say(self.style.SUCCESS(f'created superuser "{user.username}"'))

    # ------------------------------------------------------------------ help
    def _update(self, user, password, options):
        """An account with this username is already here."""
        changed = []

        # Being asked for a superuser when the row exists but is not one is
        # worth acting on — that is how an account gets demoted by accident.
        if not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            changed.append('promoted to superuser')

        if options['update_password']:
            self._validate_password(password, user.username, options)
            user.set_password(password)
            changed.append('password reset')

        if changed:
            user.save()
            for note in changed:
                self._say(self.style.SUCCESS(f'"{user.username}": {note}'))
            if 'password reset' in changed:
                self._say(self.style.WARNING(
                    'a password change signs this account out everywhere'
                ))
        else:
            self._say(
                f'"{user.username}" already exists and is a superuser; nothing to do. '
                'Pass --update-password to reset it.'
            )

    def _validate_password(self, password, username, options):
        if options['skip_password_validation']:
            self._say(self.style.WARNING(
                'password validation skipped'
            ))
            return

        try:
            # `user=None` so the similarity check has nothing to compare
            # against; the length, common-password and numeric checks still
            # run, and those are the ones that matter on a public host.
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(
                'password rejected: ' + ' '.join(exc.messages) +
                ' (use --skip-password-validation only for recovery)'
            )

    def _say(self, message):
        if not getattr(self, '_quiet', False):
            self.stdout.write(message)
