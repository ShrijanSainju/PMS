from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Sum
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt, Vehicle
from .forms import VehicleForm
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
    from .models import SystemSettings
    
    # Get customer's vehicles
    customer_vehicles = Vehicle.objects.filter(owner=request.user, is_active=True)

    # Get all plate numbers for this customer
    customer_plate_numbers = list(customer_vehicles.values_list('plate_number', flat=True))

    # Get customer's own sessions based on their registered vehicles
    customer_sessions = ParkingSession.objects.filter(
        vehicle_number__in=customer_plate_numbers
    ) if customer_plate_numbers else ParkingSession.objects.none()

    current_sessions = customer_sessions.filter(status__in=['active', 'pending'])
    recent_sessions = customer_sessions.filter(status='completed').order_by('-end_time')[:5]

    # Get vehicle status information
    vehicle_status = []
    for vehicle in customer_vehicles:
        current_session = vehicle.current_session
        vehicle_status.append({
            'vehicle': vehicle,
            'is_parked': vehicle.is_parked,
            'current_session': current_session,
            'slot': current_session.slot if current_session else None
        })

    context = {
        'user_type': 'customer',
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'total_slots': ParkingSlot.objects.count(),
        'my_vehicles': customer_vehicles,
        'vehicle_status': vehicle_status,
        'my_total_sessions': customer_sessions.count(),
        'total_spent': customer_sessions.aggregate(total=Sum('fee'))['total'] or 0,
        'current_sessions': current_sessions,
        'recent_sessions': recent_sessions,
        'has_vehicles': customer_vehicles.exists(),
        'settings': SystemSettings.load(),
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
        'user_type': 'manager',
        'total_slots': ParkingSlot.objects.count(),
        'occupied_slots': ParkingSlot.objects.filter(is_occupied=True).count(),
        'available_slots': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
        'reserved_slots': ParkingSlot.objects.filter(is_reserved=True).count(),
        'total_users': UserProfile.objects.count(),
        'customer_count': UserProfile.objects.filter(user_type='customer', approval_status='approved').count(),
        'staff_count': UserProfile.objects.filter(user_type='staff', approval_status='approved').count(),
        'manager_count': UserProfile.objects.filter(user_type='manager', approval_status='approved').count(),
        'pending_approvals_count': pending_approvals.count(),
        'pending_approvals': pending_approvals[:10],  # Show first 10 pending approvals
    }
    
    # Session statistics
    today = timezone.now().date()
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())  # Monday of current week
    month_start = today.replace(day=1)  # First day of current month
    
    context.update({
        'today_sessions': ParkingSession.objects.filter(start_time__date=today).count(),
        'completed_sessions': ParkingSession.objects.filter(status='completed').count(),
        'today_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date=today,
                fee__isnull=False
            )
        ]) or 0,
        'week_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date__gte=week_start,
                fee__isnull=False
            )
        ]) or 0,
        'month_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date__gte=month_start,
                fee__isnull=False
            )
        ]) or 0,
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


@require_manager
def revenue_analytics(request):
    """Dedicated revenue analytics page for managers"""
    today = timezone.now().date()
    from datetime import timedelta
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    context = {
        'user_type': 'manager',
        'today': today,
        'week_start': week_start,
        'month_start': month_start,
        'today_sessions': ParkingSession.objects.filter(start_time__date=today).count(),
        'completed_sessions': ParkingSession.objects.filter(status='completed').count(),
        'active_sessions': ParkingSession.objects.filter(status='active').count(),
        'today_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date=today,
                fee__isnull=False
            )
        ]) or 0,
        'week_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date__gte=week_start,
                fee__isnull=False
            )
        ]) or 0,
        'month_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                end_time__date__gte=month_start,
                fee__isnull=False
            )
        ]) or 0,
        'total_revenue': sum([
            session.fee for session in ParkingSession.objects.filter(
                status='completed',
                fee__isnull=False
            )
        ]) or 0,
    }
    
    return render(request, 'manager/revenue_analytics.html', context)


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
        'timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(stats)


# Vehicle Management Views
@require_customer
def customer_vehicles(request):
    """View for customers to manage their vehicles"""
    vehicles = Vehicle.objects.filter(owner=request.user, is_active=True)

    context = {
        'vehicles': vehicles,
        'user_type': 'customer',
    }
    return render(request, 'customer/vehicles.html', context)


@require_customer
def add_vehicle(request):
    """View for customers to add a new vehicle"""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user
            vehicle.save()
            messages.success(request, f'Vehicle {vehicle.plate_number} has been added successfully!')
            return redirect('customer_vehicles')
    else:
        form = VehicleForm()

    context = {
        'form': form,
        'user_type': 'customer',
        'title': 'Add New Vehicle'
    }
    return render(request, 'customer/vehicle_form.html', context)


@require_customer
def edit_vehicle(request, vehicle_id):
    """View for customers to edit their vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)

    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f'Vehicle {vehicle.plate_number} has been updated successfully!')
            return redirect('customer_vehicles')
    else:
        form = VehicleForm(instance=vehicle)

    context = {
        'form': form,
        'vehicle': vehicle,
        'user_type': 'customer',
        'title': f'Edit Vehicle - {vehicle.plate_number}'
    }
    return render(request, 'customer/vehicle_form.html', context)


@require_customer
def delete_vehicle(request, vehicle_id):
    """View for customers to delete their vehicle"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)

    # Check if vehicle has active sessions
    if vehicle.is_parked:
        messages.error(request, f'Cannot delete vehicle {vehicle.plate_number} - it has an active parking session.')
        return redirect('customer_vehicles')

    if request.method == 'POST':
        plate_number = vehicle.plate_number
        vehicle.is_active = False  # Soft delete
        vehicle.save()
        messages.success(request, f'Vehicle {plate_number} has been removed from your account.')
        return redirect('customer_vehicles')

    context = {
        'vehicle': vehicle,
        'user_type': 'customer',
    }
    return render(request, 'customer/delete_vehicle.html', context)


@require_customer
def vehicle_status(request, vehicle_id):
    """View to check specific vehicle status"""
    from .models import SystemSettings
    
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
    current_session = vehicle.current_session

    # Get recent sessions for this vehicle
    recent_sessions = ParkingSession.objects.filter(
        vehicle_number=vehicle.plate_number
    ).order_by('-start_time')[:10]

    context = {
        'vehicle': vehicle,
        'current_session': current_session,
        'recent_sessions': recent_sessions,
        'user_type': 'customer',
        'settings': SystemSettings.load(),
    }
    return render(request, 'customer/vehicle_status.html', context)
