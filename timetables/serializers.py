from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from rest_framework import serializers

from .accounts import UserSerializer
from .models import Lesson, Room, StudentGroup, Subject, Timetable


class TimetableSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if 'owner' in data:
            raise serializers.ValidationError({'owner': ['This field is not allowed.']})
        return super().to_internal_value(data)

    class Meta:
        model = Timetable
        fields = ("id", "name", "description")
        read_only_fields = ("id",)


class StudentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroup
        fields = ("id", "name", "size")
        read_only_fields = ("id",)

    def create(self, validated_data):
        return save_with_model_validation(super().create, validated_data)

    def update(self, instance, validated_data):
        return save_with_model_validation(super().update, instance, validated_data)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name", "description")
        read_only_fields = ("id",)


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ("id", "name", "capacity")
        read_only_fields = ("id",)

    def create(self, validated_data):
        return save_with_model_validation(super().create, validated_data)

    def update(self, instance, validated_data):
        return save_with_model_validation(super().update, instance, validated_data)


CAPACITY_TRIGGER_FIELDS = {
    "Lesson room capacity exceeded.": "room",
    "Student group exceeds assigned room capacity.": "size",
    "Room capacity below assigned group size.": "capacity",
}


def save_with_model_validation(save, *args):
    try:
        return save(*args)
    except DjangoValidationError as exc:
        if hasattr(exc, "message_dict"):
            raise serializers.ValidationError(exc.message_dict) from exc
        raise serializers.ValidationError({"non_field_errors": exc.messages}) from exc
    except IntegrityError as exc:
        if connection.vendor == "sqlite" and str(exc) in CAPACITY_TRIGGER_FIELDS:
            raise serializers.ValidationError({CAPACITY_TRIGGER_FIELDS[str(exc)]: [str(exc)]}) from exc
        if connection.vendor == "sqlite" and str(exc) in {
            "End time must be later than start time.",
            "Lesson resource is already booked for this time.",
        }:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc
        raise


class LessonWriteSerializer(serializers.ModelSerializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.filter(
        groups__name='TEACHER',
    ).distinct())
    class Meta:
        model = Lesson
        fields = (
            "id", "timetable", "student_group", "subject", "teacher", "room",
            "weekday", "start_time", "end_time",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        return save_with_model_validation(super().create, validated_data)

    def update(self, instance, validated_data):
        return save_with_model_validation(super().update, instance, validated_data)


class LessonReadSerializer(serializers.ModelSerializer):
    timetable = TimetableSerializer(read_only=True)
    student_group = StudentGroupSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = (
            "id", "timetable", "student_group", "subject", "teacher", "room",
            "weekday", "start_time", "end_time",
        )


class TimetableLessonsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    lessons = LessonReadSerializer(many=True, read_only=True)
