# authentication/permissions.py
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def check_user_permission(user, permission_code):
    """
    Kiểm tra user có permission không dựa trên bảng role_permission
    
    Args:
        user: User object (UserAccount)
        permission_code: Mã permission cần check (vd: 'manage_campus', 'view_users')
    
    Returns:
        Boolean: True nếu có quyền, False nếu không
    """
    if not user or not user.is_authenticated:
        return False
    
    # UserAccount chỉ có roleid (1 role), không có roles (many roles)
    if not user.roleid:
        return False
    
    # Import ở đây để tránh circular import
    from .models import RolePermission
    
    # Check xem role có permission này không
    has_permission = RolePermission.objects.filter(
        role=user.roleid,
        permission__name=permission_code  # ← Dùng name thay vì code
    ).exists()
    
    return has_permission


def get_user_permissions(user):
    """
    Lấy tất cả permissions của user
    
    Args:
        user: User object
    
    Returns:
        QuerySet: Danh sách Permission objects
    """
    if not user or not user.is_authenticated:
        return []
    
    if not user.roleid:
        return []
    
    from .models import Permission, RolePermission
    
    # Lấy tất cả permission IDs của role
    permission_ids = RolePermission.objects.filter(
        role=user.roleid
    ).values_list('permission_id', flat=True).distinct()
    
    return Permission.objects.filter(id__in=permission_ids)


def get_user_permission_codes(user):
    """
    Lấy danh sách mã permissions của user
    
    Args:
        user: User object
    
    Returns:
        List: Danh sách permission names
    """
    permissions = get_user_permissions(user)
    return list(permissions.values_list('name', flat=True))


def require_permission(permission_code):
    """
    Decorator để check permission cho function-based views hoặc methods
    
    Usage:
        @require_permission('manage_campus')
        def delete(self, request, *args, **kwargs):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not check_user_permission(request.user, permission_code):
                return Response(
                    {
                        'error': 'Permission denied',
                        'message': f'Bạn không có quyền: {permission_code}',
                        'detail': 'Vui lòng liên hệ admin để được cấp quyền',
                        'required_permission': permission_code
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator


class PermissionMixin:
    """
    Mixin để check permission cho ViewSet/APIView
    
    Usage:
        class CampusListCreateView(PermissionMixin, generics.ListCreateAPIView):
            permission_classes = [IsAuthenticated]
            permission_map = {
                'GET': 'view_campus',
                'POST': 'manage_campus',
            }
    """
    permission_map = {}
    
    def check_permissions(self, request):
        """
        Override method check_permissions của DRF
        """
        # Gọi check permissions mặc định của DRF (IsAuthenticated, etc.)
        super().check_permissions(request)
        
        # Check custom permission từ database
        method = request.method
        permission_code = self.permission_map.get(method)
        
        if permission_code:
            if not check_user_permission(request.user, permission_code):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    detail={
                        'error': 'Permission denied',
                        'message': f'Bạn không có quyền: {permission_code}',
                        'detail': 'Vui lòng liên hệ admin để được cấp quyền',
                        'required_permission': permission_code
                    }
                )


class RoleBasedPermissionMixin:
    """
    Mixin check permission theo role cụ thể
    
    Usage:
        class SomeView(RoleBasedPermissionMixin, generics.ListAPIView):
            required_roles = ['admin', 'manager']
    """
    required_roles = []
    
    def check_permissions(self, request):
        super().check_permissions(request)
        
        if not self.required_roles:
            return
        
        if not request.user or not request.user.is_authenticated:
            from rest_framework.exceptions import NotAuthenticated
            raise NotAuthenticated()
        
        # UserAccount có roleid (1 role), không phải roles (many)
        user_role_name = request.user.roleid.name if request.user.roleid else None
        
        # Check xem user có role trong required_roles không
        if user_role_name not in self.required_roles:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                detail={
                    'error': 'Permission denied',
                    'message': f'Bạn cần có một trong các role sau: {", ".join(self.required_roles)}',
                    'required_roles': self.required_roles,
                    'your_role': user_role_name
                }
            )


def has_any_permission(user, permission_codes):
    """
    Check user có ít nhất một trong các permissions không
    """
    for permission_code in permission_codes:
        if check_user_permission(user, permission_code):
            return True
    return False


def has_all_permissions(user, permission_codes):
    """
    Check user có tất cả các permissions không
    """
    for permission_code in permission_codes:
        if not check_user_permission(user, permission_code):
            return False
    return True


def check_role(user, role_name):
    """
    Check user có role cụ thể không
    
    Args:
        user: User object
        role_name: Tên role cần check
    
    Returns:
        Boolean: True nếu user có role đó
    """
    if not user or not user.is_authenticated:
        return False
    
    if not user.roleid:
        return False
    
    return user.roleid.name == role_name


def is_admin(user):
    """
    Check user có phải admin không
    """
    return check_role(user, 'admin')


def is_manager(user):
    """
    Check user có phải manager không
    """
    return check_role(user, 'manager')


def is_teacher(user):
    """
    Check user có phải teacher không
    """
    return check_role(user, 'teacher')


def is_student(user):
    """
    Check user có phải student không
    """
    return check_role(user, 'student')