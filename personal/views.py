from django.shortcuts import render

# Create your views here.
def home_screen_view(request):
    print(request.headers)
    return render(request, 'homepage.html', {})

from django.shortcuts import render

def navbar(request):
    return render(request, 'navbar.html',{})
