from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from .accounts import UserSerializer
from .models import Lesson, Room, StudentGroup, Subject, Timetable
from .pagination import CollectionPagination
from .permissions import SchedulingPermission
from .serializers import (
    LessonSerializer, RoomSerializer, StudentGroupSerializer,
    SubjectSerializer, TimetableSerializer,
)


class JsonModelViewSet(viewsets.ModelViewSet):
    renderer_classes = (JSONRenderer,)
    permission_classes = (SchedulingPermission,)
    pagination_class = CollectionPagination

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
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class StudentGroupViewSet(JsonModelViewSet):
    queryset = StudentGroup.objects.all()
    serializer_class = StudentGroupSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class SubjectViewSet(JsonModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name', 'description')


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.filter(groups__name='TEACHER').distinct().order_by('pk')
    serializer_class = UserSerializer
    renderer_classes = (JSONRenderer,)
    permission_classes = (SchedulingPermission,)
    pagination_class = CollectionPagination
    filter_backends = (SearchFilter,)
    search_fields = ('first_name', 'last_name')


class RoomViewSet(JsonModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class LessonViewSet(JsonModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


def unknown_api_route(request, path=""):
    return JsonResponse({"detail": "API endpoint not found."}, status=404)
