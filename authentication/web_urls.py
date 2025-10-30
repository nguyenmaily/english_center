from django.urls import path
from . import web_views


urlpatterns = [
    path('dang-nhap/', web_views.login_view, name='login'),
    path('dang-xuat/', web_views.logout_view, name='logout'),
    path('dang-ky/', web_views.register_view, name='register'),
    path('quen-mat-khau/', web_views.forgot_password_view, name='forgot-password'),
    path('dat-lai-mat-khau/', web_views.reset_password_view, name='reset-password'),
]


