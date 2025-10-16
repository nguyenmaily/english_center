from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'authentication'

# Router cho các ViewSet
router = DefaultRouter()
router.register(r'roles', views.RoleViewSet, basename='role')
router.register(r'permissions', views.PermissionViewSet, basename='permission')

# URL Patterns
urlpatterns = [
    # Authentication 
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'), 

    # Password reset 
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'), 
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),  

    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),

    # Role & Permission CRUD (tự sinh từ router) 
    path('', include(router.urls)),
]