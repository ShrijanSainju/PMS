from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

def require_staff_or_manager(view_func):
    """
    Decorator to require staff or manager permissions
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is staff or manager
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check user groups
        user_groups = request.user.groups.all()
        if any(group.name in ['Staff', 'Manager'] for group in user_groups):
            return view_func(request, *args, **kwargs)
        
        # For API views, return JSON response
        if request.path.startswith('/api/'):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # For regular views, redirect to login
        return redirect('login')
    
    return _wrapped_view

def require_approved_user(view_func):
    """
    Decorator to require approved user permissions by staff
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Superusers and staff are always approved
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Check if user has a profile and is approved
        if hasattr(request.user, 'userprofile'):
            if request.user.userprofile.is_approved:
                return view_func(request, *args, **kwargs)
        
        # For API views, return JSON response
        if request.path.startswith('/api/'):
            return JsonResponse({'error': 'User not approved'}, status=403)
        
        # For regular views, redirect to login
        return redirect('login')
    
    return _wrapped_view
