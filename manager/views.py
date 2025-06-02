from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView


# Class-based LoginView example (optional)
class AdminLoginView(LoginView):
    template_name = 'manager/login.html'


def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Access denied. You are not a staff member.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'manager/login.html')


def is_admin_user(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    return render(request, 'manager/admin_dashboard.html')


def admin_logout_view(request):
    logout(request)
    return redirect('login')

