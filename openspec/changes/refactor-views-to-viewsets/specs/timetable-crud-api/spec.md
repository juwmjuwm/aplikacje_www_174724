# Spec Delta

## ADDED Requirements

### Requirement: ViewSet-based scheduling endpoints
All scheduling collection, detail, and resource actions (`timetables`, `lessons`, `student-groups`, `subjects`, `teachers`, `rooms`) SHALL be served by DRF `ModelViewSet` or read-only `ModelViewSet` classes registered with `DefaultRouter` under `/api/`, using `select_related` and `prefetch_related` query optimizations to prevent N+1 queries.

#### Scenario: Optimized lesson collection query
- **WHEN** an authenticated client retrieves `/api/lessons/`
- **THEN** the ViewSet queries `Lesson` with `select_related('timetable', 'student_group', 'subject', 'teacher', 'room')` and `prefetch_related('teacher__groups')` without per-row `lessons_count` queries

#### Scenario: ViewSet CRUD and router dispatch
- **WHEN** an authorized client sends GET, POST, PUT, PATCH, or DELETE to a router-registered scheduling endpoint
- **THEN** the corresponding ViewSet enforces `SchedulingPermission`, validates input, and returns standard DRF responses and status codes

### Requirement: Timetable clear-lessons action
`POST /api/timetables/{id}/clear-lessons/` SHALL remove all lessons associated with the specified timetable and return HTTP 200 with the timetable `id`, `name`, and `deleted_lessons_count`. It SHALL require PLANNER or ADMIN privileges, returning HTTP 403 for VIEWER or TEACHER callers and HTTP 404 when the timetable does not exist.

#### Scenario: Authorized planner clears timetable lessons
- **WHEN** a PLANNER or ADMIN sends `POST /api/timetables/{id}/clear-lessons/` for an existing timetable with lessons
- **THEN** all lessons of that timetable are deleted, other timetables remain untouched, and HTTP 200 returns `id`, `name`, and `deleted_lessons_count`

#### Scenario: Unauthorized viewer attempts to clear lessons
- **WHEN** a VIEWER or TEACHER sends `POST /api/timetables/{id}/clear-lessons/`
- **THEN** the API returns HTTP 403 and preserves all lessons

#### Scenario: Clear lessons for missing timetable
- **WHEN** an authorized editor sends `POST /api/timetables/{id}/clear-lessons/` for a nonexistent ID
- **THEN** the API returns HTTP 404

### Requirement: Scheduling summary endpoint
`GET /api/summary/` SHALL return an aggregated JSON overview of scheduling resources for authenticated users, including `timetables_count`, `lessons_count`, `student_groups_count`, `subjects_count`, `rooms_count`, `teachers_count`, `min_room_capacity`, `max_room_capacity`, and `average_room_capacity`. Unauthenticated requests SHALL receive HTTP 401.

#### Scenario: Authenticated summary retrieval
- **WHEN** an authenticated user sends `GET /api/summary/`
- **THEN** HTTP 200 returns aggregated counts and room capacity statistics computed across the database

#### Scenario: Unauthenticated summary request
- **WHEN** an unauthenticated caller sends `GET /api/summary/`
- **THEN** the API returns HTTP 401

## MODIFIED Requirements

### Requirement: Expanded lesson response
Lesson list responses (`GET /api/lessons/`) SHALL embed compact nested objects for `timetable`, `student_group`, `subject`, `teacher`, and `room` without per-related-record `lessons_count`, `description`, helper `*_name` fields, or computed metrics. Lesson detail (`GET /api/lessons/{id}/`), create, and update responses SHALL embed complete public related objects, helper read-only fields (`timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`), and computed metrics (`duration_minutes` as integer minutes, `room_utilization_percentage` rounded to one decimal place), excluding credentials and secret account fields.

#### Scenario: List lessons with lightweight nested objects
- **WHEN** an authenticated user lists lessons via `GET /api/lessons/`
- **THEN** each lesson includes `id`, `weekday`, `start_time`, `end_time`, and compact nested objects (`timetable`, `student_group`, `subject`, `teacher`, `room`) without `lessons_count`, helper `*_name` fields, or computed metrics

#### Scenario: Read a lesson with related objects
- **WHEN** an authenticated user retrieves a single lesson via `GET /api/lessons/{id}/`
- **THEN** the lesson includes timetable `id`, `name`, `description`, `lessons_count`; group `id`, `name`, `size`, `lessons_count`; subject `id`, `name`, `description`, `lessons_count`; teacher `id`, `username`, `first_name`, `last_name`, `roles`; room `id`, `name`, `capacity`, `lessons_count`; helper fields `timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`; and computed metrics `duration_minutes` and `room_utilization_percentage`

#### Scenario: Create or edit a lesson with IDs
- **WHEN** an authorized editor creates or updates a valid lesson using related record IDs
- **THEN** the write succeeds and its response embeds the full related object shapes, helper fields, and computed metrics used by lesson detail reads

## REMOVED Requirements

### Requirement: Function-based views for scheduling resources
**Reason**: Replaced by DRF `ModelViewSet` / read-only ViewSet classes registered with `DefaultRouter`.
**Migration**: Use the ViewSet-backed endpoints under `/api/` registered via `DefaultRouter`.
