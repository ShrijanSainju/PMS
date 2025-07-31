from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def user_has_role(user, required_roles):
    """Check if user has one of the required roles and is approved"""
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'userprofile'):
        return False
    
    profile = user.userprofile
    
    # Check if user is approved
    if not profile.can_login:
        return False
    
    # Check if user has required role
    if isinstance(required_roles, str):
        required_roles = [required_roles]
    
    return profile.user_type in required_roles


def require_role(roles, redirect_url='/auth/login/', message=None):
    """
    Decorator to require specific user roles
    
    Args:
        roles: String or list of required roles
        redirect_url: URL to redirect to if access denied
        message: Custom message to display
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if message:
                    messages.error(request, message)
                return redirect(redirect_url)
            
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, "User profile not found. Please contact administrator.")
                return redirect(redirect_url)
            
            profile = request.user.userprofile
            
            # Check approval status
            if not profile.can_login:
                if profile.approval_status == 'pending':
                    messages.warning(request, "Your account is pending approval. Please wait for administrator approval.")
                elif profile.approval_status == 'rejected':
                    messages.error(request, f"Your account has been rejected. Reason: {profile.rejection_reason or 'Not specified'}")
                elif profile.approval_status == 'suspended':
                    messages.error(request, f"Your account has been suspended. Reason: {profile.rejection_reason or 'Not specified'}")
                else:
                    messages.error(request, "Your account is not active. Please contact administrator.")
                return redirect('/auth/login/')
            
            # Check role
            if not user_has_role(request.user, roles):
                messages.error(request, message or "You don't have permission to access this page.")
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_manager(view_func):
    """Decorator to require manager role"""
    return require_role(['manager'])(view_func)


def require_staff_or_manager(view_func):
    """Decorator to require staff or manager role"""
    return require_role(['staff', 'manager'])(view_func)


def require_customer(view_func):
    """Decorator to require customer role"""
    return require_role(['customer'])(view_func)


def require_approved_user(view_func):
    """Decorator to require any approved user"""
    return require_role(['customer', 'staff', 'manager'])(view_func)


# Permission check functions for user_passes_test decorator
def is_manager_user(user):
    """Check if user is manager"""
    return user_has_role(user, ['manager'])


def is_staff_or_manager(user):
    """Check if user is staff or manager"""
    return user_has_role(user, ['staff', 'manager'])


def is_customer_user(user):
    """Check if user is customer"""
    return user_has_role(user, ['customer'])


def is_approved_user(user):
    """Check if user is approved"""
    return user_has_role(user, ['customer', 'staff', 'manager'])


class RoleBasedPermissionMixin:
    """Mixin for class-based views to handle role-based permissions"""
    required_roles = None
    permission_denied_message = "You don't have permission to access this page."
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request.user):
            messages.error(request, self.permission_denied_message)
            return redirect('/auth/login/')
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self, user):
        if not self.required_roles:
            return True
        return user_has_role(user, self.required_roles)


class ManagerRequiredMixin(RoleBasedPermissionMixin):
    """Mixin to require manager access"""
    required_roles = ['manager']
    permission_denied_message = "Manager access required."


class StaffRequiredMixin(RoleBasedPermissionMixin):
    """Mixin to require staff or manager access"""
    required_roles = ['staff', 'manager']
    permission_denied_message = "Staff access required."


class CustomerRequiredMixin(RoleBasedPermissionMixin):
    """Mixin to require customer access"""
    required_roles = ['customer']
    permission_denied_message = "Customer access required."
