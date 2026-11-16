# Proposal

## Why

Account API logic currently lives in a single all-in-one module (`timetables/accounts.py`) using class-based views (`APIView`, `CreateAPIView`, `GenericViewSet` + `SimpleRouter`), while `timetables/` also houses `SafeUserAdmin`, `SafeGroupAdmin`, `bootstrap_accounts`, and `CollectionPagination`. Moving the account API layer, admin registrations, permissions, locking helper, and management command into `accounts/`—and converting account endpoints to `@api_view` function-based views—makes `accounts/` structurally consistent with `timetables/` and creates a clean one-way dependency (`timetables` -> `accounts`).

## What Changes

- **Move and split account API into `accounts/`**:
  - Split `timetables/accounts.py` into `accounts/serializers.py`, `accounts/views.py`, `accounts/urls.py`, and `accounts/permissions.py`, and remove `timetables/accounts.py`.
  - Convert all account endpoints (`RegisterView`, `PasswordChangeView`, `UserViewSet`) to explicit `@api_view` function-based views (`register_api`, `password_change_api`, `user_list_api`, `user_me_api`, `user_detail_api`, `user_role_api`) with explicit `path()` routes in `accounts/urls.py`.
  - Preserve all existing route names (`register`, `password_change`, `user-list`, `user-me`, `user-detail`, `user-role`), HTTP methods, permission checks (`IsAdmin`, `IsSelfOrAdmin`), OpenAPI schema contracts (`RequiredRoleSchema`), and response bodies.
  - Add `.prefetch_related('groups')` on user queries to avoid N+1 group lookups when serializing roles.
- **Clean up cross-app boundaries**:
  - Move `user_roles`, `user_role`, `IsAdmin`, and `IsSelfOrAdmin` from `timetables/permissions.py` into `accounts/permissions.py` (re-importing `user_roles` in `timetables`).
  - Move `lock_teacher_assignment` from `timetables/models.py` into `accounts/models.py` and replace `Lesson.objects.filter(teacher=user).exists()` in account deletion/role checks with the reverse relation `user.lessons.exists()` so `accounts/` does not import `timetables`.
  - Move `CollectionPagination` from `timetables/pagination.py` into `timetable_planner/pagination.py` for shared use across both apps.
- **Consolidate remaining account modules into `accounts/`**:
  - Move `SafeGroupAdmin`, `SafeUserAdmin`, and their forms from `timetables/admin.py` into `accounts/admin.py`.
  - Move `bootstrap_accounts` management command from `timetables/management/commands/` into `accounts/management/commands/`.
- **Update project URL routing**:
  - Mount `accounts.urls` under `/api/` in `timetable_planner/urls.py` before `timetables.urls` (ensuring `timetables/urls.py`'s `^.*$` 404 fallback does not shadow `/api/users/*` or `/api/register/`).

## Capabilities

### New Capabilities
<!-- None: pure structural and FBV refactor with no externally observable behavior changes. -->

### Modified Capabilities
<!-- None: all existing user-accounts, jwt-authentication, and api-documentation contracts remain unchanged (`skip_specs: true`). -->

## Impact

- `accounts/`: Gains `serializers.py`, `views.py`, `urls.py`, `permissions.py`, `admin.py`, `management/commands/bootstrap_accounts.py`, and `lock_teacher_assignment` in `models.py`.
- `timetables/`: Removes `accounts.py`, `pagination.py`, and `management/commands/bootstrap_accounts.py`; updates imports in `models.py`, `permissions.py`, `serializers.py`, `views.py`, and `admin.py`.
- `timetable_planner/`: Adds `pagination.py`; updates `urls.py` to include `accounts.urls` instead of `SimpleRouter` and class-based views.
- No database migrations, schema changes, or external API contract changes.
