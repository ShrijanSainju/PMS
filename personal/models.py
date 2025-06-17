from django.db import models

class ParkingSlot(models.Model):
    slot_id = models.CharField(max_length=20)
    is_occupied = models.BooleanField(default=False)  # From sensor
    is_reserved = models.BooleanField(default=False)  # Reserved for a car but not yet occupied
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Occupied" if self.is_occupied else "Reserved" if self.is_reserved else "Empty"
        return f"{self.slot_id} - {status}"


class ParkingSession(models.Model):
    SESSION_STATUS = [
        ('pending', 'Pending'),       # Reserved, waiting for car to arrive
        ('active', 'Active'),         # Car is parked (sensor confirms)
        ('completed', 'Completed'),   # Session ended
        ('cancelled', 'Cancelled'),   # Never arrived or force cancelled
    ]

    vehicle_number = models.CharField(max_length=20)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default='pending')

    def __str__(self):
        return f"{self.vehicle_number} - {self.slot.slot_id} ({self.status})"
