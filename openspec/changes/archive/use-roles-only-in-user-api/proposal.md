# Proposal

## Why

User and teacher responses expose both a primary `role` and the authoritative `roles` array. The single value is redundant and can hide combined memberships. The role update endpoint also accepts a legacy `role` request, leaving clients with two ways to express the same change.

## What Changes

- **BREAKING** Remove `role` from all user and teacher API responses, including registration, account list and detail, profile update, and role update responses.
- **BREAKING** Require `roles` for `PATCH /api/users/{id}/role/` and reject legacy `role` input with HTTP 400, including requests that send both fields.
- Preserve the existing role membership rules: `roles: []` sets a regular account to VIEWER; responses represent that account as `roles: ["VIEWER"]`. ADMIN and combined memberships remain represented in the array.
- Update the API schema and README to describe the single field.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-accounts`: Make `roles` the only role field in account responses and role update requests.
- `timetable-crud-api`: Make `roles` the only role field in teacher directory responses.

## Impact

The change affects the shared user serializer and role update handling in `timetables/accounts.py`, the teacher directory that reuses that serializer, the generated OpenAPI schema, and client integrations relying on the legacy field. The endpoint URL, stored group memberships, authorization, and lesson assignment rules remain the same.
