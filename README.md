# The Timetabler

## Timetable API

Install dependencies with `pip install -r requirements.txt`. Copy `.env.example`
to `.env` and replace its placeholders. `DJANGO_SECRET_KEY` is required for
Django and JWT signing. Set `INITIAL_ADMIN_USERNAME` and
`INITIAL_ADMIN_PASSWORD` before initial bootstrap. The `.env` file is ignored
by Git; existing host environment variables take precedence.

For a fresh database, run `python manage.py migrate`, then `python manage.py bootstrap_accounts`, then
`python manage.py runserver`. Run bootstrap after migrations on each deployment
start. It creates the `PLANNER` and `TEACHER` groups and, if none exists, an ADMIN superuser
from the initial credentials. Repeated runs preserve its password and
privileges. Missing credentials when no ADMIN exists, or a configured username
already held by a regular user, cause a clear error.
`INITIAL_ADMIN_USERNAME` is canonicalized with Unicode NFKC and case folding:
`ADMIN` creates or finds `admin`. Repeated bootstrap runs preserve an existing
ADMIN's password and privileges, even when the configured casing changes.
Choose a unique initial password with at least eight characters, including a
lowercase letter, uppercase letter, decimal digit, and punctuation or symbol.
The value in `.env.example` is illustrative and must be replaced before use.

## Authentication and users

### Swagger API reference

Start the Django server and open `http://127.0.0.1:8000/api/docs/` for Swagger UI.
The generated OpenAPI 3.0 schema is available at
`http://127.0.0.1:8000/api/schema/`. Both pages are public; API permissions
still apply to protected requests.

To try a protected request, first use `POST /api/register/` to create a VIEWER
account if needed. In Swagger UI, open `POST /api/token/`, select **Try it out**,
enter that account's `username` and `password`, and select **Execute**. Copy the
`access` value from the response. Select **Authorize** at the top of the page,
paste the access token into the `jwtAuth` field, and confirm. Swagger UI sends
it as `Authorization: Bearer <access token>` on protected operations. Try
`GET /api/rooms/` to confirm access. When the access token expires, use
`POST /api/token/refresh/` with the `refresh` value to get a new one.

Register a VIEWER with `POST /api/register/` and
`{"username":"Alice","password":"Strong-unique-pass-123","first_name":"Alice","last_name":"Nowak"}`.
Both names are required, trimmed, and must contain only Unicode letters.
Accepted names are stored with the first letter uppercase and the rest lowercase.
Registration validates passwords and rejects email and
privilege fields. A response is
`{"id":7,"username":"alice","first_name":"Alice","last_name":"Nowak","role":"VIEWER","roles":["VIEWER"]}`.
Account responses omit email and passwords.
Usernames are normalized with Unicode NFKC and case folding before storage;
the lowercase value in the response is authoritative. Registering `ALICE`
after `alice` exists returns HTTP 400 with a `username` error and creates no
account. Usernames may contain only Unicode letters, Unicode decimal digits,
and underscores, with at most 150 characters before and after normalization.
Spaces, hyphens, periods, and at signs are rejected. New passwords must have
at least eight characters and a Unicode lowercase letter, uppercase letter,
decimal digit, and punctuation or symbol. Whitespace does not count as a
special character. Existing passwords remain usable until changed.

Obtain tokens with `POST /api/token/` and
`{"username":"ALICE","password":"Strong-unique-pass-123"}`. Username input
is matched without regard to case in token and Django Admin login. Invalid or
inactive credentials are still denied. Refresh access
with `POST /api/token/refresh/` and `{"refresh":"<refresh token>"}`. Send
`Authorization: Bearer <access token>` on protected requests. Missing or invalid
tokens return HTTP 401. Role changes take effect on existing access tokens.

