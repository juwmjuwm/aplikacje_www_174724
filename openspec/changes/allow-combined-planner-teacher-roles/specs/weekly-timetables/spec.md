# Spec Delta

## Purpose

Keep weekly lessons assigned to eligible user accounts while preserving their timetable and resource conflict rules.

## ADDED Requirements

### Requirement: Teacher eligibility by membership
A lesson SHALL accept a user as its teacher when that user holds TEACHER membership, regardless of PLANNER membership or ADMIN status. A user without TEACHER membership SHALL be rejected with a `teacher` validation error. The same rule SHALL apply to API, model, and Django Admin lesson writes.

#### Scenario: Assign a planner teacher
- **WHEN** a lesson is created or updated with a user holding both PLANNER and TEACHER memberships
- **THEN** the lesson stores that user as its teacher

#### Scenario: Assign an admin teacher
- **WHEN** a lesson is created or updated with an ADMIN who also holds TEACHER membership
- **THEN** the lesson stores that user as its teacher

#### Scenario: Reject an ineligible user
- **WHEN** a lesson is created or updated with a user who lacks TEACHER membership
- **THEN** validation rejects the assignment with a `teacher` error and no invalid lesson is saved
