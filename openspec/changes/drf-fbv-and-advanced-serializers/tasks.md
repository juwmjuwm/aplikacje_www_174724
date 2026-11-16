# Tasks

## 1. Serializer Enhancements & Validations

- [x] 1.1 Add `ReadOnlyField` attributes (`timetable_name`, `student_group_name`, `subject_name`, `room_name`, `teacher_username`) and reference model `lessons_count` fields in `timetables/serializers.py` and verify serializing a lesson includes helper fields
- [x] 1.2 Implement `SerializerMethodField` fields `duration_minutes` and `room_utilization_percentage` in `LessonReadSerializer` in `timetables/serializers.py` and verify computed outputs
- [x] 1.3 Implement field-level validators `validate_start_time` and `validate_end_time` in `LessonWriteSerializer` enforcing operational hours (07:00–21:00)
- [x] 1.4 Implement cross-validation in `LessonWriteSerializer.validate()` covering duration constraints (30–240 minutes), capacity constraints (`student_group.size <= room.capacity`), teacher role verification, and schedule collision detection with `PATCH` support

## 2. Function-Based Views Implementation

- [x] 2.1 Implement `@api_view` handlers for `Timetable` (`timetable_list_create_api`, `timetable_detail_api`, `timetable_lessons_api`) in `timetables/views.py` with `prefetch_related('lessons')` and protected deletion error handling
- [x] 2.2 Implement `@api_view` handlers for `StudentGroup`, `Subject`, `Room`, and `Teacher` in `timetables/views.py` with `CollectionPagination`, search filtering, and `ProtectedError` handling
- [x] 2.3 Implement `@api_view` handlers for `Lesson` (`lesson_list_create_api`, `lesson_detail_api`) in `timetables/views.py` with calendar ordering, `select_related('timetable', 'student_group', 'subject', 'teacher', 'room')`, and `prefetch_related('teacher__groups')`

## 3. Routing & System Verification

- [x] 3.1 Update `timetables/urls.py` to route all endpoints directly to `@api_view` functions while preserving canonical route names (`timetable-list`, `lesson-list`, `room-list`, etc.) and catch-all 404 handler
- [x] 3.2 Run `.venv\Scripts\python.exe manage.py check` to verify system configuration, routing, and serializers without issues

