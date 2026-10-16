from django.contrib import admin

from .models import Lesson, Room, StudentGroup, Subject, Teacher, Timetable


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("name", "owner")
    search_fields = ("name", "owner__username")
    list_filter = ("owner",)


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "size")
    search_fields = ("name",)
    list_filter = ("size",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "academic_title", "email")
    search_fields = ("first_name", "last_name", "academic_title", "email")
    list_filter = ("academic_title",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)
    list_filter = ("capacity",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("subject", "timetable", "weekday", "start_time", "end_time", "room", "teacher", "student_group")
    search_fields = (
        "subject__name", "timetable__name", "room__name",
        "teacher__first_name", "teacher__last_name", "student_group__name",
    )
    list_filter = ("weekday", "room", "teacher", "student_group", "timetable")
    list_select_related = ("subject", "timetable", "room", "teacher", "student_group")
