from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction

from accounts.usernames import validate_username

from .models import Lesson, Room, StudentGroup, Subject, Timetable, lock_teacher_assignment
from .permissions import user_roles


User = get_user_model()


class CanonicalUsernameFormMixin:
    def clean_username(self):
        try:
            username = validate_username(self.cleaned_data['username'])
        except ValidationError as exc:
            raise ValidationError(exc.messages) from exc
        matches = User.objects.filter(username=username)
        if self.instance.pk:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise ValidationError('A user with that username already exists.')
        return username


class SafeUserCreationForm(CanonicalUsernameFormMixin, AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ('username',)


class SafeUserChangeForm(CanonicalUsernameFormMixin, UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

    def clean_groups(self):
        groups = self.cleaned_data['groups']
        if (self.instance.pk and self.instance.lessons.exists()
                and self.instance.groups.filter(name='TEACHER').exists()
                and not groups.filter(name='TEACHER').exists()):
            raise ValidationError('Reassign or delete this teacher\'s lessons before removing TEACHER.')
        return groups


admin.site.unregister(Group)


@admin.register(Group)
class SafeGroupAdmin(BaseGroupAdmin):
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return (*fields, 'name') if obj is not None and obj.name == 'TEACHER' else fields

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.name != 'TEACHER')

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions


@admin.register(User)
class SafeUserAdmin(BaseUserAdmin):
    form = SafeUserChangeForm
    add_form = SafeUserCreationForm
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name')

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or user_roles(obj) == ['VIEWER'])

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        if request.method == 'POST' and object_id is not None:
            with transaction.atomic():
                lock_teacher_assignment(object_id)
                return super().changeform_view(request, object_id, form_url, extra_context)
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "size")
    search_fields = ("name",)
    list_filter = ("size",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)
    list_filter = ("capacity",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'teacher':
            kwargs['queryset'] = User.objects.filter(groups__name='TEACHER').distinct()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ("subject", "timetable", "weekday", "start_time", "end_time", "room", "teacher", "student_group")
    search_fields = (
        "subject__name", "timetable__name", "room__name",
        "teacher__username", "student_group__name",
    )
    list_filter = ("weekday", "room", "teacher", "student_group", "timetable")
    list_select_related = ("subject", "timetable", "room", "teacher", "student_group")
