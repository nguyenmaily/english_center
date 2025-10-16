# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Profile endpoints
    path('me/', views.MyProfileView.as_view(), name='my-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # User management endpoints
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Teacher management endpoints
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('teachers/<uuid:pk>/', views.TeacherDetailView.as_view(), name='teacher-detail'),
]
