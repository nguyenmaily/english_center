
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import secrets
import string
import random


from .models import UserAccount, PasswordResetToken, Role, Permission, RolePermission
from .serializers import (
    UserAccountSerializer, UserRegistrationSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
    RefreshTokenSerializer, RoleSerializer, PermissionSerializer, 
    RolePermissionSerializer, LogoutSerializer
)


# ==================== HELPER FUNCTIONS ====================

def check_user_permission(user, permission_codename):
    """
    Kiểm tra user có permission cụ thể không (từ database)
    
    Args:
        user: UserAccount instance
        permission_codename: str - codename của permission cần kiểm tra
    
    Returns:
        bool: True nếu user có permission, False nếu không
    """
    try:
        if not user or not user.is_authenticated:
            return False
        
        user_role = user.roleid
        if not user_role:
            return False
        
        # Kiểm tra trong bảng RolePermission
        return RolePermission.objects.filter(
            role=user_role,
            permission__codename=permission_codename
        ).exists()
    except Exception:
        return False


def check_user_role(user, role_name):
    """
    Kiểm tra user có role cụ thể không
    
    Args:
        user: UserAccount instance
        role_name: str - tên role cần kiểm tra (admin, manager, teacher, student)
    
    Returns:
        bool: True nếu user có role này, False nếu không
    """
    try:
        if not user or not user.is_authenticated:
            return False
        
        return user.roleid and user.roleid.name == role_name
    except Exception:
        return False


def blacklist_token(token):
    """Blacklist a token by storing its JTI in cache"""
    try:
        access_jti = token.access_token.payload.get('jti')
        refresh_jti = token.payload.get('jti')
        
        if access_jti:
            cache.set(f'blacklisted_token:{access_jti}', True, timeout=86400 * 7)
        if refresh_jti:
            cache.set(f'blacklisted_token:{refresh_jti}', True, timeout=86400 * 7)
        return True
    except Exception:
        pass
    return False


# ==================== AUTHENTICATION ENDPOINTS ====================

class LoginView(generics.GenericAPIView):
    """
    User login endpoint
    POST /api/auth/login/
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
           
            
            return Response({
                'success': True,
                'data': {
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': UserAccountSerializer(user).data
                },
                'error': None
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'data': None,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(BaseTokenRefreshView):
    """
    JWT refresh token endpoint
    POST /api/auth/refresh/
    """
    serializer_class = RefreshTokenSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            return Response({
                'success': True,
                'data': response.data,
                'error': None
            })
        return Response({
            'success': False,
            'data': None,
            'error': response.data
        }, status=response.status_code)


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint
    POST /api/auth/logout/
    """
    serializer_class = LogoutSerializer 
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                blacklist_token(token)
            
            return Response({
                'success': True,
                'data': {'message': 'Logged out successfully.'},
                'error': None
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'Invalid token.'}
            }, status=status.HTTP_400_BAD_REQUEST)


# ==================== PASSWORD RESET ENDPOINTS ====================

