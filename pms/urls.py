from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSlotViewSet, update_slot
from . import views
from . import auth_views
from . import dashboard_views

from .views import assign_slot

router = DefaultRouter()
router.register(r'slots', ParkingSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-slot/', update_slot, name='update-slot'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # API endpoints
    path('api/slot-status/', views.slot_status_api, name='slot_status_api'),
    path('api/dashboard-analytics/', views.dashboard_analytics_api, name='dashboard_analytics_api'),
    path('api/live-stats/', views.live_stats_api, name='live_stats_api'),
    path('api/auto-assign/', views.auto_assign_slot, name='auto_assign_slot'),
    path('api/available-slots/', views.get_available_slots, name='get_available_slots'),
    path('api/security-events/', views.security_events_api, name='security_events_api'),
    path('api/security-action/', views.security_action_api, name='security_action_api'),

    # Video feed
    path('video-feed/', views.video_feed, name='video_feed'),

    # Staff operations
    path('staff/assign/', assign_slot, name='assign-slot'),
    path('staff/end/<str:slot_id>/', views.end_session, name='end-session'),
    path('staff/end-by-vehicle/', views.end_session_by_vehicle, name='end_session_by_vehicle'),

    # History and lookup
    path('history/', views.history_log, name='history-log'),
    path('customer/lookup/', views.lookup_session, name='lookup-session'),

    # Security dashboard
    path('security/', views.security_dashboard, name='security_dashboard'),

    # Legacy customer routes for backward compatibility
    path('customer/register/', auth_views.customer_register_view, name='customer_register'),
    path('customer/login/', auth_views.customer_login_view, name='customer_login'),
    path('customer/dashboard/', dashboard_views.customer_dashboard, name='customer_dashboard'),
    path('customer/logout/', auth_views.customer_logout_view, name='customer_logout'),

    # Legacy staff routes for backward compatibility
    path('staff/register/', auth_views.staff_register_view, name='staff_register'),
    path('staff/login/', auth_views.staff_login_view, name='staff_login'),
    path('staff/dashboard/', dashboard_views.staff_dashboard, name='staff_dashboard'),
    path('staff/logout/', auth_views.staff_logout_view, name='staff_logout'),

    # Legacy manager/admin routes for backward compatibility
    path('manager/login/', auth_views.admin_login_view, name='manager_login'),
    path('manager/dashboard/', dashboard_views.admin_dashboard, name='adminbase'),
    path('manager/logout/', auth_views.admin_logout_view, name='logout'),
]
