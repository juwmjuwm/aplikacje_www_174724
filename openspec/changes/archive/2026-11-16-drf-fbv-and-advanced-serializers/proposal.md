# Proposal

## Why

The current scheduling API relies entirely on DRF `ModelViewSet` and the automatic `DefaultRouter`, while serialization lacks auxiliary read fields and computed properties at the serializer layer. To fulfill Lab 5 guidelines and adhere to explicit REST architectural patterns, we need to convert all scheduling resources to function-based views decorated with `@api_view` with explicit ORM query optimizations (`select_related` and `prefetch_related`). Additionally, we must enhance the serializers with `ReadOnlyField`, nested relationship representations, computed metrics via `SerializerMethodField`, and robust multi-level serializer validations.

## What Changes

- **Convert ViewSets to FBVs**: Replace all scheduling `ModelViewSet` classes (`TimetableViewSet`, `StudentGroupViewSet`, `SubjectViewSet`, `RoomViewSet`, `LessonViewSet`, and `TeacherViewSet`) and `DefaultRouter` with explicit function-based views decorated with `@api_view` (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
- **Query Optimizations**: Optimize database queries in FBVs using `select_related` (for ForeignKeys: timetable, student group, subject, teacher, room) and `prefetch_related` (for teacher groups and timetable lessons) to prevent N+1 query overhead.
- **Enhanced Serializers**:
  - Add `ReadOnlyField` helper attributes to `Lesson` serializers (`room_name`, `subject_name`, `teacher_name`, `student_group_name`, `timetable_name`).
  - Add at least two computed fields via `SerializerMethodField` on `LessonReadSerializer`: `duration_minutes` (lesson length in minutes) and `room_utilization_percentage` (group size as a percentage of room capacity).
  - Add `lessons_count` to reference model serializers (`TimetableSerializer`, `StudentGroupSerializer`, `SubjectSerializer`, `RoomSerializer`).
- **Serializer-Level Validations**: Implement 3+ non-trivial validation rules in `LessonWriteSerializer`:
  - Field-level validation on `start_time` and `end_time` (enforcing campus operational hours: 07:00 to 21:00).
  - Object-level cross-validation in `validate()` for time order (`end_time > start_time`) and duration boundaries (minimum 30 minutes, no maximum constraint).
  - Object-level cross-validation in `validate()` verifying that student group size does not exceed room capacity.
  - Conflict checking for teacher, room, and student group double-booking.
- **Preserve API Contracts**: Maintain existing URL route names (`timetable-list`, `timetable-detail`, `lesson-list`, `lesson-detail`, etc.), pagination (`CollectionPagination`), search filtering (`SearchFilter`), permissions (`SchedulingPermission`), and error responses (`ProtectedError` -> 409 Conflict).

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `timetable-crud-api`: Enriches lesson representation with computed fields and helper read fields, adds operational hours and duration validation rules, and specifies FBV implementation with explicit query optimizations while preserving pagination, search, and conflict contracts.

## Impact

- `timetables/views.py`: Replaces CBVs with `@api_view` functions for all scheduling resources.
- `timetables/urls.py`: Replaces DRF router registration with explicit `path()` routing while keeping canonical route names and endpoints intact.
- `timetables/serializers.py`: Extends serializers with `ReadOnlyField`, `SerializerMethodField`, field validators, and cross-validation in `validate()`.
- No database migrations or schema modifications are required (existing 5 models remain unchanged).

