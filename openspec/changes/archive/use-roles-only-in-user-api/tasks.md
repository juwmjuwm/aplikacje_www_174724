# Tasks

## 1. Roles-only API contract

- [x] 1.1 Remove `role` from the shared `UserSerializer` in `timetables/accounts.py`; verify registration, account list/detail, profile PATCH, role PATCH, and teacher list/detail responses contain `roles` and no `role`, including VIEWER, combined-role, and ADMIN/TEACHER accounts.
- [x] 1.2 Require the `roles` array in `RoleSerializer`, remove legacy conversion and direct-switch handling from the role action, and verify `{"roles":[]}`, one role, and both roles work while legacy-only, mixed, missing, duplicate, and invalid values return HTTP 400 without changing memberships; verify the assigned-lesson guard still returns HTTP 409.
- [x] 1.3 Update role examples and compatibility text in `README.md`; verify they describe `roles` as the only request and response role field, with `[]` for a VIEWER update and `["VIEWER"]` in the response.
- [x] 1.4 Inspect the generated `/api/schema/` document and representative API responses; verify the user and teacher schemas omit `role`, role PATCH requires `roles`, and legacy payloads are rejected. Update existing test assertions for the removed field and run the affected suite.
