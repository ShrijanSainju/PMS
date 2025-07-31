# """
# URL configuration for mysite project.

# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/4.2/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# <<<<<<< Updated upstream
# from django.urls import path,include

# from personal.views import (
#     home_screen_view, navbar, admin_dashboard, adminbase, admin_logout_view
# =======
# from django.urls import path, include

# from personal.views import (
#     home_screen_view, navbar, admin_dashboard, adminbase, update_slot
# >>>>>>> Stashed changes
# )

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', home_screen_view),
#     path('navbar/', navbar),
#     path('admin_dashboard/', admin_dashboard),
#     path('adminbase/', adminbase),
#     path('staff/', include('staff.urls')),
#     path('manager/', include('manager.urls')),
#     path('logout/',admin_logout_view, name='logout'),
#     path('customer/', include('customer.urls')),


#     path('api/update-slot/', update_slot, name='update-slot'),
#     path('api/', include('personal.urls')),
#     path('', include('personal.urls')),
# ]


from django.contrib import admin
from django.urls import path, include

from pms.dashboard_views import (
    home_screen_view, navbar, manager_dashboard, adminbase
)
from pms.auth_views import manager_logout_view
from pms.views import update_slot, history_log

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_screen_view),
    path('navbar/', navbar),
    path('admin_dashboard/', manager_dashboard),
    path('adminbase/', adminbase),

    # Legacy app routes - now handled by consolidated pms app
    path('staff/', include('pms.urls')),  # Staff routes now in pms.urls
    path('manager/', include('pms.urls')),  # Manager routes now in pms.urls
    path('customer/', include('pms.urls')),  # Customer routes now in pms.urls

    path('logout/', manager_logout_view, name='logout'),

    path('api/update-slot/', update_slot, name='update-slot'),
    path('api/', include('pms.urls')),
    path('', include('pms.urls')),

    path('history/', history_log, name='history-log'),

    # Enhanced authentication URLs
    path('auth/', include('pms.auth_urls')),
]
