import datetime
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection
from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Lesson, Room, StudentGroup, Subject, Timetable


class TimetableSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)

    def to_internal_value(self, data):
        if 'owner' in data:
            raise serializers.ValidationError({'owner': ['This field is not allowed.']})
        return super().to_internal_value(data)

    class Meta:
        model = Timetable
        fields = ("id", "name", "description", "lessons_count")
        read_only_fields = ("id", "lessons_count")


class StudentGroupSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)

    class Meta:
        model = StudentGroup
        fields = ("id", "name", "size", "lessons_count")
        read_only_fields = ("id", "lessons_count")

    def create(self, validated_data):
        return save_with_model_validation(super().create, validated_data)

    def update(self, instance, validated_data):
        return save_with_model_validation(super().update, instance, validated_data)


class SubjectSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)

    class Meta:
        model = Subject
        fields = ("id", "name", "description", "lessons_count")
        read_only_fields = ("id", "lessons_count")


class RoomSerializer(serializers.ModelSerializer):
    lessons_count = serializers.IntegerField(source="lessons.count", read_only=True)

    class Meta:
        model = Room
        fields = ("id", "name", "capacity", "lessons_count")
        read_only_fields = ("id", "lessons_count")

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

    def validate_start_time(self, value):
        if value < datetime.time(7, 0) or value > datetime.time(21, 0):
            raise serializers.ValidationError("Start time must be within operational hours (07:00 to 21:00).")
        return value

    def validate_end_time(self, value):
        if value < datetime.time(7, 0) or value > datetime.time(21, 0):
            raise serializers.ValidationError("End time must be within operational hours (07:00 to 21:00).")
        return value

    def validate(self, attrs):
        def get_field(name):
            if name in attrs:
                return attrs[name]
            if self.instance is not None:
                return getattr(self.instance, name)
            return None

        student_group = get_field('student_group')
        teacher = get_field('teacher')
        room = get_field('room')
        weekday = get_field('weekday')
        start_time = get_field('start_time')
        end_time = get_field('end_time')

        errors = {}

        # 1. Interval order and duration constraints
        if start_time is not None and end_time is not None:
            if end_time <= start_time:
                errors['end_time'] = "End time must be later than start time."
            else:
                start_min = start_time.hour * 60 + start_time.minute
                end_min = end_time.hour * 60 + end_time.minute
                duration = end_min - start_min
                if duration < 30 or duration > 240:
                    errors['non_field_errors'] = "Lesson duration must be between 30 and 240 minutes."

        # 2. Capacity constraints
        if student_group is not None and room is not None:
            if student_group.size > room.capacity:
                errors['room'] = "Room capacity is smaller than the student group size."

        # 3. Teacher role verification
        if teacher is not None:
            from .permissions import user_roles
            if 'TEACHER' not in user_roles(teacher):
                errors['teacher'] = "Teacher must have the TEACHER role."

        # 4. Schedule collision detection (only if no interval error)
        if 'end_time' not in errors and weekday and start_time and end_time:
            candidates = Lesson.objects.filter(
                weekday=weekday,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )
            if self.instance is not None and self.instance.pk:
                candidates = candidates.exclude(pk=self.instance.pk)

            for resource, field, label in [
                (room, 'room', 'Room'),
                (teacher, 'teacher', 'Teacher'),
                (student_group, 'student_group', 'Student group'),
            ]:
                if resource is not None and candidates.filter(**{f"{field}_id": resource.pk}).exists():
                    errors[field] = f"{label} is already booked for this time."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

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

    timetable_name = serializers.ReadOnlyField(source="timetable.name")
    student_group_name = serializers.ReadOnlyField(source="student_group.name")
    subject_name = serializers.ReadOnlyField(source="subject.name")
    room_name = serializers.ReadOnlyField(source="room.name")
    teacher_username = serializers.ReadOnlyField(source="teacher.username")
    duration_minutes = serializers.SerializerMethodField()
    room_utilization_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id", "timetable", "student_group", "subject", "teacher", "room",
            "weekday", "start_time", "end_time",
            "timetable_name", "student_group_name", "subject_name", "room_name", "teacher_username",
            "duration_minutes", "room_utilization_percentage",
        )

    def get_duration_minutes(self, obj) -> int | None:
        if obj.start_time is None or obj.end_time is None:
            return None
        start_minutes = obj.start_time.hour * 60 + obj.start_time.minute
        end_minutes = obj.end_time.hour * 60 + obj.end_time.minute
        return end_minutes - start_minutes

    def get_room_utilization_percentage(self, obj) -> float | None:
        if not obj.student_group or not obj.room or not obj.room.capacity:
            return None
        return round((obj.student_group.size / obj.room.capacity) * 100.0, 1)


class TimetableLessonsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    lessons = LessonReadSerializer(many=True, read_only=True)
