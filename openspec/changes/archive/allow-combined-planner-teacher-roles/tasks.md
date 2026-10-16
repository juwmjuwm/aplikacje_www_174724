# Tasks

## 1. Account membership and API

- [x] 1.1 Add a shared current-membership helper and expose deterministic `roles` alongside the existing `role` in account and teacher serialization; verify tests for VIEWER, single-role, combined-role, and ADMIN-with-TEACHER responses.
- [x] 1.2 Extend the ADMIN role endpoint to accept an exact `roles` set while preserving legacy `role` requests, validation, and direct-switch behavior; verify API tests for both-role assignment, one-role removal, idempotence, malformed or mixed payloads, non-ADMIN callers, and ADMIN targets.
- [x] 1.3 Check actual TEACHER membership before role removal under the existing transaction and writer lock, preserving all memberships on conflict; verify API tests for assigned combined-role users, including successful PLANNER-only removal and HTTP 409 on TEACHER removal.
- [x] 1.4 Update README account and role examples for `roles` input and output, legacy `role`, and VIEWER as an empty input array; verify examples match the API tests.

## 2. Teacher eligibility and directory

- [x] 2.1 Query the teacher list and detail routes by TEACHER membership alone and retain unique, ordered results; verify API tests include PLANNER+TEACHER and ADMIN+TEACHER once each and return 404 for users without TEACHER.
- [x] 2.2 Align lesson serializer, model validation, and Django Admin teacher choices with TEACHER membership; verify API, model, and Admin tests accept combined-role and ADMIN teachers while rejecting users without TEACHER.
- [x] 2.3 Update README teacher directory and lesson examples to show combined roles and the `roles` response field; verify documented payloads against the teacher and lesson API tests.

## 3. Permissions and Admin safety

- [x] 3.1 Authorize scheduling writes from PLANNER membership or ADMIN status while preserving authenticated read access; verify tests using an existing token for combined-role, teacher-only, planner-only, and membership-removal requests.
- [x] 3.2 Allow combined groups in Django Admin user editing while retaining assigned-teacher removal protection and VIEWER-only deletion in both API and Admin; verify Admin form and request tests for accepted combinations, blocked removal, and blocked deletion.
- [x] 3.3 Update README scheduling access and account deletion guidance for combined roles; verify its examples against permission and deletion tests.

## 4. Integration checks

- [x] 4.1 Run the relevant Django test suite, system checks, and migration drift check; verify all pass and no database migration is generated.
- [x] 4.2 Run strict OpenSpec validation for this change; verify all proposal, design, spec, and task artifacts validate.
