
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.

def home_screen_view(request):
    print(request.headers)
    return render(request, 'manager/homepage.html', {})

def navbar(request):
    return render(request, 'manager/navbar.html', {})

def admin_dashboard(request):
    return render(request, 'manager/admin_dashboard.html', {})

def adminbase(request):
    return render(request, 'manager/adminbase.html', {})


# --- Staff Login View ---

def staff_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='Staff').exists():
            login(request, user)
            return redirect('/staff/dashboard/')
        else:
            messages.error(request, 'Invalid credentials or not a staff member')
    return render(request, 'staff_login.html')

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='Admin').exists():
            login(request, user)
            return redirect('/manager/dashboard/')
        else:
            messages.error(request, 'Invalid credentials or not a admin member')
    return render(request, 'admin_login.html')


# --- Login Redirect Logic ---

def login_redirect_view(request):
    if request.user.is_superuser:
        return redirect('/admin_dashboard/')
    elif request.user.groups.filter(name='Staff').exists():
        return redirect('/staff/dashboard/')
    elif request.user.groups.filter(name='Security').exists():
        return redirect('/security/dashboard/')
    else:
        return redirect('/home/')