# Design

## Context

See [proposal.md](./proposal.md) for motivation. The project uses Django's User model, a PLANNER group, and `is_superuser` for ADMIN. `user_role()` currently treats all other users as VIEWER. The role action is the only API path that edits role membership. Lesson points to a separate Teacher model, and the SQLite lesson table has insert/update triggers that enforce interval and resource conflicts. The teacher route is currently a full ModelViewSet. No main specs have been synced yet; completed change specs still describe the old Teacher CRUD resource.

## Goals / Non-Goals

**Goals:**
- Keep one effective role per regular account and apply changes to existing access tokens on subsequent requests.
- Preserve the established lesson conflict behavior while changing teacher identity to User.
- Make migration behavior explicit and safe for databases containing old lessons.

**Non-Goals:**
- Preserve old Teacher or Lesson data, including academic titles and old teacher IDs.
- Give TEACHER scheduling write privileges or create a separate teacher profile model.
- Change other scheduling resource schemas or authentication mechanisms.

## Decisions

### Role representation and transitions

Create a TEACHER group alongside PLANNER during bootstrap. Continue deriving ADMIN from `is_superuser` and regular roles from group membership; TEACHER and PLANNER membership must be mutually exclusive. The ADMIN role action accepts TEACHER from VIEWER and VIEWER from TEACHER. Keep existing VIEWER/PLANNER transitions. Require a transition through VIEWER to switch between TEACHER and PLANNER; reject direct switches with HTTP 409. Idempotent role requests remain successful. Reject role edits targeting ADMIN.

The role action checks the current role and any lesson assignments in the same transaction, then edits group membership. Before removing TEACHER, return HTTP 409 with a `detail` that says lessons must be reassigned or deleted. Keep TEACHER accounts ineligible for user deletion; the existing VIEWER-only delete rule and the lesson FK's `PROTECT` behavior provide further protection. Ensure Django Admin role editing cannot bypass the assigned-teacher guard, for example by validating user group changes there or by centralizing membership removal validation. SQLite ignores Django `select_for_update()`, so coordinate lesson writes and role removal with a SQLite write transaction or equivalent serialization before checking eligibility; do not rely on row locks alone. Alternative considered: encode a role field on User; that would require a custom user model migration and is disproportionate to the current group-based design.

### Teacher directory and lesson input

Replace TeacherViewSet's model CRUD behavior with read-only list/retrieve over users in the TEACHER group. Reuse the non-secret user representation (`id`, `username`, `email`, `role`) and keep the `/api/teachers/` route. A non-TEACHER user queried at the detail route returns 404. POST, PUT, PATCH, and DELETE are unsupported. Avoid duplicating account profile edits through the teacher route; the existing profile and role endpoints own those changes.

Set `Lesson.teacher` to `settings.AUTH_USER_MODEL` with `PROTECT` and the existing `lessons` related name. The lesson serializer accepts user IDs but restricts the teacher relation to TEACHER users, yielding a field-keyed HTTP 400 error for other IDs. `Lesson.clean()` also checks the role so Django Admin and direct model saves reject ineligible teachers. Keep lesson JSON as integer IDs. Alternative considered: retain Teacher as a one-to-one profile; it would preserve two identities and undermine the goal of removing the redundant model.

### Conflict checks and migration

Keep the current `teacher_id` conflict predicate in `Lesson.clean()` and SQLite triggers; the column name stays `teacher_id`, but its FK now targets User. Keep room, student group, and interval checks unchanged. In a new migration, remove the old lesson table and Teacher table, then recreate the lesson table with the user FK and reinstall both SQLite validation triggers. This avoids guessing a teacher-to-user mapping or adding a non-null FK to populated rows. The destructive migration is intentionally one-way for data; rollback requires a database backup. The migration must leave unrelated tables and rows intact. Alternative considered: map old teachers to accounts using email, but old emails are optional and the user explicitly permits discarding old records.

## Risks / Trade-offs

- [Old Teacher and Lesson data is lost] -> Document the destructive migration and require a database backup before deployment if that data might be needed.
- [Group edits outside the role endpoint could leave an assigned user without TEACHER] -> Protect the Django Admin editing path and use model validation for subsequent lesson writes; document that direct database writes bypass application role rules.
- [Concurrent demotion and lesson creation could race] -> Serialize the eligibility check and both write paths on SQLite; verify concurrent attempts leave either a valid assignment or a rejected role change. Row locking alone is insufficient on SQLite.
- [Clients still expect Teacher CRUD fields or old IDs] -> Document the breaking route and payload changes and return method/field errors clearly.

## Migration Plan

1. Back up any deployed database if old Teacher or Lesson data could be needed; the migration intentionally discards both.
2. Apply the schema/data migration that replaces the lesson table and removes Teacher, then installs the updated SQLite triggers.
3. Run the idempotent bootstrap command to ensure the TEACHER group exists, then deploy the updated API and Admin configuration together.
4. Verify that unrelated records remain, the teacher directory reflects role changes, and lesson validation/conflict checks work.
5. Roll back application code and restore the pre-migration database backup if rollback is required; reversing the data loss is unsupported.
