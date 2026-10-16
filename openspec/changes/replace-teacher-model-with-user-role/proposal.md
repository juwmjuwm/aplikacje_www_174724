# Proposal

## Why

Teachers already need user accounts, so a separate Teacher record duplicates their identity and can diverge from account data. Assigning a TEACHER role to an existing VIEWER makes teacher selection and lesson ownership use one identity.

## What Changes

- Add an ADMIN-managed TEACHER role for existing VIEWER users. TEACHER has the same scheduling access as VIEWER.
- **BREAKING** Replace the Teacher model with the user account as `Lesson.teacher`; only TEACHER users may be assigned to lessons.
- **BREAKING** Make `/api/teachers/` a read-only list and detail view of TEACHER users instead of a CRUD resource for Teacher records. Lesson `teacher` IDs become user IDs; teacher responses use non-secret user fields.
- Block removal of TEACHER while the user is assigned to any lesson, with a meaningful HTTP 409 response.
- Delete existing Teacher and Lesson rows in the migration, as explicitly permitted; retain other scheduling and user records.

## Capabilities

### New Capabilities

- `user-accounts`: ADMIN role assignment, exclusive TEACHER membership, and safe demotion of assigned teachers.
- `timetable-access`: TEACHER scheduling permissions remain equivalent to VIEWER.
- `weekly-timetables`: Lessons reference eligible user accounts and preserve existing scheduling rules.
- `timetable-crud-api`: Teacher directory and lesson relationship API behavior.

### Modified Capabilities

None. The project has no synced main specs yet. These paths follow the relevant existing change specs; this change supersedes their conflicting Teacher requirements when the history is reconciled.

## Impact

- Account role logic, role endpoint, bootstrap, scheduling permissions, and account deletion rules.
- Lesson model and migration, serializers, teacher and lesson views, router, Django Admin, and README.
- The migration intentionally discards existing Teacher and Lesson data. Existing clients must stop creating Teacher records and treat lesson `teacher` values as user IDs.
