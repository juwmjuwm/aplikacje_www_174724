# Proposal

## Why

Lesson writes can currently assign a student group to a room that cannot hold it, and later group or room edits can create the same invalid state. Clients also need a direct current-user endpoint and a complete, chronologically ordered timetable view with useful related data rather than relationship IDs alone.

## What Changes

- Reject lesson creation and updates when the assigned student group's size exceeds the room's capacity, with a meaningful field-specific HTTP 400 response. Reject group-size increases and room-capacity decreases that would invalidate existing lessons, including through Django Admin and direct SQLite writes.
- Add authenticated `GET /api/users/me/` returning the current user's non-secret account representation.
- Add authenticated `GET /api/timetables/{id}/lessons/` returning the timetable's `id`, `name`, and all its lessons, ordered Monday through Sunday, then by start time and lesson ID.
- Order the existing lesson collection by the same calendar-day sequence.
- **BREAKING**: Return full, non-secret related objects in every lesson response instead of relationship IDs. Lesson create and update requests continue to accept IDs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `weekly-timetables`: Define the room-capacity invariant across lesson, group, and room writes and calendar ordering for lessons.
- `timetable-crud-api`: Define capacity error responses, expanded lesson representations, and the timetable lessons route.
- `user-accounts`: Define the authenticated current-user read route and its safe response.

## Impact

The change affects lesson, room, and student-group validation; SQLite constraints; serializers and scheduling/user routes; API schema and documentation; and clients consuming lesson responses. Existing lesson request payloads and scheduling permissions remain valid. The current README has unrelated working-tree edits, which this proposal does not modify.
