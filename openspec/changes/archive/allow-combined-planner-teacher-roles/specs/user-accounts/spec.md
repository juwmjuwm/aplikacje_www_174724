# Spec Delta

## Purpose

Provide safe account role management and a complete representation of each user's permissions and teacher membership.

## ADDED Requirements

### Requirement: Combined account memberships
An ADMIN SHALL be able to set a regular user's complete PLANNER and TEACHER membership set at `PATCH /api/users/{id}/role/` using `roles`, with either, both, or neither role present. An empty array SHALL represent VIEWER. Only ADMIN SHALL change memberships; registration and profile updates SHALL reject submitted privileges, and ADMIN targets SHALL remain unchangeable through this endpoint.

#### Scenario: Assign both roles
- **WHEN** ADMIN sends `{"roles":["PLANNER","TEACHER"]}` for a regular user
- **THEN** the request succeeds and the user holds both memberships on subsequent requests, including those using an existing access token

#### Scenario: Remove only planner membership
- **WHEN** ADMIN sends `{"roles":["TEACHER"]}` for a user with both memberships
- **THEN** the user retains TEACHER membership and loses PLANNER membership

#### Scenario: Reject invalid membership changes
- **WHEN** a non-ADMIN submits a role change, an ADMIN is targeted, or `roles` contains VIEWER, ADMIN, duplicates, or unknown values
- **THEN** the request is rejected without changing memberships

### Requirement: Compatible single-role updates
The role endpoint SHALL continue to accept `{"role":"VIEWER"}`, `{"role":"PLANNER"}`, and `{"role":"TEACHER"}` as complete single-role assignments with its existing direct-switch restriction. A request SHALL contain exactly one of `role` or `roles`; supplying both SHALL return HTTP 400 without changing memberships.

#### Scenario: Existing client assigns one role
- **WHEN** ADMIN sends a valid single `role` request for a regular user
- **THEN** the endpoint applies the existing single-role transition behavior and returns the updated account

#### Scenario: Ambiguous role payload
- **WHEN** ADMIN sends both `role` and `roles` in one request
- **THEN** the endpoint returns HTTP 400 and leaves memberships unchanged

### Requirement: Complete account role representation
Account and teacher responses SHALL include an authoritative `roles` array and retain the existing `role` field. `roles` SHALL list PLANNER and TEACHER memberships; it SHALL contain VIEWER only when neither is held by a regular user. An ADMIN response SHALL include ADMIN and any held group memberships. The legacy `role` field SHALL retain its precedence of ADMIN, PLANNER, TEACHER, then VIEWER.

#### Scenario: Read a combined-role account
- **WHEN** a permitted caller retrieves an account with PLANNER and TEACHER memberships
- **THEN** the response includes both values in `roles` and `role` is PLANNER

#### Scenario: Read an admin teacher
- **WHEN** a permitted caller retrieves an ADMIN who also holds TEACHER membership
- **THEN** the response includes ADMIN and TEACHER in `roles` and `role` is ADMIN

### Requirement: Safe teacher removal and account deletion
Removing TEACHER membership from a user assigned to any lesson SHALL return HTTP 409 and preserve all memberships and lessons, including when the user retains PLANNER. The same guard SHALL apply to Django Admin group editing. Account deletion through the API and Admin SHALL remain limited to regular users with neither PLANNER nor TEACHER membership.

#### Scenario: Remove planner from an assigned teacher
- **WHEN** ADMIN removes only PLANNER from a user assigned to a lesson
- **THEN** the change succeeds and TEACHER membership and the lesson remain

#### Scenario: Remove teacher from an assigned planner
- **WHEN** ADMIN attempts to remove TEACHER from a user assigned to a lesson while retaining PLANNER
- **THEN** the request returns HTTP 409 with a reassignment or deletion explanation and leaves memberships and lessons unchanged

#### Scenario: Delete a combined-role account
- **WHEN** ADMIN attempts to delete a user who holds both PLANNER and TEACHER
- **THEN** deletion is rejected with HTTP 409
