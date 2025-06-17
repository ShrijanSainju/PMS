from django.db import models
from django.utils import timezone

class ParkingSlot(models.Model):
    slot_id = models.CharField(max_length=20)
    is_occupied = models.BooleanField(default=False)
    is_reserved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Reserved" if self.is_reserved else "Empty"
        return f"{self.slot_id} - {status}"


class ParkingSession(models.Model):
    SESSION_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    vehicle_number = models.CharField(max_length=20)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default='pending')
    fee = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.slot.slot_id} ({self.status})"

    def calculate_fee(self):
        if self.end_time and self.start_time:
            duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
            rate_per_hour = 20  # You can customize this rate
            return round(duration_hours * rate_per_hour, 2)
        return 0
