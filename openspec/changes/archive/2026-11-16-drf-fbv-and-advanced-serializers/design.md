# Design

## Context

See `proposal.md` for motivation. Currently, the `timetables` app exposes all six scheduling resources using `ModelViewSet` subclasses mounted onto a DRF `DefaultRouter`. Serializers perform minimal field-level or cross-validation directly in DRF, relying instead on underlying Django model `clean()` calls intercepted during `save()`. To meet the Lab 5 curriculum guidelines, we are transitioning all scheduling views to explicit `@api_view` decorated functions with explicit ORM query optimizations (`select_related`, `prefetch_related`) and equipping serializers with read-only convenience fields, computed properties, and explicit DRF-level validations.

## Goals / Non-Goals

**Goals:**
- Replace all 6 ViewSets in `timetables/views.py` with explicit `@api_view` function-based views supporting GET, POST, PUT, PATCH, and DELETE.
- Wire explicit `path()` entries in `timetables/urls.py` preserving existing route names (`<model>-list`, `<model>-detail`, `timetable-lessons`).
- Retain pagination format (`count`, `next`, `previous`, `results`) via `CollectionPagination` and case-insensitive search via `SearchFilter`.
- Optimize ORM queries using `.select_related()` on ForeignKeys and `.prefetch_related()` on reverse/M2M relationships.
- Add `ReadOnlyField` attributes (`room_name`, `subject_name`, `teacher_name`, `student_group_name`, `timetable_name`) and two `SerializerMethodField` properties (`duration_minutes`, `room_utilization_percentage`) to `Lesson` serializers.
- Add 3+ non-trivial validations in `LessonWriteSerializer`: operational hours (07:00–21:00), duration limits (30–240 minutes), capacity constraints, and collision detection with full `PATCH` support (`getattr(self.instance, ...)`).

**Non-Goals:**
- Creating new database entities or relationships (no `Tag` model; database schema and migrations remain untouched).
- Modifying authentication or user account endpoints in `accounts` or `timetable_planner/urls.py`.
- Writing new automated tests (adhering to project context rules).

## Decisions

### 1. Structure of Function-Based Views (`@api_view`)
Each resource will be handled by standard list-create and detail functions:
- `timetable_list_create_api`, `timetable_detail_api`, `timetable_lessons_api`
- `student_group_list_create_api`, `student_group_detail_api`
- `subject_list_create_api`, `subject_detail_api`
- `teacher_list_api`, `teacher_detail_api` (read-only: GET only)
- `room_list_create_api`, `room_detail_api`
- `lesson_list_create_api`, `lesson_detail_api`

*Rationale*: Separating list-create from detail operations is the canonical DRF function-based pattern. It simplifies routing and cleanly maps HTTP methods.
*Alternatives considered*: A single dispatcher function per resource handling all methods (rejected due to excessive branching and messy parameter handling).

### 2. Preserving Pagination and Search
In list views:
```python
def paginate_and_respond(request, queryset, serializer_class, search_fields=None):
    if search_fields:
        search_filter = SearchFilter()
        class ViewWrapper:
            pass
        view = ViewWrapper()
        view.search_fields = search_fields
        queryset = search_filter.filter_queryset(request, queryset, view)

    paginator = CollectionPagination()
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)
```
*Rationale*: Ensures exact compatibility with existing paginated response contracts and search parameters (`?search=...`, `?page=...`, `?size=...`).

### 3. ORM Query Optimization
- For `Lesson`:
  ```python
  Lesson.objects.select_related(
      'timetable', 'student_group', 'subject', 'teacher', 'room'
  ).prefetch_related('teacher__groups')
  ```
- For `Timetable`:
  ```python
  Timetable.objects.prefetch_related('lessons')
  ```
*Rationale*: Reduces queries from $O(N)$ down to a constant 2 queries for lesson collections and detail responses.

### 4. Serializer Enhancements and Computed Properties
- `LessonReadSerializer` will include:
  - `timetable_name = serializers.ReadOnlyField(source='timetable.name')`
  - `student_group_name = serializers.ReadOnlyField(source='student_group.name')`
  - `subject_name = serializers.ReadOnlyField(source='subject.name')`
  - `room_name = serializers.ReadOnlyField(source='room.name')`
  - `teacher_username = serializers.ReadOnlyField(source='teacher.username')`
  - `duration_minutes = serializers.SerializerMethodField()`
  - `room_utilization_percentage = serializers.SerializerMethodField()`
- Methods:
  - `get_duration_minutes(self, obj)`: Calculates difference between `end_time` and `start_time` in integer minutes.
  - `get_room_utilization_percentage(self, obj)`: Calculates `round((obj.student_group.size / obj.room.capacity) * 100, 1)`.

### 5. Multi-level Serializer Validation
In `LessonWriteSerializer`:
- Field validation: `validate_start_time` and `validate_end_time` verify `07:00 <= time <= 21:00`.
- Object validation `validate(self, attrs)`:
  - Resolves values using `attrs.get(field, getattr(self.instance, field, None))` to properly support partial `PATCH`.
  - Verifies `end_time > start_time`.
  - Verifies duration: $30 \le \Delta t \le 240$ minutes.
  - Verifies capacity: `student_group.size <= room.capacity`.
  - Verifies schedule conflict: checks for existing non-conflicting lessons with overlapping time windows for the same room, teacher, or student group.

## Risks / Trade-offs

- **[Risk] Route naming breaks existing API callers or tests**
  → *Mitigation*: Configure explicit `name` arguments for every `path()` in `timetables/urls.py` that precisely match DRF router names (`timetable-list`, `timetable-detail`, `lesson-list`, `lesson-detail`, `room-list`, `room-detail`, `subject-list`, `subject-detail`, `studentgroup-list`, `studentgroup-detail`, `teacher-list`, `teacher-detail`).
- **[Risk] Error format divergence on model deletion**
  → *Mitigation*: Wrap model `.delete()` calls in try/except blocks catching `ProtectedError` and returning HTTP 409 Conflict with `{"detail": "Related lessons prevent deletion of this resource."}`.

