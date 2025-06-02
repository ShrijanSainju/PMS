from django.urls import path
from .views import staff_login_view, staff_dashboard, staff_logout_view,staff_register_view, staff_dashboard

urlpatterns = [
    path('register/', staff_register_view, name='staff_register'),
    path('login/', staff_login_view, name='staff_login'),
    path('dashboard/', staff_dashboard, name='staff_dashboard'),
    path('logout/', staff_logout_view, name='staff_logout'),

]