The account holder or ADMIN may `GET` or `PATCH /api/users/{id}/`. PATCH accepts
`username`, `first_name`, and `last_name`, for example
`{"username":"ALICE","first_name":"Alicja"}`. This succeeds for `alice`
and returns `"username":"alice"`; a different account's canonical username
returns HTTP 400 with a `username` error and leaves the profile unchanged.
Submitted names are trimmed, cannot be blank, and may contain only Unicode letters;
omitted fields stay unchanged. Email, password, and privilege fields return
HTTP 400. The response includes both names, `role`, and `roles`, and omits
email and passwords. Existing accounts with empty names remain readable.
To change your own password, send `POST /api/users/me/password/` with
`{"current_password":"Strong-unique-pass-123","new_password":"Another-strong-pass-456"}`
and a valid access token. The current password must match; the new password
must differ and pass the registration password policy. Success is HTTP 204 with
an empty body. Missing, invalid, or extra fields return HTTP 400; missing
authentication returns HTTP 401. Obtain new tokens using the new password.
ADMIN may `GET /api/users/` and `PATCH /api/users/{id}/role/` with
`{"roles":["PLANNER","TEACHER"]}`, `{"roles":["TEACHER"]}`,
`{"roles":["PLANNER"]}`, or `{"roles":[]}`. The array is the complete
membership set; an empty array sets VIEWER. It cannot contain VIEWER, ADMIN,
duplicates, or unknown values. Send exactly one of `roles` or the legacy
`role` field. Responses keep `role` for compatibility and include the complete
`roles` array in ADMIN, PLANNER, TEACHER order. For a combined account,
`"role":"PLANNER"` and `"roles":["PLANNER","TEACHER"]`.
The legacy single-role requests are `{"role":"PLANNER"}`,
`{"role":"TEACHER"}`, or `{"role":"VIEWER"}`.
The ADMIN user list is paginated like the scheduling collections below.
Promote an existing VIEWER with `{"role":"TEACHER"}`. An unassigned TEACHER
may be demoted with `{"role":"VIEWER"}`. Switching directly between TEACHER
and PLANNER using the legacy `role` field returns HTTP 409; transition through
VIEWER or use `roles` to set the complete membership set. Removing TEACHER from
an assigned user, including one retaining PLANNER, returns HTTP 409 with
`{"detail":"Reassign or delete this teacher's lessons before removing TEACHER."}`.
Removing only PLANNER from an assigned combined-role teacher succeeds.
The same guard applies to Django Admin group editing. An authenticated account
holder may `DELETE /api/users/{id}/` for their own account; ADMIN may delete
another account. Other authenticated callers receive HTTP 403, and missing or
invalid authentication returns HTTP 401. A successful deletion returns HTTP 204
and removes the account immediately, so its tokens can no longer authorize
requests. VIEWER, PLANNER, unassigned TEACHER, and unassigned combined-role
accounts can be deleted without changing memberships first. Deleting any ADMIN
account, including an ADMIN's own account, returns HTTP 409. Deleting a TEACHER
with assigned lessons, including one who is also a PLANNER, returns HTTP 409;
reassign or delete those lessons first. Django Admin account deletion keeps its
existing, narrower rule: it allows only regular VIEWER accounts with neither
PLANNER nor TEACHER membership.

## Scheduling access

Authenticated VIEWER, TEACHER, PLANNER, combined-role, and ADMIN accounts can
read scheduling data. PLANNER membership and ADMIN status allow create, update,
and delete, including when the PLANNER also teaches. VIEWER and TEACHER-only
writes return HTTP 403. Removing PLANNER immediately removes write access from
existing tokens. Timetables are shared, so any PLANNER or ADMIN may edit them.

All API paths end in `/` and exchange JSON. Scheduling collections support
`GET` (200, paginated JSON object); all except the teacher directory support
`POST` (201, created record). Each detail path appends an integer
`id` and supports `GET`, `PUT`, and `PATCH` (200, JSON record), plus `DELETE`
(204, empty body), except the read-only teacher detail path. The `id` field in
every response is read-only.

`GET /api/timetables/`, `/api/lessons/`, `/api/student-groups/`,
`/api/subjects/`, `/api/teachers/`, `/api/rooms/`, and ADMIN-only
`/api/users/` return `{"count":12,"next":"http://testserver/api/rooms/?page=2","previous":null,"results":[...]}`
with the requested records in `results`. Clients that previously read a bare
array must read `results`. The default page holds 10 records. Use `page` to
select a page and `size` for a positive integer page size, for example
`GET /api/rooms/?page=2&size=5`. Values above 100 are capped at 100;
nonnumeric, zero, and negative sizes return HTTP 400 with a `size` error.
`next` and `previous` are URLs or `null`, and preserve active query parameters.

