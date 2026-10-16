# Proposal

## Why

The current timetable API permits unauthenticated writes and accepts a caller-supplied owner ID, while the project requirements call for JWT authentication, distinct user roles, and an object-ownership permission. Timetables are shared plans, so edit rights should follow a user's planning role rather than the timetable creator.

## What Changes

- Add SimpleJWT token obtain and refresh endpoints, with authenticated access to the application API.
- Add public user registration that always creates a VIEWER, user profile access protected by an ownership-checking custom permission, and ADMIN-only promotion and demotion of regular users to PLANNER. ADMIN can delete VIEWER accounts; a PLANNER must be demoted before deletion.
- Bootstrap one ADMIN from environment-supplied credentials after database migrations, without resetting its password or privileges on subsequent starts.
- Let PLANNER and ADMIN create, update, and delete any timetable, lesson, or shared scheduling reference record; let VIEWER read them.
- **BREAKING** Remove `Timetable.owner` and its API field. Timetable creation no longer takes an owner ID; existing clients supplying or expecting that field must change.
- Add authorization coverage and update API usage documentation. OpenAPI, pagination, filtering, and unrelated business endpoints remain separate project milestones.

## Capabilities

### New Capabilities

- `jwt-authentication`: Credential exchange, refresh, and authenticated API requests.
- `user-accounts`: Registration, account profiles, administrator bootstrap, role management, and restricted account deletion.
- `timetable-access`: Role-based access to timetables, lessons, and shared reference records, including the ownerless timetable representation.

### Modified Capabilities

None. This repository has no main OpenSpec specs yet. The completed `add-weekly-timetable-models` and `add-timetable-crud-api` change artifacts describe the former owner requirement; this change supersedes that behavior when implemented, and main specs must be reconciled when changes are synced or archived.

## Impact

- Django settings, API routes, serializers, viewsets, permissions, Admin configuration, model migration, dependency list, tests, and README.
- Existing timetable rows remain, but the owner column and its data are dropped by migration.
- The API's currently open write access becomes restricted, and timetable request and response bodies lose `owner`.
