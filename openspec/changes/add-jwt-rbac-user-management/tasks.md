# Tasks

## 1. JWT and environment setup

- [x] 1.1 Add compatible SimpleJWT and environment-loading dependencies, replace the committed runtime signing key with `DJANGO_SECRET_KEY`, and add a placeholder `.env.example`; verify the application loads with configured values and no real secret appears in tracked files.
- [x] 1.2 Configure JWT authentication and register `/api/token/` and `/api/token/refresh/` ahead of the catch-all route; verify valid login and refresh work and invalid credentials or refresh tokens are denied in `APITestCase` tests.
- [x] 1.3 Require bearer authentication for protected scheduling and user routes while keeping only registration and token routes public; verify missing, invalid, and deactivated-user access tokens return HTTP 401 in `APITestCase` tests.
- [x] 1.4 Document the environment variables and token request flow in README; verify documented paths and request fields match the configured routes.

## 2. Accounts and roles

- [x] 2.1 Implement an idempotent post-migration bootstrap command for the `PLANNER` group and initial ADMIN from environment credentials; verify first run creates a hashed-password superuser, repeated runs preserve it, and missing credentials or a same-name regular user fail clearly.
- [x] 2.2 Add public `/api/register/` with password validation and a VIEWER-only result; verify success, duplicate or weak credentials, and rejection of privilege fields with `APITestCase` tests.
- [x] 2.3 Add `GET` and `PATCH /api/users/{id}/` with a custom `BasePermission` ownership check, non-secret output, and username/email-only input; verify self access, ADMIN access, other-user HTTP 403, and privileged-field rejection with `APITestCase` tests.
- [x] 2.4 Add ADMIN-only `GET /api/users/` and `PATCH /api/users/{id}/role/` for VIEWER/PLANNER changes; verify promotion, demotion, immediate effect on an existing token, non-admin HTTP 403, and rejection of ADMIN targets with `APITestCase` tests.
- [x] 2.5 Add ADMIN-only `DELETE /api/users/{id}/` with a current-role check in the deletion transaction; verify VIEWER deletion returns HTTP 204, PLANNER and ADMIN deletion return HTTP 409, non-admin deletion returns HTTP 403, and demotion makes a former PLANNER deletable in `APITestCase` tests.
- [x] 2.6 Document registration, profile, role administration, VIEWER-only deletion, and bootstrap behavior in README; verify the examples use the actual JSON field names and endpoint paths.

## 3. Shared timetable access and owner removal

- [x] 3.1 Remove `Timetable.owner` from the model and Admin configuration, create its schema migration, and verify a migrated database retains existing timetable and lesson rows while dropping the owner column.
- [x] 3.2 Remove owner from timetable responses and reject owner on POST, PUT, and PATCH; verify ownerless create succeeds and supplied owner returns HTTP 400 without a write in `APITestCase` tests.
- [x] 3.3 Apply a custom `BasePermission` to all six scheduling viewsets so authenticated VIEWER can read and only PLANNER/ADMIN can write; verify role and method combinations, including cross-creator timetable deletion and existing lesson/protected-delete rules, with `APITestCase` tests.
- [x] 3.4 Update README timetable examples and migration notes to omit owner and explain the breaking change; verify every documented timetable request matches the new serializer.

## 4. Integration verification

- [x] 4.1 Run Django system checks, migration consistency checks, and the full API test suite; verify there are no failures and at least three `APITestCase` cases assert HTTP status and permission behavior.
- [x] 4.2 Exercise registration, token issue and refresh, ADMIN promotion, PLANNER timetable edit and delete, VIEWER read and denied write, and ADMIN deletion of both a newly registered VIEWER and a PLANNER after demotion; verify role changes take effect without reissuing access tokens and deleted accounts lose access.
