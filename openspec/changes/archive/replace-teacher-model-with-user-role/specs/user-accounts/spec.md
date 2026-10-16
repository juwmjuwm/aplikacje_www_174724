# Spec Delta

## Purpose

Provide account registration, profile access, role management, and safe account deletion for people who use the timetable service.

## ADDED Requirements

### Requirement: Teacher role assignment
The system SHALL let ADMIN assign TEACHER to an existing VIEWER through `PATCH /api/users/{id}/role/` with `{"role":"TEACHER"}`. TEACHER SHALL be distinct from PLANNER and ADMIN. Only ADMIN SHALL change roles; registration and profile updates SHALL NOT grant TEACHER.

#### Scenario: Promote a viewer to teacher
- **WHEN** ADMIN sets an existing VIEWER's role to TEACHER
- **THEN** the role endpoint returns the account with role TEACHER and subsequent requests using an existing token use that role

#### Scenario: Unauthorized teacher promotion
- **WHEN** a non-ADMIN user attempts to assign TEACHER or submits a role through registration or profile update
- **THEN** the request is rejected without changing role membership

#### Scenario: Assign teacher to another role
- **WHEN** ADMIN attempts to set an ADMIN or PLANNER account directly to TEACHER
- **THEN** the role endpoint rejects the change without changing the account

### Requirement: Teacher role removal
The system SHALL let ADMIN set an unassigned TEACHER back to VIEWER. It SHALL reject any change that removes TEACHER from a user assigned to a lesson with HTTP 409 and a `detail` message explaining that lessons must first be reassigned or deleted.

#### Scenario: Demote an unassigned teacher
- **WHEN** ADMIN sets an unassigned TEACHER's role to VIEWER
- **THEN** the role endpoint succeeds and the account is no longer eligible for teacher assignment

#### Scenario: Block demotion of an assigned teacher
- **WHEN** ADMIN attempts to change an assigned TEACHER to VIEWER or PLANNER
- **THEN** the endpoint returns HTTP 409 with a meaningful `detail` and leaves the role and lessons unchanged

### Requirement: Teacher account deletion
The system SHALL continue to allow ADMIN to delete only current VIEWER accounts. TEACHER accounts SHALL receive HTTP 409 until they are safely demoted to VIEWER.

#### Scenario: Delete a teacher account
- **WHEN** ADMIN attempts to delete a TEACHER account
- **THEN** the endpoint returns HTTP 409 without deleting the account or its lessons
