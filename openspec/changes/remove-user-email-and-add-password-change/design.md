# Design

## Context

The project uses Django's built-in `auth.User`; account and teacher serializers expose its optional `email` field. The account table is `auth_user`, with group and permission join tables, and `Lesson.teacher` references the configured user model. Both `timetables` migration `0001` and `0003` use a swappable user dependency. The only current test module is `timetables/tests.py`. See `proposal.md` for motivation and the two delta specs for behavior.

## Goals / Non-Goals

**Goals:**

- Make the active account model and physical account table email-free while keeping existing account keys and relationships stable.
- Give authenticated users a dedicated password change action whose serializer cannot expose or accept unrelated fields.
- Support both fresh database creation and transition of an already migrated SQLite database.

**Non-Goals:**

- Administrator password resets, email recovery, or changes to role authorization and teacher eligibility.
- Adding or keeping automated tests; the user explicitly requested removal of all existing tests and no new tests.

## Decisions

### Use a dedicated custom user app while retaining the physical user table

Create a custom `AbstractUser` subclass in a small account app, with `email = None`, a username/password-only manager, and `db_table = 'auth_user'`. Set `AUTH_USER_MODEL` to it. Its initial migration must define the model, because existing swappable dependencies resolve to the configured model's first migration. Keep compatible primary key, password, flags, groups, and permission join tables so existing accounts and lesson foreign keys retain their IDs. Adapt bootstrap and Django Admin to the new model, avoiding inherited forms, fieldsets, or search fields that assume email. Remove the application-level email backend configuration and user-email references.

An alternative is a new user table with row copying and foreign-key rewiring. Reusing the physical table avoids changing `Lesson.teacher_id`, Admin log references, and existing membership join rows. Leaving `auth.User` in service while hiding email would fail the model and database requirements.

### Handle the installed-database migration graph before normal migrate

Switching `AUTH_USER_MODEL` changes the dependency target of already-applied migrations. A populated database can therefore fail Django's consistency check before it reaches a normal migration. Provide an explicit, idempotent pre-migrate transition for an existing SQLite database: verify the expected `auth_user` schema and applied history, take/require a backup, then record the custom user app's initial state migration as applied only when its compatible physical tables already exist. The following database migration removes the old email column while preserving rows and constraints. A fresh database runs the initial migration normally and creates an email-free table, then the column-removal step is a no-op. Check the resulting migration graph and schema on both paths; do not fake arbitrary migrations or delete user rows.

The alternative of simply adding `AUTH_USER_MODEL` and running `migrate` is insufficient for already-applied swappable dependencies. The migration transition must be a documented deployment step. Keep the historical `Teacher.email` field in old, already-applied migration definitions so Django can reconstruct that historical state; the active Teacher model was removed by migration `0003`.

### Use a separate self-service endpoint

Mount `POST /api/users/me/password/` before the user router. Authenticate the request, validate an exact `current_password` and `new_password` payload, call the configured password validators with the current user, reject reuse of the current password, and save through `set_password()`. Return 204 with no body. Keep `PATCH /api/users/{id}/` limited to username, so ADMIN's existing profile permission cannot turn into an administrator password reset. Existing JWT lifetime and refresh behavior are unchanged; this endpoint changes the credential checked at token issuance.

An alternative is a detail action under `/api/users/{id}/password/`. A `me` route avoids a target ID and makes the self-only rule explicit.

### Remove test code and verify without adding tests

Delete `timetables/tests.py` and do not add replacement unit, integration, or migration test files. During application, run Django system checks, migration drift and plan checks, and targeted manual requests for registration, password change, and email rejection. For the migration, inspect a disposable copy of a populated database and a fresh database, comparing account IDs, hashes, memberships, lesson references, foreign keys, and physical columns before and after.

## Risks / Trade-offs

- [The auth-model switch makes an existing migration history inconsistent] -> Use the guarded pre-migrate transition and exercise it on a disposable copy before deployment.
- [The account table rebuild or column drop loses linked rows] -> Back up the SQLite database, preserve the table's key and join-table names, and compare pre/post row identities and foreign-key checks.
- [Inherited Django Admin forms or managers still refer to email] -> Define compatible custom manager/Admin configuration and perform a source search for active email references.
- [Removing tests reduces regression coverage] -> Record manual verification steps and Django check results in the implementation summary; do not create tests against the user's instruction.

## Migration Plan

1. Prepare the custom user initial migration, email-column removal migration, and guarded existing-database transition. Document the exact order before switching a populated deployment.
2. On a disposable populated database copy, back up the original, run the pre-migrate transition, then normal migrations. Compare account rows, password hashes, group/permission memberships, lessons, `PRAGMA foreign_key_check`, and account columns. Repeat normal migration to confirm idempotence.
3. On an empty disposable database, run standard migrations and bootstrap. Confirm there is no email column and the authentication and teacher flows work.
4. For deployment, stop writers, back up the SQLite database, run the guarded transition, apply migrations, and restart with the new code. Existing email values are intentionally discarded. Restore the database backup and previous code to roll back; adding the old email column back is not a supported reverse migration.
