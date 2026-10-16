# Spec Delta

## Purpose

Provide a JSON REST interface for managing weekly timetables, lessons, and their shared reference records, with clear responses for successful and invalid requests.

## ADDED Requirements

### Requirement: CRUD resources
The system SHALL expose list, retrieve, create, full update, partial update, and delete operations under `/api/` for Timetable, Lesson, StudentGroup, Subject, Teacher, and Room records.

#### Scenario: Create and retrieve a resource
- **WHEN** a client creates a valid record for any of the six models and retrieves its returned ID
- **THEN** creation returns HTTP 201 with the record in JSON and retrieval returns HTTP 200 with that record in JSON

#### Scenario: List and update a resource
- **WHEN** a client lists a resource collection or updates a valid record with PUT or PATCH
- **THEN** the response is HTTP 200 with the corresponding JSON collection or updated record

#### Scenario: Delete a resource
- **WHEN** a client deletes an existing record that is permitted by the existing model relationships
- **THEN** the response is HTTP 204 and a subsequent retrieval returns HTTP 404

### Requirement: Relationship input and output
The system SHALL represent model relationships using record IDs in JSON and SHALL reject references to records that do not exist.

#### Scenario: Create a timetable and lesson
- **WHEN** a client supplies an existing owner ID for a timetable and existing timetable, student group, subject, teacher, and room IDs for a lesson
- **THEN** the records can be created and their JSON representations include those relationship IDs

#### Scenario: Unknown related record
- **WHEN** a client supplies a nonexistent owner or related record ID
- **THEN** the API returns HTTP 400 with a JSON error identifying the invalid relationship field

### Requirement: Lesson scheduling validation
The API SHALL enforce the existing valid-interval and shared-resource conflict rules when creating or updating lessons and SHALL return field-specific JSON errors for violations.

#### Scenario: Invalid lesson interval
- **WHEN** a client submits a lesson whose end time is not later than its start time
- **THEN** the API returns HTTP 400 with an `end_time` error explaining the interval problem and stores no invalid change

#### Scenario: Resource conflict
- **WHEN** a client submits an overlapping lesson using an already booked room, teacher, or student group
- **THEN** the API returns HTTP 400 with an error on the conflicting resource field and stores no invalid change

### Requirement: JSON error responses
The API SHALL return a meaningful JSON error body for missing records or routes, invalid input, unsupported methods, and deletion blocked by a related lesson.

#### Scenario: Missing record or API route
- **WHEN** a client requests a nonexistent resource ID or an unknown path under `/api/`
- **THEN** the response is HTTP 404 with a JSON `detail` message saying the resource or endpoint was not found

#### Scenario: Invalid field value
- **WHEN** a client submits a missing required field or invalid field value
- **THEN** the response is HTTP 400 with a JSON error associated with the affected field

#### Scenario: Unsupported method
- **WHEN** a client uses an HTTP method unsupported by an API endpoint
- **THEN** the response is HTTP 405 with a JSON `detail` message identifying the disallowed method

#### Scenario: Protected deletion
- **WHEN** a client attempts to delete a room, teacher, subject, or student group referenced by a lesson
- **THEN** the response is HTTP 409 with a JSON `detail` message explaining that related lessons prevent deletion
