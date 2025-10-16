from django.urls import path
from . import views

app_name = 'campus'

urlpatterns = [
    path('campuses/', views.CampusListCreateView.as_view(), name='campus-list-create'),
    path('campuses/<uuid:pk>/', views.CampusDetailView.as_view(), name='campus-detail'),
    path('campuses/<uuid:pk>/rooms/', views.CampusRoomsView.as_view(), name='campus-rooms'),
    path('rooms/', views.RoomListCreateView.as_view(), name='room-list-create'),
    path('rooms/<uuid:pk>/', views.RoomDetailView.as_view(), name='room-detail'),
    path('rooms/<uuid:pk>/equipments/', views.RoomEquipmentsView.as_view(), name='room-equipments'),
    path('rooms/<uuid:pk>/toggle-repair/', views.RoomToggleRepairView.as_view(), name='room-toggle-repair'),
    path('equipments/', views.EquipmentListCreateView.as_view(), name='equipment-list-create'),
    path('equipments/<uuid:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    path('equipments/<uuid:pk>/change-status/', views.EquipmentChangeStatusView.as_view(), name='equipment-change-status'),
]
