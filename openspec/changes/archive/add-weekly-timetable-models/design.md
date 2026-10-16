# Design

## Context

The `timetables` app has placeholder model, Admin, and test modules. Django 6.1.2 and SQLite are configured, and there are no existing timetable migrations or OpenSpec capabilities. See the proposal for the milestone motivation and the `weekly-timetables` and `lesson-conflicts` specs for required behavior.

## Goals / Non-Goals

**Goals:**

- Establish a relational weekly timetable schema that later REST endpoints can reuse.
- Make Admin creation and editing enforce the scheduling rules with readable validation errors.
- Produce an initial migration that can be applied to the configured SQLite database.

**Non-Goals:**

- API serializers or endpoints, JWT authorization, and calendar-date exceptions.
- Support for non-SQLite database backends.
- Automatically creating an administrator account or sample records.

## Decisions

### Six models and ownership

Use `Timetable` (`name`, `owner` FK to `settings.AUTH_USER_MODEL`, optional description), `StudentGroup` (`name`, positive `size`), `Subject` (`name`, optional description), `Teacher` (`first_name`, `last_name`, `academic_title`, optional email), `Room` (`name`, positive `capacity`), and `Lesson` (FKs to the other five, weekday, start time, end time). Timetable ownership provides a future authorization anchor. Room, teacher, and student group records are shared references, so conflict checks cover all lessons, even across different timetables. Use explicit `related_name` and deliberate `on_delete` choices: deleting a timetable cascades to its lessons; deleting a referenced room, teacher, subject, or group is protected because lessons in other timetables use it. Give every model `Meta` ordering and labels, plus `__str__`.

Alternative: put a student group directly on Timetable. That would make one timetable equivalent to one group and complicate schedules with more than one group, so the group belongs on each lesson instead.

### Weekly time representation

Store weekday as a fixed choice and start/end as local `TimeField` values. A lesson recurs on that weekday every week. Reject end times less than or equal to start times, so intervals stay within one day. Use half-open intervals, `[start, end)`, to allow adjacent lessons.

Alternative: `DateTimeField` for individual occurrences. That models dated bookings rather than a repeating weekly plan and would add recurrence expansion to this milestone.

### Python and SQLite conflict validation

Implement `Lesson.clean()` with a query for the same weekday and the strict overlap predicates `start_time__lt=self.end_time` and `end_time__gt=self.start_time`. Exclude `self.pk` when editing, then reject a match on any of `room_id`, `teacher_id`, or `student_group_id`, with resource-specific `ValidationError` messages. Guard queries until the relevant fields are present so incomplete Admin forms report field errors normally. Ensure application saves run `full_clean()`; Admin's model form also invokes model validation.

Create SQLite `BEFORE INSERT` and `BEFORE UPDATE` triggers in a reversible migration. Both triggers reject `NEW.end_time <= NEW.start_time` and any row on `NEW.weekday` satisfying `existing.start_time < NEW.end_time AND existing.end_time > NEW.start_time` while sharing `room_id`, `teacher_id`, or `student_group_id`. The update trigger excludes `OLD.id` from the overlap query. Use `RAISE(ABORT, ...)` so raw SQL and ORM paths that bypass `full_clean()` cannot persist invalid lessons. Keep trigger checks aligned with the Python rules and use reverse migration operations to drop the triggers before the lesson table is removed.

Alternative: Python-only checks offer clearer application errors but cannot protect writes that bypass model validation. Keeping both layers gives Admin readable errors and SQLite database enforcement.

### Admin and migration

Register all six models with useful `list_display`, `search_fields`, and `list_filter` choices; show weekday and related resources on the lesson list. Generate `0001_initial` with Django migrations, add trigger creation and removal after the lesson table definition, inspect its SQL, and apply it to the existing SQLite configuration. Keep a migration file in version control, while the local database file remains environment data.

## Risks / Trade-offs

- [Bulk operations, raw SQL, or other code paths bypass model validation] -> SQLite triggers reject invalid intervals and conflicts; future API writes should still invoke model validation for readable errors.
- [Concurrent writers can both pass a Python conflict check] -> SQLite triggers enforce the rule at write time, including when application checks race.
- [Trigger rules drift from Python validation] -> Test equivalent cases through model saves and raw SQL inserts and updates.
- [Changing a room, teacher, or group record may affect existing schedules] -> Keep resource identity stable and protect deletion while referenced; later stages can add lifecycle rules if needed.

## Migration Plan

1. Define the models and generate `timetables/migrations/0001_initial.py`, including reversible SQLite trigger SQL after the lesson table definition.
2. Inspect `sqlmigrate timetables 0001`, then run `migrate` on the configured SQLite database. Verify the triggers are installed.
3. Run Django system checks, the model and raw SQL trigger tests, and the migration consistency check. Verify the six models appear in Admin. An administrator account can be created interactively with `createsuperuser` when needed.
4. If rollback is needed before real data exists, reverse the `timetables` migration. After data exists, back up the SQLite database before reversing because dropping the app tables loses timetable records.
