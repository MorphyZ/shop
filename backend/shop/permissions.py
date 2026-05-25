from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name="admin").exists()


def is_user_role(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return is_admin(user) or user.groups.filter(name="user").exists()


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return is_admin(request.user)


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsAdminOrUserCanCreateSale(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if view.action == "create":
            return is_user_role(request.user)
        return is_admin(request.user)

