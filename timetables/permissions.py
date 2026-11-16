from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import user_roles


class SchedulingPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_active
            and (request.method in SAFE_METHODS or request.user.is_superuser
                 or 'PLANNER' in user_roles(request.user))
        )
