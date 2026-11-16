# Proposal

## Why

The REST API layer in `timetables` and `accounts` currently relies on repetitive function-based views (`@api_view`) and manual URL entries, duplicating boilerplate for serialization, `get_object_or_404`, pagination, and method dispatching. Migrating to DRF `ModelViewSet`, `DefaultRouter`, dynamic `get_serializer_class()`, `@action` routes, and `APIView` aligns the project with standard DRF class-based architecture, eliminates N+1 `lessons_count` queries on lesson lists, and satisfies the Lab 6 refactoring requirements while keeping the canonical `/api/` URL space.

## What Changes

- Refactor `timetables` views from `@api_view` functions into `ModelViewSet` classes (`TimetableViewSet`, `LessonViewSet`, `StudentGroupViewSet`, `SubjectViewSet`, `RoomViewSet`) and a read-only ViewSet (`TeacherViewSet`) registered with `DefaultRouter` under `/api/`.
- Refactor `accounts` views into `UserViewSet` (preserving `GET /api/users/`, `GET/PATCH/DELETE /api/users/{id}/`, and exposing `me`, `me/password`, and `role` via `@action`) and `RegisterAPIView(APIView)` at `POST /api/register/`.
- **BREAKING** Implement `get_serializer_class()` on `LessonViewSet` so `list` (`GET /api/lessons/`) returns a lightweight `LessonListSerializer` (retaining compact nested objects for related records while omitting `lessons_count`, `description`, redundant `*_name` fields, and computed metrics), whereas `retrieve`, `create`, and `update`/`partial_update` return the full `LessonReadSerializer` payload (with `LessonWriteSerializer` validating input IDs).
- Convert `GET /api/timetables/{id}/lessons/` into a `@action(detail=True, methods=['get'])` method on `TimetableViewSet`.
- Add a state-mutating `@action(detail=True, methods=['post'], url_path='clear-lessons')` on `TimetableViewSet` (`POST /api/timetables/{id}/clear-lessons/`) that deletes all lessons belonging to that timetable for authorized editors (`PLANNER`/`ADMIN`).
- Add `SchedulingSummaryAPIView(APIView)` at `GET /api/summary/` returning aggregated scheduling statistics (`Count`, `Avg`, `Min`, `Max`).
- Preserve `/api/` URL prefix, existing `basename` route names where applicable, `SchedulingPermission`, `ProtectedError` -> HTTP 409 handling, `CollectionPagination`, `SearchFilter`, and drf-spectacular OpenAPI schema behavior.

## Capabilities

### New Capabilities

- None (new scheduling endpoints extend the existing `timetable-crud-api` capability).

### Modified Capabilities

- `timetable-crud-api`: Replace the function-based view implementation requirement with DRF `ModelViewSet`/`ReadOnlyModelViewSet` and `DefaultRouter`; update `Expanded lesson response` so `GET /api/lessons/` returns lightweight nested objects while detail/create/update return the full representation; add requirements for `POST /api/timetables/{id}/clear-lessons/` and `GET /api/summary/`.

## Impact

- `timetables/views.py` (or `timetables/viewsets.py` + `timetables/views.py`), `timetables/serializers.py`, `timetables/urls.py`
- `accounts/views.py`, `accounts/urls.py`
- `timetable_planner/urls.py`, `timetable_planner/schema.py` (verifying `/api/` root and `DefaultRouter` inclusion)
- OpenAPI schema (`/api/schema/` and `/api/docs/`) and existing API tests whose `GET /api/lessons/` or route names are affected by the refactor
