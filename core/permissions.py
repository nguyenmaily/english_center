from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions only to the owner of the object
        return obj.user == request.user


class IsManagerOrAdmin(BasePermission):
    """
    Permission for manager and admin roles
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.roleid in ['manager', 'admin']
        )


class IsAdminOnly(BasePermission):
    """
    Permission for admin role only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.roleid == 'admin'
        )


class IsTeacherOrAbove(BasePermission):
    """
    Permission for teacher, manager and admin roles
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.roleid in ['teacher', 'manager', 'admin']
        )
