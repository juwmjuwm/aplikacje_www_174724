# Tasks

## 1. DRF setup

- [x] 1.1 Add a compatible stable Django REST Framework dependency and `rest_framework` app configuration; verify dependency installation and `manage.py check` succeed.

## 2. Resource serialization

- [x] 2.1 Add serializers for Timetable, StudentGroup, Subject, Teacher, Room, and Lesson with read-only IDs and writable relationship IDs; verify each serializes an existing record and rejects a nonexistent related ID with a field error.
- [x] 2.2 Convert Django model validation raised during lesson create, PUT, or PATCH into DRF HTTP 400 field errors, and map only known SQLite scheduling trigger errors to HTTP 400; verify invalid intervals and resource conflicts leave records unchanged and return meaningful JSON.

## 3. CRUD routes and errors

- [x] 3.1 Add six JSON-rendering ModelViewSets and register their collection and detail routes under `/api/`; manually verify POST, GET list/detail, PUT, PATCH, and DELETE for each model return the specified success statuses and bodies.
- [x] 3.2 Add JSON handling for missing records, unknown `/api/` routes, unsupported methods, and protected deletions; manually verify representative 404, 405, and 409 responses include meaningful `detail` messages.
- [x] 3.3 Document the six route paths, owner and foreign-key ID request fields, error response shapes, and timetable deletion cascade in the project README; verify the documented request paths match the router.

## 4. Integration verification

- [x] 4.1 Run `manage.py check` and `manage.py makemigrations --check --dry-run`, then manually exercise a timetable with related lessons through the API and confirm the existing scheduling rules still hold without a new database migration.
