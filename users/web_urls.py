from django.urls import path
from . import web_views


urlpatterns = [
    path('ho-so/', web_views.profile_view, name='profile'),
    path('doi-mat-khau/', web_views.change_password_view, name='change-password-web'),
    path('nguoi-dung/', web_views.user_list_view, name='user-list-web'),
    path('nguoi-dung/<uuid:id>/', web_views.user_detail_view, name='user-detail-web'),
]


