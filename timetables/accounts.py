from collections.abc import Mapping

from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .permissions import IsAdmin, IsSelfOrAdmin, user_roles
from .models import Lesson, lock_teacher_assignment
from .pagination import CollectionPagination
from accounts.usernames import validate_username
from accounts.names import normalize_name

User = get_user_model()


def username_conflict(error):
    return f'UNIQUE constraint failed: {User._meta.db_table}.username' in str(error)


class CanonicalUsernameMixin:
    username = serializers.CharField(max_length=150, validators=[])

    def validate_username(self, value):
        try:
            canonical = validate_username(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        matches = User.objects.filter(username=canonical)
        if self.instance is not None:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return canonical


class StrictFieldsMixin:
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            return super().to_internal_value(data)
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({field: ['This field is not allowed.'] for field in unknown})
        return super().to_internal_value(data)


class NameFieldsMixin:
    def validate_first_name(self, value):
        try:
            return normalize_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_last_name(self, value):
        try:
            return normalize_name(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'roles')

    def get_roles(self, obj) -> list[str]:
        return user_roles(obj)


class RegisterSerializer(CanonicalUsernameMixin, NameFieldsMixin, StrictFieldsMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    last_name = serializers.CharField(allow_blank=False, trim_whitespace=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name')

    def validate(self, attrs):
        candidate = User(
            username=attrs['username'],
            first_name=attrs['first_name'],
            last_name=attrs['last_name'],
        )
        try:
            password_validation.validate_password(attrs['password'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(CanonicalUsernameMixin, NameFieldsMixin, StrictFieldsMixin, serializers.ModelSerializer):
    first_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    last_name = serializers.CharField(allow_blank=False, trim_whitespace=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')


class PasswordChangeSerializer(StrictFieldsMixin, serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({'current_password': ['Incorrect password.']})
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': ['Choose a different password.']})
        try:
            password_validation.validate_password(attrs['new_password'], user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': exc.messages}) from exc
        return attrs


class PasswordChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={
            204: None,
            400: OpenApiResponse(description='Invalid password change request.'),
            401: OpenApiResponse(description='Authentication required.'),
        },
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleSerializer(StrictFieldsMixin, serializers.Serializer):
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=('PLANNER', 'TEACHER')),
        allow_empty=True,
    )

    def validate(self, attrs):
        if len(attrs['roles']) != len(set(attrs['roles'])):
            raise serializers.ValidationError({'roles': ['Duplicate roles are not allowed.']})
        return attrs


ROLE_REQUEST_SCHEMA = {
    'type': 'object',
    'properties': {
        'roles': {
            'type': 'array',
            'items': {'type': 'string', 'enum': ['PLANNER', 'TEACHER']},
        },
    },
    'required': ['roles'],
    'additionalProperties': False,
}


class RequiredRoleSchema(AutoSchema):
    def _get_request_body(self, direction='request'):
        body = super()._get_request_body(direction)
        body['required'] = True
        return body


@extend_schema_view(
    post=extend_schema(
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description='Invalid registration fields or username conflict.'),
        },
        auth=[],
    ),
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = serializer.save()
        except IntegrityError as exc:
            if not username_conflict(exc):
                raise
            raise serializers.ValidationError({'username': ['A user with that username already exists.']}) from exc
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('pk')
    serializer_class = UserSerializer
    pagination_class = CollectionPagination
    http_method_names = ('get', 'patch', 'delete', 'head', 'options')

    def get_permissions(self):
        if self.action in ('list', 'role'):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsSelfOrAdmin()]

    @extend_schema(
        responses={200: UserSerializer, 401: OpenApiResponse(description='Authentication required.')},
    )
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        request=ProfileSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Invalid profile fields or username conflict.'),
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='Account access denied.'),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
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

    @extend_schema(
        request={media_type: ROLE_REQUEST_SCHEMA for media_type in (
            'application/json', 'application/x-www-form-urlencoded', 'multipart/form-data',
        )},
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description='Invalid role selection.'),
            401: OpenApiResponse(description='Authentication required.'),
            403: OpenApiResponse(description='ADMIN role required.'),
            409: OpenApiResponse(description='Role transition conflicts with account or lesson assignments.'),
        },
    )
    @action(detail=True, methods=['patch'], schema=RequiredRoleSchema())
    def role(self, request, pk=None):
        self.get_object()
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            lock_teacher_assignment(pk)
            user = User.objects.select_for_update().get(pk=pk)
            if user.is_superuser:
                return Response({'detail': 'ADMIN role cannot be changed.'}, status=status.HTTP_409_CONFLICT)
            current_roles = set(user_roles(user))
            target_roles = set(serializer.validated_data['roles'])
            if 'TEACHER' in current_roles and 'TEACHER' not in target_roles and Lesson.objects.filter(teacher=user).exists():
                return Response({'detail': 'Reassign or delete this teacher\'s lessons before removing TEACHER.'}, status=status.HTTP_409_CONFLICT)
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
        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        self.get_object()
        try:
            with transaction.atomic():
                lock_teacher_assignment(kwargs['pk'])
                user = User.objects.select_for_update().get(pk=kwargs['pk'])
                if user.is_superuser:
                    return Response({'detail': 'ADMIN accounts cannot be deleted.'}, status=status.HTTP_409_CONFLICT)
                if Lesson.objects.filter(teacher=user).exists():
                    return Response({'detail': 'Reassign or delete this teacher\'s lessons before deleting the account.'}, status=status.HTTP_409_CONFLICT)
                user.delete()
        except ProtectedError:
            return Response({'detail': 'Related lessons prevent deletion of this account.'}, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)
