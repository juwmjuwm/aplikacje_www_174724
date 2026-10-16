# timetable-access Specification

## Purpose

Make weekly timetables and their shared scheduling data readable by all signed-in users and editable by authorized planners without per-timetable ownership.

## Requirements

### Requirement: Role-based scheduling access
The system SHALL allow authenticated VIEWER, PLANNER, and ADMIN users to read timetables, lessons, student groups, subjects, teachers, and rooms. It SHALL allow only PLANNER and ADMIN users to create, update, and delete those records. VIEWER writes SHALL return HTTP 403 without changing data. PLANNER and ADMIN writes SHALL follow existing validation and protected-deletion rules without creator ownership restrictions.

#### Scenario: Planner updates shared data
- **WHEN** a PLANNER updates a timetable or scheduling reference record
- **THEN** the operation follows the existing validation rules

### Requirement: Timetable without owner
The system SHALL store and represent timetables without an owner relationship. A timetable create or update request SHALL NOT require or permit an `owner` field, and timetable responses SHALL omit it. Supplied `owner` SHALL return HTTP 400 without a write. Removing the owner column SHALL preserve existing timetable and lesson rows.

#### Scenario: Ownerless timetable creation
- **WHEN** a PLANNER or ADMIN submits a valid timetable name
- **THEN** the API creates a timetable without an owner field

### Requirement: Teacher scheduling access
An authenticated TEACHER SHALL have the same scheduling access as VIEWER: read access to scheduling resources and no permission to create, update, or delete them. PLANNER and ADMIN SHALL retain their existing write access.

#### Scenario: Teacher reads scheduling data
- **WHEN** a TEACHER requests a scheduling collection or record
- **THEN** the request is authorized for reading

#### Scenario: Teacher attempts to edit scheduling data
- **WHEN** a TEACHER attempts to create, update, or delete a timetable, lesson, student group, subject, or room
- **THEN** the request returns HTTP 403 and no scheduling data changes

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
