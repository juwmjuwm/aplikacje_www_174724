from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Invalid registration fields or username conflict.'),
        },
        auth=[],
    )
    def post(self, request):
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


@extend_schema_view(
    list=extend_schema(
        responses={
            200: UserSerializer(many=True),
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='ADMIN role required.'),
        },
    ),
    create=extend_schema(exclude=True),
    retrieve=extend_schema(
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='Account access denied.'),
            404: OpenApiResponse(description='User not found.'),
        },
    ),
    partial_update=extend_schema(
        request=ProfileSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Invalid profile fields or username conflict.'),
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='Account access denied.'),
            404: OpenApiResponse(description='User not found.'),
        },
    ),
    destroy=extend_schema(
        responses={
            204: None,
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='Account access denied.'),
            404: OpenApiResponse(description='User not found.'),
            409: OpenApiResponse(description='Account cannot be deleted.'),
        },
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related('groups').order_by('pk')
    pagination_class = CollectionPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ('list', 'role', 'create'):
            return [IsAuthenticated(), IsAdmin()]
        if self.action in ('retrieve', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSelfOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return ProfileSerializer
        if self.action == 'change_password':
            return PasswordChangeSerializer
        if self.action == 'role':
            return RoleSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError as exc:
            if not username_conflict(exc):
                raise
            raise serializers.ValidationError({'username': ['A user with that username already exists.']}) from exc
        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        pk = user.pk
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
            return Response(
                {'detail': 'Related lessons prevent deletion of this account.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description='Authentication required.'),
        },
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        user = User.objects.prefetch_related('groups').get(pk=request.user.pk)
        return Response(UserSerializer(user).data)

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={
            204: None,
            400: OpenApiResponse(description='Invalid password change request.'),
            401: OpenApiResponse(description='Authentication required.'),
        },
    )
    @action(detail=False, methods=['post'], url_path='me/password')
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
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
    @action(detail=True, methods=['patch'], schema=RequiredRoleSchema())
    def role(self, request, pk=None):
        get_object_or_404(self.get_queryset(), pk=pk)
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
