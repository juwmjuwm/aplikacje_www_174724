from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse, JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .accounts import UserSerializer
from .models import Lesson, Room, StudentGroup, Subject, Timetable, ordered_lessons
from .pagination import CollectionPagination
from .permissions import SchedulingPermission
from .serializers import (
    LessonReadSerializer, LessonWriteSerializer, RoomSerializer, StudentGroupSerializer,
    SubjectSerializer, TimetableLessonsSerializer, TimetableSerializer,
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

    @extend_schema(
        responses={200: TimetableLessonsSerializer, 401: OpenApiResponse(description='Authentication required.'),
                   404: OpenApiResponse(description='Timetable not found.')},
    )
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        timetable = self.get_object()
        lessons = ordered_lessons(Lesson.objects.filter(timetable=timetable).select_related(
            'timetable', 'student_group', 'subject', 'teacher', 'room',
        ).prefetch_related('teacher__groups'))
        return Response({'id': timetable.pk, 'name': timetable.name,
                         'lessons': LessonReadSerializer(lessons, many=True).data})


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


@extend_schema_view(
    list=extend_schema(description='BREAKING response contract: lesson relationships are expanded objects.', responses=LessonReadSerializer(many=True)),
    retrieve=extend_schema(description='BREAKING response contract: lesson relationships are expanded objects.', responses=LessonReadSerializer),
    create=extend_schema(description='Accept relationship IDs; return expanded related objects (BREAKING response contract).', request=LessonWriteSerializer, responses={201: LessonReadSerializer}),
    update=extend_schema(description='Accept relationship IDs; return expanded related objects (BREAKING response contract).', request=LessonWriteSerializer, responses=LessonReadSerializer),
    partial_update=extend_schema(description='Accept relationship IDs; return expanded related objects (BREAKING response contract).', request=LessonWriteSerializer, responses=LessonReadSerializer),
)
class LessonViewSet(JsonModelViewSet):
    queryset = Lesson.objects.select_related(
        'timetable', 'student_group', 'subject', 'teacher', 'room',
    ).prefetch_related('teacher__groups')
    serializer_class = LessonReadSerializer

    def get_queryset(self):
        return ordered_lessons(super().get_queryset())

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return LessonWriteSerializer
        return LessonReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(LessonReadSerializer(lesson).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        lesson = self.get_object()
        serializer = self.get_serializer(lesson, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        return Response(LessonReadSerializer(lesson).data)


def unknown_api_route(request, path=""):
    return JsonResponse({"detail": "API endpoint not found."}, status=404)
