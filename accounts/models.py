from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required.')
        user = self.model(username=self.model.normalize_username(username), **extra_fields)
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
    groups = models.ManyToManyField(
        Group, blank=True, related_name='user_set', related_query_name='user',
        db_table='auth_user_groups',
    )
    user_permissions = models.ManyToManyField(
        Permission, blank=True, related_name='user_set', related_query_name='user',
        db_table='auth_user_user_permissions',
    )

    objects = UserManager()

    class Meta:
        db_table = 'auth_user'
