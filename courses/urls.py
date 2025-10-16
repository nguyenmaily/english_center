from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course endpoints
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<uuid:course_id>/skills/', views.CourseSkillsListView.as_view(), name='course-skills-list'),
    path('courses/<uuid:course_id>/skills/create/', views.CourseSkillsCreateView.as_view(), name='course-skills-create'),
    path('courses/<uuid:course_id>/classes/', views.CourseClassesListView.as_view(), name='course-classes-list'),
    
    # Skill endpoints
    path('skills/<uuid:pk>/', views.SkillDetailView.as_view(), name='skill-detail'),
    
    # Class endpoints
    path('classes/', views.ClassListCreateView.as_view(), name='class-list-create'),
    path('classes/<uuid:pk>/', views.ClassDetailView.as_view(), name='class-detail'),
    path('classes/<uuid:pk>/assign-teacher/', views.ClassAssignTeacherView.as_view(), name='class-assign-teacher'),
]