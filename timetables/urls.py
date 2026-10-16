from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("timetables", views.TimetableViewSet)
router.register("lessons", views.LessonViewSet)
router.register("student-groups", views.StudentGroupViewSet)
router.register("subjects", views.SubjectViewSet)
router.register("teachers", views.TeacherViewSet)
router.register("rooms", views.RoomViewSet)

urlpatterns = [
    path("", include(router.urls)),
    re_path(r"^.*$", views.unknown_api_route),
]
