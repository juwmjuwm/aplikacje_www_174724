# timetable-crud-api Specification

## Purpose

Provide a JSON REST interface for managing weekly timetables, lessons, and their shared reference records, with clear responses for successful and invalid requests.

## Requirements

### Requirement: Paginated scheduling collections
Authenticated clients SHALL receive paginated results from `GET /api/timetables/`, `/api/lessons/`, `/api/student-groups/`, `/api/subjects/`, `/api/teachers/`, and `/api/rooms/`. Each response SHALL contain `count`, `next`, `previous`, and `results`. The default page size SHALL be 10; `page` SHALL select a page, and positive integer `size` SHALL set its size up to a maximum of 100.

#### Scenario: Default page
- **WHEN** an authenticated client lists a scheduling collection without pagination parameters and more than 10 records exist
- **THEN** `results` contains the first 10 records in a stable order, `count` is the total number of matching records, and `next` links to the next page

#### Scenario: Requested page and size
- **WHEN** an authenticated client requests `?page=2&size=25` from a collection with more than 25 records
- **THEN** `results` contains the second page of up to 25 records in the same stable order and `previous` links to the first page

#### Scenario: Size cap
- **WHEN** an authenticated client requests a `size` greater than 100
- **THEN** the response contains no more than 100 records in `results`

#### Scenario: Invalid page size
- **WHEN** an authenticated client supplies a nonnumeric, zero, or negative `size`
- **THEN** the API returns HTTP 400 with a JSON error identifying `size`

### Requirement: Searchable scheduling collections
Authenticated clients SHALL be able to use `search` on the existing timetable, student group, subject, teacher, and room list routes. Matching SHALL be case-insensitive and include partial field values. Timetables, student groups, and rooms SHALL match `name`; subjects SHALL match `name` or `description`; teachers SHALL match `first_name` or `last_name` among TEACHER members only. Search SHALL apply before pagination.

#### Scenario: Search by subject description
- **WHEN** an authenticated client requests `/api/subjects/?search=biology` and a subject description contains `Biology` while its name does not
- **THEN** that subject appears in `results` and unrelated subjects do not

#### Scenario: Search by teacher surname
- **WHEN** an authenticated client requests `/api/teachers/?search=Nowak` and a TEACHER member's `last_name` contains `Nowak`
- **THEN** that teacher appears in `results`, while a matching account without TEACHER membership does not

#### Scenario: Search with pagination
- **WHEN** an authenticated client requests a searchable collection with both `search` and `page` or `size`
- **THEN** `count`, navigation links, and `results` describe only the matching records

### Requirement: CRUD resources
The system SHALL expose list, retrieve, create, full update, partial update, and delete operations under `/api/` for Timetable, Lesson, StudentGroup, Subject, Teacher, and Room records.

#### Scenario: Create and retrieve a resource
- **WHEN** a client creates a valid record for any of the six models and retrieves its returned ID
- **THEN** creation returns HTTP 201 with the record in JSON and retrieval returns HTTP 200 with that record in JSON

#### Scenario: List and update a resource
- **WHEN** a client lists a resource collection or updates a valid record with PUT or PATCH
- **THEN** the response is HTTP 200 with the corresponding JSON collection or updated record

#### Scenario: Delete a resource
- **WHEN** a client deletes an existing record that is permitted by the existing model relationships
- **THEN** the response is HTTP 204 and a subsequent retrieval returns HTTP 404

### Requirement: Relationship input and output
The API SHALL accept existing record IDs for lesson relationships and SHALL reject IDs that do not identify eligible related records. Lesson responses SHALL instead represent each relationship as a complete, non-secret related object.

#### Scenario: Create a timetable and lesson
- **WHEN** a client creates a timetable and then supplies its ID and existing student group, subject, eligible teacher, and room IDs to create a lesson
- **THEN** the records can be created, and the lesson response includes the related objects rather than bare relationship IDs

#### Scenario: Unknown related record
- **WHEN** a client supplies a nonexistent or ineligible related record ID for a lesson
- **THEN** the API returns HTTP 400 with a JSON error identifying the invalid relationship field

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

### Requirement: JSON error responses
The API SHALL return a meaningful JSON error body for missing records or routes, invalid input, unsupported methods, and deletion blocked by a related lesson.

#### Scenario: Missing record or API route
- **WHEN** a client requests a nonexistent resource ID or an unknown path under `/api/`
- **THEN** the response is HTTP 404 with a JSON `detail` message saying the resource or endpoint was not found

#### Scenario: Invalid field value
- **WHEN** a client submits a missing required field or invalid field value
- **THEN** the response is HTTP 400 with a JSON error associated with the affected field

#### Scenario: Unsupported method
- **WHEN** a client uses an HTTP method unsupported by an API endpoint
- **THEN** the response is HTTP 405 with a JSON `detail` message identifying the disallowed method

#### Scenario: Protected deletion
- **WHEN** a client attempts to delete a room, teacher, subject, or student group referenced by a lesson
- **THEN** the response is HTTP 409 with a JSON `detail` message explaining that related lessons prevent deletion

### Requirement: Teacher user directory
Authenticated users SHALL be able to list TEACHER users at `GET /api/teachers/` and retrieve one at `GET /api/teachers/{id}/`. Responses SHALL contain `id`, `username`, and `roles` without `role` or secrets. Non-TEACHER users SHALL be excluded, and teacher creation, update, and deletion through this route SHALL be unsupported.

#### Scenario: List available teachers
- **WHEN** an authenticated user requests `GET /api/teachers/`
- **THEN** the response contains only users with TEACHER in `roles` and their user IDs, without a `role` field

