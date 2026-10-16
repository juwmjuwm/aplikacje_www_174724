# Spec Delta

## Purpose

Define which signed-in account roles may read or change shared timetable and scheduling resources.

## ADDED Requirements

### Requirement: Teacher scheduling access
An authenticated TEACHER SHALL have the same scheduling access as VIEWER: read access to scheduling resources and no permission to create, update, or delete them. PLANNER and ADMIN SHALL retain their existing write access.

#### Scenario: Teacher reads scheduling data
- **WHEN** a TEACHER requests a scheduling collection or record
- **THEN** the request is authorized for reading

#### Scenario: Teacher attempts to edit scheduling data
- **WHEN** a TEACHER attempts to create, update, or delete a timetable, lesson, student group, subject, or room
- **THEN** the request returns HTTP 403 and no scheduling data changes
