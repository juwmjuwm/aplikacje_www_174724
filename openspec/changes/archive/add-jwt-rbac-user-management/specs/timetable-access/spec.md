# Spec Delta

## Purpose

Make weekly timetables and their shared scheduling data readable by all signed-in users and editable by authorized planners without per-timetable ownership.

## ADDED Requirements

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
