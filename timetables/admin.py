from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Lesson, Room, StudentGroup, Subject, Timetable

User = get_user_model()


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "size")
    search_fields = ("name",)
    list_filter = ("size",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)
    list_filter = ("capacity",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'teacher':
            kwargs['queryset'] = User.objects.filter(groups__name='TEACHER').distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ("subject", "timetable", "weekday", "start_time", "end_time", "room", "teacher", "student_group")
    search_fields = (
        "subject__name", "timetable__name", "room__name",
        "teacher__username", "student_group__name",
    )
    list_filter = ("weekday", "room", "teacher", "student_group", "timetable")
    list_select_related = ("subject", "timetable", "room", "teacher", "student_group")
