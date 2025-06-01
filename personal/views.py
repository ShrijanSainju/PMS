from django.shortcuts import render

# Create your views here.
def home_screen_view(request):
    print(request.headers)
    return render(request, 'admin/homepage.html', {})

from django.shortcuts import render

def navbar(request):
    return render(request, 'admin/navbar.html',{})


def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html',{})


def adminbase(request):
    return render(request, 'admin/adminbase.html',{})