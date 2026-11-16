# Tasks

## 1. Lightweight Lesson Serializers

- [x] 1.1 Add compact nested summary serializers (`TimetableSummarySerializer`, `StudentGroupSummarySerializer`, `SubjectSummarySerializer`, `RoomSummarySerializer`, `TeacherSummarySerializer`) and `LessonListSerializer` in `timetables/serializers.py` without `lessons_count`, `description`, helper `*_name` fields, or computed metrics; verify serializer imports and field definitions via `python manage.py check`.
- [x] 1.2 Ensure `LessonReadSerializer` and `LessonWriteSerializer` remain intact for detail and write validation/output; verify `LessonListSerializer` vs `LessonReadSerializer` field sets in a Django shell check.

## 2. Scheduling ViewSets, Actions, and Summary APIView

- [x] 2.1 Replace the scheduling `@api_view` functions in `timetables/views.py` with `ProtectedDeleteMixin`, `TimetableViewSet`, `LessonViewSet`, `StudentGroupViewSet`, `SubjectViewSet`, `RoomViewSet`, and `TeacherViewSet` (`ReadOnlyModelViewSet`), preserving `CollectionPagination`, `SearchFilter`, `SchedulingPermission`, `ordered_lessons()`, `select_related`/`prefetch_related`, and HTTP 409 `ProtectedError` handling; verify via `python manage.py check`.
- [x] 2.2 Implement `get_serializer_class()` on `LessonViewSet` returning `LessonListSerializer` for `list`, `LessonReadSerializer` for `retrieve`, and `LessonWriteSerializer` for `create`/`update`/`partial_update`, overriding `create()` and `update()` to return `LessonReadSerializer` data using `get_optimized_lesson_queryset()`; verify request/response shapes via OpenAPI schema generation.
- [x] 2.3 Add `@action(detail=True, methods=['get']) def lessons(...)` and `@action(detail=True, methods=['post'], url_path='clear-lessons') def clear_lessons(...)` to `TimetableViewSet` (with `@extend_schema` annotations); verify both action URLs resolve under `/api/timetables/{id}/lessons/` and `/api/timetables/{id}/clear-lessons/`.
- [x] 2.4 Implement `SchedulingSummaryAPIView(APIView)` in `timetables/views.py` using `Count`, `Min`, `Max`, and `Avg` aggregations and `IsAuthenticated` permission; verify `/api/summary/` resolves and returns the expected summary keys.
- [x] 2.5 Replace manual CRUD paths in `timetables/urls.py` with `DefaultRouter` registrations preserving existing `basename` values (`timetable`, `lesson`, `studentgroup`, `subject`, `room`, `teacher`), mount `summary/`, and keep `unknown_api_route` as the final fallback; verify URL resolution and `python manage.py check`.

## 3. Account ViewSet, Registration APIView, and Routing

- [x] 3.1 Replace the account `@api_view` functions in `accounts/views.py` with `RegisterAPIView(APIView)` and `UserViewSet(viewsets.ModelViewSet)` (restricting `POST /api/users/` and `PUT /api/users/{id}/` with HTTP 405, preserving `CollectionPagination`, `IsAdmin`/`IsSelfOrAdmin`, atomic deletion/role lock checks, `RequiredRoleSchema`, and `@extend_schema` annotations); verify via `python manage.py check`.
- [x] 3.2 Expose `me` (`@action(detail=False, methods=['get'])`), `change_password` (`@action(detail=False, methods=['post'], url_path='me/password')`), and `role` (`@action(detail=True, methods=['patch'])`) on `UserViewSet`, and configure `accounts/urls.py` with `SimpleRouter` (so `timetables` `DefaultRouter` owns the `/api/` root) while preserving route names `register` and `password_change`; verify `reverse('register')`, `reverse('password_change')`, and `GET /api/` API Root output.

## 4. Integration & Schema Verification

- [x] 4.1 Verify OpenAPI schema generation at `/api/schema/` (`drf-spectacular`) accurately documents all `/api/` ViewSets, `@action` endpoints, `SchedulingSummaryAPIView`, `RegisterAPIView`, and `PATCH /api/users/{id}/role/` requestBody contract without duplicate `/timetables/` or fallback routes.
- [x] 4.2 Run `python manage.py test` across existing suites and inspect any failures caused by the intentional `GET /api/lessons/` lightweight list contract change.
