from datetime import time
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Barrier

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, RequestFactory, TestCase, TransactionTestCase
from rest_framework.test import APIClient

from .admin import SafeUserChangeForm
from .models import Lesson, Room, StudentGroup, Subject, Timetable
from .permissions import user_role


User = get_user_model()


class TeacherRoleTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'Strong-password-123')
        self.viewer = User.objects.create_user('viewer', password='Strong-password-123')
        self.planner = User.objects.create_user('planner', password='Strong-password-123')
        self.teacher = User.objects.create_user('teacher', password='Strong-password-123')
        Group.objects.get_or_create(name='PLANNER')[0].user_set.add(self.planner)
        Group.objects.get_or_create(name='TEACHER')[0].user_set.add(self.teacher)
        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)

    def role(self, user, role):
        return self.client.patch(f'/api/users/{user.pk}/role/', {'role': role}, format='json')

    def resources(self):
        return (
            Timetable.objects.create(name='Autumn'),
            StudentGroup.objects.create(name='Group A', size=12),
            Subject.objects.create(name='Math'),
            Room.objects.create(name='R1', capacity=20),
        )

    def lesson(self, teacher=None, weekday='MON', start=time(9), end=time(10), resources=None):
        timetable, group, subject, room = resources or self.resources()
        return Lesson.objects.create(
            timetable=timetable, student_group=group, subject=subject,
            teacher=teacher or self.teacher, room=room, weekday=weekday,
            start_time=start, end_time=end,
        )

    def test_role_transitions_and_existing_token(self):
        token = self.client.post('/api/token/', {'username': 'viewer', 'password': 'Strong-password-123'}, format='json').data['access']
        self.assertEqual(self.role(self.viewer, 'TEACHER').status_code, 200)
        self.assertEqual(self.role(self.viewer, 'TEACHER').status_code, 200)
        self.assertEqual(user_role(self.viewer), 'TEACHER')
        reader = APIClient()
        reader.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(reader.get(f'/api/users/{self.viewer.pk}/').data['role'], 'TEACHER')
        self.assertEqual(reader.post('/api/timetables/', {'name': 'Denied'}, format='json').status_code, 403)
        self.assertEqual(self.role(self.viewer, 'PLANNER').status_code, 409)
        self.assertEqual(self.role(self.planner, 'TEACHER').status_code, 409)
        self.assertEqual(self.role(self.admin_user, 'TEACHER').status_code, 409)
        self.assertEqual(self.role(self.viewer, 'VIEWER').status_code, 200)
        self.assertEqual(self.role(self.viewer, 'PLANNER').status_code, 200)
        self.assertEqual(self.role(self.planner, 'VIEWER').status_code, 200)

    def test_bootstrap_is_idempotent(self):
        output = StringIO()
        call_command('bootstrap_accounts', stdout=output)
        call_command('bootstrap_accounts', stdout=output)
        self.assertEqual(Group.objects.filter(name='PLANNER').count(), 1)
        self.assertEqual(Group.objects.filter(name='TEACHER').count(), 1)

    def test_assigned_teacher_cannot_be_demoted_or_deleted(self):
        lesson = self.lesson()
        response = self.role(self.teacher, 'VIEWER')
        self.assertEqual(response.status_code, 409)
        self.assertIn('detail', response.data)
        self.assertEqual(self.role(self.teacher, 'PLANNER').status_code, 409)
        self.assertEqual(self.client.delete(f'/api/users/{self.teacher.pk}/').status_code, 409)
        self.assertTrue(Lesson.objects.filter(pk=lesson.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.teacher.pk).exists())
        self.assertEqual(user_role(self.teacher), 'TEACHER')
        form = SafeUserChangeForm(instance=self.teacher, data={})
        form.cleaned_data = {'groups': Group.objects.none()}
        with self.assertRaises(ValidationError):
            form.clean_groups()
        browser = Client()
        browser.force_login(self.admin_user)
        admin_response = browser.post(f'/admin/auth/user/{self.teacher.pk}/change/', {
            'username': self.teacher.username, 'email': self.teacher.email,
            'is_active': 'on', 'is_staff': '', 'is_superuser': '',
            'first_name': '', 'last_name': '', 'groups': [], 'user_permissions': [],
            '_save': 'Save',
        })
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "Reassign or delete this teacher&#x27;s lessons")
        self.assertTrue(self.teacher.groups.filter(name='TEACHER').exists())
        self.assertTrue(Lesson.objects.filter(pk=lesson.pk).exists())
        self.assertEqual(browser.get(f'/admin/auth/user/{self.teacher.pk}/delete/').status_code, 403)
        teacher_group = Group.objects.get(name='TEACHER')
        self.assertEqual(browser.get(f'/admin/auth/group/{teacher_group.pk}/delete/').status_code, 403)
        self.assertIn('name', admin.site._registry[Group].get_readonly_fields(None, teacher_group))

    def test_teacher_directory_and_lesson_api(self):
        anonymous = APIClient()
        self.assertEqual(anonymous.get('/api/teachers/').status_code, 401)
        response = self.client.get('/api/teachers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{'id': self.teacher.pk, 'username': 'teacher', 'email': '', 'role': 'TEACHER'}])
        self.assertEqual(self.client.get(f'/api/teachers/{self.viewer.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/teachers/{self.teacher.pk}/').data['role'], 'TEACHER')
        self.assertEqual(self.client.post('/api/teachers/', {}, format='json').status_code, 405)
        self.assertEqual(self.client.put(f'/api/teachers/{self.teacher.pk}/', {}, format='json').status_code, 405)
        self.assertEqual(self.client.patch(f'/api/teachers/{self.teacher.pk}/', {}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(f'/api/teachers/{self.teacher.pk}/').status_code, 405)
        timetable, group, subject, room = self.resources()
        payload = dict(timetable=timetable.pk, student_group=group.pk, subject=subject.pk,
                       teacher=self.teacher.pk, room=room.pk, weekday='MON',
                       start_time='09:00:00', end_time='10:00:00')
        created = self.client.post('/api/lessons/', payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data['teacher'], self.teacher.pk)
        for ineligible in (self.viewer.pk, self.planner.pk, self.admin_user.pk, 999999):
            rejected = self.client.patch(f"/api/lessons/{created.data['id']}/", {'teacher': ineligible}, format='json')
            self.assertEqual(rejected.status_code, 400)
            self.assertIn('teacher', rejected.data)
        payload['teacher'] = self.viewer.pk
        self.assertEqual(self.client.post('/api/lessons/', payload, format='json').status_code, 400)
        payload['teacher'] = self.teacher.pk
        self.assertEqual(self.client.post('/api/lessons/', payload, format='json').status_code, 400)

    def test_role_cannot_be_granted_by_non_admin_or_profile(self):
        reader = APIClient()
        reader.force_authenticate(self.viewer)
        self.assertEqual(reader.patch(f'/api/users/{self.viewer.pk}/role/', {'role': 'TEACHER'}, format='json').status_code, 403)
        self.assertEqual(reader.patch(f'/api/users/{self.viewer.pk}/', {'role': 'TEACHER'}, format='json').status_code, 400)
        self.assertEqual(user_role(self.viewer), 'VIEWER')

    def test_model_conflicts_and_admin_field(self):
        resources = self.resources()
        self.lesson(resources=resources)
        with self.assertRaises(ValidationError) as error:
            self.lesson(teacher=self.viewer, resources=resources, weekday='TUE')
        self.assertIn('teacher', error.exception.message_dict)
        self.lesson(resources=resources, start=time(10), end=time(11))
        other_timetable = Timetable.objects.create(name='Spring')
        with self.assertRaises(ValidationError) as error:
            self.lesson(resources=(other_timetable, resources[1], resources[2], resources[3]),
                        start=time(9, 30), end=time(10, 30))
        self.assertIn('teacher', error.exception.message_dict)
        lesson_admin = admin.site._registry[Lesson]
        teacher_field = lesson_admin.formfield_for_foreignkey(Lesson._meta.get_field('teacher'), None)
        self.assertEqual(list(teacher_field.queryset), [self.teacher])
        self.assertFalse(teacher_field.clean(self.teacher.pk) is None)
        with self.assertRaises(ValidationError):
            teacher_field.clean(self.viewer.pk)
        admin_request = RequestFactory().get('/admin/timetables/lesson/add/')
        admin_request.user = self.admin_user
        lesson_form = lesson_admin.get_form(admin_request)
        payload = dict(timetable=resources[0].pk, student_group=resources[1].pk,
                       subject=resources[2].pk, teacher=self.viewer.pk,
                       room=resources[3].pk, weekday='THU', start_time='09:00:00', end_time='10:00:00')
        invalid_form = lesson_form(data=payload)
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('teacher', invalid_form.errors)
        payload['teacher'] = self.teacher.pk
        self.assertTrue(lesson_form(data=payload).is_valid())

    def test_teacher_scheduling_permissions(self):
        resources = self.resources()
        lesson = self.lesson(resources=resources)
        teacher_client = APIClient()
        teacher_client.force_authenticate(self.teacher)
        for route in ('timetables', 'student-groups', 'subjects', 'rooms', 'lessons', 'teachers'):
            self.assertEqual(teacher_client.get(f'/api/{route}/').status_code, 200)
        for route in ('timetables', 'student-groups', 'subjects', 'rooms', 'lessons'):
            self.assertEqual(teacher_client.post(f'/api/{route}/', {}, format='json').status_code, 403)
        self.assertEqual(teacher_client.patch(f'/api/lessons/{lesson.pk}/', {}, format='json').status_code, 403)
        self.assertEqual(teacher_client.delete(f'/api/lessons/{lesson.pk}/').status_code, 403)
        self.assertEqual(self.client.patch(f'/api/lessons/{lesson.pk}/', {'weekday': 'TUE'}, format='json').status_code, 200)
        self.client.force_authenticate(self.planner)
        self.assertEqual(self.client.patch(f'/api/lessons/{lesson.pk}/', {'weekday': 'WED'}, format='json').status_code, 200)


class TeacherMigrationTests(TransactionTestCase):
    def test_populated_database_retains_unrelated_rows(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('timetables', '0002_remove_timetable_owner')])
        old_apps = executor.loader.project_state([('timetables', '0002_remove_timetable_owner')]).apps
        OldTeacher = old_apps.get_model('timetables', 'Teacher')
        OldLesson = old_apps.get_model('timetables', 'Lesson')
        OldTimetable = old_apps.get_model('timetables', 'Timetable')
        OldGroup = old_apps.get_model('timetables', 'StudentGroup')
        OldSubject = old_apps.get_model('timetables', 'Subject')
        OldRoom = old_apps.get_model('timetables', 'Room')
        user = User.objects.create_user('retained')
        timetable = OldTimetable.objects.create(name='Retained')
        group = OldGroup.objects.create(name='Retained group', size=10)
        subject = OldSubject.objects.create(name='Retained subject')
        room = OldRoom.objects.create(name='Retained room', capacity=10)
        teacher = OldTeacher.objects.create(first_name='Old', last_name='Teacher')
        OldLesson.objects.create(timetable=timetable, student_group=group, subject=subject,
                                 teacher=teacher, room=room, weekday='MON',
                                 start_time=time(9), end_time=time(10))
        executor = MigrationExecutor(connection)
        executor.migrate([('timetables', '0003_teacher_users')])
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='timetables_lesson'")
            triggers = {row[0] for row in cursor.fetchall()}
            cursor.execute('PRAGMA foreign_key_list(timetables_lesson)')
            foreign_keys = cursor.fetchall()
        self.assertNotIn('timetables_teacher', tables)
        self.assertEqual(Lesson.objects.count(), 0)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(Timetable.objects.filter(pk=timetable.pk).exists())
        self.assertTrue(StudentGroup.objects.filter(pk=group.pk).exists())
        self.assertTrue(Subject.objects.filter(pk=subject.pk).exists())
        self.assertTrue(Room.objects.filter(pk=room.pk).exists())
        self.assertEqual(triggers, {'timetables_lesson_validate_insert', 'timetables_lesson_validate_update'})
        self.assertTrue(any(row[2] == User._meta.db_table and row[3] == 'teacher_id' for row in foreign_keys))


class TeacherConcurrencyTests(TransactionTestCase):
    def test_assignment_and_demotion_never_leave_ineligible_lesson(self):
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'Strong-password-123')
        teacher = User.objects.create_user('teacher')
        Group.objects.get_or_create(name='TEACHER')[0].user_set.add(teacher)
        timetable = Timetable.objects.create(name='Autumn')
        group = StudentGroup.objects.create(name='A', size=10)
        subject = Subject.objects.create(name='Math')
        room = Room.objects.create(name='R1', capacity=10)
        barrier = Barrier(2)

        def assign():
            client = APIClient()
            client.force_authenticate(admin_user)
            barrier.wait()
            try:
                return client.post('/api/lessons/', {
                    'timetable': timetable.pk, 'student_group': group.pk,
                    'subject': subject.pk, 'teacher': teacher.pk, 'room': room.pk,
                    'weekday': 'MON', 'start_time': '09:00:00', 'end_time': '10:00:00',
                }, format='json').status_code
            finally:
                connections.close_all()

        def demote():
            client = APIClient()
            client.force_authenticate(admin_user)
            barrier.wait()
            try:
                return client.patch(f'/api/users/{teacher.pk}/role/', {'role': 'VIEWER'}, format='json').status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            assignment = pool.submit(assign)
            demotion = pool.submit(demote)
            assignment_status = assignment.result()
            demotion_status = demotion.result()
        self.assertIn((assignment_status, demotion_status), {(201, 409), (400, 200)})
        if Lesson.objects.filter(teacher_id=teacher.pk).exists():
            self.assertEqual(user_role(User.objects.get(pk=teacher.pk)), 'TEACHER')
