from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_role(user):
    if user.is_superuser:
        return 'ADMIN'
    if user.groups.filter(name='PLANNER').exists():
        return 'PLANNER'
    return 'VIEWER'


class SchedulingPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_active
            and (request.method in SAFE_METHODS or user_role(request.user) in ('PLANNER', 'ADMIN'))
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active and request.user.is_superuser)


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user.is_superuser or obj.pk == request.user.pk)
