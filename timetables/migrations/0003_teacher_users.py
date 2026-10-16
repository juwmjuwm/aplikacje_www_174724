from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


INSERT_TRIGGER = """
CREATE TRIGGER timetables_lesson_validate_insert
BEFORE INSERT ON timetables_lesson
BEGIN
    SELECT RAISE(ABORT, 'End time must be later than start time.')
    WHERE NEW.end_time <= NEW.start_time;
    SELECT RAISE(ABORT, 'Lesson resource is already booked for this time.')
    WHERE EXISTS (
        SELECT 1 FROM timetables_lesson AS existing
        WHERE existing.weekday = NEW.weekday
          AND existing.start_time < NEW.end_time
          AND existing.end_time > NEW.start_time
          AND (existing.room_id = NEW.room_id
               OR existing.teacher_id = NEW.teacher_id
               OR existing.student_group_id = NEW.student_group_id)
    );
END;
"""

UPDATE_TRIGGER = """
CREATE TRIGGER timetables_lesson_validate_update
BEFORE UPDATE ON timetables_lesson
BEGIN
    SELECT RAISE(ABORT, 'End time must be later than start time.')
    WHERE NEW.end_time <= NEW.start_time;
    SELECT RAISE(ABORT, 'Lesson resource is already booked for this time.')
    WHERE EXISTS (
        SELECT 1 FROM timetables_lesson AS existing
        WHERE existing.id != OLD.id
          AND existing.weekday = NEW.weekday
          AND existing.start_time < NEW.end_time
          AND existing.end_time > NEW.start_time
          AND (existing.room_id = NEW.room_id
               OR existing.teacher_id = NEW.teacher_id
               OR existing.student_group_id = NEW.student_group_id)
    );
END;
"""


class Migration(migrations.Migration):
    dependencies = [
        ('timetables', '0002_remove_timetable_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            'DROP TRIGGER IF EXISTS timetables_lesson_validate_insert;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            'DROP TRIGGER IF EXISTS timetables_lesson_validate_update;',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.DeleteModel(name='Lesson'),
        migrations.DeleteModel(name='Teacher'),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.CharField(choices=[('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')], max_length=3)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='timetables.room')),
                ('student_group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='timetables.studentgroup')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to='timetables.subject')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lessons', to=settings.AUTH_USER_MODEL)),
                ('timetable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='timetables.timetable')),
            ],
            options={
                'verbose_name': 'lesson',
                'verbose_name_plural': 'lessons',
                'ordering': ('weekday', 'start_time', 'pk'),
            },
        ),
        migrations.RunSQL(INSERT_TRIGGER, reverse_sql='DROP TRIGGER timetables_lesson_validate_insert;'),
        migrations.RunSQL(UPDATE_TRIGGER, reverse_sql='DROP TRIGGER timetables_lesson_validate_update;'),
    ]
