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
The system SHALL represent model relationships using record IDs in JSON and SHALL reject references to records that do not exist.

#### Scenario: Create a timetable and lesson
- **WHEN** a client supplies an existing owner ID for a timetable and existing timetable, student group, subject, teacher, and room IDs for a lesson
- **THEN** the records can be created and their JSON representations include those relationship IDs

#### Scenario: Unknown related record
- **WHEN** a client supplies a nonexistent owner or related record ID
- **THEN** the API returns HTTP 400 with a JSON error identifying the invalid relationship field

### Requirement: Lesson scheduling validation
The API SHALL enforce the existing valid-interval and shared-resource conflict rules when creating or updating lessons and SHALL return field-specific JSON errors for violations.

#### Scenario: Invalid lesson interval
- **WHEN** a client submits a lesson whose end time is not later than its start time
- **THEN** the API returns HTTP 400 with an `end_time` error explaining the interval problem and stores no invalid change

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
Authenticated users SHALL be able to list TEACHER users at `GET /api/teachers/` and retrieve one at `GET /api/teachers/{id}/`. Responses SHALL contain `id`, `username`, `email`, and `role`, without secrets. Non-TEACHER users SHALL be excluded, and teacher creation, update, and deletion through this route SHALL be unsupported.

#### Scenario: List available teachers
- **WHEN** an authenticated user requests `GET /api/teachers/`
- **THEN** the response contains only users with role TEACHER and their user IDs

#### Scenario: Retrieve an ineligible user as teacher
- **WHEN** an authenticated user requests `/api/teachers/{id}/` for a user who is not TEACHER
- **THEN** the endpoint returns HTTP 404

#### Scenario: Attempt legacy teacher write
- **WHEN** a client sends POST, PUT, PATCH, or DELETE to a teacher directory route
- **THEN** the endpoint rejects the unsupported method and does not change any account

### Requirement: Lesson teacher relationship in JSON
The lesson API SHALL accept and return the teacher's user ID in its `teacher` field. It SHALL reject a nonexistent or non-TEACHER user ID with HTTP 400 and a `teacher` field error.

#### Scenario: Create a lesson with a teacher user
- **WHEN** a PLANNER or ADMIN creates a valid lesson using a TEACHER user's ID
- **THEN** the response includes that user ID in `teacher`

#### Scenario: Submit an ineligible teacher ID
- **WHEN** a PLANNER or ADMIN submits a lesson with a VIEWER, PLANNER, ADMIN, or nonexistent user ID as `teacher`
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

### Requirement: Complete teacher user directory
Authenticated users SHALL be able to list and retrieve every user with TEACHER membership at `GET /api/teachers/` and `GET /api/teachers/{id}/`, regardless of PLANNER membership or ADMIN status. Users without TEACHER membership SHALL be absent and return HTTP 404 at the detail route. Responses SHALL contain `id`, `username`, `email`, `role`, and `roles`, without secrets; the route SHALL remain read-only.

#### Scenario: List a planner teacher
- **WHEN** an authenticated user lists teachers and a user holds both PLANNER and TEACHER memberships
- **THEN** that user appears once with both memberships in `roles`

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated user retrieves an ADMIN who also holds TEACHER membership through the teacher route
- **THEN** the endpoint returns that user with ADMIN and TEACHER in `roles`

#### Scenario: Retrieve a non-teacher
- **WHEN** an authenticated user requests a teacher detail for an account lacking TEACHER membership
- **THEN** the endpoint returns HTTP 404

### Requirement: Lesson teacher ID acceptance
The lesson API SHALL accept a user ID in `teacher` whenever that user holds TEACHER membership, including a PLANNER or ADMIN who also holds TEACHER. It SHALL reject a nonexistent user ID or one without TEACHER membership with HTTP 400 and a `teacher` field error.

#### Scenario: Create a lesson for a combined-role teacher
- **WHEN** an authorized editor creates a valid lesson with the ID of a user holding both PLANNER and TEACHER
- **THEN** the response contains that user ID in `teacher`

#### Scenario: Reject a planner without teacher membership
- **WHEN** an authorized editor submits the ID of a PLANNER who lacks TEACHER membership
- **THEN** the API returns HTTP 400 with a `teacher` error and saves no invalid lesson

### Requirement: Email-free teacher directory
Authenticated callers SHALL be able to list and retrieve TEACHER members at `GET /api/teachers/` and `GET /api/teachers/{id}/`. Each teacher representation SHALL include `id`, `username`, `first_name`, `last_name`, `role`, and `roles` and SHALL omit email and passwords. Existing membership eligibility, ordering, and read-only behavior SHALL remain in effect.

#### Scenario: List a combined-role teacher
- **WHEN** an authenticated caller lists teachers and an account holds PLANNER and TEACHER memberships
- **THEN** the account appears once with both memberships, its first and last names, and no email field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated caller retrieves an ADMIN who holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles`, first and last names, and no email field
