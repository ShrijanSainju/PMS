from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomerRegisterForm

def customer_register_view(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('customer_login')
    else:
        form = CustomerRegisterForm()
    return render(request, 'customer/register.html', {'form': form})

def customer_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'customer/login.html')

@login_required
def customer_dashboard(request):
    return render(request, 'customer/customer_dashboard.html')

def customer_logout_view(request):
    logout(request)
    return redirect('customer/login')
    