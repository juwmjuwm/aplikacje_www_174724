from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from rest_framework import status, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .models import Lesson, Room, StudentGroup, Subject, Teacher, Timetable
from .permissions import SchedulingPermission
from .serializers import (
    LessonSerializer, RoomSerializer, StudentGroupSerializer,
    SubjectSerializer, TeacherSerializer, TimetableSerializer,
)


class JsonModelViewSet(viewsets.ModelViewSet):
    renderer_classes = (JSONRenderer,)
    permission_classes = (SchedulingPermission,)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Related lessons prevent deletion of this resource."},
                status=status.HTTP_409_CONFLICT,
            )


class TimetableViewSet(JsonModelViewSet):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer


class StudentGroupViewSet(JsonModelViewSet):
    queryset = StudentGroup.objects.all()
    serializer_class = StudentGroupSerializer


class SubjectViewSet(JsonModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class TeacherViewSet(JsonModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer


class RoomViewSet(JsonModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class LessonViewSet(JsonModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


def unknown_api_route(request, path=""):
    return JsonResponse({"detail": "API endpoint not found."}, status=404)
