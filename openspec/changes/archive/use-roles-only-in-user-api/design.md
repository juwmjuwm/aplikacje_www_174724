# Design

## Context

See `proposal.md` for the motivation and the two delta specs for the API contract. `UserSerializer` in `timetables/accounts.py` supplies registration, account, role update, and teacher directory responses. `RoleSerializer` accepts both request fields, and the role action contains a branch for the legacy field and its direct-switch restriction. Membership and authorization already use `user_roles()` in `timetables/permissions.py`. OpenAPI response and request schemas derive from these serializers.

## Goals / Non-Goals

**Goals:**
- Use one serialized field, `roles`, for every user representation and role update request.
- Keep the current membership ordering and VIEWER representation while making the OpenAPI contract match behavior.

**Non-Goals:**
- Rename the `/api/users/{id}/role/` action or change how groups and administrator status are stored.
- Change authorization, teacher eligibility, or the assigned-lesson guard.

## Decisions

### Remove the response field at the shared serializer

Delete the `role` method field from `UserSerializer` and its field list. All affected routes use that serializer, so this changes their shape consistently and updates the generated response schema. Keep `roles` backed by `user_roles()`. Removing the field separately in each view would duplicate a rule and risk inconsistent responses.

### Accept only the complete membership array

Make `roles` required in `RoleSerializer` and remove its `role` field. `StrictFieldsMixin` already rejects unknown keys, so legacy-only and mixed payloads return HTTP 400 before membership changes. Remove the role action's legacy conversion and direct-switch branch; use the validated `roles` array as the complete target set. The existing VIEWER, ADMIN, duplicate, and unknown-value validation and lesson guard stay in place. Keeping the old request as an undocumented alias would contradict the roles-only contract.

### Document the required PATCH body explicitly

Keep `UserSerializer` as the response schema and `RoleSerializer` as the runtime request validator. drf-spectacular automatically makes serializer fields optional when generating a PATCH request schema, even though this action requires the complete `roles` array. Give the role action an explicit OpenAPI request schema with `roles` required, restricted to PLANNER and TEACHER values, and no legacy `role` property. Preserve the endpoint's JSON, form, and multipart request formats. Verify the generated document and update the README request and response examples to match.

## Risks / Trade-offs

- [Existing API clients send or read `role`] -> Treat this as a breaking contract change; clients must switch to `roles` before deploying the new API behavior.
- [Existing test assertions still encode the old response shape] -> Revise them to match the roles-only contract, as explicitly requested, and verify the generated schema.
- [A legacy request could silently pass if unknown fields are ignored] -> Retain strict request-field validation and verify HTTP 400 with unchanged memberships.

## Migration Plan

1. Update clients to read `roles` and submit `{"roles": [...]}`; use `[]` for VIEWER.
2. Deploy the serializer and action changes with the README and generated schema updated together. No database migration is needed.
3. Verify registration, account, and teacher responses; valid single, combined, and empty membership updates; and rejection of legacy payloads.
4. If rollback is necessary, restore the previous API implementation and schema together while clients are still compatible with it.
