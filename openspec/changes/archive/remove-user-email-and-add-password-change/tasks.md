# Tasks

## 1. User model and database transition

- [x] 1.1 Add an email-free custom User model, compatible manager, and `AUTH_USER_MODEL` setting while retaining the `auth_user` table and existing key and membership table layout; verify the new model has no email field and Django system checks pass.
- [x] 1.2 Create the custom user app's initial migration and an idempotent, guarded pre-migrate transition for populated SQLite databases; verify a disposable populated copy can pass Django's migration consistency check without losing account IDs, hashes, flags, memberships, permissions, or lesson references.
- [x] 1.3 Add the physical email-column removal migration and document the backup, transition, migrate, and rollback order; verify fresh and populated disposable databases have no active user email column, pass foreign-key checks, and can run migrations a second time without changes.

## 2. Account and teacher interfaces

- [x] 2.1 Remove email from registration, profile input, account and teacher responses, and related configuration; verify manual requests reject submitted email with HTTP 400 and return only the documented non-secret account fields.
- [x] 2.2 Add `POST /api/users/me/password/` with current-password verification, a distinct validated new password, strict payload validation, and HTTP 204 success; verify manually that new credentials authenticate, old credentials fail, and invalid or unauthenticated requests do not change the password.
- [x] 2.3 Adapt Django Admin account forms, fieldsets, list/search fields, and lesson teacher search for the custom user while retaining role and teacher-removal safeguards; verify Admin pages load without email fields and existing role and teacher actions remain available.
- [x] 2.4 Update README registration, account, teacher, password-change, and migration examples; verify the examples match the implemented routes and responses.

## 3. Existing test removal

- [x] 3.1 Delete the existing `timetables/tests.py` test suite and add no replacement test files; verify the repository contains no project test modules.

## 4. Integration checks

- [x] 4.1 Run Django system checks, migration drift and plan checks, and focused manual API checks on disposable fresh and populated databases; verify account preservation, email absence, password changes, teacher responses, and role access without creating tests.
- [x] 4.2 Run strict OpenSpec validation for this change; verify proposal, design, specs, and tasks validate.
