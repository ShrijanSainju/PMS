from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.customer_register_view, name='customer_register'),
    path('login/', views.customer_login_view, name='customer_login'),
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('logout/', views.customer_logout_view, name='customer_logout'),
]
