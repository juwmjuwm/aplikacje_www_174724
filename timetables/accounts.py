from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .permissions import IsAdmin, IsSelfOrAdmin, user_role
from .models import Lesson, lock_teacher_assignment

User = get_user_model()


class StrictFieldsMixin:
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({field: ['This field is not allowed.'] for field in unknown})
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role')

    def get_role(self, obj):
        return user_role(obj)


class RegisterSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        candidate = User(username=attrs['username'], email=attrs.get('email', ''))
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
        fields = ('username', 'email')


class RoleSerializer(StrictFieldsMixin, serializers.Serializer):
    role = serializers.ChoiceField(choices=('VIEWER', 'PLANNER', 'TEACHER'))


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
        if self.action in ('list', 'role', 'destroy'):
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
            current_role = user_role(user)
            target_role = serializer.validated_data['role']
            if {current_role, target_role} == {'TEACHER', 'PLANNER'}:
                return Response({'detail': 'Switch between TEACHER and PLANNER through VIEWER.'}, status=status.HTTP_409_CONFLICT)
            if current_role == 'TEACHER' and target_role != 'TEACHER' and Lesson.objects.filter(teacher=user).exists():
                return Response({'detail': 'Reassign or delete this teacher\'s lessons before removing TEACHER.'}, status=status.HTTP_409_CONFLICT)
            planner, _ = Group.objects.get_or_create(name='PLANNER')
            teacher, _ = Group.objects.get_or_create(name='TEACHER')
            if target_role == 'PLANNER':
                user.groups.add(planner)
            else:
                user.groups.remove(planner)
            if target_role == 'TEACHER':
                user.groups.add(teacher)
            else:
                user.groups.remove(teacher)
        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        self.get_object()
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=kwargs['pk'])
            if user_role(user) != 'VIEWER':
                return Response({'detail': 'Only VIEWER accounts may be deleted.'}, status=status.HTTP_409_CONFLICT)
            user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
