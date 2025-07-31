from django.urls import path
from . import auth_views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.enhanced_login_view, name='login'),
    path('register/', auth_views.enhanced_register_view, name='register'),
    path('logout/', auth_views.enhanced_logout_view, name='logout'),
    
    # Email verification
    path('verify-email/<str:token>/', auth_views.verify_email_view, name='verify_email'),
    
    # Password reset
    path('password-reset/', auth_views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/<str:token>/', auth_views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Profile management
    path('profile/', auth_views.profile_view, name='profile'),
    path('change-password/', auth_views.change_password_view, name='change_password'),
    
    # AJAX endpoints
    path('check-username/', auth_views.check_username_availability, name='check_username'),
    path('check-email/', auth_views.check_email_availability, name='check_email'),

    # Session management
    path('ping/', auth_views.session_ping, name='session_ping'),
]
