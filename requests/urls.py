from rest_framework.routers import DefaultRouter
from .views import ReserveRequestViewSet, LeaveRequestViewSet


router = DefaultRouter()
router.register(r'reserve-requests', ReserveRequestViewSet, basename='reserve-request')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = router.urls



