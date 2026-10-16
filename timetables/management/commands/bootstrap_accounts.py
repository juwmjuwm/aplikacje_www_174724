import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Create the PLANNER and TEACHER groups and initial ADMIN after migrations.'

    def handle(self, *args, **options):
        username = os.getenv('INITIAL_ADMIN_USERNAME', '').strip()
        password = os.getenv('INITIAL_ADMIN_PASSWORD', '')
        User = get_user_model()

        with transaction.atomic():
            Group.objects.get_or_create(name='PLANNER')
            Group.objects.get_or_create(name='TEACHER')
            if username:
                existing = User.objects.select_for_update().filter(username=username).first()
                if existing:
                    if not existing.is_superuser:
                        raise CommandError('Initial ADMIN username belongs to a regular user.')
                    self.stdout.write('Initial ADMIN already exists; unchanged.')
                    return
            if User.objects.filter(is_superuser=True).exists():
                self.stdout.write('An ADMIN already exists; unchanged.')
                return
            if not username or not password:
                raise CommandError('INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD are required when no ADMIN exists.')
            User.objects.create_superuser(username=username, password=password)
            self.stdout.write('Initial ADMIN created.')
