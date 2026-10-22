from django.db import migrations


LESSON_TRIGGER = """
CREATE TRIGGER timetables_lesson_validate_{event}
BEFORE {operation} ON timetables_lesson
BEGIN
    SELECT RAISE(ABORT, 'End time must be later than start time.')
    WHERE NEW.end_time <= NEW.start_time;
    SELECT RAISE(ABORT, 'Lesson resource is already booked for this time.')
    WHERE EXISTS (
        SELECT 1 FROM timetables_lesson AS existing
        WHERE {exclude_self}
          existing.weekday = NEW.weekday
          AND existing.start_time < NEW.end_time
          AND existing.end_time > NEW.start_time
          AND (existing.room_id = NEW.room_id
               OR existing.teacher_id = NEW.teacher_id
               OR existing.student_group_id = NEW.student_group_id)
    );
    {capacity_check}
END;
"""

LESSON_CAPACITY_CHECK = """
SELECT RAISE(ABORT, 'Lesson room capacity exceeded.')
WHERE (SELECT size FROM timetables_studentgroup WHERE id = NEW.student_group_id)
    > (SELECT capacity FROM timetables_room WHERE id = NEW.room_id);
"""

GROUP_TRIGGER = """
CREATE TRIGGER timetables_studentgroup_validate_capacity_update
BEFORE UPDATE OF size ON timetables_studentgroup
BEGIN
    SELECT RAISE(ABORT, 'Student group exceeds assigned room capacity.')
    WHERE EXISTS (
        SELECT 1 FROM timetables_lesson AS lesson
        JOIN timetables_room AS room ON room.id = lesson.room_id
        WHERE lesson.student_group_id = NEW.id AND NEW.size > room.capacity
    );
END;
"""

ROOM_TRIGGER = """
CREATE TRIGGER timetables_room_validate_capacity_update
BEFORE UPDATE OF capacity ON timetables_room
BEGIN
    SELECT RAISE(ABORT, 'Room capacity below assigned group size.')
    WHERE EXISTS (
        SELECT 1 FROM timetables_lesson AS lesson
        JOIN timetables_studentgroup AS student_group ON student_group.id = lesson.student_group_id
        WHERE lesson.room_id = NEW.id AND student_group.size > NEW.capacity
    );
END;
"""


def preflight(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT lesson.id FROM timetables_lesson AS lesson
            JOIN timetables_studentgroup AS student_group ON student_group.id = lesson.student_group_id
            JOIN timetables_room AS room ON room.id = lesson.room_id
            WHERE student_group.size > room.capacity ORDER BY lesson.id
        """)
        ids = [row[0] for row in cursor.fetchall()]
    if ids:
        raise RuntimeError(f'Existing lessons exceed room capacity; lesson IDs: {ids}')


def install_triggers(apps, schema_editor, capacity):
    if schema_editor.connection.vendor != 'sqlite':
        return
    with schema_editor.connection.cursor() as cursor:
        for event, operation, exclude_self in (
            ('insert', 'INSERT', ''),
            ('update', 'UPDATE', 'existing.id != OLD.id AND'),
        ):
            cursor.execute(f'DROP TRIGGER IF EXISTS timetables_lesson_validate_{event}')
            cursor.execute(LESSON_TRIGGER.format(
                event=event, operation=operation, exclude_self=exclude_self,
                capacity_check=LESSON_CAPACITY_CHECK if capacity else '',
            ))
        for name in ('timetables_studentgroup_validate_capacity_update',
                     'timetables_room_validate_capacity_update'):
            cursor.execute(f'DROP TRIGGER IF EXISTS {name}')
        if capacity:
            cursor.execute(GROUP_TRIGGER)
            cursor.execute(ROOM_TRIGGER)


def forwards(apps, schema_editor):
    install_triggers(apps, schema_editor, True)


def backwards(apps, schema_editor):
    install_triggers(apps, schema_editor, False)


class Migration(migrations.Migration):
    dependencies = [('timetables', '0003_teacher_users')]
    operations = [
        migrations.RunPython(preflight, migrations.RunPython.noop),
        migrations.RunPython(forwards, backwards),
    ]
