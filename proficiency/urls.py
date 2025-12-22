from django.urls import path
from . import views, admin_views

app_name = 'proficiency'

urlpatterns = [
    # Student endpoints
    path('profile/', views.ProficiencyProfileView.as_view(), name='profile'),
    path('upload-certificate/', views.UploadCertificateView.as_view(), name='upload-certificate'),
    path('placement-test-result/', views.PlacementTestResultView.as_view(), name='placement-test-result'),
    path('history/', views.CertificateHistoryView.as_view(), name='history'),
    
    # Admin endpoints
    path('admin/pending/', admin_views.PendingCertificatesListView.as_view(), name='admin-pending'),
    path('admin/debug/', admin_views.DebugCertificatesView.as_view(), name='admin-debug'),
    path('admin/<int:pk>/', admin_views.CertificateDetailView.as_view(), name='admin-detail'),
    path('admin/<int:pk>/approve/', admin_views.ApproveCertificateView.as_view(), name='admin-approve'),
    path('admin/<int:pk>/reject/', admin_views.RejectCertificateView.as_view(), name='admin-reject'),
]

