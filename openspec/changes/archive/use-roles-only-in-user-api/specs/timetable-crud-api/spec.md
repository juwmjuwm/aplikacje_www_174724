# Spec Delta

## MODIFIED Requirements

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

### Requirement: Email-free teacher directory
Authenticated callers SHALL be able to list and retrieve TEACHER members at `GET /api/teachers/` and `GET /api/teachers/{id}/`. Each teacher representation SHALL include `id`, `username`, `first_name`, `last_name`, and `roles` and SHALL omit `role`, email, and passwords. Existing membership eligibility, ordering, and read-only behavior SHALL remain in effect.

#### Scenario: List a combined-role teacher
- **WHEN** an authenticated caller lists teachers and an account holds PLANNER and TEACHER memberships
- **THEN** the account appears once with both memberships, its first and last names, and no `role` or email field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated caller retrieves an ADMIN who holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles`, first and last names, and no `role` or email field
