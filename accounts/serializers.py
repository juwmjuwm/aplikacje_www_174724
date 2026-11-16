from collections.abc import Mapping

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .names import normalize_name
from .permissions import user_roles
from .usernames import validate_username

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
