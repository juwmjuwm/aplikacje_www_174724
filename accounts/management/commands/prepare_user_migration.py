"""Back up a database before moving from the complete historical migration chain."""

import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


HISTORICAL_MIGRATIONS = {
    *(('accounts', name) for name in (
        '0001_initial', '0002_drop_legacy_email', '0003_canonical_usernames',
        '0004_alter_user_username', '0005_account_name_preflight',
    )),
    *(('timetables', name) for name in (
        '0001_initial', '0002_remove_timetable_owner',
        '0003_teacher_users', '0004_lesson_capacity',
    )),
}


class Command(BaseCommand):
    help = 'Back up a database that completed the historical migrations before using the squashed migrations.'

    def add_arguments(self, parser):
        parser.add_argument('--backup', required=True, help='New path for a SQLite database backup.')

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3' or database['NAME'] == ':memory:':
            raise CommandError('Only file-backed SQLite databases are supported.')
        source = Path(database['NAME']).resolve()
        backup = Path(options['backup']).resolve()
        if not source.is_file() or backup == source:
            raise CommandError('Source must exist and backup must be a distinct file.')
        if backup.exists():
            raise CommandError('Backup path must be new; refusing to overwrite it.')

        with sqlite3.connect(source, timeout=30) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'django_migrations', 'auth_user', 'timetables_lesson'} <= tables:
                raise CommandError('Database is missing required tables.')
            applied = set(db.execute('SELECT app, name FROM django_migrations'))
            squashed = {
                ('accounts', '0001_squashed_0005'),
                ('timetables', '0001_squashed_0004'),
            }
            if not (HISTORICAL_MIGRATIONS <= applied or squashed <= applied):
                raise CommandError(
                    'This database has an incomplete historical migration chain. '
                    'Finish migrations with the previous project revision before switching '
                    'to the squashed migration files.'
                )
            columns = {row[1] for row in db.execute('PRAGMA table_info(auth_user)')}
            if 'email' in columns:
                raise CommandError('Legacy email column is still present; finish old migrations first.')
            if list(db.execute('PRAGMA foreign_key_check')):
                raise CommandError('Foreign-key violations exist; backup aborted.')

            backup.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(backup) as backup_db:
                db.backup(backup_db)

        self.stdout.write(f'Backup created at {backup}. Run migrate to record the squashed migrations.')
