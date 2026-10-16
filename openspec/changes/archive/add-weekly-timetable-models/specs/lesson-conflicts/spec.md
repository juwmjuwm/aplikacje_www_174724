# Spec Delta

## Purpose

Prevent invalid weekly lesson times and double booking of shared rooms, teachers, and student groups when lessons are created or edited through the application or directly in SQLite.

## ADDED Requirements

### Requirement: Valid lesson interval
The system SHALL reject a lesson whose end time is not later than its start time; overnight lessons are not supported.

#### Scenario: Zero-length lesson
- **WHEN** a lesson is submitted with equal start and end times
- **THEN** the system rejects it with a validation error

#### Scenario: Overnight interval
- **WHEN** a lesson is submitted with an end time earlier than its start time
- **THEN** the system rejects it with a validation error

### Requirement: Weekly interval overlap
The system SHALL treat two lessons as overlapping only when they have the same weekday and the existing start is before the new end AND the existing end is after the new start.

#### Scenario: Back-to-back lessons
- **WHEN** a new lesson starts exactly when an existing lesson ends on the same weekday
- **THEN** the system does not treat the two intervals as overlapping

#### Scenario: Different weekdays
- **WHEN** two lessons have the same times on different weekdays
- **THEN** the system does not treat the two intervals as overlapping

### Requirement: Resource conflict rejection
The system SHALL reject an overlapping lesson if it uses the same room, teacher, or student group as an existing lesson, including one in a different timetable.

#### Scenario: Room double booking
- **WHEN** a lesson is submitted for a room already used by an overlapping lesson on that weekday
- **THEN** the system rejects it with a room conflict validation error

#### Scenario: Teacher or student group double booking
- **WHEN** a lesson is submitted with a teacher or student group assigned to an overlapping lesson on that weekday
- **THEN** the system rejects it with the corresponding conflict validation error

#### Scenario: Independent parallel lessons
- **WHEN** two lessons overlap in time but use different rooms, teachers, and student groups
- **THEN** both lessons can be stored

### Requirement: Conflict checks on edits
The system SHALL check an edited lesson against other lessons while excluding that lesson's current record from the comparison.

#### Scenario: Edit without new conflict
- **WHEN** a lesson is edited without creating a conflict with another lesson
- **THEN** the edit succeeds

#### Scenario: Edit into a conflict
- **WHEN** a lesson is edited to overlap another lesson using the same room
- **THEN** the edit is rejected with a room conflict validation error

### Requirement: Database enforcement of scheduling rules
The SQLite database SHALL reject lesson inserts and updates with an invalid interval or an overlap on the same weekday involving the same room, teacher, or student group, including across timetables. Database checks SHALL use half-open intervals and exclude the updated lesson itself. Django model validation SHALL continue to provide readable errors before normal application writes.

#### Scenario: Raw insert violates a scheduling rule
- **WHEN** a lesson is inserted directly through SQL with an invalid interval or a room, teacher, or student group conflict
- **THEN** SQLite rejects the insert and no invalid lesson is stored

#### Scenario: Raw update violates a scheduling rule
- **WHEN** a lesson is updated directly through SQL to have an invalid interval or a room, teacher, or student group conflict
- **THEN** SQLite rejects the update and preserves the previous lesson values

#### Scenario: Raw write is valid
- **WHEN** a lesson is inserted or updated directly through SQL with a valid interval and no shared-resource overlap, including a back-to-back or independent parallel lesson
- **THEN** SQLite accepts the write
