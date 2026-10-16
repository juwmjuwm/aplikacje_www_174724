# The Timetabler

## Timetable API

Install dependencies with `pip install -r requirements.txt`, apply migrations with
`python manage.py migrate`, and run the development server with
`python manage.py runserver`.

All API paths end in `/` and exchange JSON. Each collection supports `GET` (200,
JSON array) and `POST` (201, created record). Each detail path appends an integer
`id` and supports `GET`, `PUT`, and `PATCH` (200, JSON record), plus `DELETE`
(204, empty body). The `id` field in every response is read-only.

| Collection path | Writable request fields |
| --- | --- |
| `/api/timetables/` | `name`, `owner` (existing user ID), optional `description` |
| `/api/student-groups/` | `name`, `size` (positive integer) |
| `/api/subjects/` | `name`, optional `description` |
| `/api/teachers/` | `first_name`, `last_name`, optional `academic_title`, optional `email` |
| `/api/rooms/` | `name`, `capacity` (positive integer) |
| `/api/lessons/` | `timetable`, `student_group`, `subject`, `teacher`, `room` (existing record IDs); `weekday` (`MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, or `SUN`); `start_time`, `end_time` (for example, `09:00:00`) |

For example, create a timetable with
`POST /api/timetables/` and `{"name":"Autumn","owner":1}`. Create a lesson
with `POST /api/lessons/` and a body such as:

```json
{
  "timetable": 1,
  "student_group": 1,
  "subject": 1,
  "teacher": 1,
  "room": 1,
  "weekday": "MON",
  "start_time": "09:00:00",
  "end_time": "10:00:00"
}
```

Relations are returned as IDs. A missing or nonexistent related ID returns
HTTP 400 with errors keyed by field, such as `{"room":["Invalid pk ..."]}`.
Invalid lesson intervals return an `end_time` error; overlapping room, teacher,
or student group bookings return an error keyed by the conflicting resource.
Unexpected concurrent conflicts caught by the SQLite scheduling trigger return
HTTP 400 with `non_field_errors`.

Missing records and unknown `/api/` paths return HTTP 404 with a JSON `detail`
message. Unsupported methods return HTTP 405 with the method named in `detail`.
Deleting a student group, subject, teacher, or room used by a lesson returns
HTTP 409 with a `detail` message explaining that related lessons prevent
deletion. Deleting a timetable removes its lessons as well.
