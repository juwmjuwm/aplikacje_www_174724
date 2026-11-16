from django.urls import path, re_path

from . import views

urlpatterns = [
    path("timetables/", views.timetable_list_create_api, name="timetable-list"),
    path("timetables/<int:pk>/", views.timetable_detail_api, name="timetable-detail"),
    path("timetables/<int:pk>/lessons/", views.timetable_lessons_api, name="timetable-lessons"),
    path("lessons/", views.lesson_list_create_api, name="lesson-list"),
    path("lessons/<int:pk>/", views.lesson_detail_api, name="lesson-detail"),
    path("student-groups/", views.student_group_list_create_api, name="studentgroup-list"),
    path("student-groups/<int:pk>/", views.student_group_detail_api, name="studentgroup-detail"),
    path("subjects/", views.subject_list_create_api, name="subject-list"),
    path("subjects/<int:pk>/", views.subject_detail_api, name="subject-detail"),
    path("rooms/", views.room_list_create_api, name="room-list"),
    path("rooms/<int:pk>/", views.room_detail_api, name="room-detail"),
    path("teachers/", views.teacher_list_api, name="teacher-list"),
    path("teachers/<int:pk>/", views.teacher_detail_api, name="teacher-detail"),
    re_path(r"^.*$", views.unknown_api_route),
]
