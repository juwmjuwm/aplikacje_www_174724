from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Max, Min
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import UserSerializer
from timetable_planner.pagination import CollectionPagination
from .models import Lesson, Room, StudentGroup, Subject, Timetable, ordered_lessons
from .permissions import SchedulingPermission
from .serializers import (
    LessonListSerializer,
    LessonReadSerializer,
    LessonWriteSerializer,
    RoomSerializer,
    SchedulingSummarySerializer,
    StudentGroupSerializer,
    SubjectSerializer,
    TimetableClearLessonsSerializer,
    TimetableLessonsSerializer,
    TimetableSerializer,
)


def get_optimized_lesson_queryset():
    return Lesson.objects.select_related(
        'timetable', 'student_group', 'subject', 'teacher', 'room'
    ).prefetch_related('teacher__groups')


class ProtectedDeleteMixin:
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Related lessons prevent deletion of this resource."},
                status=status.HTTP_409_CONFLICT,
            )


class TimetableViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Timetable.objects.prefetch_related('lessons')
    serializer_class = TimetableSerializer
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination
    filter_backends = [SearchFilter]
    search_fields = ('name',)

    @extend_schema(
        responses={
            200: TimetableLessonsSerializer,
            401: OpenApiResponse(description='Authentication required.'),
            404: OpenApiResponse(description='Timetable not found.'),
        }
    )
    @action(detail=True, methods=['get'])
    def lessons(self, request, pk=None):
        timetable = self.get_object()
        lessons = ordered_lessons(
            get_optimized_lesson_queryset().filter(timetable=timetable)
        )
        return Response({
            'id': timetable.pk,
            'name': timetable.name,
            'lessons': LessonReadSerializer(lessons, many=True).data,
        })

    @extend_schema(
        request=None,
        responses={
            200: TimetableClearLessonsSerializer,
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='PLANNER or ADMIN role required.'),
            404: OpenApiResponse(description='Timetable not found.'),
        }
    )
    @action(detail=True, methods=['post'], url_path='clear-lessons')
    def clear_lessons(self, request, pk=None):
        timetable = self.get_object()
        with transaction.atomic():
            deleted_count, _ = timetable.lessons.all().delete()
        return Response({
            'id': timetable.pk,
            'name': timetable.name,
            'deleted_lessons_count': deleted_count,
        })


class StudentGroupViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = StudentGroup.objects.all()
    serializer_class = StudentGroupSerializer
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination
    filter_backends = [SearchFilter]
    search_fields = ('name',)


class SubjectViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination
    filter_backends = [SearchFilter]
    search_fields = ('name', 'description')


class RoomViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination
    filter_backends = [SearchFilter]
    search_fields = ('name',)


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        get_user_model()
        .objects.filter(groups__name='TEACHER')
        .prefetch_related('groups')
        .distinct()
        .order_by('pk')
    )
    serializer_class = UserSerializer
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination
    filter_backends = [SearchFilter]
    search_fields = ('first_name', 'last_name')


@extend_schema_view(
    create=extend_schema(
        request=LessonWriteSerializer,
        responses={201: LessonReadSerializer},
    ),
    update=extend_schema(
        request=LessonWriteSerializer,
        responses={200: LessonReadSerializer},
    ),
    partial_update=extend_schema(
        request=LessonWriteSerializer,
        responses={200: LessonReadSerializer},
    ),
)
class LessonViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    permission_classes = [SchedulingPermission]
    pagination_class = CollectionPagination

    def get_queryset(self):
        return ordered_lessons(get_optimized_lesson_queryset())

    def get_serializer_class(self):
        if self.action == 'list':
            return LessonListSerializer
        if self.action == 'retrieve':
            return LessonReadSerializer
        return LessonWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save()
        refetched = get_optimized_lesson_queryset().get(pk=lesson.pk)
        return Response(LessonReadSerializer(refetched).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        refetched = get_optimized_lesson_queryset().get(pk=updated.pk)
        return Response(LessonReadSerializer(refetched).data)


class SchedulingSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: SchedulingSummarySerializer,
            401: OpenApiResponse(description='Authentication required.'),
        }
    )
    def get(self, request):
        room_stats = Room.objects.aggregate(
            rooms_count=Count('id'),
            min_room_capacity=Min('capacity'),
            max_room_capacity=Max('capacity'),
            average_room_capacity=Avg('capacity'),
        )
        avg_capacity = room_stats['average_room_capacity']
        return Response({
            'timetables_count': Timetable.objects.aggregate(count=Count('id'))['count'],
            'lessons_count': Lesson.objects.aggregate(count=Count('id'))['count'],
            'student_groups_count': StudentGroup.objects.aggregate(count=Count('id'))['count'],
            'subjects_count': Subject.objects.aggregate(count=Count('id'))['count'],
            'rooms_count': room_stats['rooms_count'],
            'teachers_count': get_user_model().objects.filter(groups__name='TEACHER').aggregate(
                count=Count('id', distinct=True)
            )['count'],
            'min_room_capacity': room_stats['min_room_capacity'] or 0,
            'max_room_capacity': room_stats['max_room_capacity'] or 0,
            'average_room_capacity': round(avg_capacity, 2) if avg_capacity is not None else 0.0,
        })


def unknown_api_route(request, path=""):
    return JsonResponse({"detail": "API endpoint not found."}, status=404)
