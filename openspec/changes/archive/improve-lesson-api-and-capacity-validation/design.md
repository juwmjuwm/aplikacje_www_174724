# Design

## Context

See [proposal.md](./proposal.md) for the motivation and the three [spec deltas](./specs/). `Lesson.save()` already runs `full_clean()` and converts model errors to API errors through `LessonSerializer`; `StudentGroup` and `Room` currently rely on serializer validation and do not check their assigned lessons. SQLite triggers currently protect lesson time and double-booking rules, but not room capacity. The lesson model's string-based weekday ordering places codes alphabetically. Existing user serialization exposes only `id`, `username`, names, and roles.

## Goals / Non-Goals

**Goals:**

- Keep the room-capacity invariant at normal application entry points and at the SQLite boundary.
- Preserve ID-based lesson write payloads while making the expanded response shape explicit in API documentation.
- Share one weekday ranking for both lesson read routes.

**Non-Goals:**

- Change authorization, lesson request field names, existing collection pagination, or the timetable's ordinary detail representation.
- Introduce nested write payloads or paginate the timetable-specific lessons array.

## Decisions

### Capacity checks at model and database layers

Add capacity validation to `Lesson.clean()`, checking the selected room and group when both IDs exist. Add group and room model validation that checks all referenced lessons before accepting a size increase or capacity decrease. Ensure supported model saves invoke this validation and remain atomic. Add a new migration that recreates the lesson insert and update triggers with a capacity check and adds group-update and room-update triggers. Distinct, stable trigger messages let API serializers map database races to the same field-specific HTTP 400 shape as model errors. The database checks are necessary because direct SQL and concurrent writes bypass model validation; model checks provide readable Admin and API errors.

The migration must inspect existing assignments before enabling the invariant and stop with affected IDs if any are already invalid, rather than silently retaining invalid rows. Removing the new triggers is the rollback path; existing time and conflict triggers must be restored on rollback. An alternative of serializer-only validation would leave Admin, model, and direct SQL writes unprotected.

### Separate lesson write and read shapes

Keep a write serializer with primary-key related fields and teacher eligibility validation. Use a read serializer that nests the existing timetable, student-group, subject, room, and safe user serializers. Make create and update actions serialize their saved instance with the read serializer, as list and retrieve do. Document the different request and response components in the generated API schema. Load the five foreign keys with `select_related` and prefetch teacher groups when serializing collections to avoid one query per nested object. A single serializer with fields that change shape between input and output would make the API schema ambiguous.

### Timetable lessons action and calendar ordering

Add a read-only detail action on the timetable viewset so the existing router owns `/api/timetables/{id}/lessons/` and its permission behavior. Fetch the timetable through normal object lookup, then return `id`, `name`, and a complete `lessons` array. Build one explicit weekday rank from `MON` through `SUN` and use it in the timetable action and the paginated `/api/lessons/` queryset, ordering by rank, start time, and primary key. Sorting by weekday strings is incorrect because their codes are not lexically chronological. Keep the unpaginated action separate from ordinary collection pagination.

### Current-user route

Add `GET /api/users/me/` as an authenticated read action or explicit route ahead of numeric user-detail matching. Serialize `request.user` with the existing `UserSerializer` so current roles are read from membership rather than token claims and secrets remain excluded. Keep `/api/users/me/password/` and existing user detail permissions intact.

## Risks / Trade-offs

- [Existing oversized assignments may block migration] -> Run an explicit preflight with IDs and repair such data before applying the trigger migration.
- [Concurrent updates can pass application checks] -> Retain SQLite triggers as the final guard and translate their known errors to API validation responses.
- [Nested objects increase response size and query cost] -> Use relation loading and keep collection pagination; the timetable-specific route intentionally returns every lesson.
- [Clients expect integer lesson relationships] -> Mark the response change as breaking, update documentation and schema, and keep request payloads unchanged.

## Migration Plan

1. Inspect and correct any pre-existing lessons whose group size exceeds room capacity.
2. Apply the migration that guards lesson, group, and room writes while preserving the existing time and overlap checks.
3. Deploy API serializers and routes with the schema and documentation update. If rolled back, remove the new capacity triggers and restore the previous lesson triggers before reverting application code.
