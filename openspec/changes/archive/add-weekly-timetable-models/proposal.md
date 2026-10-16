# Proposal

## Why

The timetable planner has no domain models yet, so it cannot store a weekly schedule or demonstrate the related Django ORM models, migrations, and Admin configuration required for the first project milestone. A usable foundation must also reject lessons that assign the same room, teacher, or student group to overlapping times.

## What Changes

- Add six related models: Timetable, StudentGroup, Subject, Teacher, Room, and Lesson, with field validation, relationship options, `__str__()`, and `Meta` definitions.
- Represent lessons as weekly recurring weekday and time intervals, with Python model validation and SQLite triggers for valid intervals and resource conflicts.
- Register and configure the models in Django Admin so schedules and their reference data can be managed there.
- Generate and apply the initial migrations for the timetable models.

## Capabilities

### New Capabilities

- `weekly-timetables`: Store and manage timetables, their reference data, and weekly lessons.
- `lesson-conflicts`: Reject invalid lesson intervals and overlapping room, teacher, or student group assignments through application validation and SQLite database triggers.

### Modified Capabilities

None.

## Impact

This change affects the `timetables` Django app, its migrations (including SQLite triggers), Admin registration, and model and database tests. It uses the existing SQLite database and Django installation. REST endpoints, JWT roles, OpenAPI documentation, and deployment are later project stages; no new API or package dependency is introduced here.
