from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login_view, name='manager_login'),
    path('dashboard/', views.admin_dashboard, name='adminbase'),
    path('logout/', views.admin_logout_view, name='logout'),

]
