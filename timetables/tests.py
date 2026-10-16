"""REST API contract tests for scheduling resources."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Lesson, Room, StudentGroup, Subject, Timetable


def api_reverse(name, args=None):
    """Resolve a scheduling route under the canonical /api/ prefix."""
    return reverse(name, args=args).replace("/timetables/", "/api/", 1)


class SchedulingAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.planner = user_model.objects.create_user("planner", "SecurePass1!", first_name="Pat", last_name="Plan")
        cls.teacher = user_model.objects.create_user("teacher", "SecurePass1!", first_name="Tina", last_name="Nowak")
        cls.viewer = user_model.objects.create_user("viewer", "SecurePass1!", first_name="Vera", last_name="View")
        cls.admin = user_model.objects.create_superuser("admin", "SecurePass1!", first_name="Ada", last_name="Admin")
        planner_group = Group.objects.create(name="PLANNER")
        teacher_group = Group.objects.create(name="TEACHER")
        cls.planner.groups.add(planner_group)
        cls.teacher.groups.add(teacher_group)

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def make_lesson_data(self, **changes):
        timetable = Timetable.objects.create(name="Autumn")
        group = StudentGroup.objects.create(name="Class A", size=20)
        subject = Subject.objects.create(name="Math")
        room = Room.objects.create(name="101", capacity=30)
        data = {
            "timetable": timetable.pk,
            "student_group": group.pk,
            "subject": subject.pk,
            "teacher": self.teacher.pk,
            "room": room.pk,
            "weekday": "MON",
            "start_time": "09:00:00",
            "end_time": "10:00:00",
        }
        data.update(changes)
        return data

    def test_given_planner_and_valid_room_when_created_then_returns_room_body(self):
        # Given
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("room-list"), {"name": "Lab", "capacity": 25}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"id": response.data["id"], "name": "Lab", "capacity": 25})
        self.assertTrue(Room.objects.filter(pk=response.data["id"]).exists())

    def test_given_planner_and_group_when_created_then_returns_group_body(self):
        # Given
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("studentgroup-list"), {"name": "Class A", "size": 20}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"id": response.data["id"], "name": "Class A", "size": 20})
        self.assertTrue(StudentGroup.objects.filter(pk=response.data["id"]).exists())

    def test_given_planner_and_timetable_when_created_then_returns_ownerless_body(self):
        # Given
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("timetable-list"), {"name": "Autumn"}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"id": response.data["id"], "name": "Autumn", "description": ""})
        self.assertTrue(Timetable.objects.filter(pk=response.data["id"]).exists())

    def test_given_room_when_retrieved_then_returns_its_body(self):
        # Given
        room = Room.objects.create(name="Lab", capacity=25)
        self.authenticate(self.viewer)

        # When
        response = self.client.get(api_reverse("room-detail", args=[room.pk]))

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": room.pk, "name": "Lab", "capacity": 25})

    def test_given_rooms_when_listed_with_page_size_then_returns_paginated_body(self):
        # Given
        Room.objects.bulk_create([Room(name=f"Room {number:02}", capacity=20) for number in range(3)])
        self.authenticate(self.viewer)

        # When
        response = self.client.get(api_reverse("room-list"), {"size": 2, "page": 2})

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertIsNone(response.data["next"])
        self.assertIn("size=2", response.data["previous"])
        self.assertEqual(response.data["results"], [{"id": Room.objects.get(name="Room 02").pk, "name": "Room 02", "capacity": 20}])

    def test_given_invalid_page_size_when_listing_rooms_then_returns_field_error(self):
        # Given
        self.authenticate(self.viewer)

        # When
        response = self.client.get(api_reverse("room-list"), {"size": 0})

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"size": ["Enter a positive integer."]})

    def test_given_subject_description_when_searched_then_returns_only_match(self):
        # Given
        match = Subject.objects.create(name="Science", description="Intro to Biology")
        Subject.objects.create(name="History")
        self.authenticate(self.viewer)

        # When
        response = self.client.get(api_reverse("subject-list"), {"search": "biology"})

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"count": 1, "next": None, "previous": None, "results": [
            {"id": match.pk, "name": "Science", "description": "Intro to Biology"},
        ]})

    def test_given_teacher_and_viewer_when_listing_teachers_then_returns_teacher_only(self):
        # Given
        self.authenticate(self.viewer)

        # When
        response = self.client.get("/api/teachers/")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"count": 1, "next": None, "previous": None, "results": [
            {"id": self.teacher.pk, "username": "teacher", "first_name": "Tina", "last_name": "Nowak", "role": "TEACHER", "roles": ["TEACHER"]},
        ]})

    def test_given_teacher_directory_when_posted_to_then_returns_method_error(self):
        # Given
        self.authenticate(self.planner)

        # When
        response = self.client.post("/api/teachers/", {"name": "Other"}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, {"detail": 'Method "POST" not allowed.'})

    def test_given_viewer_when_creating_room_then_returns_forbidden(self):
        # Given
        self.authenticate(self.viewer)

        # When
        response = self.client.post(api_reverse("room-list"), {"name": "Lab", "capacity": 25}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})
        self.assertEqual(Room.objects.count(), 0)

    def test_given_no_token_when_listing_rooms_then_returns_unauthorized(self):
        # Given
        Room.objects.create(name="Lab", capacity=25)

        # When
        response = self.client.get(api_reverse("room-list"))

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_given_planner_and_room_when_patched_then_returns_updated_body(self):
        # Given
        room = Room.objects.create(name="Lab", capacity=25)
        self.authenticate(self.planner)

        # When
        response = self.client.patch(api_reverse("room-detail", args=[room.pk]), {"capacity": 30}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": room.pk, "name": "Lab", "capacity": 30})

    def test_given_room_when_fully_updated_by_planner_then_returns_replacement_body(self):
        # Given
        room = Room.objects.create(name="Lab", capacity=25)
        self.authenticate(self.planner)

        # When
        response = self.client.put(api_reverse("room-detail", args=[room.pk]), {"name": "Lecture", "capacity": 40}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": room.pk, "name": "Lecture", "capacity": 40})

    def test_given_room_when_deleted_by_planner_then_returns_empty_body(self):
        # Given
        room = Room.objects.create(name="Lab", capacity=25)
        self.authenticate(self.planner)

        # When
        response = self.client.delete(api_reverse("room-detail", args=[room.pk]))

        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Room.objects.filter(pk=room.pk).exists())

    def test_given_missing_room_when_retrieved_then_returns_not_found(self):
        # Given
        self.authenticate(self.viewer)

        # When
        response = self.client.get(api_reverse("room-detail", args=[999]))

        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "No Room matches the given query."})

    def test_given_unknown_api_path_when_requested_then_returns_json_error(self):
        # Given
        self.authenticate(self.viewer)

        # When
        response = self.client.get("/api/no-such-resource/")

        # Then
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json(), {"detail": "API endpoint not found."})

    def test_given_valid_relationships_when_creating_lesson_then_returns_ids(self):
        # Given
        data = self.make_lesson_data()
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("lesson-list"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"id": response.data["id"], **data})
        self.assertEqual(Lesson.objects.count(), 1)

    def test_given_lesson_when_retrieved_then_returns_relationship_ids(self):
        # Given
        data = self.make_lesson_data()
        self.authenticate(self.planner)
        created = self.client.post(api_reverse("lesson-list"), data, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        # When
        response = self.client.get(api_reverse("lesson-detail", args=[created.data["id"]]))

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, created.data)

    def test_given_invalid_interval_when_creating_lesson_then_returns_field_error(self):
        # Given
        data = self.make_lesson_data(end_time="09:00:00")
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("lesson-list"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"end_time": ["End time must be later than start time."]})
        self.assertEqual(Lesson.objects.count(), 0)

    def test_given_non_teacher_id_when_creating_lesson_then_returns_teacher_error(self):
        # Given
        data = self.make_lesson_data(teacher=self.viewer.pk)
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("lesson-list"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("teacher", response.data)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_given_booked_room_when_creating_overlapping_lesson_then_returns_conflict_field(self):
        # Given
        data = self.make_lesson_data()
        self.authenticate(self.planner)
        first = self.client.post(api_reverse("lesson-list"), data, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        other_group = StudentGroup.objects.create(name="Class B", size=20)
        other_teacher = get_user_model().objects.create_user("teacher2", "SecurePass1!", first_name="Tom", last_name="Tutor")
        other_teacher.groups.add(Group.objects.get(name="TEACHER"))
        data.update(student_group=other_group.pk, teacher=other_teacher.pk, start_time="09:30:00", end_time="10:30:00")

        # When
        response = self.client.post(api_reverse("lesson-list"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"room": ["Room is already booked for this time."]})
        self.assertEqual(Lesson.objects.count(), 1)

    def test_given_room_used_by_lesson_when_deleted_then_returns_conflict(self):
        # Given
        data = self.make_lesson_data()
        self.authenticate(self.planner)
        self.assertEqual(self.client.post(api_reverse("lesson-list"), data, format="json").status_code, status.HTTP_201_CREATED)

        # When
        response = self.client.delete(api_reverse("room-detail", args=[data["room"]]))

        # Then
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {"detail": "Related lessons prevent deletion of this resource."})

    def test_given_owner_field_when_creating_timetable_then_returns_field_error(self):
        # Given
        self.authenticate(self.planner)

        # When
        response = self.client.post(api_reverse("timetable-list"), {"name": "Autumn", "owner": self.planner.pk}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"owner": ["This field is not allowed."]})
        self.assertEqual(Timetable.objects.count(), 0)