| Collection path | Writable request fields |
| --- | --- |
| `/api/timetables/` | `name`, optional `description` |
| `/api/student-groups/` | `name`, `size` (positive integer) |
| `/api/subjects/` | `name`, optional `description` |
| `/api/teachers/` | Read-only directory of every TEACHER group member, including PLANNER and ADMIN teachers; no writable fields |
| `/api/rooms/` | `name`, `capacity` (positive integer) |
| `/api/lessons/` | `timetable`, `student_group`, `subject`, `room` (existing record IDs), `teacher` (TEACHER user ID); `weekday` (`MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, or `SUN`); `start_time`, `end_time` (for example, `09:00:00`) |

Use `search` for case-insensitive partial matches on timetable, student group,
and room `name`; subject `name` or `description`; and TEACHER member
`first_name` or `last_name`. Search filters before pagination. For example,
`GET /api/subjects/?search=biology&size=5&page=2` returns the second page of
up to five matching subjects, with `count` and navigation URLs for the same
search. Lessons and the ADMIN user list have no `search` filter.

`GET /api/teachers/` returns users such as
`{"count":1,"next":null,"previous":null,"results":[{"id":7,"username":"alice","first_name":"Alice","last_name":"Nowak","role":"PLANNER","roles":["PLANNER","TEACHER"]}]}`.
`GET /api/teachers/7/` returns the same object. An ADMIN teacher has
`"role":"ADMIN"` and `"roles":["ADMIN","TEACHER"]`. Users without TEACHER
membership are omitted and return HTTP 404 at the detail path. Teacher POST, PUT, PATCH, and DELETE return
HTTP 405. Assign roles through the user role endpoint.

For example, create a timetable with
`POST /api/timetables/` and `{"name":"Autumn"}`. Create a lesson
with `POST /api/lessons/` and a body such as:

```json
{
  "timetable": 1,
  "student_group": 1,
  "subject": 1,
  "teacher": 7,
  "room": 1,
  "weekday": "MON",
  "start_time": "09:00:00",
  "end_time": "10:00:00"
}
```

Relations, including `teacher`, are returned as IDs. A missing, nonexistent, or
user ID without TEACHER membership in `teacher` returns HTTP 400 with a `teacher`
field error. A PLANNER or ADMIN with TEACHER membership is eligible.
Other missing or nonexistent related IDs return
HTTP 400 with errors keyed by field, such as `{"room":["Invalid pk ..."]}`.
Invalid lesson intervals return an `end_time` error; overlapping room, teacher,
or student group bookings return an error keyed by the conflicting resource.
Unexpected concurrent conflicts caught by the SQLite scheduling trigger return
HTTP 400 with `non_field_errors`.

Missing records and unknown `/api/` paths return HTTP 404 with a JSON `detail`
message. Unsupported methods return HTTP 405 with the method named in `detail`.
Deleting a student group, subject, or room used by a lesson returns
HTTP 409 with a `detail` message explaining that related lessons prevent
deletion. Deleting a timetable removes its lessons as well.

### Owner removal migration

`Timetable.owner` has been removed from storage and JSON. Clients must stop
sending or expecting `owner`; POST, PUT, and PATCH with that field return HTTP
400. Existing timetable and lesson rows survive migration 0002, but owner IDs
are discarded. Back up the SQLite database before migrating if those IDs are
needed for historical records. Existing clients must obtain a JWT before using
scheduling or user routes.

### Teacher replacement migration

Migration 0003 **discards every row in `timetables_teacher` and
`timetables_lesson`** and recreates the lesson table with `teacher_id` pointing
to the configured User table. User accounts, timetables, student groups,
subjects, and rooms are unaffected. Back up the SQLite database before
running `python manage.py migrate` if old teacher or lesson data might be
needed. Run `python manage.py bootstrap_accounts` afterward to create the
TEACHER group. To roll back, restore the database backup together with the
pre-migration application code; reversing the migration cannot recover the
discarded rows. Existing clients must use TEACHER user IDs in lesson payloads.

### Email-free user migration

Fresh databases need only `python manage.py migrate` followed by
`python manage.py bootstrap_accounts`. The active user table is `auth_user`,
without an email column. Registration and profile requests containing email
return HTTP 400, and account and teacher responses omit it.

For an existing SQLite database already migrated through `timetables.0003`,
stop all writers. With the new code and environment loaded, run
`python manage.py prepare_user_migration --backup path/to/backup.sqlite3`
before `python manage.py migrate`. The command checks the expected legacy
tables, columns, migration history, and foreign keys, creates a new backup,
and records the compatible custom user initial migration. It is safe to rerun
after that migration has been recorded. Run `python manage.py migrate`, then
`python manage.py bootstrap_accounts`, and restart the application. Existing
account IDs, password hashes, roles, permissions, and lesson references remain;
stored email values are discarded. To roll back, restore the backup together
with the previous application code. Reversing the email removal migration is
unsupported.

### Canonical username migration

Before deploying the username change, stop account writers and back up the
database. Inspect existing usernames using Django's NFKC normalization followed
by Unicode `casefold()`. Accounts that produce the same canonical name, or a
canonical name that fails the username syntax or 150-character limit, must be
renamed to distinct valid names. Run `python manage.py migrate`. Migration
`accounts.0003_canonical_usernames` preflights every account before changing
any row. If it finds a problem, it stops with `Cannot canonicalize usernames`
and reports each affected account ID and current username. Correct those rows
manually and rerun `python manage.py migrate`; the failed attempt changes no
usernames. Successful migration preserves account IDs, password hashes,
privileges, group memberships, and lesson references. Returned account and
teacher usernames use the canonical lowercase form. Future bulk imports that
bypass model saves must apply the same normalization and validation before
writing usernames. Restoring the old casing requires the database backup.

### Account format transition

Before deploying the new account rules to an existing database, stop account
writers and back up the database. Inspect usernames for spaces, punctuation,
or other characters outside Unicode letters, decimal digits, and underscores.
Inspect nonempty first and last names for digits, spaces, hyphens, apostrophes,
or other nonletters. Correct invalid values while preserving account IDs and
relationships; choose unique canonical usernames. Then run
`python manage.py migrate`. Migration `accounts.0005_account_name_preflight`
reports each invalid account ID and field and makes no account changes if any
are found. Correct the reported values and rerun migration. On success it
capitalizes valid nonempty names, leaves legacy empty names empty, and retains
password hashes, privileges, memberships, and lesson references. New passwords
are checked when set; existing hashes do not need conversion. Bulk database
writes bypass application validation, so validate imported account data before
writing it. Roll back with the matching application version and database backup.
