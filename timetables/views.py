from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from accounts.serializers import UserSerializer
from timetable_planner.pagination import CollectionPagination
from .models import Lesson, Room, StudentGroup, Subject, Timetable, ordered_lessons
from .permissions import SchedulingPermission
from .serializers import (
    LessonReadSerializer, LessonWriteSerializer, RoomSerializer, StudentGroupSerializer,
    SubjectSerializer, TimetableLessonsSerializer, TimetableSerializer,
)


def _paginate_and_respond(request, queryset, serializer_class, search_fields=None):
    if search_fields:
        search_filter = SearchFilter()
        class ViewWrapper:
            pass
        view = ViewWrapper()
        view.search_fields = search_fields
        queryset = search_filter.filter_queryset(request, queryset, view)

    paginator = CollectionPagination()
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)


# ----------------------------------------------------------------------
# Timetable Views
# ----------------------------------------------------------------------

@extend_schema(
    request=TimetableSerializer,
    responses={
        200: TimetableSerializer(many=True),
        201: TimetableSerializer,
    }
)
@api_view(['GET', 'POST'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def timetable_list_create_api(request):
    if request.method == 'GET':
        queryset = Timetable.objects.prefetch_related('lessons')
        return _paginate_and_respond(request, queryset, TimetableSerializer, search_fields=('name',))

    serializer = TimetableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=TimetableSerializer,
    responses={
        200: TimetableSerializer,
        404: OpenApiResponse(description='Timetable not found.'),
        409: OpenApiResponse(description='Related lessons prevent deletion.'),
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def timetable_detail_api(request, pk):
    timetable = get_object_or_404(Timetable.objects.prefetch_related('lessons'), pk=pk)

    if request.method == 'GET':
        return Response(TimetableSerializer(timetable).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = TimetableSerializer(timetable, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    try:
        timetable.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ProtectedError:
        return Response(
            {"detail": "Related lessons prevent deletion of this resource."},
            status=status.HTTP_409_CONFLICT,
        )


@extend_schema(
    responses={
        200: TimetableLessonsSerializer,
        401: OpenApiResponse(description='Authentication required.'),
        404: OpenApiResponse(description='Timetable not found.'),
    }
)
@api_view(['GET'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def timetable_lessons_api(request, pk):
    timetable = get_object_or_404(Timetable, pk=pk)
    lessons = ordered_lessons(
        Lesson.objects.filter(timetable=timetable)
        .select_related('timetable', 'student_group', 'subject', 'teacher', 'room')
        .prefetch_related('teacher__groups')
    )
    return Response({
        'id': timetable.pk,
        'name': timetable.name,
        'lessons': LessonReadSerializer(lessons, many=True).data,
    })


# ----------------------------------------------------------------------
# StudentGroup Views
# ----------------------------------------------------------------------

@extend_schema(
    request=StudentGroupSerializer,
    responses={
        200: StudentGroupSerializer(many=True),
        201: StudentGroupSerializer,
    }
)
@api_view(['GET', 'POST'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def student_group_list_create_api(request):
    if request.method == 'GET':
        queryset = StudentGroup.objects.all()
        return _paginate_and_respond(request, queryset, StudentGroupSerializer, search_fields=('name',))

    serializer = StudentGroupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=StudentGroupSerializer,
    responses={
        200: StudentGroupSerializer,
        404: OpenApiResponse(description='Student group not found.'),
        409: OpenApiResponse(description='Related lessons prevent deletion.'),
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def student_group_detail_api(request, pk):
    group = get_object_or_404(StudentGroup, pk=pk)

    if request.method == 'GET':
        return Response(StudentGroupSerializer(group).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = StudentGroupSerializer(group, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    try:
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ProtectedError:
        return Response(
            {"detail": "Related lessons prevent deletion of this resource."},
            status=status.HTTP_409_CONFLICT,
        )


# ----------------------------------------------------------------------
# Subject Views
# ----------------------------------------------------------------------

@extend_schema(
    request=SubjectSerializer,
    responses={
        200: SubjectSerializer(many=True),
        201: SubjectSerializer,
    }
)
@api_view(['GET', 'POST'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def subject_list_create_api(request):
    if request.method == 'GET':
        queryset = Subject.objects.all()
        return _paginate_and_respond(request, queryset, SubjectSerializer, search_fields=('name', 'description'))

    serializer = SubjectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=SubjectSerializer,
    responses={
        200: SubjectSerializer,
        404: OpenApiResponse(description='Subject not found.'),
        409: OpenApiResponse(description='Related lessons prevent deletion.'),
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def subject_detail_api(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'GET':
        return Response(SubjectSerializer(subject).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = SubjectSerializer(subject, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    try:
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ProtectedError:
        return Response(
            {"detail": "Related lessons prevent deletion of this resource."},
            status=status.HTTP_409_CONFLICT,
        )


# ----------------------------------------------------------------------
# Room Views
# ----------------------------------------------------------------------

@extend_schema(
    request=RoomSerializer,
    responses={
        200: RoomSerializer(many=True),
        201: RoomSerializer,
    }
)
@api_view(['GET', 'POST'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def room_list_create_api(request):
    if request.method == 'GET':
        queryset = Room.objects.all()
        return _paginate_and_respond(request, queryset, RoomSerializer, search_fields=('name',))

    serializer = RoomSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=RoomSerializer,
    responses={
        200: RoomSerializer,
        404: OpenApiResponse(description='Room not found.'),
        409: OpenApiResponse(description='Related lessons prevent deletion.'),
    }
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def room_detail_api(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'GET':
        return Response(RoomSerializer(room).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = RoomSerializer(room, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    try:
        room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ProtectedError:
        return Response(
            {"detail": "Related lessons prevent deletion of this resource."},
            status=status.HTTP_409_CONFLICT,
        )


# ----------------------------------------------------------------------
# Teacher Views (Read-Only)
# ----------------------------------------------------------------------

@extend_schema(
    responses={
        200: UserSerializer(many=True),
    }
)
@api_view(['GET'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def teacher_list_api(request):
    queryset = get_user_model().objects.filter(groups__name='TEACHER').distinct().order_by('pk')
    return _paginate_and_respond(request, queryset, UserSerializer, search_fields=('first_name', 'last_name'))


@extend_schema(
    responses={
        200: UserSerializer,
        404: OpenApiResponse(description='Teacher not found.'),
    }
)
@api_view(['GET'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def teacher_detail_api(request, pk):
    teacher = get_object_or_404(get_user_model().objects.filter(groups__name='TEACHER').distinct(), pk=pk)
    return Response(UserSerializer(teacher).data)


# ----------------------------------------------------------------------
# Lesson Views
# ----------------------------------------------------------------------

def get_optimized_lesson_queryset():
    return Lesson.objects.select_related(
        'timetable', 'student_group', 'subject', 'teacher', 'room'
    ).prefetch_related('teacher__groups')


@extend_schema(
    responses={
        200: LessonReadSerializer(many=True),
        201: LessonReadSerializer,
    },
    request=LessonWriteSerializer,
)
@api_view(['GET', 'POST'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def lesson_list_create_api(request):
    if request.method == 'GET':
        queryset = ordered_lessons(get_optimized_lesson_queryset())
        return _paginate_and_respond(request, queryset, LessonReadSerializer)

    serializer = LessonWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    lesson = serializer.save()
    refetched = get_optimized_lesson_queryset().get(pk=lesson.pk)
    return Response(LessonReadSerializer(refetched).data, status=status.HTTP_201_CREATED)


@extend_schema(
    responses={
        200: LessonReadSerializer,
        404: OpenApiResponse(description='Lesson not found.'),
        409: OpenApiResponse(description='Related records prevent deletion.'),
    },
    request=LessonWriteSerializer,
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([SchedulingPermission])
@renderer_classes([JSONRenderer])
def lesson_detail_api(request, pk):
    base_qs = get_optimized_lesson_queryset()
    lesson = get_object_or_404(base_qs, pk=pk)

    if request.method == 'GET':
        return Response(LessonReadSerializer(lesson).data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = LessonWriteSerializer(lesson, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        refetched = base_qs.get(pk=updated.pk)
        return Response(LessonReadSerializer(refetched).data)

    try:
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ProtectedError:
        return Response(
            {"detail": "Related lessons prevent deletion of this resource."},
            status=status.HTTP_409_CONFLICT,
        )


def unknown_api_route(request, path=""):
    return JsonResponse({"detail": "API endpoint not found."}, status=404)
