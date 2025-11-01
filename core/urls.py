"""
Core app URLs - Public endpoints
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints for landing page (no authentication required)
    path('public/stats/', views.public_stats, name='public-stats'),
    path('public/courses/', views.public_courses, name='public-courses'),
    path('public/classes/', views.public_classes, name='public-classes'),
]

