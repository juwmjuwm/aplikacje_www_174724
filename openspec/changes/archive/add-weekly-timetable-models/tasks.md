# Tasks

## 1. Weekly timetable models

- [x] 1.1 Define Timetable, StudentGroup, Subject, Teacher, Room, and Lesson with the planned fields, relations, `related_name`, `on_delete`, defaults, labels, ordering, and `__str__`; verify `manage.py check` finds no model errors.

## 2. Scheduling validation

- [x] 2.1 Implement Python validation for same-day intervals and room, teacher, and student group overlap across timetables, excluding the current lesson on edit.
- [x] 2.2 Ensure normal application saves invoke model validation and return readable errors for invalid lesson times or conflicts.
- [x] 2.3 Add reversible SQLite `BEFORE INSERT` and `BEFORE UPDATE` lesson triggers that reject invalid intervals and overlapping room, teacher, or student group assignments on the same weekday across timetables; exclude the current row on update and allow back-to-back lessons.

## 3. Django Admin

- [x] 3.1 Register all six models with useful list columns, search, and filters, including weekday and resource views for lessons; verify an authenticated Admin page shows all registrations and intended columns.

## 4. Migration and integration

- [x] 4.1 Generate the initial `timetables` migration and inspect `sqlmigrate timetables 0001`; verify the migration creates all six tables, the intended foreign keys, and both SQLite triggers with reverse removal.
- [x] 4.2 Apply migrations to the configured SQLite database, confirm both triggers exist in `sqlite_master`, then run `manage.py check` and `manage.py makemigrations --check --dry-run`; verify both commands succeed and no further model changes are detected.
