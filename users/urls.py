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
    
    path('managers/', views.ManagerListView.as_view(), name='manager-list'),
    path('manager/dashboard-stats/', views.ManagerDashboardStatsView.as_view(), name='manager-dashboard-stats'),
    path('admin/dashboard-stats/', views.AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    
    path('students/', views.StudentListView.as_view(), name='student-list'),
    path('students/my-level/', views.MyLevelView.as_view(), name='student-my-level'),
    
    # Teacher class registration
    path('teachers/available-classes/', views.TeacherAvailableClassesView.as_view(), name='teacher-available-classes'),
    path('teachers/register-class/', views.TeacherRegisterClassView.as_view(), name='teacher-register-class'),
    path('teachers/cancel-class-registration/', views.TeacherCancelClassRegistrationView.as_view(), name='teacher-cancel-class-registration'),
]
