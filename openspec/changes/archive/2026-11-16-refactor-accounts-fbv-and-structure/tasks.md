# Tasks

## 1. Shared Foundation & One-Way Boundaries

- [x] 1.1 Move `CollectionPagination` to `timetable_planner/pagination.py`, remove `timetables/pagination.py`, update `timetables/views.py` to import from `timetable_planner.pagination`, and verify `python manage.py check` passes
- [x] 1.2 Move `lock_teacher_assignment` into `accounts/models.py`, update `timetables/models.py` to import it from `accounts.models`, and verify `python manage.py makemigrations --check --dry-run` reports no pending migrations
- [x] 1.3 Create `accounts/permissions.py` with `user_roles`, `user_role`, `IsAdmin`, and `IsSelfOrAdmin`, update `timetables/permissions.py` and `timetables/models.py` to import `user_roles` from `accounts.permissions`, and verify `python manage.py check` passes

## 2. Account Serializers, `@api_view` Endpoints & Routing

- [x] 2.1 Create `accounts/serializers.py` containing `CanonicalUsernameMixin`, `StrictFieldsMixin`, `NameFieldsMixin`, `UserSerializer`, `RegisterSerializer`, `ProfileSerializer`, `PasswordChangeSerializer`, `RoleSerializer`, `ROLE_REQUEST_SCHEMA`, and `username_conflict`, update `timetables/serializers.py` and `timetables/views.py` to import `UserSerializer` from `accounts.serializers`, and verify imports resolve via `python manage.py check`
- [x] 2.2 Create `accounts/views.py` implementing `@api_view` functions `register_api`, `password_change_api`, `user_list_api`, `user_me_api`, `user_detail_api` (with explicit `IsSelfOrAdmin` check and `user.lessons.exists()`), and `user_role_api` (with `@schema(RequiredRoleSchema())` and `.prefetch_related('groups')`), and verify schema generation succeeds with `python manage.py spectacular --validate --file nul` (or stdout)
- [x] 2.3 Create `accounts/urls.py` with explicit `path()` routes (`register`, `password_change`, `user-list`, `user-me`, `user-detail`, `user-role`), update `timetable_planner/urls.py` to include `accounts.urls` under `api/` before `timetables.urls` without `SimpleRouter`, remove `timetables/accounts.py`, and verify `python manage.py test accounts` passes

## 3. Admin & Management Command Relocation

- [x] 3.1 Move `CanonicalUsernameFormMixin`, `SafeUserCreationForm`, `SafeUserChangeForm` (using `self.instance.lessons.exists()`), `SafeGroupAdmin`, and `SafeUserAdmin` into `accounts/admin.py`, remove them from `timetables/admin.py`, and verify `python manage.py check` passes
- [x] 3.2 Move `bootstrap_accounts.py` from `timetables/management/commands/` to `accounts/management/commands/`, remove `timetables/management/`, and verify `python manage.py bootstrap_accounts --help` runs cleanly

## 4. Final Verification

- [x] 4.1 Search the repository for any remaining imports or references to `timetables.accounts` or `timetables.pagination`, then run `python manage.py check` and `python manage.py test accounts` to confirm all account, permission, and OpenAPI schema checks pass
