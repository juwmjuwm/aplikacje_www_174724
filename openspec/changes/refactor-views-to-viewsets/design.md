# Design

## Context

Currently both `timetables` and `accounts` expose REST endpoints via `@api_view` function-based views and explicit `path()` entries, with `timetables.urls` and `accounts.urls` both mounted under `/api/` in `timetable_planner/urls.py` (and `timetables.urls` additionally mounted at `/timetables/`). Existing contracts rely on `CollectionPagination` (`page`/`size`), `SearchFilter` (`search`), `SchedulingPermission`, `IsAdmin`/`IsSelfOrAdmin`, `ProtectedError` -> HTTP 409 conflict handling, `drf-spectacular` schema filtering (`timetable_planner/schema.py`), and preserved route names (`register`, `password_change`, `room-list`, `studentgroup-list`, etc.). See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Replace all scheduling and account `@api_view` endpoints with DRF `ModelViewSet` (or read-only ViewSet where writes are disallowed), `@action` methods, and `APIView` classes.
- Use `DefaultRouter` under `/api/` without route collisions between `accounts` and `timetables` and without breaking existing route names or `unknown_api_route` JSON 404 fallback.
- Implement `get_serializer_class()` on `LessonViewSet` so `list` returns lightweight nested objects while `retrieve`, `create`, and `update`/`partial_update` use full detail/write serialization with complete `LessonReadSerializer` output.
- Implement `POST /api/timetables/{id}/clear-lessons/` (`@action(detail=True, methods=['post'])`) and `GET /api/summary/` (`SchedulingSummaryAPIView(APIView)`).

**Non-Goals:**
- Introducing `/api/v1/` path versioning (the project stays on `/api/`).
- Changing database models or adding migrations.
- Modifying JWT token endpoints (`TokenObtainPairView`, `TokenRefreshView`), Swagger/OpenAPI views, or permission semantics.

## Decisions

### 1. Shared vs split router configuration under `/api/`
- **Decision:** Keep `accounts` and `timetables` ViewSets decoupled in their own apps, but expose a single combined `DefaultRouter` (or use `SimpleRouter` in `accounts/urls.py` and `DefaultRouter` in `timetables/urls.py`, or register all ViewSets on one `DefaultRouter` in `timetable_planner/urls.py` / an `api` router).
- **Rationale:** Both `accounts.urls` and `timetables.urls` are mounted at `path('api/', ...)` in `timetable_planner/urls.py`. If `accounts.urls` used its own `DefaultRouter` first, `GET /api/` (API Root) would only show `users` and hide all `timetables` resources. Using `SimpleRouter` in `accounts/urls.py` (with `DefaultRouter` in `timetables/urls.py`) or mounting a unified `DefaultRouter` at `api/` ensures `GET /api/` lists the scheduling API root cleanly while keeping `/api/users/...` and `/timetables/` intact. Placing `SimpleRouter` in `accounts/urls.py` and `DefaultRouter` in `timetables/urls.py` also keeps the `/timetables/` legacy mount free of `/timetables/users/`.
- **Alternative considered:** Separate `DefaultRouter` in both apps — rejected because the first router shadows the second router's API Root view.

### 2. LessonViewSet serializer split (`get_serializer_class()` + write output)
- **Decision:** Add lightweight nested summary serializers (`TimetableSummarySerializer`, `StudentGroupSummarySerializer`, `SubjectSummarySerializer`, `RoomSummarySerializer`, `TeacherSummarySerializer`) used by `LessonListSerializer` (for `self.action == 'list'`). Keep `LessonReadSerializer` for `retrieve` and `LessonWriteSerializer` for `create`, `update`, `partial_update`. Override `create()` and `update()` (or `LessonWriteSerializer.to_representation()`) on `LessonViewSet` to re-fetch with `get_optimized_lesson_queryset()` and serialize the response via `LessonReadSerializer`.
- **Rationale:** Calling `LessonReadSerializer` on `list` currently triggers 4 extra `COUNT(*)` queries per row via `lessons_count = IntegerField(source="lessons.count")`. A dedicated `LessonListSerializer` preserves nested objects on `list` as requested, avoids N+1 count queries, and keeps `retrieve`/`create`/`update` returning the full payload. Overriding `create()`/`update()` on `LessonViewSet` also ensures `drf-spectacular` cleanly inspects `LessonWriteSerializer` for request bodies and `LessonReadSerializer` / `LessonListSerializer` for responses via `@extend_schema_view` or `get_serializer_class()`.
- **Alternative considered:** Returning bare FK IDs on `list` — rejected per user preference to keep nested objects in lesson responses.

