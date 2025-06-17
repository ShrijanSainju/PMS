from django.contrib import admin
from .models import ParkingSlot, ParkingSession

admin.site.register(ParkingSlot)
admin.site.register(ParkingSession)
