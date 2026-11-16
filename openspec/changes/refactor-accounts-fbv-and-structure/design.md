# Design

## Context

See `proposal.md` for motivation. Scheduling endpoints were previously refactored into `@api_view` function-based views separated by layer (`models.py`, `serializers.py`, `views.py`, `urls.py`), while account endpoints remained in `timetables/accounts.py` using `APIView`, `CreateAPIView`, `GenericViewSet`, and `SimpleRouter`, alongside account admin/bootstrap code in `timetables/`. This design details how to move account modules into `accounts/`, convert account views to `@api_view`, and keep dependencies strictly one-way (`timetables` -> `accounts`) without altering external API, OpenAPI, admin, or CLI contracts.

## Goals / Non-Goals

**Goals:**
- Mirror `timetables/`'s layered file organization inside `accounts/` (`models.py`, `permissions.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `management/commands/`).
- Replace `RegisterView`, `PasswordChangeView`, and `UserViewSet` (+ `SimpleRouter`) with explicit `@api_view` FBVs and `path()` routes while preserving exact URL paths, route names, HTTP methods, status codes, permissions, and OpenAPI schema output.
- Eliminate reverse imports from `accounts/` into `timetables/` so the dependency graph is strictly acyclic (`timetables` -> `accounts`).
- Eliminate N+1 queries on user collection responses via `.prefetch_related('groups')`.

**Non-Goals:**
- Changing SimpleJWT's built-in `TokenObtainPairView` / `TokenRefreshView` endpoints.
- Altering any URL paths, request/response payloads, validation rules, error formats, or database schema/migrations.
- Adding or modifying automated test suites.

## Decisions

### 1. One-Way App Dependency Boundary (`timetables` -> `accounts`)
- **Move `user_roles`, `user_role`, `IsAdmin`, `IsSelfOrAdmin` to `accounts/permissions.py`**: These helpers depend only on `rest_framework.permissions`, `user.is_superuser`, and `user.groups`. `timetables/permissions.py` will import `user_roles` from `accounts.permissions` and retain only `SchedulingPermission`. `timetables/models.py` (`Lesson.clean`) can import `user_roles` from `accounts.permissions` directly.
- **Move `lock_teacher_assignment` to `accounts/models.py`**: This helper only executes a SQLite writer-lock `UPDATE` against `auth_user` (`get_user_model()._meta.db_table`) and has no dependency on `timetables` models. `timetables/models.py` will import it from `accounts.models`.
- **Use reverse relation `user.lessons.exists()`**: In `accounts/views.py` (`user_role_api`, `user_detail_api` delete) and `accounts/admin.py` (`SafeUserChangeForm.clean_groups`), checking `user.lessons.exists()` avoids importing `Lesson` from `timetables.models`.
- **Move `CollectionPagination` to `timetable_planner/pagination.py`**: Because both `accounts/views.py` and `timetables/views.py` paginate with `CollectionPagination` (which depends only on DRF), placing it at the project package level alongside `timetable_planner/schema.py` avoids cross-app coupling.
- *Alternative considered*: Keeping account views inside `timetables/` split across `serializers.py`/`views.py` or importing `timetables.pagination`/`timetables.models` from `accounts/`. Rejected because `accounts/` already owns `User`, auth backends, and `accounts/tests.py`, and bidirectional imports create circular-import risk.

### 2. Function-Based Account Views (`@api_view`)
Map existing CBVs/ViewSet actions 1-to-1 to explicit `@api_view` functions in `accounts/views.py`:
- `register_api` (`@api_view(['POST'])`, `@permission_classes([AllowAny])`) -> `/api/register/` (`name='register'`)
- `password_change_api` (`@api_view(['POST'])`, `@permission_classes([IsAuthenticated])`) -> `/api/users/me/password/` (`name='password_change'`)
- `user_list_api` (`@api_view(['GET'])`, `@permission_classes([IsAuthenticated, IsAdmin])`) -> `/api/users/` (`name='user-list'`)
- `user_me_api` (`@api_view(['GET'])`, `@permission_classes([IsAuthenticated])`) -> `/api/users/me/` (`name='user-me'`)
- `user_detail_api` (`@api_view(['GET', 'PATCH', 'DELETE'])`, `@permission_classes([IsAuthenticated])`) -> `/api/users/<int:pk>/` (`name='user-detail'`)
- `user_role_api` (`@api_view(['PATCH'])`, `@permission_classes([IsAuthenticated, IsAdmin])`) -> `/api/users/<int:pk>/role/` (`name='user-role'`)

