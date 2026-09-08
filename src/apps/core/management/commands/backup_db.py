"""
Take a database backup and keep only the newest few.

Run it from cron, a systemd timer, or `docker compose exec`. It shells out to
`pg_dump` rather than using `dumpdata`: a JSON fixture cannot restore a
database that has since changed shape, loses sequence positions, and takes
minutes on a table `pg_dump` handles in seconds. For SQLite — develop only —
it copies the file, which is the equivalent operation.

Rotation is the reason this exists as a command rather than a one-line cron
entry. A backup job with no retention fills the disk, and a full disk takes
the site down in a way that also prevents the next backup from running.
"""
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# How many to keep. Three is a deliberate floor rather than a round number:
# it survives the case where the most recent backup captured a database that
# was already corrupted, and the one before it did too.
DEFAULT_KEEP = 3


class Command(BaseCommand):
    help = 'Dump the database and keep only the newest --keep backups.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep', type=int, default=DEFAULT_KEEP,
            help=f'How many backups to retain (default: {DEFAULT_KEEP}).',
        )
        parser.add_argument(
            '--output-dir', default=None,
            help='Where to write. Defaults to BACKUP_DIR, then <project>/backups.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Report what would happen without writing or deleting.',
        )

    def handle(self, *args, **options):
        keep = options['keep']
        if keep < 1:
            raise CommandError('--keep must be at least 1')

        target = Path(
            options['output_dir']
            or getattr(settings, 'BACKUP_DIR', settings.BASE_DIR / 'backups')
        )
        target.mkdir(parents=True, exist_ok=True)

        db = settings.DATABASES['default']
        engine = db['ENGINE']

        # UTC in the filename: a server whose timezone changes, or two servers
        # in different zones, would otherwise produce names that sort wrongly
        # against each other — and sort order is what rotation relies on.
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')

        if 'postgresql' in engine:
            path = target / f'dental-{stamp}.sql'
            self._dump_postgres(db, path, options['dry_run'])
        elif 'sqlite' in engine:
            path = target / f'dental-{stamp}.sqlite3'
            self._dump_sqlite(db, path, options['dry_run'])
        else:
            raise CommandError(f'No backup strategy for engine: {engine}')

        self._rotate(target, keep, options['dry_run'])

    # ------------------------------------------------------------------ dump
    def _dump_postgres(self, db, path, dry_run):
        command = [
            'pg_dump',
            '--host', db.get('HOST') or 'localhost',
            '--port', str(db.get('PORT') or 5432),
            '--username', db['USER'],
            '--dbname', db['NAME'],
            '--no-owner',        # restorable into a differently-named role
            '--no-privileges',   # same reason: grants rarely transfer
            # Without these the dump is CREATE-and-COPY only, so restoring it
            # over a live database *merges* instead of replacing: every table
            # already exists, each CREATE fails, and the rows that survive are
            # whichever ones happened not to collide. A restore that leaves
            # post-backup rows in place is worse than one that refuses to run.
            '--clean',
            '--if-exists',       # so the DROPs are silent on an empty target
            '--file', str(path),
        ]

        if dry_run:
            self.stdout.write(f'[dry-run] would run: {" ".join(command)}')
            return

        # The password goes in the environment, not on the command line, where
        # it would be visible to anyone who can run `ps`.
        env = {'PGPASSWORD': db.get('PASSWORD') or ''}

        try:
            subprocess.run(
                command, check=True, capture_output=True, text=True,
                env={**dict(__import__('os').environ), **env},
            )
        except FileNotFoundError:
            raise CommandError(
                'pg_dump not found. Install postgresql-client, or run this '
                'inside the web container, where it is present.'
            )
        except subprocess.CalledProcessError as exc:
            # A partial file is worse than none: it looks like a backup.
            path.unlink(missing_ok=True)
            raise CommandError(f'pg_dump failed: {exc.stderr.strip()}')

        self.stdout.write(self.style.SUCCESS(
            f'wrote {path.name} ({path.stat().st_size / 1024:.0f} KB)'
        ))

    def _dump_sqlite(self, db, path, dry_run):
        source = Path(db['NAME'])
        if not source.exists():
            raise CommandError(f'database file not found: {source}')

        if dry_run:
            self.stdout.write(f'[dry-run] would copy {source} -> {path}')
            return

        # `copy2` preserves mtime, so the copy carries the moment the data was
        # last written rather than the moment it was copied.
        shutil.copy2(source, path)
        self.stdout.write(self.style.SUCCESS(
            f'wrote {path.name} ({path.stat().st_size / 1024:.0f} KB)'
        ))

    # --------------------------------------------------------------- rotate
    def _rotate(self, target, keep, dry_run):
        """
        Delete everything past the newest `keep`.

        Sorted by name, not by mtime: the timestamp is in the filename, and a
        file's mtime changes if it is touched, copied or restored from another
        machine — none of which should reorder the history.
        """
        backups = sorted(
            [p for p in target.glob('dental-*') if p.is_file()],
            reverse=True,
        )

        stale = backups[keep:]
        if not stale:
            self.stdout.write(f'{len(backups)} backup(s) kept, nothing to remove')
            return

        for path in stale:
            if dry_run:
                self.stdout.write(f'[dry-run] would delete {path.name}')
            else:
                path.unlink()
                self.stdout.write(f'removed {path.name}')

        self.stdout.write(self.style.SUCCESS(
            f'{min(len(backups), keep)} backup(s) kept, {len(stale)} removed'
        ))