#### Scenario: Retrieve an ineligible user as teacher
- **WHEN** an authenticated user requests `/api/teachers/{id}/` for a user who is not TEACHER
- **THEN** the endpoint returns HTTP 404

#### Scenario: Attempt legacy teacher write
- **WHEN** a client sends POST, PUT, PATCH, or DELETE to a teacher directory route
- **THEN** the endpoint rejects the unsupported method and does not change any account

### Requirement: Lesson teacher relationship in JSON
The lesson API SHALL accept the teacher's user ID in its `teacher` request field and SHALL return the teacher's non-secret account representation in its `teacher` response field. It SHALL reject a nonexistent user ID or a user without TEACHER membership with HTTP 400 and a `teacher` field error.

#### Scenario: Create a lesson with a teacher user
- **WHEN** a PLANNER or ADMIN creates a valid lesson using a TEACHER user's ID
- **THEN** the response includes a `teacher` object with that user's `id`, `username`, `first_name`, `last_name`, and `roles`

#### Scenario: Submit an ineligible teacher ID
- **WHEN** a PLANNER or ADMIN submits a lesson with the ID of a user lacking TEACHER membership, or a nonexistent user ID, as `teacher`
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

### Requirement: Complete teacher user directory
Authenticated users SHALL be able to list and retrieve every user with TEACHER membership at `GET /api/teachers/` and `GET /api/teachers/{id}/`, regardless of PLANNER membership or ADMIN status. Users without TEACHER membership SHALL be absent and return HTTP 404 at the detail route. Responses SHALL contain `id`, `username`, and `roles` without `role` or secrets; the route SHALL remain read-only.

#### Scenario: List a planner teacher
- **WHEN** an authenticated user lists teachers and a user holds both PLANNER and TEACHER memberships
- **THEN** that user appears once with both memberships in `roles` and no `role` field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated user retrieves an ADMIN who also holds TEACHER membership through the teacher route
- **THEN** the endpoint returns that user with ADMIN and TEACHER in `roles` and no `role` field

#### Scenario: Retrieve a non-teacher
- **WHEN** an authenticated user requests a teacher detail for an account lacking TEACHER membership
- **THEN** the endpoint returns HTTP 404

### Requirement: Lesson teacher ID acceptance
The lesson API SHALL accept a user ID in `teacher` whenever that user holds TEACHER membership, including a PLANNER or ADMIN who also holds TEACHER. It SHALL reject a nonexistent user ID or one without TEACHER membership with HTTP 400 and a `teacher` field error. Successful lesson responses SHALL embed the teacher's non-secret account representation.

#### Scenario: Create a lesson for a combined-role teacher
- **WHEN** an authorized editor creates a valid lesson with the ID of a user holding both PLANNER and TEACHER
- **THEN** the response contains that user's account object in `teacher`, including both memberships in `roles`

#### Scenario: Reject a planner without teacher membership
- **WHEN** an authorized editor submits the ID of a PLANNER who lacks TEACHER membership
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

### Requirement: Email-free teacher directory
Authenticated callers SHALL be able to list and retrieve TEACHER members at `GET /api/teachers/` and `GET /api/teachers/{id}/`. Each teacher representation SHALL include `id`, `username`, `first_name`, `last_name`, and `roles` and SHALL omit `role`, email, and passwords. Existing membership eligibility, ordering, and read-only behavior SHALL remain in effect.

#### Scenario: List a combined-role teacher
- **WHEN** an authenticated caller lists teachers and an account holds PLANNER and TEACHER memberships
- **THEN** the account appears once with both memberships, its first and last names, and no `role` or email field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated caller retrieves an ADMIN who holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles`, first and last names, and no `role` or email field

### Requirement: Expanded lesson response
Lesson list, detail, create, and update responses SHALL embed `timetable`, `student_group`, `subject`, `teacher`, and `room` as objects. They SHALL include each related resource's public fields, helper read-only fields (`timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`), and computed metrics (`duration_minutes` as integer minutes, `room_utilization_percentage` as percentage of capacity rounded to one decimal place). They SHALL exclude credentials and other secret account fields.

#### Scenario: Read a lesson with related objects
- **WHEN** an authenticated user lists or retrieves lessons
- **THEN** each lesson includes timetable `id`, `name`, `description`; group `id`, `name`, `size`; subject `id`, `name`, `description`; teacher `id`, `username`, `first_name`, `last_name`, `roles`; room `id`, `name`, `capacity`; helper fields `timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`; and computed metrics `duration_minutes` and `room_utilization_percentage`

#### Scenario: Create or edit a lesson with IDs
- **WHEN** an authorized editor creates or updates a valid lesson using related record IDs
- **THEN** the write succeeds and its response embeds the same related object shapes, helper fields, and computed metrics used by lesson reads

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

### Requirement: Function-based views for scheduling resources
All scheduling collection, detail, and specialized actions (`timetables`, `lessons`, `student-groups`, `subjects`, `teachers`, `rooms`) SHALL be served by explicit function-based views decorated with `@api_view`, with database query optimizations using `select_related` for ForeignKeys and `prefetch_related` for reverse/many-to-many relationships.

#### Scenario: Optimized lesson collection query
- **WHEN** an authenticated client retrieves `/api/lessons/`
- **THEN** the view queries `Lesson` using `select_related('timetable', 'student_group', 'subject', 'teacher', 'room')` and `prefetch_related('teacher__groups')`, avoiding N+1 queries for nested representations

#### Scenario: Functional CRUD operations
- **WHEN** an authorized client interacts with scheduling routes via GET, POST, PUT, PATCH, or DELETE
- **THEN** the corresponding function-based view processes the request, enforces permissions and validations, and returns standard DRF responses and status codes
