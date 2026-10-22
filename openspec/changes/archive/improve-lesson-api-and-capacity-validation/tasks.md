# Tasks

## 1. Capacity invariant

- [x] 1.1 Add model validation for lesson assignments and changes to student-group size or room capacity, with atomic supported saves; verify oversized combinations are rejected through model and Django Admin writes while equal size and capacity are accepted.
- [x] 1.2 Add a migration preflight for existing oversized assignments and SQLite triggers for lesson inserts/updates and group/room updates, preserving existing time and conflict triggers; verify invalid direct SQL writes fail and migration/rollback leave the intended triggers present.
- [x] 1.3 Translate model and known SQLite capacity errors in lesson, group, and room API serializers to field-specific HTTP 400 responses with no partial write; verify each endpoint returns the specified `room`, `size`, or `capacity` error for a conflicting change.
- [x] 1.4 Document the capacity rule and its API errors in the scheduling documentation; verify the examples match the live request fields and error responses.

## 2. Lesson responses and ordering

- [x] 2.1 Separate lesson ID-based write serialization from expanded read serialization, including safe teacher details; verify create, update, list, and detail responses embed all five related objects while write payloads still accept IDs.
- [x] 2.2 Apply a shared Monday-to-Sunday ranking with start time and lesson ID tie breakers to the paginated lesson collection, and load related records efficiently; verify mixed-weekday pages follow calendar order with stable pagination.
- [x] 2.3 Update the API schema and lesson documentation for distinct request and response shapes, marking the response contract change; verify the generated schema shows ID inputs and nested object outputs.

## 3. Timetable and account read routes

- [x] 3.1 Add the authenticated timetable detail action returning `id`, `name`, and every expanded lesson in calendar order; verify populated, empty, missing-ID, and unauthenticated responses have the specified shapes and status codes.
- [x] 3.2 Add the authenticated current-user route using the safe account serializer and current memberships; verify self-only details, fresh roles after a membership change, HTTP 401 without authentication, and continued access to the password route.
- [x] 3.3 Document both new endpoints and their response examples; verify the generated API schema and documentation include their paths, authentication, and payload shapes.

## 4. Integration verification

- [x] 4.1 Check the combined API behavior after migration: capacity violations through each write route, nested lesson objects, weekday ordering, and both new read routes; verify existing timetable permissions and lesson ID-based writes still behave as specified.
