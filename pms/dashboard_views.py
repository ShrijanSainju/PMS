from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt
import json


def is_customer(user):
    """Check if user is a customer"""
    return hasattr(user, 'userprofile') and user.userprofile.user_type == 'customer'


def is_staff_user(user):
    """Check if user is staff"""
    return user.is_staff or (hasattr(user, 'userprofile') and user.userprofile.user_type == 'staff')


def is_manager_user(user):
    """Check if user is manager"""
    return hasattr(user, 'userprofile') and user.userprofile.user_type == 'manager'


def is_admin_user(user):
    """Check if user is admin"""
    return user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.user_type == 'admin')


@login_required
def customer_dashboard(request):
    """Customer dashboard view"""
    context = {
        'user_type': 'customer',
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'total_slots': ParkingSlot.objects.count(),
    }
    
    # Get user's active sessions
    if hasattr(request.user, 'userprofile'):
        context['active_sessions'] = ParkingSession.objects.filter(
            status='active'
        ).count()
    
    return render(request, 'customer/customer_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    """Staff dashboard view"""
    context = {
        'user_type': 'staff',
        'total_slots': ParkingSlot.objects.count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved_slots': ParkingSlot.objects.filter(is_reserved=True).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'pending_sessions': ParkingSession.objects.filter(status='pending').count(),
    }
    
    # Recent sessions for staff to manage
    context['recent_sessions'] = ParkingSession.objects.filter(
        status__in=['active', 'pending']
    ).order_by('-start_time')[:10]
    
    return render(request, 'staff/staff_dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Admin dashboard view - enhanced version"""
    context = {
        'user_type': 'admin',
        'total_slots': ParkingSlot.objects.count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved_slots': ParkingSlot.objects.filter(is_reserved=True).count(),
        'total_users': UserProfile.objects.count(),
        'customer_count': UserProfile.objects.filter(user_type='customer').count(),
        'staff_count': UserProfile.objects.filter(user_type='staff').count(),
        'manager_count': UserProfile.objects.filter(user_type='manager').count(),
    }
    
    # Session statistics
    today = timezone.now().date()
    context.update({
        'today_sessions': ParkingSession.objects.filter(start_time__date=today).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'completed_sessions': ParkingSession.objects.filter(status='completed').count(),
        'total_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed', fee__isnull=False
            )
        ]) or 0,
    })
    
    # Recent login attempts for security monitoring
    context['recent_login_attempts'] = LoginAttempt.objects.filter(
        success=False
    ).order_by('-timestamp')[:5]
    
    return render(request, 'manager/adminbase.html', context)


@login_required
def dashboard_view(request):
    """Universal dashboard that redirects based on user type"""
    if not hasattr(request.user, 'userprofile'):
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=request.user, user_type='customer')
    
    user_type = request.user.userprofile.user_type
    
    if user_type == 'customer':
        return customer_dashboard(request)
    elif user_type == 'staff':
        return staff_dashboard(request)
    elif user_type == 'manager':
        return admin_dashboard(request)
    elif user_type == 'admin':
        return admin_dashboard(request)
    else:
        # Default to customer dashboard
        return customer_dashboard(request)


# Legacy views for backward compatibility
def adminbase(request):
    """Legacy admin base view"""
    return admin_dashboard(request)


def admin_dashboard_legacy(request):
    """Legacy admin dashboard view"""
    return admin_dashboard(request)


def home_screen_view(request):
    """Home screen view"""
    if request.user.is_authenticated:
        return dashboard_view(request)
    return render(request, 'manager/homepage.html', {})


def navbar(request):
    """Navbar view"""
    return render(request, 'manager/navbar.html', {})


# API endpoints for dashboard analytics
@login_required
def dashboard_analytics_api(request):
    """API endpoint for dashboard analytics"""
    if not (is_staff_user(request.user) or is_admin_user(request.user)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Slot statistics
    slot_stats = {
        'total': ParkingSlot.objects.count(),
        'occupied': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved': ParkingSlot.objects.filter(is_reserved=True).count(),
    }
    
    # Session statistics
    today = timezone.now().date()
    session_stats = {
        'active': ParkingSession.objects.filter(status='active').count(),
        'today_total': ParkingSession.objects.filter(start_time__date=today).count(),
        'completed_today': ParkingSession.objects.filter(
            status='completed', 
            end_time__date=today
        ).count(),
    }
    
    # Revenue statistics
    revenue_stats = {
        'today': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed', 
                end_time__date=today,
                fee__isnull=False
            )
        ]) or 0,
        'total': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                fee__isnull=False
            )
        ]) or 0,
    }
    
    return JsonResponse({
        'slots': slot_stats,
        'sessions': session_stats,
        'revenue': revenue_stats,
        'timestamp': timezone.now().isoformat(),
    })


@login_required
def live_stats_api(request):
    """API endpoint for live statistics"""
    if not (is_staff_user(request.user) or is_admin_user(request.user)):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    stats = {
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)
