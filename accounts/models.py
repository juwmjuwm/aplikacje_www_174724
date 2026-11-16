from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import connection, models

from .usernames import validate_username
from .names import normalize_name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required.')
        user = self.model(username=validate_username(username), **extra_fields)
        if password is not None:
            password_validation.validate_password(password, user)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True or extra_fields['is_superuser'] is not True:
            raise ValueError('A superuser must have is_staff and is_superuser set to True.')
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = None
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_username],
        help_text='Required. 150 characters or fewer. Letters, decimal digits, and underscores only.',
        error_messages={'unique': 'A user with that username already exists.'},
        verbose_name='username',
    )
    groups = models.ManyToManyField(
        Group, blank=True, related_name='user_set', related_query_name='user',
        db_table='auth_user_groups',
    )
    user_permissions = models.ManyToManyField(
        Permission, blank=True, related_name='user_set', related_query_name='user',
        db_table='auth_user_user_permissions',
    )

    objects = UserManager()

    def save(self, *args, **kwargs):
        self.username = validate_username(self.username)
        for field in ('first_name', 'last_name'):
            value = getattr(self, field)
            if value:
                setattr(self, field, normalize_name(value))
        return super().save(*args, **kwargs)

    class Meta:
        db_table = 'auth_user'


def lock_teacher_assignment(user_id):
    """Acquire SQLite's writer lock before checking role or lesson assignment."""
    if user_id is not None and connection.vendor == 'sqlite':
        user_table = connection.ops.quote_name(get_user_model()._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f'UPDATE {user_table} SET last_login = last_login WHERE id = %s', [user_id])