### 3. Preserving read-only / restricted HTTP methods on `TeacherViewSet` and `UserViewSet`
- **Decision:**
  - Implement `TeacherViewSet(viewsets.ReadOnlyModelViewSet)` (or `ModelViewSet` with `http_method_names = ['get', 'head', 'options']`) registered at `r'teachers'` (`basename='teacher'`).
  - Implement `UserViewSet(viewsets.ModelViewSet)` with `http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']`, overriding `create()` to raise `MethodNotAllowed('POST')` (since account creation is exclusively via `RegisterAPIView` at `/api/register/`, while `POST` remains allowed in `http_method_names` so `@action(detail=False, methods=['post'], url_path='me/password')` works!).
  - Preserve existing URL name `password_change` by keeping/aliasing `path('users/me/password/', UserViewSet.as_view({'post': 'change_password'}), name='password_change')` alongside the router or configuring `url_name` appropriately (noting `DefaultRouter`/`SimpleRouter` prefixes `basename`, so an explicit alias before `router.urls` guarantees `reverse('password_change')` keeps working).
- **Rationale:** Using `ModelViewSet` for `UserViewSet` matches the refactor goal while maintaining exact HTTP 405 behavior on `POST /api/users/` and `PUT /api/users/{id}/` and keeping `reverse('password_change')` and `reverse('register')` compatible.
- **Alternative considered:** Leaving `accounts` as `@api_view` — rejected per user decision to migrate `accounts` as well.

### 4. Preserving `ProtectedError` -> HTTP 409, `SearchFilter`, `CollectionPagination`, and `SchedulingSummaryAPIView`
- **Decision:**
  - Extract a small `ProtectedDeleteMixin` for `TimetableViewSet`, `StudentGroupViewSet`, `SubjectViewSet`, and `RoomViewSet` so `destroy()` catches `ProtectedError` and returns HTTP 409 `{"detail": "Related lessons prevent deletion of this resource."}`.
  - Configure `pagination_class = CollectionPagination` and `filter_backends = [SearchFilter]` with model-appropriate `search_fields` on the ViewSets (`TimetableViewSet`, `StudentGroupViewSet`, `SubjectViewSet`, `RoomViewSet`, `TeacherViewSet`, `UserViewSet`).
  - In `LessonViewSet.get_queryset()`, apply `ordered_lessons(get_optimized_lesson_queryset())`.
  - Add `clear_lessons` (`@action(detail=True, methods=['post'], url_path='clear-lessons')`) on `TimetableViewSet` deleting `timetable.lessons.all()` inside `transaction.atomic()` and returning `{"id": timetable.pk, "name": timetable.name, "deleted_lessons_count": deleted_count}`.
  - Add `SchedulingSummaryAPIView(APIView)` with `permission_classes = [IsAuthenticated]` at `path('summary/', ...)`, using `Count`, `Min`, `Max`, `Avg` aggregations to return counts (`timetables_count`, `lessons_count`, `student_groups_count`, `subjects_count`, `rooms_count`, `teachers_count`) and room capacity statistics (`min_room_capacity`, `max_room_capacity`, `average_room_capacity` rounded to 2 decimals or `0.0`).
  - Keep `RegisterAPIView(APIView)` with `permission_classes = [AllowAny]` and `auth=[]` in schema at `path('register/', ...)`.
  - Keep `re_path(r"^.*$", unknown_api_route)` at the very end of `timetables/urls.py` after `include(router.urls)` and `summary/`, and ensure `timetable_planner/schema.py` excludes `unknown_api_route` if needed (since it is not a DRF `APIView`, `drf-spectacular` already ignores it, as before).

## Risks / Trade-offs

- **Route name changes from `DefaultRouter`** -> Use explicit `basename` matching existing names (`timetable`, `lesson`, `studentgroup`, `subject`, `room`, `teacher`, `user`) and keep `name='password_change'` / `name='register'` so existing `reverse(...)` calls do not break.
- **OpenAPI schema (`drf-spectacular`) accuracy** -> Ensure `UserViewSet.role` keeps `@extend_schema(request=..., responses=...)` and `RequiredRoleSchema` (or equivalent `AutoSchema` override) so `PATCH /api/users/{id}/role/` still marks `requestBody.required = True` and `roles` as required; add `@extend_schema` annotations on `SchedulingSummaryAPIView`, `RegisterAPIView`, `TimetableViewSet.clear_lessons`, and `LessonViewSet` so Swagger UI reflects exact request/response schemas.
- **Breaking response shape on `GET /api/lessons/`** -> Documented in proposal and delta spec (`LessonListSerializer` returns compact nested objects instead of `LessonReadSerializer`). Any consumer or test expecting `duration_minutes` or `lessons_count` on the list endpoint will need to use `GET /api/lessons/{id}/` or be updated if appropriate.
