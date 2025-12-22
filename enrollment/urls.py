from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import EnrollmentViewSet
from .payment_views import VNPayReturnView, VNPayIPNView, VNPayTestReturnView


router = DefaultRouter()
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')

urlpatterns = router.urls + [
    path('payments/vnpay/return/', VNPayReturnView.as_view(), name='vnpay-return'),
    path('payments/vnpay/notify/', VNPayIPNView.as_view(), name='vnpay-ipn'),
    path('payments/vnpay/test-return/', VNPayTestReturnView.as_view(), name='vnpay-test-return'),
]



