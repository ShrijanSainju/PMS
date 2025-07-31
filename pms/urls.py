from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSlotViewSet, update_slot
from . import views
from . import auth_views
from . import dashboard_views
from . import user_management_views

from .views import assign_slot

router = DefaultRouter()
router.register(r'slots', ParkingSlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('update-slot/', update_slot, name='update-slot'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # API endpoints
    path('api/update-slot/', update_slot, name='api_update_slot'),
    path('api/slot-status/', views.slot_status_api, name='slot_status_api'),
    path('api/slot-status-sync/', views.slot_status_sync_api, name='slot_status_sync_api'),
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

    # Legacy manager routes for backward compatibility
    path('manager/login/', auth_views.manager_login_view, name='manager_login'),
    path('manager/logout/', auth_views.manager_logout_view, name='logout'),

    # Role-based dashboard routes (these are the main ones)
    path('manager/dashboard/', dashboard_views.manager_dashboard, name='manager_dashboard'),
    path('staff/dashboard/', dashboard_views.staff_dashboard, name='staff_dashboard'),
    path('customer/dashboard/', dashboard_views.customer_dashboard, name='customer_dashboard'),

    # Legacy admin route for backward compatibility
    path('adminbase/', dashboard_views.manager_dashboard, name='adminbase'),

    # User management routes
    path('manager/users/', user_management_views.manager_user_management, name='manager_user_management'),
    path('manager/create-staff/', user_management_views.manager_create_staff, name='manager_create_staff'),
    path('manager/create-customer/', user_management_views.manager_create_customer, name='manager_create_customer'),
    path('manager/assign-slot/', assign_slot, name='manager_assign_slot'),
    path('manager/approve-user/<int:user_id>/', user_management_views.approve_user, name='manager_approve_user'),
    path('manager/reject-user/<int:user_id>/', user_management_views.reject_user, name='manager_reject_user'),
    path('manager/settings/', user_management_views.manager_system_settings, name='manager_system_settings'),

    # Staff management routes
    path('staff/customers/', user_management_views.staff_customer_management, name='staff_customer_management'),
    path('staff/create-customer/', user_management_views.staff_create_customer, name='staff_create_customer'),
    path('staff/approve-customer/<int:user_id>/', user_management_views.approve_customer, name='staff_approve_customer'),
    path('staff/reject-customer/<int:user_id>/', user_management_views.reject_customer, name='staff_reject_customer'),

    # API endpoints for role-based features
    path('api/pending-approvals-count/', user_management_views.pending_approvals_count_api, name='pending_approvals_count_api'),
    path('api/staff-stats/', user_management_views.staff_stats_api, name='staff_stats_api'),
]
