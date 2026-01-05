from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course endpoints
    path('courses/', views.CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<uuid:course_id>/skill/', views.CourseSkillView.as_view(), name='course-skill'),
    path('courses/<uuid:course_id>/assign-skill/', views.CourseAssignSkillView.as_view(), name='course-assign-skill'),
    path('courses/<uuid:course_id>/classes/', views.CourseClassesListView.as_view(), name='course-classes-list'),
    path('courses/<uuid:course_id>/eligible-classes/', views.CourseEligibleClassesView.as_view(), name='course-eligible-classes'),
    
    # Skill endpoints
    path('skills/', views.SkillListView.as_view(), name='skill-list'),
    path('skills/<uuid:pk>/', views.SkillDetailView.as_view(), name='skill-detail'),
]