from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSlotViewSet, update_slot
from . import views

router = DefaultRouter()
router.register(r'slots', ParkingSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-slot/', update_slot, name='update-slot'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/slot-status/', views.slot_status_api, name='slot_status_api'),
    path('video-feed/', views.video_feed, name='video_feed'),
    path('video-feed/', views.video_feed, name='video_feed'),

]
