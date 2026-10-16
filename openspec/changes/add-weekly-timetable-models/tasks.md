# Tasks

## 1. Weekly timetable models

- [x] 1.1 Define Timetable, StudentGroup, Subject, Teacher, Room, and Lesson with the planned fields, relations, `related_name`, `on_delete`, defaults, labels, ordering, and `__str__`; verify `manage.py check` finds no model errors.
- [x] 1.2 Add model tests for relation persistence, weekday choices, and positive room capacity; verify the focused `timetables` tests pass.

## 2. Scheduling validation

- [x] 2.1 Implement Python validation for same-day intervals and room, teacher, and student group overlap across timetables, excluding the current lesson on edit; verify focused model tests cover all three resources, back-to-back lessons, different weekdays, independent parallel lessons, and edits.
- [x] 2.2 Ensure normal application saves invoke model validation and return readable errors for invalid lesson times or conflicts; verify direct model-save tests reject invalid records and accept valid ones.
- [x] 2.3 Add reversible SQLite `BEFORE INSERT` and `BEFORE UPDATE` lesson triggers that reject invalid intervals and overlapping room, teacher, or student group assignments on the same weekday across timetables; exclude the current row on update and allow back-to-back lessons.
- [x] 2.4 Add raw SQL tests for both triggers covering invalid intervals, each shared resource, cross-timetable conflicts, back-to-back and independent lessons, and conflicting and nonconflicting edits; verify rejected updates preserve the original row.

## 3. Django Admin

- [x] 3.1 Register all six models with useful list columns, search, and filters, including weekday and resource views for lessons; verify an Admin test or authenticated Admin page check shows all registrations and intended columns.
- [x] 3.2 Verify the Admin lesson form rejects an overlapping room booking and accepts a nonconflicting edit through an authenticated Admin test.

## 4. Migration and integration

- [x] 4.1 Generate the initial `timetables` migration and inspect `sqlmigrate timetables 0001`; verify the migration creates all six tables, the intended foreign keys, and both SQLite triggers with reverse removal.
- [x] 4.2 Apply migrations to the configured SQLite database, confirm both triggers exist in `sqlite_master`, then run `manage.py check`, `manage.py makemigrations --check --dry-run`, and the focused `timetables` test suite; verify all commands succeed and no further model changes are detected.
