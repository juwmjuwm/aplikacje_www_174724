from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, connection
from rest_framework import serializers

from .models import Lesson, Room, StudentGroup, Subject, Teacher, Timetable


class TimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = ("id", "name", "owner", "description")
        read_only_fields = ("id",)


class StudentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroup
        fields = ("id", "name", "size")
        read_only_fields = ("id",)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name", "description")
        read_only_fields = ("id",)


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ("id", "first_name", "last_name", "academic_title", "email")
        read_only_fields = ("id",)


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "name", "capacity")
        read_only_fields = ("id",)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            "id", "timetable", "student_group", "subject", "teacher", "room",
            "weekday", "start_time", "end_time",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except (DjangoValidationError, IntegrityError) as exc:
            self._raise_api_validation_error(exc)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except (DjangoValidationError, IntegrityError) as exc:
            self._raise_api_validation_error(exc)

    @staticmethod
    def _raise_api_validation_error(exc):
        if isinstance(exc, DjangoValidationError):
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict) from exc
            raise serializers.ValidationError({"non_field_errors": exc.messages}) from exc

        known_trigger_messages = {
            "End time must be later than start time.",
            "Lesson resource is already booked for this time.",
        }
        if connection.vendor == "sqlite" and str(exc) in known_trigger_messages:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc
        raise exc
