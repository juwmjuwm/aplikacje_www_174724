# Spec Delta

## Purpose

Control read and write access to shared scheduling resources using each account's current memberships and administrator status.

## ADDED Requirements

### Requirement: Scheduling access with combined memberships
An active authenticated user SHALL be able to read scheduling resources. Writes SHALL be allowed for ADMIN and users with PLANNER membership, including users who also hold TEACHER. A user with only TEACHER or neither group membership SHALL have read access only. Changes in membership SHALL affect subsequent requests using existing access tokens.

#### Scenario: Combined-role user edits a lesson
- **WHEN** a user with both PLANNER and TEACHER memberships creates or updates a valid lesson
- **THEN** the request is authorized for writing

#### Scenario: Teacher-only user attempts a write
- **WHEN** a user with TEACHER membership but no PLANNER membership attempts a scheduling write
- **THEN** the request returns HTTP 403 without changing scheduling data

#### Scenario: Planner membership is removed
- **WHEN** ADMIN removes PLANNER while leaving TEACHER and the user retries a scheduling write with an existing token
- **THEN** the write returns HTTP 403
