# Proposal

## Why

Accounts currently expose and store email even though identity in this application is based on username and password. Users also cannot change their own password through the API.

## What Changes

- **BREAKING** Remove email from the active User model and database column, registration and profile input, account and teacher responses, Django Admin, configuration, and documentation. Requests that supply email will be rejected.
- Add an authenticated, self-service password change endpoint that requires the current password and validates the new password. It will not expose a password in responses or allow an administrator to change another user's password through this endpoint.
- Preserve existing account IDs, password hashes, privileges, group memberships, and lesson references while switching to an email-free custom User model. Discard stored email values.
- Remove the existing test suite and create no new tests, as requested. Use Django system, migration, and focused manual API checks for implementation verification.

## Capabilities

### New Capabilities

- `user-accounts`: Username-only account identity, account representation, profile editing, and self-service password changes.
- `timetable-crud-api`: Email-free teacher directory responses for TEACHER members.

### Modified Capabilities

None. The project has no synced main specs. Earlier completed change specs that mention email are superseded by this change.

## Impact

The change affects Django's configured user model and migration history, account and teacher API serializers and routes, bootstrap compatibility, Django Admin fields and search, README examples, and the sole existing test file. Existing clients consuming or submitting `email` must update. No new dependency is expected.
