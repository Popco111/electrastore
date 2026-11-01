from rest_framework import permissions

class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Гости и покупатели могут только смотреть.
    Владелец товара и админ могут редактировать/удалять.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller == request.user or request.user.is_staff or request.user.role == 'admin'

class IsAdminOrReadOnly(permissions.BasePermission):
    """Категории может изменять только администратор."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_staff or request.user.role == 'admin')