All account FBVs will include `@renderer_classes([JSONRenderer])` to match `timetables/views.py`. User querysets in `user_list_api`, `user_me_api`, and `user_detail_api` will apply `.prefetch_related('groups')` so `UserSerializer` computes `roles` without per-row queries.

### 3. Preserving Object-Level Permissions in `user_detail_api`
DRF `GenericViewSet.get_object()` automatically invokes `check_object_permissions()`, whereas `@api_view` functions do not. In `user_detail_api`, after fetching `user = get_object_or_404(User.objects.prefetch_related('groups'), pk=pk)`, the view will explicitly verify `IsSelfOrAdmin().has_object_permission(request, None, user)` and raise `PermissionDenied()` when false.
- *Rationale*: Preserves exact `404` (missing ID) vs. `403` (unauthorized target account) precedence matching `GenericViewSet`.

### 4. Preserving OpenAPI Schema for `PATCH /api/users/{id}/role/`
`accounts/tests.py` asserts that `/api/users/{id}/role/` marks `requestBody.required == True` with `properties == {"roles"}` and `required == ["roles"]`. On `user_role_api`, combine `@extend_schema(...)` with DRF's `@schema(RequiredRoleSchema())` (where `RequiredRoleSchema` subclasses `drf_spectacular.openapi.AutoSchema` and sets `body['required'] = True` in `_get_request_body`).
- *Alternative considered*: Relying solely on `@extend_schema` with a raw dict request schema, which defaults `requestBody.required` to `False` in `drf-spectacular`.

### 5. URL Ordering Against `timetables/urls.py` Catch-All
`timetables/urls.py` ends with `re_path(r"^.*$", views.unknown_api_route)` to return JSON `404` on unknown `/api/` paths. In `timetable_planner/urls.py`, `path('api/', include('accounts.urls'))` MUST be mounted **before** `path('api/', include('timetables.urls'))`. Inside `accounts/urls.py`, `users/me/` and `users/me/password/` are ordered before `users/<int:pk>/`.

### 6. Admin & Management Command Relocation
- Move `CanonicalUsernameFormMixin`, `SafeUserCreationForm`, `SafeUserChangeForm`, `SafeGroupAdmin`, and `SafeUserAdmin` (plus `admin.site.unregister(Group)`) from `timetables/admin.py` to `accounts/admin.py`.
- Move `timetables/management/commands/bootstrap_accounts.py` to `accounts/management/commands/bootstrap_accounts.py` and remove the empty `timetables/management/` directory tree.

## Risks / Trade-offs

- **[Risk] Catch-all route shadows `/api/users/*` or `/api/register/`** -> Mitigation: Mount `accounts.urls` before `timetables.urls` in `timetable_planner/urls.py` and verify existing API tests pass.
- **[Risk] Missing object-level permission check in `user_detail_api` exposes other users' profiles** -> Mitigation: Explicitly enforce `IsSelfOrAdmin` right after `get_object_or_404` inside `user_detail_api` for `GET`, `PATCH`, and `DELETE`.
- **[Risk] `@api_view` changes OpenAPI schema output for `user_role_api` or `register_api`** -> Mitigation: Attach `@schema(RequiredRoleSchema())` to `user_role_api` and `@extend_schema(auth=[], ...)` to `register_api`, then verify `/api/schema/` via `accounts/tests.py` and `manage.py spectacular` / test run.
- **[Risk] External imports referencing `timetables.accounts` or `timetables.pagination`** -> Mitigation: Grep the repository and update all internal references (`timetable_planner/urls.py`, `timetables/serializers.py`, `timetables/views.py`, `timetables/models.py`, `timetables/permissions.py`, `timetables/admin.py`).
