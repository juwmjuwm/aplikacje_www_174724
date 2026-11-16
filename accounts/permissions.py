from rest_framework.permissions import BasePermission


def user_roles(user):
    memberships = {group.name for group in user.groups.all() if group.name in ('PLANNER', 'TEACHER')}
    roles = (['ADMIN'] if user.is_superuser else []) + [
        role for role in ('PLANNER', 'TEACHER') if role in memberships
    ]
    return roles or ['VIEWER']


def user_role(user):
    return user_roles(user)[0]


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active and request.user.is_superuser)


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_superuser or obj.pk == request.user.pk)
