"""
The backup command.

Rotation is the part worth pinning. A backup job with no retention fills the
disk, and a full disk takes the site down in a way that also stops the next
backup from running — so the failure mode is silent until it is total.
"""
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings


class BackupRotationTests(TestCase):
    """
    The dump itself is pointed at a throwaway SQLite file rather than the test
    database: under test that is an in-memory URI, which has no file to copy.
    Rotation — the part that can lose data — behaves identically either way.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='dental-backup-test-'))

        self.source = self.dir / 'source.sqlite3'
        # Contents are irrelevant: the SQLite path copies the file whole, so
        # anything on disk exercises the same code.
        self.source.write_text('not a real database', encoding='utf-8')

        self.settings_override = override_settings(DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': str(self.source),
            }
        })
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def _existing(self):
        return sorted(p.name for p in self.dir.glob('dental-*'))

    def _seed(self, *stamps):
        """Pre-existing backups, named the way the command names them."""
        for stamp in stamps:
            (self.dir / f'dental-{stamp}.sql').write_text('-- dump', encoding='utf-8')

    def test_a_backup_is_written(self):
        call_command('backup_db', output_dir=str(self.dir), verbosity=0)

        self.assertEqual(len(self._existing()), 1)

    def test_nothing_is_removed_below_the_limit(self):
        self._seed('20260101-000000', '20260102-000000')

        call_command('backup_db', output_dir=str(self.dir), keep=3, verbosity=0)

        self.assertEqual(len(self._existing()), 3)

    def test_the_oldest_is_removed_above_the_limit(self):
        self._seed('20260101-000000', '20260102-000000', '20260103-000000')

        call_command('backup_db', output_dir=str(self.dir), keep=3, verbosity=0)

        surviving = self._existing()
        self.assertEqual(len(surviving), 3)
        self.assertNotIn('dental-20260101-000000.sql', surviving,
                         'the oldest backup should have been rotated out')
        self.assertIn('dental-20260103-000000.sql', surviving)

    def test_rotation_keeps_the_newest_not_an_arbitrary_three(self):
        self._seed(
            '20260101-000000', '20260102-000000',
            '20260103-000000', '20260104-000000', '20260105-000000',
        )

        call_command('backup_db', output_dir=str(self.dir), keep=3, verbosity=0)

        surviving = self._existing()
        self.assertEqual(len(surviving), 3)
        # The run just wrote one, so the two survivors from the seed must be
        # the two most recent of them.
        self.assertIn('dental-20260105-000000.sql', surviving)
        self.assertIn('dental-20260104-000000.sql', surviving)

    def test_unrelated_files_are_never_deleted(self):
        """
        Rotation globs `dental-*`. A dump someone took by hand, or an old
        export, must survive — deleting a file the command did not create is
        not its business.
        """
        (self.dir / 'liara-dumpall-20260726.sql').write_text('-- manual', encoding='utf-8')
        self._seed('20260101-000000', '20260102-000000', '20260103-000000')

        call_command('backup_db', output_dir=str(self.dir), keep=1, verbosity=0)

        self.assertTrue((self.dir / 'liara-dumpall-20260726.sql').exists())

    def test_dry_run_writes_and_deletes_nothing(self):
        self._seed('20260101-000000', '20260102-000000', '20260103-000000')
        before = self._existing()

        call_command('backup_db', output_dir=str(self.dir), keep=1,
                     dry_run=True, verbosity=0)

        self.assertEqual(self._existing(), before)

    def test_keep_zero_is_refused(self):
        """`--keep 0` would delete the backup it just took."""
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command('backup_db', output_dir=str(self.dir), keep=0, verbosity=0)


class PostgresDumpFlagTests(TestCase):
    """
    The flags on the `pg_dump` call, pinned because getting them wrong fails
    silently.

    Without `--clean` the dump is CREATE-and-COPY only. Restoring one over a
    live database *merges* into it: every table already exists, each CREATE
    fails, and what survives is whichever rows happened not to collide. A real
    restore of such a dump reported "finished" while leaving rows written
    after the backup in place and dropping a whole table's contents.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='dental-pgflags-test-'))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

        self.settings_override = override_settings(DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'dental_test', 'USER': 'dental',
                'PASSWORD': 'secret', 'HOST': 'db', 'PORT': '5432',
            }
        })
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def _dump_command(self):
        """The argv `backup_db` would hand to subprocess."""
        def fake_pg_dump(command, *args, **kwargs):
            # The command reports the size of what pg_dump wrote, so the file
            # named by `--file` has to exist afterwards.
            Path(command[command.index('--file') + 1]).write_text('-- dump')
            return mock.Mock(returncode=0, stderr='')

        with mock.patch('apps.core.management.commands.backup_db.subprocess.run',
                        side_effect=fake_pg_dump) as run:
            call_command('backup_db', output_dir=str(self.dir), verbosity=0)

        return run.call_args[0][0]

    def test_the_dump_drops_before_it_creates(self):
        command = self._dump_command()

        self.assertIn('--clean', command)

    def test_the_drops_tolerate_an_empty_target(self):
        """
        `--clean` alone emits bare DROPs, which error on a fresh database —
        and restoring into an empty one is the case that matters most.
        """
        command = self._dump_command()

        self.assertIn('--if-exists', command)

    def test_the_password_is_not_in_the_argv(self):
        """It goes through the environment; a process list is world-readable."""
        command = self._dump_command()

        self.assertNotIn('secret', ' '.join(command))
