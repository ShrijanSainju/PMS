
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import StaffRegisterForm
from django.contrib.auth.views import LoginView




def staff_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff:  # Only allow staff users
                login(request, user)
                return redirect('staff_dashboard')  # Redirect after login
            else:
                messages.error(request, 'Access denied. You are not a staff member.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'staff/login.html')

def is_staff_user(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    return render(request, 'staff/staff_dashboard.html')


def staff_logout_view(request):
    logout(request)
    return redirect('/staff/login')

def staff_register_view(request):
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Optionally assign user to a staff group here
            login(request, user)  # Log the user in immediately after registration
            return redirect('staff_dashboard')  # Redirect to staff dashboard or desired page
    else:
        form = StaffRegisterForm()
    return render(request, 'staff/register.html', {'form': form})
