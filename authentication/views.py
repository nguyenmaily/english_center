
from django.db.models.base import transaction
from django.db import connection
from drf_yasg.views import APIView
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from datetime import timedelta
import secrets
import string
import random
import logging
import urllib.parse
import urllib.request
import json
import unicodedata
import time
import base64

from users.models import Student


from .models import UserAccount, PasswordResetToken, Role, Permission, RolePermission
from .serializers import (
    UserAccountSerializer, UserRegistrationSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
    RefreshTokenSerializer, RoleSerializer, PermissionSerializer, 
    RolePermissionSerializer, LogoutSerializer, GoogleAuthSerializer,
    GoogleCallbackSerializer
)


# ==================== HELPER FUNCTIONS ====================

# Logger for OAuth
logger = logging.getLogger(__name__)


def clean_text(text):
    """
    Clean và normalize text từ Google để tránh encoding errors với PostgreSQL
    
    Args:
        text: str hoặc bytes - text cần clean
    
    Returns:
        str: cleaned text
    """
    if text is None:
        return None
    
    try:
        # Chuyển bytes sang string nếu cần
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        # Normalize Unicode (NFKD)
        text = unicodedata.normalize('NFKD', text)
        
        # Loại bỏ các ký tự không hợp lệ
        # Chỉ giữ lại printable characters và whitespace
        cleaned = ''.join(c for c in text if c.isprintable() or c.isspace())
        
        # Thử encode/decode để đảm bảo UTF-8 hợp lệ
        cleaned.encode('utf-8')
        
        return cleaned.strip()
    except Exception as e:
        logger.warning(f"[OAUTH] Error cleaning text: {e}, using ASCII fallback")
        # Fallback: chỉ giữ lại ASCII
        try:
            if isinstance(text, bytes):
                text = text.decode('ascii', errors='replace')
            return ''.join(c for c in text if c.isascii() and (c.isprintable() or c.isspace())).strip()
        except Exception:
            return str(text)[:255]  # Fallback cuối cùng

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
    POST /api/auth/register/ - Đăng ký Student
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = []
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate role
        role_name = serializer.validated_data.get('role', '').lower()
        if role_name != 'student':
            return Response({
                'success': False,
                'error': 'Only students can self-register.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Tạo user
        user = serializer.save()
        
        # Tạo student profile
        Student.objects.create(
            user_account=user,
            commitment_status=Student.CommitmentStatus.NOT_COMMITTED,
            target_score=None
        )
        
        return Response({
            'success': True,
            'message': 'Student account registered successfully',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': 'student'
            }
        }, status=status.HTTP_201_CREATED)


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Role CRUD operations
    Chỉ admin mới có quyền truy cập (kiểm tra từ database)
    """
    queryset = Role.objects.prefetch_related('role_permissions__permission').all()
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


# ==================== GOOGLE OAUTH ENDPOINTS ====================

class GoogleLoginView(generics.GenericAPIView):
    """
    Lấy Google OAuth URL để redirect user đến Google login
    GET /api/auth/google/login/
    """
    serializer_class = GoogleAuthSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        try:
            # Kiểm tra Google OAuth đã được cấu hình chưa
            client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
            client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)
            
            if not client_id or not client_secret:
                logger.error(f"[OAUTH] Google OAuth not configured. CLIENT_ID: {bool(client_id)}, CLIENT_SECRET: {bool(client_secret)}")
                return Response({
                    'success': False,
                    'data': None,
                    'error': {
                        'message': 'Google OAuth not configured. Please set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET in settings or .env file.'
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Lấy redirect_uri từ query params hoặc dùng default
            redirect_uri = request.GET.get('redirect_uri')
            if not redirect_uri:
                scheme = request.scheme
                host = request.get_host()
                redirect_uri = f"{scheme}://{host}/api/auth/google/callback/"
            
            # Lấy frontend_redirect_uri từ query params (optional)
            frontend_redirect_uri = request.GET.get('frontend_redirect_uri', '')
            
            # Tạo OAuth URL
            oauth_params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'openid email profile',
                'access_type': 'offline',
                'prompt': 'consent',
            }
            
            # Thêm state nếu có frontend_redirect_uri
            if frontend_redirect_uri:
                oauth_params['state'] = frontend_redirect_uri
            
            auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(oauth_params)}"
            
            # CustomJSONRenderer sẽ tự động wrap response với success/data/error
            # Nên chỉ cần return data thôi
            return Response({
                'auth_url': auth_url,
                'redirect_uri': redirect_uri,
                'frontend_redirect_uri': frontend_redirect_uri
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"[OAUTH] Error in GoogleLoginView.get(): {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'data': None,
                'error': {
                    'message': f'Internal server error: {str(e)}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _process_oauth_callback(code, redirect_uri, request):
    """
    Xử lý OAuth callback từ Google
    
    Args:
        code: str - Authorization code từ Google
        redirect_uri: str - Redirect URI đã dùng trong OAuth request
        request: HttpRequest - Request object
    
    Returns:
        dict: {
            'success': bool,
            'data': {
                'access_token': str,
                'refresh_token': str,
                'user': dict
            } hoặc None,
            'error': dict hoặc None
        }
    """
    logger.info(f"[OAUTH] Starting OAuth callback processing for code: {code[:20]}...")
    
    # Kiểm tra Google OAuth đã được cấu hình chưa
    client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', None)
    
    if not client_id or not client_secret:
        logger.error(f"[OAUTH] Google OAuth not configured in _process_oauth_callback")
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Google OAuth not configured. Please set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET in settings or .env file.'}
        }
    
    # Bước 1: Exchange authorization code for access token
    max_retries = 2
    wait_times = [2, 4]  # Exponential backoff
    
    token_data = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[OAUTH] Attempting to get access token from Google (attempt {attempt + 1}/{max_retries + 1})")
            
            token_url = 'https://oauth2.googleapis.com/token'
            token_params = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            data = urllib.parse.urlencode(token_params).encode('utf-8')
            req = urllib.request.Request(token_url, data=data)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8', errors='replace')
                token_data = json.loads(response_data)
                logger.info("[OAUTH] Successfully got access token from Google")
                break
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            logger.error(f"[OAUTH] HTTPError getting access token: {e.code} - {error_body}")
            try:
                error_data = json.loads(error_body)
                error_message = error_data.get('error_description', error_data.get('error', 'Failed to get access token from Google'))
            except:
                error_message = f"Failed to get access token from Google: {e.code}"
            
            if attempt < max_retries:
                wait_time = wait_times[attempt]
                logger.info(f"[OAUTH] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': {'message': error_message}
                }
                
        except (urllib.error.URLError, TimeoutError) as e:
            logger.error(f"[OAUTH] Connection error getting access token: {e}")
            if attempt < max_retries:
                wait_time = wait_times[attempt]
                logger.info(f"[OAUTH] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': {'message': 'Connection timeout when connecting to Google'}
                }
        except Exception as e:
            logger.error(f"[OAUTH] Unexpected error getting access token: {e}")
            return {
                'success': False,
                'data': None,
                'error': {'message': f'Failed to get access token from Google: {str(e)}'}
            }
    
    if not token_data:
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Failed to get access token from Google'}
        }
    
    access_token = token_data.get('access_token')
    if not access_token:
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Access token not found in Google response'}
        }
    
    # Bước 2: Lấy thông tin user từ Google
    user_info = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[OAUTH] Attempting to get user info from Google (attempt {attempt + 1}/{max_retries + 1})")
            
            userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            req = urllib.request.Request(userinfo_url)
            req.add_header('Authorization', f'Bearer {access_token}')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8', errors='replace')
                user_info = json.loads(response_data)
                logger.info("[OAUTH] Successfully got user info from Google")
                break
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='replace')
            logger.error(f"[OAUTH] HTTPError getting user info: {e.code} - {error_body}")
            if attempt < max_retries:
                wait_time = wait_times[attempt]
                logger.info(f"[OAUTH] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': {'message': 'Failed to get user info from Google'}
                }
                
        except (urllib.error.URLError, TimeoutError) as e:
            logger.error(f"[OAUTH] Connection error getting user info: {e}")
            if attempt < max_retries:
                wait_time = wait_times[attempt]
                logger.info(f"[OAUTH] Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': {'message': 'Connection timeout when connecting to Google'}
                }
        except Exception as e:
            logger.error(f"[OAUTH] Unexpected error getting user info: {e}")
            return {
                'success': False,
                'data': None,
                'error': {'message': f'Failed to get user info from Google: {str(e)}'}
            }
    
    if not user_info:
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Failed to get user info from Google'}
        }
    
    # Bước 3: Clean và normalize dữ liệu
    email = clean_text(user_info.get('email'))
    if not email:
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Email not provided by Google'}
        }
    
    full_name = clean_text(user_info.get('name'))
    first_name = clean_text(user_info.get('given_name'))
    last_name = clean_text(user_info.get('family_name'))
    picture_url = user_info.get('picture')
    
    # Bước 4: Tìm hoặc tạo user
    logger.info(f"[OAUTH] Looking for user with email: {email}")
    
    user = None
    user_id = None
    
    # Bước 4.1: Tìm user theo email bằng raw SQL (tránh encoding issues)
    try:
        logger.info("[OAUTH] Step 1: Querying user by email with raw SQL")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM user_accounts WHERE email = %s",
                [email]
            )
            row = cursor.fetchone()
            if row:
                user_id = row[0]
                logger.info(f"[OAUTH] Step 2: User found with id: {user_id}, trying to get user with ORM")
                
                # Thử dùng ORM để lấy user
                try:
                    user = UserAccount.objects.select_related('roleid').get(id=user_id)
                    logger.info(f"[OAUTH] Step 3: User retrieved with ORM: {user.username}")
                    logger.info(f"[OAUTH] Step 3: User role from ORM: {user.roleid.name if user.roleid else 'None'}")
                except Exception as e:
                    logger.warning(f"[OAUTH] Step 3: Error getting user with ORM: {e}, using raw SQL")
                    # Nếu ORM lỗi, dùng raw SQL để lấy thông tin
                    cursor.execute(
                        "SELECT id, username, email, full_name, avatar_url, status, role_id FROM user_accounts WHERE id = %s",
                        [user_id]
                    )
                    row = cursor.fetchone()
                    if row:
                        # Tạo UserAccount object từ raw data (không save)
                        user = UserAccount()
                        user.id = row[0]
                        user.username = row[1]
                        user.email = row[2]
                        user.fullname = row[3]
                        user.urlImage = row[4]
                        user.status = row[5]
                        if row[6]:  # role_id
                            try:
                                user.roleid = Role.objects.get(id=row[6])
                                logger.info(f"[OAUTH] Step 3: User role from raw SQL: {user.roleid.name}")
                            except Role.DoesNotExist:
                                logger.error(f"[OAUTH] Step 3: Role with id {row[6]} not found")
                                user.roleid = None
                        else:
                            user.roleid = None
                            logger.warning(f"[OAUTH] Step 3: User has no role_id")
                        # Đánh dấu để dùng raw SQL UPDATE sau này
                        user._use_raw_update = True
    except Exception as e:
        logger.warning(f"[OAUTH] Error querying user by email: {e}, will create new user")
    
    # Bước 4.2: Update user nếu đã tồn tại
    if user:
        logger.info(f"[OAUTH] Updating existing user: {user.username}")
        updated = False
        
        # Update avatar nếu chưa có và Google có picture
        if picture_url and not user.urlImage:
            user.urlImage = picture_url
            updated = True
        
        # Update fullname nếu chưa có và Google có name
        if full_name and not user.fullname:
            user.fullname = full_name
            updated = True
        
        if updated:
            try:
                if hasattr(user, '_use_raw_update') and user._use_raw_update:
                    # Dùng raw SQL UPDATE
                    logger.info("[OAUTH] Updating user with raw SQL")
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE user_accounts SET avatar_url = %s, full_name = %s WHERE id = %s",
                            [user.urlImage, user.fullname, user.id]
                        )
                    logger.info("[OAUTH] User updated successfully with raw SQL")
                else:
                    # Dùng ORM
                    user.save(update_fields=['urlImage', 'fullname'])
                    logger.info("[OAUTH] User saved successfully with ORM")
            except Exception as e:
                logger.warning(f"[OAUTH] Error saving user: {e}, trying raw SQL")
                # Fallback: dùng raw SQL
                try:
                    # Clean fullname lại
                    user.fullname = clean_text(user.fullname)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE user_accounts SET avatar_url = %s, full_name = %s WHERE id = %s",
                            [user.urlImage, user.fullname, user.id]
                        )
                    logger.info("[OAUTH] User updated successfully with raw SQL (fallback)")
                except Exception as e2:
                    logger.error(f"[OAUTH] Error updating user with raw SQL: {e2}")
    
    # Bước 4.3: Tạo user mới nếu chưa tồn tại
    else:
        logger.info("[OAUTH] Creating new user")
        
        # Tạo username từ email
        username_base = email.split('@')[0]
        username = username_base
        
        # Kiểm tra username đã tồn tại chưa
        counter = 1
        while True:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id FROM user_accounts WHERE username = %s",
                        [username]
                    )
                    if cursor.fetchone():
                        username = f"{username_base}{counter}"
                        counter += 1
                    else:
                        break
            except Exception:
                break
        
        # Lấy role student
        try:
            student_role = Role.objects.get(name='student')
        except Role.DoesNotExist:
            logger.error("[OAUTH] Student role not found")
            return {
                'success': False,
                'data': None,
                'error': {'message': 'Student role not found. Please run: python manage.py setup_auth_data'}
            }
        
        # Tạo password ngẫu nhiên (OAuth users không dùng password này)
        random_password = secrets.token_urlsafe(32)
        
        # Tạo user
        try:
            user = UserAccount.objects.create_user(
                username=username,
                email=email,
                password=random_password,
                roleid=student_role,
                fullname=full_name or username,
                urlImage=picture_url,
                status='active'
            )
            logger.info(f"[OAUTH] User created successfully: {username}")
        except Exception as e:
            logger.warning(f"[OAUTH] Error creating user with ORM: {e}, trying with ASCII fallback")
            # Fallback: thử lại với fullname chỉ là ASCII
            try:
                user = UserAccount.objects.create_user(
                    username=username,
                    email=email,
                    password=random_password,
                    roleid=student_role,
                    fullname=username,  # Dùng username làm fullname
                    urlImage=picture_url,
                    status='active'
                )
                logger.info(f"[OAUTH] User created successfully with ASCII fallback: {username}")
            except Exception as e2:
                logger.error(f"[OAUTH] Error creating user: {e2}")
                return {
                    'success': False,
                    'data': None,
                    'error': {'message': f'Failed to create user: {str(e2)}'}
                }
        
        # Tạo Student profile
        try:
            Student.objects.create(
                user_account=user,
                commitment_status=Student.CommitmentStatus.NOT_COMMITTED,
                target_score=None
            )
            logger.info("[OAUTH] Student profile created successfully")
        except Exception as e:
            logger.warning(f"[OAUTH] Error creating student profile: {e}")
            # Không fail nếu không tạo được student profile
    
    # Bước 5: Kiểm tra user status
    if user.status != 'active':
        return {
            'success': False,
            'data': None,
            'error': {'message': 'Account is not active.'}
        }
    
    # Bước 6: Generate JWT tokens
    try:
        refresh = RefreshToken.for_user(user)
        access_token_jwt = str(refresh.access_token)
        refresh_token_jwt = str(refresh)
        
        logger.info(f"[OAUTH] JWT tokens generated successfully for user: {user.username}")
        
        # Serialize user info
        try:
            # Log fullname trước khi serialize để debug encoding
            logger.info(f"[OAUTH] User fullname before serialize (raw): {repr(user.fullname)}")
            logger.info(f"[OAUTH] User fullname before serialize (display): {user.fullname}")
            
            user_data = UserAccountSerializer(user).data
            logger.info(f"[OAUTH] User serialized. Role in serialized data: {user_data.get('role', 'N/A')}")
            logger.info(f"[OAUTH] User fullname after serialize (raw): {repr(user_data.get('fullname', 'N/A'))}")
            logger.info(f"[OAUTH] User fullname after serialize (display): {user_data.get('fullname', 'N/A')}")
        except Exception as e:
            logger.error(f"[OAUTH] Error serializing user: {e}", exc_info=True)
            # Fallback: tạo user_data thủ công
            # Đảm bảo fullname được encode đúng UTF-8
            fullname = user.fullname
            if fullname:
                # Nếu fullname là bytes, decode sang string
                if isinstance(fullname, bytes):
                    try:
                        fullname = fullname.decode('utf-8')
                    except UnicodeDecodeError:
                        # Thử decode với errors='replace' để tránh crash
                        fullname = fullname.decode('utf-8', errors='replace')
                        logger.warning(f"[OAUTH] Fullname had encoding issues, used replace mode")
            
            user_data = {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'fullname': fullname,
                'urlImage': user.urlImage,
                'status': user.status,
                'role': user.roleid.name if user.roleid else None,
                'role_id': str(user.roleid.id) if user.roleid else None
            }
            logger.warning(f"[OAUTH] Using fallback user_data. Role: {user_data.get('role', 'N/A')}")
            logger.warning(f"[OAUTH] Fallback fullname (raw): {repr(user_data.get('fullname', 'N/A'))}")
        
        return {
            'success': True,
            'data': {
                'access_token': access_token_jwt,
                'refresh_token': refresh_token_jwt,
                'user': user_data
            },
            'error': None
        }
    except Exception as e:
        logger.error(f"[OAUTH] Error generating JWT tokens: {e}")
        return {
            'success': False,
            'data': None,
            'error': {'message': f'Failed to generate tokens: {str(e)}'}
        }


class GoogleCallbackView(generics.GenericAPIView):
    """
    Xử lý callback từ Google OAuth
    GET /api/auth/google/callback/ - Google redirect về đây
    POST /api/auth/google/callback/ - Frontend gửi code
    """
    serializer_class = GoogleCallbackSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        """Xử lý GET request từ Google redirect"""
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state', '')  # frontend_redirect_uri
        
        # Kiểm tra error từ Google
        if error:
            error_message = request.GET.get('error_description', error)
            frontend_redirect_uri = state or settings.FRONTEND_URL + settings.FRONTEND_LOGIN_PAGE
            
            # Redirect về frontend với error
            redirect_url = f"{frontend_redirect_uri}?error={urllib.parse.quote(error_message)}&success=false"
            return HttpResponseRedirect(redirect_url)
        
        if not code:
            frontend_redirect_uri = state or settings.FRONTEND_URL + settings.FRONTEND_LOGIN_PAGE
            redirect_url = f"{frontend_redirect_uri}?error={urllib.parse.quote('Authorization code not provided.')}&success=false"
            return HttpResponseRedirect(redirect_url)
        
        # Lấy redirect_uri từ query params hoặc dùng default
        redirect_uri = request.GET.get('redirect_uri')
        if not redirect_uri:
            scheme = request.scheme
            host = request.get_host()
            redirect_uri = f"{scheme}://{host}/api/auth/google/callback/"
        
        # Xử lý OAuth callback
        result = _process_oauth_callback(code, redirect_uri, request)
        
        # Lấy frontend_redirect_uri từ state
        frontend_redirect_uri = state or settings.FRONTEND_URL + settings.FRONTEND_LOGIN_PAGE
        
        if result['success']:
            # Redirect về frontend với tokens và user info
            access_token = result['data']['access_token']
            refresh_token = result['data']['refresh_token']
            user_info = result['data'].get('user')
            
            logger.info(f"[OAUTH] Redirecting to frontend. User info exists: {bool(user_info)}")
            if user_info:
                logger.info(f"[OAUTH] User role from database: {user_info.get('role', 'N/A')}")
            
            # Encode user info thành base64 để gửi trong URL
            user_info_encoded = ''
            if user_info:
                try:
                    # Log fullname trước khi encode
                    logger.info(f"[OAUTH] Fullname before JSON encode (raw): {repr(user_info.get('fullname', 'N/A'))}")
                    logger.info(f"[OAUTH] Fullname before JSON encode (display): {user_info.get('fullname', 'N/A')}")
                    
                    # Encode JSON với ensure_ascii=False để giữ nguyên UTF-8 characters
                    user_info_json = json.dumps(user_info, ensure_ascii=False)
                    logger.info(f"[OAUTH] JSON string (first 200 chars): {user_info_json[:200]}")
                    
                    # Encode sang UTF-8 bytes
                    user_info_bytes = user_info_json.encode('utf-8')
                    logger.info(f"[OAUTH] UTF-8 bytes length: {len(user_info_bytes)}")
                    
                    # Encode base64
                    user_info_encoded = base64.b64encode(user_info_bytes).decode('utf-8')
                    logger.info(f"[OAUTH] User info encoded successfully. Length: {len(user_info_encoded)}")
                    logger.info(f"[OAUTH] Base64 string (first 100 chars): {user_info_encoded[:100]}")
                except Exception as e:
                    logger.error(f"[OAUTH] Error encoding user info: {e}", exc_info=True)
            
            redirect_url = f"{frontend_redirect_uri}?token={urllib.parse.quote(access_token)}&refresh_token={urllib.parse.quote(refresh_token)}&success=true"
            if user_info_encoded:
                redirect_url += f"&user_info={urllib.parse.quote(user_info_encoded)}"
                logger.info(f"[OAUTH] User info added to redirect URL")
            else:
                logger.warning(f"[OAUTH] User info NOT added to redirect URL (empty or encoding failed)")
            
            return HttpResponseRedirect(redirect_url)
        else:
            # Redirect về frontend với error
            error_message = result['error'].get('message', 'OAuth callback failed')
            redirect_url = f"{frontend_redirect_uri}?error={urllib.parse.quote(error_message)}&success=false"
            return HttpResponseRedirect(redirect_url)
    
    def post(self, request, *args, **kwargs):
        """Xử lý POST request từ frontend"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'data': None,
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        code = serializer.validated_data['code']
        redirect_uri = serializer.validated_data.get('redirect_uri')
        
        if not redirect_uri:
            scheme = request.scheme
            host = request.get_host()
            redirect_uri = f"{scheme}://{host}/api/auth/google/callback/"
        
        # Xử lý OAuth callback
        result = _process_oauth_callback(code, redirect_uri, request)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
