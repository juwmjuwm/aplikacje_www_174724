# Spec Delta

## Purpose

Persist weekly lessons and their shared resources while assigning each lesson to an eligible teacher account.

## ADDED Requirements

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
