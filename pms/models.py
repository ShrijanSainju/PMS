from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

from django.utils.timezone import now
from django.db import models

class ParkingSession(models.Model):
    SESSION_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    session_id = models.CharField(max_length=30, unique=True, blank=True, null=True, editable=False)

    vehicle_number = models.CharField(max_length=20)
    slot = models.ForeignKey('ParkingSlot', on_delete=models.CASCADE)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default='pending')
    fee = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle_number} - {self.slot.slot_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.session_id:
            prefix = "SESS"
            date_str = now().strftime('%Y%m%d')
            # Get the count of sessions created today to generate unique number suffix
            today_count = ParkingSession.objects.filter(
                session_id__startswith=f"{prefix}-{date_str}"
            ).count() + 1
            self.session_id = f"{prefix}-{date_str}-{today_count:04d}"
        super().save(*args, **kwargs)

    def calculate_fee(self):
        end_time = self.end_time or now()
        duration = end_time - self.start_time
        minutes = int(duration.total_seconds() // 60)
        return minutes * 2  # Rs. 2 per minute


class UserProfile(models.Model):
    USER_TYPES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"Password reset for {self.user.username}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    class Meta:
        ordering = ['-created_at']


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, null=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
