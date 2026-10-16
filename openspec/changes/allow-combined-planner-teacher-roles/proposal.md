# Proposal

## Why

The application currently treats PLANNER and TEACHER as mutually exclusive even though a person may need to plan timetables and teach lessons. The teacher directory also omits TEACHER group members who hold another role, making those accounts unavailable for lesson assignment.

## What Changes

- Allow a regular account to hold PLANNER and TEACHER memberships together through the ADMIN role endpoint and Django Admin.
- Add a `roles` array to account and teacher responses and accept `{"roles":["PLANNER","TEACHER"]}` at the existing role endpoint. Retain the existing single `role` field and its request behavior for current clients.
- List and retrieve every TEACHER group member through `/api/teachers/`, including members who are also PLANNER or ADMIN; accept those members as lesson teachers in API, model, and Admin validation.
- Grant scheduling writes based on PLANNER membership or ADMIN status, while retaining the guard against removing TEACHER from an account assigned to lessons and the VIEWER-only account deletion rule.
- Update documentation and tests for combined roles and the expanded teacher directory.

## Capabilities

### New Capabilities

- `user-accounts`: Account role membership, role management, representation, and safe removal and deletion.
- `timetable-access`: Scheduling permissions for accounts with multiple memberships.
- `weekly-timetables`: Lesson teacher eligibility based on TEACHER membership.
- `timetable-crud-api`: Teacher directory membership and lesson teacher ID behavior.

### Modified Capabilities

None. No capabilities have been synced to the main `openspec/specs/` directory; the completed `replace-teacher-model-with-user-role` change contains the exclusive-role requirements this change supersedes.

## Impact

The change affects account serialization and role updates, scheduling permission checks, teacher list and lesson validation, Django Admin role editing, tests, and README examples. It uses the existing Django groups and requires no schema migration or new dependency. The existing `role` response field stays for compatibility; `roles` becomes the complete membership representation.
