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


from django.utils.timezone import now
from django.db import models
import uuid

class ParkingSession(models.Model):
    SESSION_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]


    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    vehicle_number = models.CharField(max_length=20)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default='pending')
    fee = models.FloatField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.slot.slot_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.session_id:
            prefix = "SESS"
            count = ParkingSession.objects.count() + 1
            self.session_id = f"{prefix}-{now().strftime('%Y%m%d')}-{count:04d}"
        super().save(*args, **kwargs)

    def calculate_fee(self):
        end_time = self.end_time or now()
        duration = end_time - self.start_time
        self.duration = duration
        minutes = int(duration.total_seconds() // 60)
        return minutes * 2  # Assuming Rs. 2 per minute

