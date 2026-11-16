from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"timetables", views.TimetableViewSet, basename="timetable")
router.register(r"lessons", views.LessonViewSet, basename="lesson")
router.register(r"student-groups", views.StudentGroupViewSet, basename="studentgroup")
router.register(r"subjects", views.SubjectViewSet, basename="subject")
router.register(r"rooms", views.RoomViewSet, basename="room")
router.register(r"teachers", views.TeacherViewSet, basename="teacher")

urlpatterns = [
    path("summary/", views.SchedulingSummaryAPIView.as_view(), name="scheduling-summary"),
    path("", include(router.urls)),
    re_path(r"^.*$", views.unknown_api_route),
]
