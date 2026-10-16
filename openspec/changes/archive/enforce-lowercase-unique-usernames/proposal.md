# Proposal

## Why

The current username constraint distinguishes uppercase and lowercase letters, so accounts can claim names that users perceive as the same identity. Usernames should have one lowercase representation and remain unique across registration, profile edits, administrator setup, and other account creation paths.

## What Changes

- **BREAKING** Accept mixed-case username input but canonicalize and store usernames in lowercase for new accounts and profile edits; return lowercase usernames in account and teacher responses.
- Reject registration and profile username changes that collide after case-insensitive normalization with an HTTP 400 `username` error, while allowing an account to submit its own username in another case.
- Enforce the canonical username's uniqueness in the database so concurrent requests and non-API account creation cannot create duplicate identities.
- Accept mixed-case usernames at token login by applying the same normalization before credential lookup; keep invalid-credential responses unchanged.
- Convert existing usernames to the canonical form during migration. Stop with an actionable conflict report if existing accounts would collapse to the same username, without changing their IDs, credentials, roles, or lesson references.
- Update API and deployment documentation for the new username behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-accounts`: Case-insensitive global uniqueness, lowercase storage and representation, conflict responses, and safe migration of existing usernames.
- `jwt-authentication`: Case-insensitive username input for token acquisition.

## Impact

The change affects the user model and manager, account serializers and views, administrator bootstrap and Django Admin account edits, token acquisition, a user-data migration, and the README. Existing clients may receive a different casing for stored usernames. Databases with usernames that collide after normalization require an explicit rename before migration can complete.
