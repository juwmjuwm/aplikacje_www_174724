# Spec Delta

## Purpose

Provide persistent, administrable timetables and related reference data so a user can describe a repeating weekly schedule of lessons.

## ADDED Requirements

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
