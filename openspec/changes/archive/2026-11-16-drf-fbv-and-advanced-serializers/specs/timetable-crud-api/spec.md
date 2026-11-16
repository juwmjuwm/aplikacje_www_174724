# Spec Delta

## MODIFIED Requirements

### Requirement: Expanded lesson response
Lesson list, detail, create, and update responses SHALL embed `timetable`, `student_group`, `subject`, `teacher`, and `room` as objects. They SHALL include each related resource's public fields, helper read-only fields (`timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`), and computed metrics (`duration_minutes` as integer minutes, `room_utilization_percentage` as percentage of capacity rounded to one decimal place). They SHALL exclude credentials and other secret account fields.

#### Scenario: Read a lesson with related objects
- **WHEN** an authenticated user lists or retrieves lessons
- **THEN** each lesson includes timetable `id`, `name`, `description`; group `id`, `name`, `size`; subject `id`, `name`, `description`; teacher `id`, `username`, `first_name`, `last_name`, `roles`; room `id`, `name`, `capacity`; helper fields `timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`; and computed metrics `duration_minutes` and `room_utilization_percentage`

#### Scenario: Create or edit a lesson with IDs
- **WHEN** an authorized editor creates or updates a valid lesson using related record IDs
- **THEN** the write succeeds and its response embeds the same related object shapes, helper fields, and computed metrics used by lesson reads

### Requirement: Lesson scheduling validation
The API SHALL enforce valid-interval rules, operational hours (between 07:00 and 21:00), lesson duration constraints (between 30 and 240 minutes), and shared-resource conflict rules when creating or updating lessons and SHALL return field-specific JSON errors for violations.

#### Scenario: Invalid lesson interval
- **WHEN** a client submits a lesson whose end time is not later than its start time
- **THEN** the API returns HTTP 400 with an `end_time` error explaining the interval problem and stores no invalid change

#### Scenario: Outside operational hours
- **WHEN** a client submits a lesson starting before 07:00:00 or ending after 21:00:00
- **THEN** the API returns HTTP 400 with a field error identifying the invalid start or end time

#### Scenario: Out of range lesson duration
- **WHEN** a client submits a lesson with duration under 30 minutes or exceeding 240 minutes
- **THEN** the API returns HTTP 400 with an error explaining the duration requirement

#### Scenario: Resource conflict
- **WHEN** a client submits an overlapping lesson using an already booked room, teacher, or student group
- **THEN** the API returns HTTP 400 with an error on the conflicting resource field and stores no invalid change

## ADDED Requirements

### Requirement: Function-based views for scheduling resources
All scheduling collection, detail, and specialized actions (`timetables`, `lessons`, `student-groups`, `subjects`, `teachers`, `rooms`) SHALL be served by explicit function-based views decorated with `@api_view`, with database query optimizations using `select_related` for ForeignKeys and `prefetch_related` for reverse/many-to-many relationships.

#### Scenario: Optimized lesson collection query
- **WHEN** an authenticated client retrieves `/api/lessons/`
- **THEN** the view queries `Lesson` using `select_related('timetable', 'student_group', 'subject', 'teacher', 'room')` and `prefetch_related('teacher__groups')`, avoiding N+1 queries for nested representations

#### Scenario: Functional CRUD operations
- **WHEN** an authorized client interacts with scheduling routes via GET, POST, PUT, PATCH, or DELETE
- **THEN** the corresponding function-based view processes the request, enforces permissions and validations, and returns standard DRF responses and status codes

