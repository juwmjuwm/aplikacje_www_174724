# Tasks

## 1. Role management

- [x] 1.1 Add TEACHER group bootstrap and effective-role handling, keeping TEACHER distinct from PLANNER; verify repeated bootstrap is idempotent and user responses show TEACHER after promotion.
- [x] 1.2 Extend the ADMIN role action for VIEWER/TEACHER transitions, disallow direct TEACHER/PLANNER switches and ADMIN targets, and reject removal of assigned TEACHER with HTTP 409 `detail`; verify each transition and rejection through API requests, including one using an existing access token.
- [x] 1.3 Keep assigned TEACHER role removal blocked through Django Admin group editing and preserve VIEWER-only account deletion; verify Admin and API attempts leave assigned users and lessons unchanged.
- [x] 1.4 Document TEACHER assignment, demotion, and deletion behavior in README; verify the examples match the role endpoint and error shape.

## 2. Lesson model and migration

- [x] 2.1 Create a migration that discards existing Lesson and Teacher rows, removes Teacher, recreates Lesson with `teacher` targeting the configured User model, and reinstalls both SQLite conflict triggers; verify it on a populated disposable database by inspecting retained records and checking for no pending model changes.
- [x] 2.2 Enforce TEACHER eligibility in Lesson model validation and preserve interval, room, teacher-user, and student-group conflict rules; verify valid assignment, invalid roles, back-to-back lessons, and cross-timetable conflicts through model and Admin operations.
- [x] 2.3 Serialize SQLite lesson assignment with TEACHER demotion checks so concurrent writes cannot leave an ineligible assigned user; verify competing assignment and demotion requests leave a valid state.
- [x] 2.4 Update Lesson Admin form, list, search, and filters for user-backed teachers; verify Admin accepts TEACHER users and reports a field error for other users.
- [x] 2.5 Document migration data loss and backup/rollback instructions in README; verify it explicitly names both discarded tables and unaffected records.

## 3. Teacher and lesson API

- [x] 3.1 Replace the Teacher ModelViewSet and serializer with a read-only user directory at the existing teacher route; verify authenticated list/detail, non-TEACHER exclusion and 404, non-secret fields, and unsupported write methods through API requests.
- [x] 3.2 Make the lesson serializer accept and return TEACHER user IDs and report HTTP 400 `teacher` errors for other or missing users; verify create and update, including existing conflict error behavior, through API requests.
- [x] 3.3 Verify through API requests that TEACHER has VIEWER-equivalent scheduling read access and HTTP 403 for writes while PLANNER and ADMIN retain writes.
- [x] 3.4 Update README teacher route and lesson payload examples, removing Teacher CRUD and academic-title guidance; verify documented JSON matches observed API responses.

## 4. Integration verification

- [x] 4.1 Run Django checks, migration checks, and OpenSpec validation; verify role promotion, teacher listing, lesson assignment, blocked demotion, and migration outcomes together through observable requests and database inspection.
