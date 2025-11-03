# users/urls.py

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('role-fields/', views.RoleFieldsSchemaView.as_view(), name='role-fields-schema'),

    path('me/', views.MyProfileView.as_view(), name='my-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<uuid:id>/', views.UserDetailView.as_view(), name='user-detail'),

    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),

    path('teachers/<uuid:teacher_id>/', views.TeacherDetailView.as_view(), name='teacher-detail'),
    
   
]
