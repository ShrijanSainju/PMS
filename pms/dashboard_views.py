from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt
from .permissions import require_manager, require_staff_or_manager, require_customer, require_approved_user
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


# is_admin_user function removed - using is_manager_user instead


@require_customer
def customer_dashboard(request):
    """Customer dashboard view - limited access for customers only"""
    # Get customer's own sessions
    customer_sessions = ParkingSession.objects.filter(
        vehicle_number__icontains=request.user.username  # This might need adjustment based on how you link vehicles to users
    )

    current_sessions = customer_sessions.filter(status__in=['active', 'pending'])
    recent_sessions = customer_sessions.filter(status='completed').order_by('-end_time')[:5]

    context = {
        'user_type': 'customer',
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'total_slots': ParkingSlot.objects.count(),
        'my_active_sessions': current_sessions.count(),
        'my_total_sessions': customer_sessions.count(),
        'total_spent': customer_sessions.aggregate(total=Sum('fee'))['total'] or 0,
        'current_sessions': current_sessions,
        'recent_sessions': recent_sessions,
    }

    return render(request, 'customer/customer_dashboard.html', context)


@require_staff_or_manager
def staff_dashboard(request):
    """Staff dashboard view - can manage customers and approve registrations"""
    # Get pending customer approvals
    pending_customers = UserProfile.objects.filter(
        user_type='customer',
        approval_status='pending'
    ).select_related('user')

    context = {
        'user_type': 'staff',
        'total_slots': ParkingSlot.objects.count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved_slots': ParkingSlot.objects.filter(is_reserved=True).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'pending_sessions': ParkingSession.objects.filter(status='pending').count(),
        'customer_count': UserProfile.objects.filter(user_type='customer', approval_status='approved').count(),
        'pending_customers_count': pending_customers.count(),
        'pending_customers': pending_customers[:5],  # Show first 5 pending customers
    }

    # Recent sessions for staff to manage
    context['recent_sessions'] = ParkingSession.objects.filter(
        status__in=['active', 'pending']
    ).order_by('-start_time')[:10]

    return render(request, 'staff/staff_dashboard.html', context)


@require_manager
def manager_dashboard(request):
    """Manager dashboard view - full system management access"""
    # Get pending approvals for all user types
    pending_approvals = UserProfile.objects.filter(
        approval_status='pending'
    ).select_related('user')

    context = {
        'user_type': 'admin',
        'total_slots': ParkingSlot.objects.count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved_slots': ParkingSlot.objects.filter(is_reserved=True).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'total_users': UserProfile.objects.count(),
        'customer_count': UserProfile.objects.filter(user_type='customer', approval_status='approved').count(),
        'staff_count': UserProfile.objects.filter(user_type='staff', approval_status='approved').count(),
        'manager_count': UserProfile.objects.filter(user_type='manager', approval_status='approved').count(),
        'pending_approvals_count': pending_approvals.count(),
        'pending_approvals': pending_approvals[:10],  # Show first 10 pending approvals
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

    return render(request, 'manager/manager_dashboard.html', context)


@require_approved_user
def dashboard_view(request):
    """Universal dashboard that redirects based on user type and approval status"""
    if not hasattr(request.user, 'userprofile'):
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=request.user, user_type='customer')

    profile = request.user.userprofile

    # Check if user is approved
    if not profile.can_login:
        messages.error(request, "Your account is not approved. Please contact administrator.")
        return redirect('login')

    user_type = profile.user_type

    if user_type == 'customer':
        return redirect('customer_dashboard')
    elif user_type == 'staff':
        return redirect('staff_dashboard')
    elif user_type in ['manager', 'admin']:
        return redirect('manager_dashboard')
    else:
        # Default to customer dashboard
        return redirect('customer_dashboard')


# Legacy views for backward compatibility
def adminbase(request):
    """Legacy admin base view"""
    return manager_dashboard(request)


def admin_dashboard_legacy(request):
    """Legacy admin dashboard view - redirects to manager dashboard"""
    return manager_dashboard(request)


def home_screen_view(request):
    """Home screen view"""
    if request.user.is_authenticated:
        return dashboard_view(request)
    return render(request, 'manager/homepage.html', {})


def navbar(request):
    """Navbar view"""
    return render(request, 'manager/navbar.html', {})


# API endpoints for dashboard analytics
@require_approved_user
def dashboard_analytics_api(request):
    """API endpoint for dashboard analytics"""
    
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


@require_approved_user
def live_stats_api(request):
    """API endpoint for live statistics"""
    
    stats = {
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)
