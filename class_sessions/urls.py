from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, SessionViewSet

router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'attendances', AttendanceViewSet, basename='attendance')

urlpatterns = router.urls



