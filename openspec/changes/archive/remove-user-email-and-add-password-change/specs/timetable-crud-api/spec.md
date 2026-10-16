# Spec Delta

## Purpose

Expose scheduling resources and the teacher directory using the current, email-free account identity of every eligible TEACHER user.

## ADDED Requirements

### Requirement: Email-free teacher directory
Authenticated callers SHALL be able to list and retrieve TEACHER members at `GET /api/teachers/` and `GET /api/teachers/{id}/`. Each teacher representation SHALL include `id`, `username`, `role`, and `roles` and SHALL omit email and passwords. Existing membership eligibility, ordering, and read-only behavior SHALL remain in effect.

#### Scenario: List a combined-role teacher
- **WHEN** an authenticated caller lists teachers and an account holds PLANNER and TEACHER memberships
- **THEN** the account appears once with both memberships and no email field

#### Scenario: Retrieve an admin teacher
- **WHEN** an authenticated caller retrieves an ADMIN who holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles` and no email field
