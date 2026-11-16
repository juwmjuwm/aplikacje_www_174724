from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, renderer_classes, schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, OpenApiResponse

from timetable_planner.pagination import CollectionPagination
from .models import lock_teacher_assignment
from .permissions import IsAdmin, IsSelfOrAdmin, user_roles
from .serializers import (
    PasswordChangeSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ROLE_REQUEST_SCHEMA,
    RoleSerializer,
    UserSerializer,
    username_conflict,
)

User = get_user_model()


class RequiredRoleSchema(AutoSchema):
    def _get_request_body(self, direction='request'):
        body = super()._get_request_body(direction)
        body['required'] = True
        return body


@extend_schema(
    request=RegisterSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(description='Invalid registration fields or username conflict.'),
    },
    auth=[],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            user = serializer.save()
    except IntegrityError as exc:
        if not username_conflict(exc):
            raise
        raise serializers.ValidationError({'username': ['A user with that username already exists.']}) from exc
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    request=PasswordChangeSerializer,
    responses={
        204: None,
        400: OpenApiResponse(description='Invalid password change request.'),
        401: OpenApiResponse(description='Authentication required.'),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def password_change_api(request):
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save(update_fields=['password'])
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    responses={
        200: UserSerializer(many=True),
        401: OpenApiResponse(description='Authentication required.'),
        403: OpenApiResponse(description='ADMIN role required.'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
@renderer_classes([JSONRenderer])
def user_list_api(request):
    queryset = User.objects.prefetch_related('groups').order_by('pk')
    paginator = CollectionPagination()
    page = paginator.paginate_queryset(queryset, request)
    if page is not None:
        serializer = UserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = UserSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Authentication required.'),
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def user_me_api(request):
    user = User.objects.prefetch_related('groups').get(pk=request.user.pk)
    return Response(UserSerializer(user).data)


@extend_schema(
    methods=['GET'],
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Authentication required.'),
        403: OpenApiResponse(description='Account access denied.'),
        404: OpenApiResponse(description='User not found.'),
    },
)
@extend_schema(
    methods=['PATCH'],
    request=ProfileSerializer,
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Invalid profile fields or username conflict.'),
        401: OpenApiResponse(description='Authentication required.'),
        403: OpenApiResponse(description='Account access denied.'),
        404: OpenApiResponse(description='User not found.'),
    },
)
@extend_schema(
    methods=['DELETE'],
    responses={
        204: None,
        401: OpenApiResponse(description='Authentication required.'),
        403: OpenApiResponse(description='Account access denied.'),
        404: OpenApiResponse(description='User not found.'),
        409: OpenApiResponse(description='Account cannot be deleted.'),
    },
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer])
def user_detail_api(request, pk):
    user = get_object_or_404(User.objects.prefetch_related('groups'), pk=pk)
    if not IsSelfOrAdmin().has_object_permission(request, None, user):
        raise PermissionDenied()

    if request.method == 'GET':
        return Response(UserSerializer(user).data)

    if request.method == 'PATCH':
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            if not username_conflict(exc):
                raise
            raise serializers.ValidationError({'username': ['A user with that username already exists.']}) from exc
        return Response(UserSerializer(user).data)

    try:
        with transaction.atomic():
            lock_teacher_assignment(pk)
            locked_user = User.objects.select_for_update().get(pk=pk)
            if locked_user.is_superuser:
                return Response({'detail': 'ADMIN accounts cannot be deleted.'}, status=status.HTTP_409_CONFLICT)
            if locked_user.lessons.exists():
                return Response(
                    {'detail': "Reassign or delete this teacher's lessons before deleting the account."},
                    status=status.HTTP_409_CONFLICT,
                )
            locked_user.delete()
    except ProtectedError:
        return Response({'detail': 'Related lessons prevent deletion of this account.'}, status=status.HTTP_409_CONFLICT)
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    request={media_type: ROLE_REQUEST_SCHEMA for media_type in (
        'application/json', 'application/x-www-form-urlencoded', 'multipart/form-data',
    )},
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description='Invalid role selection.'),
        401: OpenApiResponse(description='Authentication required.'),
        403: OpenApiResponse(description='ADMIN role required.'),
        404: OpenApiResponse(description='User not found.'),
        409: OpenApiResponse(description='Role transition conflicts with account or lesson assignments.'),
    },
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
@renderer_classes([JSONRenderer])
@schema(RequiredRoleSchema())
def user_role_api(request, pk):
    get_object_or_404(User.objects.prefetch_related('groups'), pk=pk)
    serializer = RoleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        lock_teacher_assignment(pk)
        user = User.objects.select_for_update().get(pk=pk)
        if user.is_superuser:
            return Response({'detail': 'ADMIN role cannot be changed.'}, status=status.HTTP_409_CONFLICT)
        current_roles = set(user_roles(user))
        target_roles = set(serializer.validated_data['roles'])
        if 'TEACHER' in current_roles and 'TEACHER' not in target_roles and user.lessons.exists():
            return Response(
                {'detail': "Reassign or delete this teacher's lessons before removing TEACHER."},
                status=status.HTTP_409_CONFLICT,
            )
        planner, _ = Group.objects.get_or_create(name='PLANNER')
        teacher, _ = Group.objects.get_or_create(name='TEACHER')
        if 'PLANNER' in target_roles:
            user.groups.add(planner)
        else:
            user.groups.remove(planner)
        if 'TEACHER' in target_roles:
            user.groups.add(teacher)
        else:
            user.groups.remove(teacher)
    user = User.objects.prefetch_related('groups').get(pk=pk)
    return Response(UserSerializer(user).data)
