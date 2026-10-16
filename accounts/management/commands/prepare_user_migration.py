"""Prepare a fully migrated legacy SQLite database for the custom user model."""

import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


REQUIRED_MIGRATIONS = {
    ('auth', '0012_alter_user_first_name_max_length'),
    ('admin', '0003_logentry_add_action_flag_choices'),
    ('timetables', '0003_teacher_users'),
}
REQUIRED_COLUMNS = {
    'id', 'password', 'last_login', 'is_superuser', 'username',
    'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined',
}
REQUIRED_TABLES = {
    'auth_user', 'auth_user_groups', 'auth_user_user_permissions',
    'timetables_lesson', 'django_migrations',
}


class Command(BaseCommand):
    help = 'Back up and prepare an already migrated SQLite database for the email-free user model.'

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

        with sqlite3.connect(source, timeout=30) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not REQUIRED_TABLES <= tables:
                raise CommandError(f'Missing legacy tables: {sorted(REQUIRED_TABLES - tables)}')
            columns = {row[1] for row in db.execute('PRAGMA table_info(auth_user)')}
            applied = set(db.execute('SELECT app, name FROM django_migrations'))
            if ('accounts', '0001_initial') in applied:
                if ('accounts', '0002_drop_legacy_email') in applied and 'email' not in columns:
                    self.stdout.write('Email-free user migration is already complete; unchanged.')
                    return
                if ('accounts', '0002_drop_legacy_email') not in applied and REQUIRED_COLUMNS <= columns:
                    self.stdout.write('Initial custom user migration is already recorded; unchanged.')
                    return
                raise CommandError('Custom user migration history and schema disagree.')
            if not REQUIRED_COLUMNS <= columns:
                raise CommandError(f'Unexpected legacy user schema: missing {sorted(REQUIRED_COLUMNS - columns)}')
            for table, key in (('auth_user_groups', 'group_id'), ('auth_user_user_permissions', 'permission_id')):
                join_columns = {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
                if not {'id', 'user_id', key} <= join_columns:
                    raise CommandError(f'Unexpected {table} layout.')
            if not REQUIRED_MIGRATIONS <= applied:
                raise CommandError(f'Missing prerequisite migrations: {sorted(REQUIRED_MIGRATIONS - applied)}')
            if list(db.execute('PRAGMA foreign_key_check')):
                raise CommandError('Foreign-key violations exist; transition aborted.')
            if backup.exists():
                raise CommandError('Backup path must be new; refusing to overwrite it.')

            backup.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(backup) as backup_db:
                db.backup(backup_db)
            try:
                db.execute('BEGIN IMMEDIATE')
                # Recheck under the write lock before changing migration history.
                current = set(db.execute('SELECT app, name FROM django_migrations'))
                if current != applied:
                    raise CommandError('Migration history changed during backup; transition aborted.')
                db.execute(
                    "INSERT INTO django_migrations (app, name, applied) VALUES (?, ?, CURRENT_TIMESTAMP)",
                    ('accounts', '0001_initial'),
                )
                db.commit()
            except Exception:
                db.rollback()
                raise
        self.stdout.write(f'Backup created at {backup}; accounts.0001 recorded. Run migrate next.')
