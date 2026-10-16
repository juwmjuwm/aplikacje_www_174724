# Proposal

## Why

The existing collection endpoints return every record in one array and do not support API search, leaving the project's pagination and search requirement unmet. Teacher names already exist in the user model but cannot be supplied during registration or read and corrected through the API.

## What Changes

- **BREAKING** Paginate the timetable, lesson, student group, subject, teacher, room, and admin-only user collections. Return pagination metadata and a `results` array instead of a bare array, with 10 records by default and a `size` parameter capped at 100.
- Add `search` on the existing timetable, student group, subject, teacher, and room collections. Search names for the named scheduling resources, subject name and description, and teacher first and last names. Allow search and pagination together.
- **BREAKING** Require nonblank `first_name` and `last_name` in new account registration. Include these fields in account and teacher representations and allow account holders or admins to edit them through the existing profile PATCH endpoint.
- Update API documentation and examples for the new request and response contracts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `timetable-crud-api`: Paginated scheduling collections and searchable timetable, student group, subject, teacher, and room lists.
- `user-accounts`: Required registration names, readable and editable account names, and paginated administrator user listing.

## Impact

The change affects DRF pagination and filtering configuration, scheduling and account viewsets, account serializers, API response shapes, and the README. Existing account rows can retain blank names; no database schema change is needed because the user model already has both fields. Existing list clients must read `results`, and new registration clients must supply both names. Access control and write permissions remain as currently specified.
