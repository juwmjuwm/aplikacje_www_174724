# Tasks

## 1. Account deletion endpoint

- [x] 1.1 Apply `IsSelfOrAdmin` object permission to `destroy` while keeping list and role actions ADMIN-only; verify an authenticated non-ADMIN receives HTTP 403 for another user's account and can reach their own deletion flow.
- [x] 1.2 Update `destroy` to re-read and lock the target inside a transaction, reject any ADMIN target with HTTP 409, reject assigned TEACHER targets with HTTP 409, and delete other eligible accounts; verify VIEWER, PLANNER, unassigned TEACHER, and unassigned combined-role deletions return HTTP 204 for self and ADMIN callers.
- [x] 1.3 Preserve protected Lesson references and translate any protected-deletion failure into HTTP 409; verify self and ADMIN attempts against assigned TEACHER and assigned combined-role accounts leave the user, memberships, and Lessons intact.
- [x] 1.4 Update README account deletion guidance to match the API rules while distinguishing Django Admin's existing policy; verify the documented path, roles, callers, and response codes against observable requests.
- [x] 1.5 Run Django system and migration checks and exercise the deletion permission matrix with API requests, including unauthenticated access, non-ADMIN deletion of another user, ADMIN self deletion, ADMIN target deletion, successful deletion, and denial of access with a deleted user's credentials; verify no checks fail and each response matches the spec delta.
