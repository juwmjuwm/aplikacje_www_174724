# Spec Delta

## Purpose

Expose JSON timetable resources and a teacher directory so clients can choose eligible user IDs for lessons.

## ADDED Requirements

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
