from collections.abc import Mapping

from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdmin, IsSelfOrAdmin, user_role, user_roles
from .models import Lesson, lock_teacher_assignment

User = get_user_model()


class StrictFieldsMixin:
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            return super().to_internal_value(data)
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({field: ['This field is not allowed.'] for field in unknown})
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'role', 'roles')

    def get_role(self, obj):
        return user_role(obj)

    def get_roles(self, obj):
        return user_roles(obj)


class RegisterSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')

    def validate(self, attrs):
        candidate = User(username=attrs['username'])
        try:
            password_validation.validate_password(attrs['password'], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


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

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleSerializer(StrictFieldsMixin, serializers.Serializer):
    role = serializers.ChoiceField(choices=('VIEWER', 'PLANNER', 'TEACHER'), required=False)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=('PLANNER', 'TEACHER')),
        required=False, allow_empty=True,
    )

    def validate(self, attrs):
        if ('role' in attrs) == ('roles' in attrs):
            raise serializers.ValidationError('Supply exactly one of role or roles.')
        if 'roles' in attrs and len(attrs['roles']) != len(set(attrs['roles'])):
            raise serializers.ValidationError({'roles': ['Duplicate roles are not allowed.']})
        return attrs


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('pk')
    serializer_class = UserSerializer
    http_method_names = ('get', 'patch', 'delete', 'head', 'options')

    def get_permissions(self):
        if self.action in ('list', 'role'):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsSelfOrAdmin()]

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=['patch'])
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
            legacy = 'role' in serializer.validated_data
            target_roles = ({serializer.validated_data['role']}
                            if legacy else set(serializer.validated_data['roles']))
            target_roles.discard('VIEWER')
            if legacy and {user_role(user), serializer.validated_data['role']} == {'TEACHER', 'PLANNER'}:
                return Response({'detail': 'Switch between TEACHER and PLANNER through VIEWER.'}, status=status.HTTP_409_CONFLICT)
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