class ForgotPasswordView(generics.GenericAPIView):
    """
    Gửi OTP qua email
    POST /api/auth/forgot-password/
    
    Request:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "message": "OTP sent to your email"
        }
    }
    """
    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = UserAccount.objects.get(email=email)
            
            # Tạo OTP 6 số ngẫu nhiên
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Lưu OTP vào cache (Redis/Memory) - tồn tại 10 phút
            cache_key = f'password_reset_otp:{email}'
            cache.set(cache_key, otp, timeout=600)  # 10 phút
            
            # Gửi email với OTP
            message = f"""
Hi {user.fullname},

You requested a password reset. Please use the following OTP code:

{otp}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
English Center Team
            """
            
            try:
                send_mail(
                    'Password Reset OTP',
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                return Response({
                    'success': True,
                    'data': {'message': 'OTP sent to your email successfully.'},
                    'error': None
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {'message': 'Failed to send email.'}
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'success': False,
            'data': None,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    """
    Reset password với OTP
    POST /api/auth/reset-password/
    
    Request:
    {
        "email": "user@example.com",
        "otp": "123456",
        "new_password": "NewPass123!",
        "confirm_password": "NewPass123!"
    }
    
    Response:
    {
        "success": true,
        "data": {
            "message": "Password updated successfully"
        }
    }
    """
    serializer_class = ResetPasswordSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            # Kiểm tra OTP từ cache
            cache_key = f'password_reset_otp:{email}'
            stored_otp = cache.get(cache_key)
            
            if not stored_otp:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {'message': 'OTP has expired or not found.'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if stored_otp != otp:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {'message': 'Invalid OTP.'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # OTP đúng → Update password
            try:
                user = UserAccount.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Xóa OTP khỏi cache
                cache.delete(cache_key)
                
                return Response({
                    'success': True,
                    'data': {'message': 'Password updated successfully.'},
                    'error': None
                }, status=status.HTTP_200_OK)
                
            except UserAccount.DoesNotExist:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {'message': 'User not found.'}
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'data': None,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# ==================== REGISTRATION ENDPOINT ====================

class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /api/auth/register/
    """
    serializer_class = UserRegistrationSerializer
    queryset = UserAccount.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        # Set user status to active

        user.status = 'active' 
        user.save()
        return Response({
            'success': True,
            'data': {
                'user': UserAccountSerializer(user).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            },
            'error': None
        }, status=status.HTTP_201_CREATED)


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Role CRUD operations
    Chỉ admin mới có quyền truy cập (kiểm tra từ database)
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """Lấy danh sách role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def create(self, request, *args, **kwargs):
        """Tạo role mới - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Xem chi tiết role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def update(self, request, *args, **kwargs):
        """Cập nhật role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def destroy(self, request, *args, **kwargs):
        """Xóa role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'data': {'message': 'Role deleted successfully.'},
            'error': None
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='permissions')
    def add_permissions(self, request, pk=None):
        """Thêm permission vào role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        role = self.get_object()
        serializer = RolePermissionSerializer(data=request.data)
        
        if serializer.is_valid():
            permission_ids = serializer.validated_data['permission_ids']
            
            # Thêm từng permission thông qua RolePermission model
            for permission_id in permission_ids:
                try:
                    permission = Permission.objects.get(id=permission_id)
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                except Permission.DoesNotExist:
                    pass
            
            return Response({
                'success': True,
                'data': RoleSerializer(role).data,
                'error': None
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'data': None,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='permissions/(?P<permission_id>[^/.]+)')
    def remove_permission(self, request, pk=None, permission_id=None):
        """Xoá permission khỏi role - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        role = self.get_object()
        
        try:
            permission = Permission.objects.get(id=permission_id)
            
            # Xóa thông qua bảng trung gian RolePermission
            deleted_count, _ = RolePermission.objects.filter(
                role=role,
                permission=permission
            ).delete()
            
            if deleted_count > 0:
                return Response({
                    'success': True,
                    'data': {'message': 'Permission removed successfully.'},
                    'error': None
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'data': None,
                    'error': {'message': 'Permission not assigned to this role.'}
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Permission.DoesNotExist:
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'Permission not found.'}
            }, status=status.HTTP_404_NOT_FOUND)


# ==================== PERMISSION MANAGEMENT ENDPOINTS ====================

class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Permission CRUD operations
    Chỉ admin mới có quyền truy cập (kiểm tra từ database)
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """Lấy danh sách permission - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def create(self, request, *args, **kwargs):
        """Tạo permission mới - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Xem chi tiết permission - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def update(self, request, *args, **kwargs):
        """Cập nhật permission - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def destroy(self, request, *args, **kwargs):
        """Xóa permission - Chỉ admin"""
        # Kiểm tra quyền từ database
        if not check_user_role(request.user, 'admin'):
            return Response({
                'success': False,
                'data': None,
                'error': {'message': 'You do not have permission to perform this action.'}
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'data': {'message': 'Permission deleted successfully.'},
            'error': None
        }, status=status.HTTP_200_OK)
