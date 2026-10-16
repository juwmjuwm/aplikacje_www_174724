# Design

## Context

The timetable app has six Django models and Admin registrations. `Lesson.save()` calls `full_clean()`; `Lesson.clean()` reports invalid intervals and overlapping room, teacher, and student group assignments. The initial SQLite migration also installs conflict triggers. The project currently has a welcome view only and does not include DRF. See `proposal.md` for motivation and `specs/timetable-crud-api/spec.md` for observable behavior.

## Goals / Non-Goals

**Goals:**

- Keep API representation simple and consistent across all six models.
- Convert existing Django model validation and protected-deletion failures into stable client-facing JSON responses.
- Add the API without changing the database schema or scheduling rules.

**Non-Goals:**

- Authentication or authorization rules, including automatic assignment of the timetable owner.
- Automated tests in this change, as requested by the user.
- Pagination, search, filtering, OpenAPI, and custom business endpoints.

## Decisions

### Six ModelViewSets and flat resource routes

Add DRF and `rest_framework` to installed apps. Use one `ModelSerializer` and `ModelViewSet` for each model, registered on a router at `/api/timetables/`, `/api/lessons/`, `/api/student-groups/`, `/api/subjects/`, `/api/teachers/`, and `/api/rooms/`. Standard detail URLs append an integer ID and trailing slash. Expose `id` as read-only and foreign keys as writable integer IDs, including the required `owner` ID. Use JSON rendering for these routes. A flat router keeps each model's full CRUD operations available; nesting lessons under timetables would complicate independent lesson lookup and updates.

### Preserve model validation at the API boundary

Use serializer field validation for missing, malformed, out-of-range, and nonexistent related IDs. On create and update, retain the model's `save()` validation and convert Django `ValidationError.message_dict` into DRF field errors with HTTP 400. This handles PATCH because the model instance retains omitted fields. Map a known SQLite trigger rejection during a concurrent or bypassing write to a non-field HTTP 400 response; do not turn unrelated database errors into client errors. Keep the existing model and database rules as the source of truth instead of duplicating the overlap algorithm in serializers.

### Explicit JSON errors

Use field-keyed JSON errors for invalid input and lesson validation. DRF detail lookups return HTTP 404 with a descriptive `detail`; disallowed methods return HTTP 405 with the method named in `detail`. Add a final `/api/` catch-all after registered routes so unknown API paths also return a JSON 404 body, including while Django DEBUG is enabled. Catch `ProtectedError` on deletion of referenced Room, Teacher, Subject, or StudentGroup records and return HTTP 409 with a clear `detail`. Successful delete remains HTTP 204. Keep other site routes, including Admin and the welcome view, outside this API error behavior.

### Owner field during this phase

The client supplies an existing user ID for `Timetable.owner` on create or update. This preserves the required model relation without introducing authentication or a role policy in this change. The endpoint is therefore suitable only for the current development stage; a later authorization change must restrict who can set or change ownership and who can mutate records.

## Risks / Trade-offs

- [Unauthenticated CRUD permits anyone reaching the development API to change records] -> Keep this API on a trusted development environment until the later auth and permissions change.
- [Model validation and SQLite triggers can surface different exception types] -> Translate known validation and trigger errors at the API boundary while allowing unexpected database errors to surface for diagnosis.
- [Deleting a timetable cascades to its lessons] -> Preserve the model's current `on_delete` behavior and document it in the API usage notes.
- [No automated tests in this phase] -> Manually exercise one successful CRUD path per resource and representative 400, 404, 405, and 409 responses during implementation; add `APITestCase` coverage in a later change.

## Migration Plan

1. Install a Django 6.1 and Python 3.13 compatible stable DRF release and update project dependencies and settings.
2. Add serializers, viewsets, and routes without a database migration.
3. Run Django checks and manual API requests for success and error cases. Roll back by removing the API routes and DRF integration; existing data and tables remain intact.
