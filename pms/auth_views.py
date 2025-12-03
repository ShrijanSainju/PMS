from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.crypto import get_random_string
from datetime import timedelta
import uuid
import json

from .models import UserProfile, PasswordResetRequest, LoginAttempt
from .forms import (
    EnhancedUserCreationForm, 
    EnhancedAuthenticationForm, 
    CustomPasswordResetForm, 
    CustomSetPasswordForm,
    UserProfileForm
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login_attempt(username, ip_address, success, user_agent=None):
    """Log login attempt for security monitoring"""
    LoginAttempt.objects.create(
        username=username,
        ip_address=ip_address,
        success=success,
        user_agent=user_agent
    )


def enhanced_login_view(request):
    """Enhanced login view with security features"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = EnhancedAuthenticationForm()
    
    if request.method == 'POST':
        form = EnhancedAuthenticationForm(request, data=request.POST)
        username = request.POST.get('username', '')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    # Check if user is approved
                    if hasattr(user, 'userprofile') and not user.userprofile.can_login:
                        log_login_attempt(username, ip_address, False, user_agent)
                        if user.userprofile.approval_status == 'pending':
                            messages.warning(request, 'Your account is pending approval. Please wait for administrator approval.')
                        elif user.userprofile.approval_status == 'rejected':
                            messages.error(request, f'Your account has been rejected. Reason: {user.userprofile.rejection_reason or "Not specified"}')
                        elif user.userprofile.approval_status == 'suspended':
                            messages.error(request, f'Your account has been suspended. Reason: {user.userprofile.rejection_reason or "Not specified"}')
                        else:
                            messages.error(request, 'Your account is not active. Please contact administrator.')
                        return render(request, 'auth/login.html', {'form': form})

                    login(request, user)

                    # Set session expiry based on remember me
                    if not remember_me:
                        request.session.set_expiry(0)  # Session expires when browser closes
                    else:
                        request.session.set_expiry(1209600)  # 2 weeks

                    # Update user profile with login info
                    if hasattr(user, 'userprofile'):
                        user.userprofile.last_login_ip = ip_address
                        user.userprofile.save()

                    # Log successful login
                    log_login_attempt(username, ip_address, True, user_agent)

                    # Redirect based on user type
                    if hasattr(user, 'userprofile'):
                        user_type = user.userprofile.user_type
                        if user_type == 'staff':
                            return redirect('staff_dashboard')
                        elif user_type == 'manager':
                            return redirect('manager_dashboard')
                        else:
                            return redirect('customer_dashboard')
                    
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account is disabled.')
                    log_login_attempt(username, ip_address, False, user_agent)
            else:
                messages.error(request, 'Invalid username or password.')
                log_login_attempt(username, ip_address, False, user_agent)
        else:
            log_login_attempt(username, ip_address, False, user_agent)
    
    return render(request, 'auth/login.html', {'form': form})


def enhanced_register_view(request):
    """Enhanced registration view - users require approval"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = EnhancedUserCreationForm()

    if request.method == 'POST':
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Set user as inactive until approved
            user.is_active = False
            user.save()

            # Ensure user profile is set to pending approval
            if hasattr(user, 'userprofile'):
                user.userprofile.approval_status = 'pending'
                user.userprofile.save()

            # Send email verification
            send_verification_email(user)

            messages.success(request, 'Account created successfully! Your account is pending approval. You will be notified once approved.')
            return redirect('login')

    return render(request, 'auth/register.html', {'form': form})


def send_verification_email(user):
    """Send email verification"""
    token = str(uuid.uuid4())
    user.userprofile.email_verification_token = token
    user.userprofile.save()
    
    verification_url = f"{settings.SITE_URL}/auth/verify-email/{token}/"
    
    subject = 'Verify your email - Parking Management System'
    message = f"""
    Hi {user.first_name},
    
    Thank you for registering with our Parking Management System.
    
    Please click the link below to verify your email address:
    {verification_url}
    
    If you didn't create this account, please ignore this email.
    
    Best regards,
    PMS Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send verification email: {e}")


def verify_email_view(request, token):
    """Verify email address"""
    try:
        profile = UserProfile.objects.get(email_verification_token=token)
        if not profile.email_verified:
            profile.email_verified = True
            profile.email_verification_token = None
            profile.save()
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.info(request, 'Email already verified.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification token.')
    
    return redirect('login')


def password_reset_request_view(request):
    """Request password reset"""
    form = CustomPasswordResetForm()
    
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Create password reset request
            token = get_random_string(50)
            expires_at = timezone.now() + timedelta(hours=1)
            
            PasswordResetRequest.objects.create(
                user=user,
                token=token,
                expires_at=expires_at,
                ip_address=get_client_ip(request)
            )
            
            # Send password reset email
            send_password_reset_email(user, token)
            
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('login')
    
    return render(request, 'auth/password_reset_request.html', {'form': form})


def send_password_reset_email(user, token):
    """Send password reset email"""
    reset_url = f"{settings.SITE_URL}/auth/password-reset/{token}/"
    
    subject = 'Password Reset - Parking Management System'
    message = f"""
    Hi {user.first_name},
    
    You requested a password reset for your account.
    
    Please click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this reset, please ignore this email.
    
    Best regards,
    PMS Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send password reset email: {e}")


def password_reset_confirm_view(request, token):
    """Confirm password reset"""
    try:
        reset_request = PasswordResetRequest.objects.get(token=token, used=False)
        if reset_request.is_expired():
            messages.error(request, 'Password reset link has expired.')
            return redirect('password_reset_request')
        
        form = CustomSetPasswordForm(reset_request.user)
        
        if request.method == 'POST':
            form = CustomSetPasswordForm(reset_request.user, request.POST)
            if form.is_valid():
                form.save()
                reset_request.used = True
                reset_request.save()
                
                messages.success(request, 'Password reset successfully! You can now log in with your new password.')
                return redirect('login')
        
        return render(request, 'auth/password_reset_confirm.html', {'form': form})
        
    except PasswordResetRequest.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('password_reset_request')


@login_required
def profile_view(request):
    """User profile view"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'auth/profile.html', {'form': form, 'profile': profile})


@login_required
def change_password_view(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'auth/change_password.html', {'form': form})


def enhanced_logout_view(request):
    """Enhanced logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@csrf_exempt
@require_http_methods(["POST"])
def check_username_availability(request):
    """AJAX view to check username availability"""
    data = json.loads(request.body)
    username = data.get('username', '')
    
    is_available = not User.objects.filter(username=username).exists()
    
    return JsonResponse({
        'available': is_available,
        'message': 'Username is available' if is_available else 'Username is already taken'
    })


@csrf_exempt
@require_http_methods(["POST"])
def check_email_availability(request):
    """AJAX view to check email availability"""
    data = json.loads(request.body)
    email = data.get('email', '')

    is_available = not User.objects.filter(email=email).exists()

    return JsonResponse({
        'available': is_available,
        'message': 'Email is available' if is_available else 'Email is already registered'
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def session_ping(request):
    """Keep session alive endpoint"""
    request.session.modified = True
    return JsonResponse({'status': 'ok', 'timestamp': timezone.now().isoformat()})


# Legacy authentication views for backward compatibility
def customer_login_view(request):
    """Legacy customer login view - redirects to enhanced login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_login_attempt(username, ip_address, True, user_agent)

            # Ensure user has customer profile
            if hasattr(user, 'userprofile'):
                if user.userprofile.user_type != 'customer':
                    user.userprofile.user_type = 'customer'
                    user.userprofile.save()
            else:
                UserProfile.objects.create(user=user, user_type='customer')

            return redirect('customer_dashboard')
        else:
            log_login_attempt(username, ip_address, False, user_agent)
            messages.error(request, "Invalid username or password.")

    return render(request, 'customer/login.html')


def customer_logout_view(request):
    """Legacy customer logout view"""
    logout(request)
    return redirect('customer_login')


def staff_login_view(request):
    """Legacy staff login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user should have staff access
            if user.is_staff or (hasattr(user, 'userprofile') and user.userprofile.user_type in ['staff', 'manager', 'admin']):
                login(request, user)
                log_login_attempt(username, ip_address, True, user_agent)

                # Ensure user has staff profile
                if hasattr(user, 'userprofile'):
                    if user.userprofile.user_type == 'customer':
                        user.userprofile.user_type = 'staff'
                        user.userprofile.save()
                else:
                    UserProfile.objects.create(user=user, user_type='staff')

                # Set is_staff if not already set
                if not user.is_staff:
                    user.is_staff = True
                    user.save()

                return redirect('staff_dashboard')
            else:
                log_login_attempt(username, ip_address, False, user_agent)
                messages.error(request, 'Access denied. You are not a staff member.')
        else:
            log_login_attempt(username, ip_address, False, user_agent)
            messages.error(request, 'Invalid username or password.')

    return render(request, 'staff/login.html')


def staff_logout_view(request):
    """Legacy staff logout view"""
    logout(request)
    return redirect('staff_login')


def manager_login_view(request):
    """Manager login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user should have manager access
            if user.is_staff or user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.user_type == 'manager'):
                login(request, user)
                log_login_attempt(username, ip_address, True, user_agent)

                # Ensure user has appropriate profile
                if hasattr(user, 'userprofile'):
                    if user.userprofile.user_type in ['customer', 'staff']:
                        user.userprofile.user_type = 'manager'
                        user.userprofile.save()
                else:
                    UserProfile.objects.create(user=user, user_type='manager')

                # Set is_staff if not already set
                if not user.is_staff:
                    user.is_staff = True
                    user.save()

                return redirect('manager_dashboard')
            else:
                log_login_attempt(username, ip_address, False, user_agent)
                messages.error(request, 'Access denied. You are not authorized.')
        else:
            log_login_attempt(username, ip_address, False, user_agent)
            messages.error(request, 'Invalid username or password.')

    return render(request, 'manager/login.html')


def manager_logout_view(request):
    """Manager logout view"""
    logout(request)
    return render(request, 'manager/logout.html')


# Legacy registration views
from .forms import CustomerRegisterForm, StaffRegisterForm

def customer_register_view(request):
    """Legacy customer registration view"""
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('customer_login')
    else:
        form = CustomerRegisterForm()
    return render(request, 'customer/register.html', {'form': form})


def staff_register_view(request):
    """Legacy staff registration view"""
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Staff account created successfully! Your account is pending approval. You will be notified once approved.')
            return redirect('staff_login')
    else:
        form = StaffRegisterForm()
    return render(request, 'staff/register.html', {'form': form})
