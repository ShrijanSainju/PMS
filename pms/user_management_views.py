from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .models import UserProfile, ParkingSession
from .permissions import require_manager, require_staff_or_manager
from .forms import EnhancedUserCreationForm
import json


@require_manager
def manager_user_management(request):
    """Manager view to manage all users"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    user_type_filter = request.GET.get('user_type', '')
    
    users = UserProfile.objects.select_related('user').all()
    
    if search_query:
        users = users.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if status_filter:
        users = users.filter(approval_status=status_filter)
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    users = users.order_by('-created_at')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'user_type_filter': user_type_filter,
        'status_choices': UserProfile.APPROVAL_STATUS,
        'user_type_choices': UserProfile.USER_TYPES,
    }
    
    return render(request, 'manager/user_management.html', context)


@require_staff_or_manager
def staff_customer_management(request):
    """Staff view to manage customers only"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    customers = UserProfile.objects.filter(user_type='customer').select_related('user')
    
    if search_query:
        customers = customers.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if status_filter:
        customers = customers.filter(approval_status=status_filter)
    
    customers = customers.order_by('-created_at')
    
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': UserProfile.APPROVAL_STATUS,
    }
    
    return render(request, 'staff/customer_management.html', context)


@require_manager
@require_POST
def approve_user(request, user_id):
    """Manager endpoint to approve any user"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        if profile.approval_status != 'pending':
            return JsonResponse({'success': False, 'message': 'User is not pending approval'})
        
        profile.approve(request.user)
        user.is_active = True
        user.save()
        
        return JsonResponse({'success': True, 'message': 'User approved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_manager
@require_POST
def reject_user(request, user_id):
    """Manager endpoint to reject any user"""
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')
        
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        if profile.approval_status != 'pending':
            return JsonResponse({'success': False, 'message': 'User is not pending approval'})
        
        profile.reject(request.user, reason)
        
        return JsonResponse({'success': True, 'message': 'User rejected successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_staff_or_manager
@require_POST
def approve_customer(request, user_id):
    """Staff endpoint to approve customers only"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        if profile.user_type != 'customer':
            return JsonResponse({'success': False, 'message': 'Only customers can be approved by staff'})
        
        if profile.approval_status != 'pending':
            return JsonResponse({'success': False, 'message': 'Customer is not pending approval'})
        
        profile.approve(request.user)
        user.is_active = True
        user.save()
        
        return JsonResponse({'success': True, 'message': 'Customer approved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_staff_or_manager
@require_POST
def reject_customer(request, user_id):
    """Staff endpoint to reject customers only"""
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')
        
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        if profile.user_type != 'customer':
            return JsonResponse({'success': False, 'message': 'Only customers can be rejected by staff'})
        
        if profile.approval_status != 'pending':
            return JsonResponse({'success': False, 'message': 'Customer is not pending approval'})
        
        profile.reject(request.user, reason)
        
        return JsonResponse({'success': True, 'message': 'Customer rejected successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_manager
def manager_create_staff(request):
    """Manager view to create new staff members"""
    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Set as staff and approved
            profile = user.userprofile
            profile.user_type = 'staff'
            profile.approval_status = 'approved'
            profile.approved_by = request.user
            profile.save()
            
            user.is_active = True
            user.save()
            
            messages.success(request, f'Staff member {user.username} created successfully!')
            return redirect('manager_user_management')
    else:
        form = EnhancedUserCreationForm()
    
    return render(request, 'manager/create_staff.html', {'form': form})


@require_staff_or_manager
def staff_create_customer(request):
    """Staff view to create new customers"""
    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Set as customer and approved (staff can directly approve customers)
            profile = user.userprofile
            profile.user_type = 'customer'
            profile.approval_status = 'approved'
            profile.approved_by = request.user
            profile.save()

            user.is_active = True
            user.save()

            messages.success(request, f'Customer {user.username} created successfully!')
            return redirect('staff_customer_management')
    else:
        form = EnhancedUserCreationForm()

    return render(request, 'staff/create_customer.html', {'form': form})


@require_manager
def manager_create_customer(request):
    """Manager view to create new customers"""
    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Set as customer and approved (managers can directly approve customers)
            profile = user.userprofile
            profile.user_type = 'customer'
            profile.approval_status = 'approved'
            profile.approved_by = request.user
            profile.save()

            user.is_active = True
            user.save()

            messages.success(request, f'Customer {user.username} created successfully!')
            return redirect('manager_user_management')
    else:
        form = EnhancedUserCreationForm()

    return render(request, 'manager/create_customer.html', {'form': form})


@require_manager
def manager_system_settings(request):
    """Manager view for system settings"""
    context = {
        'total_users': UserProfile.objects.count(),
        'pending_approvals': UserProfile.objects.filter(approval_status='pending').count(),
        'total_sessions': ParkingSession.objects.count(),
    }
    
    return render(request, 'manager/system_settings.html', context)


# API endpoints for dashboard updates
@require_manager
def pending_approvals_count_api(request):
    """API endpoint to get pending approvals count"""
    count = UserProfile.objects.filter(approval_status='pending').count()
    return JsonResponse({'count': count})


@require_staff_or_manager
def staff_stats_api(request):
    """API endpoint to get staff dashboard stats"""
    data = {
        'pending_customers_count': UserProfile.objects.filter(
            user_type='customer',
            approval_status='pending'
        ).count(),
        'total_customers': UserProfile.objects.filter(
            user_type='customer',
            approval_status='approved'
        ).count(),
    }
    return JsonResponse(data)
