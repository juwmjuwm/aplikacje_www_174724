# weekly-timetables Specification

## Purpose

Provide persistent, administrable timetables and related reference data so a user can describe a repeating weekly schedule of lessons.

## Requirements

### Requirement: Timetable data model
The system SHALL persist Timetable, StudentGroup, Subject, Teacher, Room, and Lesson records and their relationships. Each timetable SHALL have an owner, and each lesson SHALL reference a timetable, student group, subject, teacher, and room.

#### Scenario: Store a related timetable
- **WHEN** an authorized administrator creates a timetable and its related lessons and reference records
- **THEN** the records remain available after application restart with their relationships intact

### Requirement: Weekly lessons
The system SHALL represent each lesson with a weekday, start time, and end time that repeat every week, without requiring a calendar date.

#### Scenario: Weekly recurrence
- **WHEN** a lesson is stored for Monday from 09:00 to 10:00
- **THEN** it represents that interval on every Monday

### Requirement: Model metadata and field rules
The system SHALL give each domain model a readable display name and a stable default ordering, and SHALL validate required fields and bounded values for its domain data.

#### Scenario: Invalid reference data
- **WHEN** an administrator attempts to save a room with nonpositive capacity
- **THEN** the system rejects the record with a field validation error

### Requirement: Admin management
The system SHALL make all six timetable models manageable in Django Admin with useful list columns, search, and filters for relevant fields.

#### Scenario: Manage a lesson in Admin
- **WHEN** an authorized administrator opens the lesson list
- **THEN** the lesson's timetable, weekday, time interval, room, teacher, and student group are visible or filterable

### Requirement: Lesson teacher account
Each lesson SHALL reference a user account whose current role is TEACHER. A user with any other role SHALL NOT be assigned as a lesson teacher. The separate Teacher record SHALL no longer exist.

#### Scenario: Assign an eligible teacher
- **WHEN** an authorized editor creates or updates a lesson with a TEACHER user's ID
- **THEN** the lesson stores that user as its teacher

#### Scenario: Reject an ineligible teacher
- **WHEN** an authorized editor creates or updates a lesson with a VIEWER, PLANNER, or ADMIN user's ID
- **THEN** the lesson is rejected with a `teacher` validation error and no invalid assignment is saved

### Requirement: Preserve teacher conflict rules
The system SHALL continue to reject overlapping lessons that assign the same teacher user on the same weekday, including lessons in different timetables. Existing room, student group, and time interval rules SHALL continue to apply.

#### Scenario: Teacher user is double booked
- **WHEN** a proposed lesson overlaps another lesson assigned to the same teacher user on the same weekday
- **THEN** the system rejects it as a teacher conflict

### Requirement: Teacher data migration
The migration SHALL remove the separate Teacher records and their existing Lesson records. It SHALL retain users, timetables, student groups, subjects, and rooms.

#### Scenario: Upgrade a populated database
- **WHEN** a database containing Teacher and Lesson rows is migrated
- **THEN** those rows are removed, the new lesson teacher relationship targets users, and unrelated records remain

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
