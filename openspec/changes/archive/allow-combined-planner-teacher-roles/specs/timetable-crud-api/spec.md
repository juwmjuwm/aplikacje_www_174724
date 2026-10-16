# Spec Delta

## Purpose

Expose scheduling resources and a teacher directory that identifies every user eligible for lesson assignment.

## ADDED Requirements

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
