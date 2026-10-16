# Proposal

## Why

The six timetable models can currently be managed through Django Admin, but the project exposes no REST API for creating or managing their records. A basic DRF CRUD API is the next step toward the required project interface and lets clients manage complete weekly schedules.

## What Changes

- Add list, retrieve, create, update, partial update, and delete endpoints for Timetable, Lesson, StudentGroup, Subject, Teacher, and Room.
- Represent relationships with record IDs and return serialized records in JSON.
- Return meaningful JSON error bodies for missing records, invalid input, scheduling conflicts, and unsupported methods.
- Preserve the existing lesson time and shared-resource conflict rules for API writes.

## Capabilities

### New Capabilities

- `timetable-crud-api`: REST management of timetable records and related reference data, including predictable success and error responses.

### Modified Capabilities

None. The existing weekly timetable and conflict rules remain as defined in the completed model change.

## Impact

This change adds Django REST Framework as a dependency and affects the timetable app's serializers, views, and URL routing, plus the project API route. Timetable creation supplies an existing user ID for the required owner field. JWT, roles, ownership permissions, registration, dedicated non-CRUD endpoints, OpenAPI, pagination, filtering, and automated tests are deferred to later changes.
