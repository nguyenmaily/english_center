from django.urls import path
from . import views

app_name = 'assignments'

urlpatterns = [
    # ==================== STUDENT ROUTES ====================
    # Student Assignment endpoints
    path('my-homework/', views.StudentAssignmentListView.as_view(), name='student-assignment-list'),
    path('my-homework/<uuid:pk>/', views.StudentAssignmentDetailView.as_view(), name='student-assignment-detail'),
    path('my-homework/<uuid:pk>/start/', views.StudentAssignmentStartView.as_view(), name='student-assignment-start'),
    path('my-homework/<uuid:pk>/submit/', views.StudentAssignmentSubmitView.as_view(), name='student-assignment-submit'),
    path('my-homework/<uuid:pk>/result/', views.StudentAssignmentResultView.as_view(), name='student-assignment-result'),
    
    # Student Submission endpoints
    path('submissions/', views.StudentSubmissionListView.as_view(), name='student-submission-list'),
    path('submissions/<uuid:pk>/', views.StudentSubmissionDetailView.as_view(), name='student-submission-detail'),
    path('submissions/<uuid:pk>/resubmit/', views.StudentSubmissionResubmitView.as_view(), name='student-submission-resubmit'),
    
    # ==================== TEACHER ROUTES ====================
    # Teacher Assignment endpoints
    path('assignments/', views.TeacherAssignmentListCreateView.as_view(), name='teacher-assignment-list-create'),
    path('assignments/<uuid:pk>/', views.TeacherAssignmentDetailView.as_view(), name='teacher-assignment-detail'),
    path('assignments/<uuid:pk>/submissions/', views.TeacherAssignmentSubmissionsView.as_view(), name='teacher-assignment-submissions'),
    
    # Teacher Answer Key endpoints
    path('assignments/<uuid:assignment_id>/answer-keys/', views.TeacherAssignmentAnswerKeysView.as_view(), name='teacher-assignment-answer-keys-list'),
    path('assignments/<uuid:assignment_id>/answer-keys/create/', views.TeacherAssignmentAnswerKeysCreateView.as_view(), name='teacher-assignment-answer-keys-create'),
    path('answer-keys/<uuid:pk>/', views.TeacherAnswerKeyDetailView.as_view(), name='teacher-answer-key-detail'),
    
    # Teacher Submission endpoints
    path('teacher-submissions/', views.TeacherSubmissionListView.as_view(), name='teacher-submission-list'),
    path('teacher-submissions/<uuid:pk>/', views.TeacherSubmissionDetailView.as_view(), name='teacher-submission-detail'),
    path('teacher-submissions/<uuid:pk>/grade/', views.TeacherSubmissionGradeView.as_view(), name='teacher-submission-grade'),
    path('teacher-submissions/<uuid:pk>/request-resubmit/', views.TeacherSubmissionRequestResubmitView.as_view(), name='teacher-submission-request-resubmit'),
]
