# Spec Delta

## MODIFIED Requirements

### Requirement: Relationship input and output
The API SHALL accept existing record IDs for lesson relationships and SHALL reject IDs that do not identify eligible related records. Lesson responses SHALL instead represent each relationship as a complete, non-secret related object.

#### Scenario: Create a timetable and lesson
- **WHEN** a client creates a timetable and then supplies its ID and existing student group, subject, eligible teacher, and room IDs to create a lesson
- **THEN** the records can be created, and the lesson response includes the related objects rather than bare relationship IDs

#### Scenario: Unknown related record
- **WHEN** a client supplies a nonexistent or ineligible related record ID for a lesson
- **THEN** the API returns HTTP 400 with a JSON error identifying the invalid relationship field

### Requirement: Lesson teacher relationship in JSON
The lesson API SHALL accept the teacher's user ID in its `teacher` request field and SHALL return the teacher's non-secret account representation in its `teacher` response field. It SHALL reject a nonexistent user ID or a user without TEACHER membership with HTTP 400 and a `teacher` field error.

#### Scenario: Create a lesson with a teacher user
- **WHEN** a PLANNER or ADMIN creates a valid lesson using a TEACHER user's ID
- **THEN** the response includes a `teacher` object with that user's `id`, `username`, `first_name`, `last_name`, and `roles`

#### Scenario: Submit an ineligible teacher ID
- **WHEN** a PLANNER or ADMIN submits a lesson with the ID of a user lacking TEACHER membership, or a nonexistent user ID, as `teacher`
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

### Requirement: Lesson teacher ID acceptance
The lesson API SHALL accept a user ID in `teacher` whenever that user holds TEACHER membership, including a PLANNER or ADMIN who also holds TEACHER. It SHALL reject a nonexistent user ID or one without TEACHER membership with HTTP 400 and a `teacher` field error. Successful lesson responses SHALL embed the teacher's non-secret account representation.

#### Scenario: Create a lesson for a combined-role teacher
- **WHEN** an authorized editor creates a valid lesson with the ID of a user holding both PLANNER and TEACHER
- **THEN** the response contains that user's account object in `teacher`, including both memberships in `roles`

#### Scenario: Reject a planner without teacher membership
- **WHEN** an authorized editor submits the ID of a PLANNER who lacks TEACHER membership
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

## ADDED Requirements

### Requirement: Expanded lesson response
Lesson list, detail, create, and update responses SHALL embed `timetable`, `student_group`, `subject`, `teacher`, and `room` as objects. They SHALL include each related resource's public fields and exclude credentials and other secret account fields.

#### Scenario: Read a lesson with related objects
- **WHEN** an authenticated user lists or retrieves lessons
- **THEN** each lesson includes timetable `id`, `name`, `description`; group `id`, `name`, `size`; subject `id`, `name`, `description`; teacher `id`, `username`, `first_name`, `last_name`, `roles`; and room `id`, `name`, `capacity`

#### Scenario: Create or edit a lesson with IDs
- **WHEN** an authorized editor creates or updates a valid lesson using related record IDs
- **THEN** the write succeeds and its response embeds the same related object shapes used by lesson reads

### Requirement: Timetable lessons endpoint
`GET /api/timetables/{id}/lessons/` SHALL return the requested timetable's `id`, `name`, and all its lessons in an unpaginated `lessons` array. It SHALL use the expanded lesson representation and calendar ordering. The endpoint SHALL follow timetable read permissions.

#### Scenario: Read a populated timetable
- **WHEN** an authenticated user requests lessons for an existing timetable
- **THEN** HTTP 200 returns that timetable's `id` and `name` and all its lessons ordered Monday through Sunday, then by start time and lesson ID

#### Scenario: Read an empty timetable
- **WHEN** an authenticated user requests lessons for an existing timetable with no lessons
- **THEN** HTTP 200 returns the timetable's `id`, `name`, and `lessons: []`

#### Scenario: Missing timetable
- **WHEN** an authenticated user requests lessons for a nonexistent timetable ID
- **THEN** the API returns HTTP 404 with a JSON `detail` message

#### Scenario: Unauthenticated request
- **WHEN** a caller without valid authentication requests a timetable's lessons
- **THEN** the API returns HTTP 401

### Requirement: Lesson collection calendar order
`GET /api/lessons/` SHALL order lessons Monday through Sunday, then by ascending start time and lesson ID, before pagination.

#### Scenario: Page across weekdays
- **WHEN** an authenticated user requests a page of lessons with records on several weekdays
- **THEN** the page and its navigation follow calendar-day order rather than alphabetical weekday-code order

### Requirement: Capacity validation errors
The API SHALL reject writes that would make an assigned student group larger than its lesson room with HTTP 400, a meaningful error on the relevant field, and no partial change.

#### Scenario: Oversized group on lesson creation or edit
- **WHEN** a PLANNER or ADMIN creates or edits a lesson whose group size exceeds its room capacity
- **THEN** HTTP 400 identifies `room` with a capacity explanation and preserves the previous data

#### Scenario: Group size increase invalidates lessons
- **WHEN** a PLANNER or ADMIN updates a group's `size` beyond the capacity of a room used by one of its lessons
- **THEN** HTTP 400 identifies `size` with a capacity explanation and leaves the group unchanged

#### Scenario: Room capacity decrease invalidates lessons
- **WHEN** a PLANNER or ADMIN updates a room's `capacity` below a group size assigned to one of its lessons
- **THEN** HTTP 400 identifies `capacity` with a size explanation and leaves the room unchanged
