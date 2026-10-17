"""REST API contract tests for accounts and JWT authentication."""

import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


PASSWORD = "SecurePass1!"


class AccountAPITests(APITestCase):
    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_given_valid_mixed_case_username_when_registering_then_returns_canonical_account(self):
        # Given
        data = {"username": "ALICE", "password": PASSWORD, "first_name": " alice ", "last_name": " nowak "}

        # When
        response = self.client.post(reverse("register"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {
            "id": response.data["id"], "username": "alice", "first_name": "Alice", "last_name": "Nowak",
            "roles": ["VIEWER"],
        })
        self.assertTrue(get_user_model().objects.get(pk=response.data["id"]).check_password(PASSWORD))

    def test_given_existing_username_when_registering_different_case_then_returns_username_error(self):
        # Given
        get_user_model().objects.create_user("alice", PASSWORD, first_name="Alice", last_name="Nowak")
        data = {"username": "ALICE", "password": PASSWORD, "first_name": "Alice", "last_name": "Nowak"}

        # When
        response = self.client.post(reverse("register"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"username": ["A user with that username already exists."]})
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_given_invalid_password_when_registering_then_returns_password_error(self):
        # Given
        data = {"username": "alice", "password": "password", "first_name": "Alice", "last_name": "Nowak"}

        # When
        response = self.client.post(reverse("register"), data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_given_valid_uppercase_credentials_when_requesting_token_then_returns_token_pair(self):
        # Given
        get_user_model().objects.create_user("alice", PASSWORD)

        # When
        response = self.client.post(reverse("token_obtain_pair"), {"username": "ALICE", "password": PASSWORD}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"access", "refresh"})
        self.assertTrue(all(isinstance(value, str) and value for value in response.data.values()))

    def test_given_wrong_password_when_requesting_token_then_returns_authentication_error(self):
        # Given
        get_user_model().objects.create_user("alice", PASSWORD)

        # When
        response = self.client.post(reverse("token_obtain_pair"), {"username": "alice", "password": "WrongPass1!"}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "No active account found with the given credentials"})

    def test_given_refresh_token_when_refreshed_then_returns_new_access_token(self):
        # Given
        get_user_model().objects.create_user("alice", PASSWORD)
        token_response = self.client.post(reverse("token_obtain_pair"), {"username": "alice", "password": PASSWORD}, format="json")
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)

        # When
        response = self.client.post(reverse("token_refresh"), {"refresh": token_response.data["refresh"]}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"access"})
        self.assertTrue(response.data["access"])

    def test_given_own_account_when_patched_then_returns_updated_profile(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD, first_name="Alice", last_name="Nowak")
        self.authenticate(user)

        # When
        response = self.client.patch(f"/api/users/{user.pk}/", {"first_name": " alicja "}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": user.pk, "username": "alice", "first_name": "Alicja", "last_name": "Nowak", "roles": ["VIEWER"]})

    def test_given_other_account_when_patched_by_viewer_then_returns_forbidden(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD)
        other = get_user_model().objects.create_user("bob", PASSWORD)
        self.authenticate(user)

        # When
        response = self.client.patch(f"/api/users/{other.pk}/", {"first_name": "Robert"}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})
        other.refresh_from_db()
        self.assertEqual(other.first_name, "")

    def test_given_viewer_when_listing_users_then_returns_forbidden(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(user)

        # When
        response = self.client.get("/api/users/")

        # Then
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    def test_given_admin_and_viewer_when_assigning_roles_then_returns_combined_roles(self):
        # Given
        admin = get_user_model().objects.create_superuser("admin", PASSWORD)
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(admin)

        # When
        response = self.client.patch(f"/api/users/{user.pk}/role/", {"roles": ["PLANNER", "TEACHER"]}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"id": user.pk, "username": "alice", "first_name": "", "last_name": "", "roles": ["PLANNER", "TEACHER"]})

    def test_given_duplicate_roles_when_assigning_roles_then_returns_validation_error(self):
        # Given
        admin = get_user_model().objects.create_superuser("admin", PASSWORD)
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(admin)

        # When
        response = self.client.patch(f"/api/users/{user.pk}/role/", {"roles": ["TEACHER", "TEACHER"]}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"roles": ["Duplicate roles are not allowed."]})

    def test_given_legacy_or_missing_role_payload_when_assigning_roles_then_preserves_memberships(self):
        admin = get_user_model().objects.create_superuser("admin", PASSWORD)
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(admin)

        for payload in ({"role": "PLANNER"}, {"role": "PLANNER", "roles": ["TEACHER"]}, {}):
            with self.subTest(payload=payload):
                response = self.client.patch(f"/api/users/{user.pk}/role/", payload, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertFalse(user.groups.exists())

    def test_given_role_patch_schema_when_read_then_requires_roles_only(self):
        response = self.client.get("/api/schema/", HTTP_ACCEPT="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = json.loads(response.content)
        self.assertNotIn("role", schema["components"]["schemas"]["User"]["properties"])
        request_body = schema["paths"]["/api/users/{id}/role/"]["patch"]["requestBody"]
        self.assertTrue(request_body["required"])
        for content in request_body["content"].values():
            request_schema = content["schema"]
            self.assertEqual(request_schema["required"], ["roles"])
            self.assertEqual(set(request_schema["properties"]), {"roles"})

    def test_given_correct_current_password_when_changing_password_then_returns_empty_body(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(user)
        new_password = "AnotherPass2!"

        # When
        response = self.client.post(reverse("password_change"), {"current_password": PASSWORD, "new_password": new_password}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

    def test_given_wrong_current_password_when_changing_password_then_returns_field_error(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(user)

        # When
        response = self.client.post(reverse("password_change"), {"current_password": "WrongPass1!", "new_password": "AnotherPass2!"}, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"current_password": ["Incorrect password."]})
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))

    def test_given_own_account_when_deleted_then_returns_empty_body(self):
        # Given
        user = get_user_model().objects.create_user("alice", PASSWORD)
        self.authenticate(user)

        # When
        response = self.client.delete(f"/api/users/{user.pk}/")

        # Then
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(get_user_model().objects.filter(pk=user.pk).exists())

    def test_given_admin_account_when_deleted_then_returns_conflict(self):
        # Given
        admin = get_user_model().objects.create_superuser("admin", PASSWORD)
        self.authenticate(admin)

        # When
        response = self.client.delete(f"/api/users/{admin.pk}/")

        # Then
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {"detail": "ADMIN accounts cannot be deleted."})
        self.assertTrue(get_user_model().objects.filter(pk=admin.pk).exists())
