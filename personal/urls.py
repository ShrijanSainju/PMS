from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSlotViewSet, update_slot
from . import views

from .views import assign_slot

router = DefaultRouter()
router.register(r'slots', ParkingSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-slot/', update_slot, name='update-slot'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/slot-status/', views.slot_status_api, name='slot_status_api'),
    path('video-feed/', views.video_feed, name='video_feed'),
    path('video-feed/', views.video_feed, name='video_feed'),

    path('staff/assign/', assign_slot, name='assign-slot'),

    path('staff/end/<str:slot_id>/', views.end_session, name='end-session'),
    path('history/', views.history_log, name='history-log'),
    path('customer/lookup/', views.lookup_session, name='lookup-session'),

    path('staff/end-by-vehicle/', views.end_session_by_vehicle, name='end_session_by_vehicle'),

    

]
