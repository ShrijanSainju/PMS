from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class SystemSettings(models.Model):
    """Singleton model to store system-wide settings"""
    price_per_minute = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=2.00,
        help_text="Parking fee per minute in Rs."
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion
        pass

    @classmethod
    def load(cls):
        """Load the singleton settings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"System Settings - Rs. {self.price_per_minute}/min"

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
    created_at = models.DateTimeField(auto_now_add=True, null=True)  # Track when session was created

    def __str__(self):
        return f"{self.vehicle_number} - {self.slot.slot_id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.session_id:
            import uuid
            from django.db import transaction

            # Use atomic transaction to prevent race conditions
            with transaction.atomic():
                prefix = "SESS"
                date_str = now().strftime('%Y%m%d')

                # Try to generate unique session ID with retry logic
                max_attempts = 10
                for attempt in range(max_attempts):
                    # Get the count of sessions created today
                    today_count = ParkingSession.objects.filter(
                        session_id__startswith=f"{prefix}-{date_str}"
                    ).count() + 1 + attempt  # Add attempt to avoid duplicates

                    potential_session_id = f"{prefix}-{date_str}-{today_count:04d}"

                    # Check if this ID already exists
                    if not ParkingSession.objects.filter(session_id=potential_session_id).exists():
                        self.session_id = potential_session_id
                        break
                else:
                    # Fallback to UUID if all attempts fail
                    unique_suffix = str(uuid.uuid4())[:8].upper()
                    self.session_id = f"{prefix}-{date_str}-{unique_suffix}"

        super().save(*args, **kwargs)

    def calculate_fee(self):
        end_time = self.end_time or now()
        duration = end_time - self.start_time
        minutes = int(duration.total_seconds() // 60)
        settings = SystemSettings.load()
        return float(minutes * settings.price_per_minute)  # Use system settings

    @property
    def duration(self):
        """Calculate and return duration as a formatted string"""
        if not self.start_time:
            return "N/A"
        
        end_time = self.end_time or now()
        duration = end_time - self.start_time
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class Vehicle(models.Model):
    """Model to represent customer vehicles"""
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('motorcycle', 'Motorcycle'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('suv', 'SUV'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    plate_number = models.CharField(max_length=20, unique=True, help_text="Vehicle plate/registration number")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='car')
    make = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Toyota, Honda")
    model = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Camry, Civic")
    year = models.IntegerField(blank=True, null=True, help_text="Manufacturing year")
    color = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Whether this vehicle is actively used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plate_number} ({self.owner.username})"

    @property
    def display_name(self):
        """Return a friendly display name for the vehicle"""
        parts = []
        if self.year:
            parts.append(str(self.year))
        if self.make:
            parts.append(self.make)
        if self.model:
            parts.append(self.model)

        if parts:
            return f"{' '.join(parts)} - {self.plate_number}"
        return self.plate_number

    @property
    def current_session(self):
        """Get the current active parking session for this vehicle"""
        return ParkingSession.objects.filter(
            vehicle_number=self.plate_number,
            status__in=['pending', 'active']
        ).first()

    @property
    def is_parked(self):
        """Check if the vehicle is currently parked"""
        return self.current_session is not None


class UserProfile(models.Model):
    USER_TYPES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('manager', 'Manager'),
    ]

    APPROVAL_STATUS = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='customer')
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_users')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
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
        return f"{self.user.username} - {self.user_type} ({self.approval_status})"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    @property
    def is_approved(self):
        return self.approval_status == 'approved'

    @property
    def is_pending(self):
        return self.approval_status == 'pending'

    @property
    def can_login(self):
        """Check if user can login based on approval status"""
        return self.approval_status == 'approved' and self.user.is_active

    def approve(self, approved_by_user):
        """Approve the user"""
        from django.utils import timezone
        self.approval_status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = None
        self.save()

    def reject(self, rejected_by_user, reason=None):
        """Reject the user"""
        self.approval_status = 'rejected'
        self.approved_by = rejected_by_user
        self.rejection_reason = reason
        self.save()

    def suspend(self, suspended_by_user, reason=None):
        """Suspend the user"""
        self.approval_status = 'suspended'
        self.approved_by = suspended_by_user
        self.rejection_reason = reason
        self.save()


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


class Booking(models.Model):
    """Model for parking slot bookings/reservations"""
    BOOKING_STATUS = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('active', 'Currently Parked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    booking_id = models.CharField(max_length=30, unique=True, blank=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE, related_name='bookings')
    slot = models.ForeignKey('ParkingSlot', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    
    booking_time = models.DateTimeField(auto_now_add=True)
    scheduled_arrival = models.DateTimeField(help_text="When customer plans to arrive")
    expected_duration = models.IntegerField(help_text="Expected duration in minutes")
    
    actual_arrival = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    parking_session = models.OneToOneField('ParkingSession', null=True, blank=True, on_delete=models.SET_NULL, related_name='booking')
    
    # Dual confirmation fields for booking activation
    camera_detected = models.BooleanField(default=False, help_text="Camera has detected vehicle in slot")
    camera_detected_at = models.DateTimeField(null=True, blank=True, help_text="When camera first detected vehicle")
    
    notes = models.TextField(blank=True, null=True, help_text="Additional notes or special requests")
    estimated_fee = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_arrival']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['scheduled_arrival']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.customer.username} - {self.vehicle.plate_number} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            import uuid
            from django.db import transaction

            with transaction.atomic():
                prefix = "BOOK"
                date_str = timezone.now().strftime('%Y%m%d')

                max_attempts = 10
                for attempt in range(max_attempts):
                    today_count = Booking.objects.filter(
                        booking_id__startswith=f"{prefix}-{date_str}"
                    ).count() + 1 + attempt

                    potential_booking_id = f"{prefix}-{date_str}-{today_count:04d}"

                    if not Booking.objects.filter(booking_id=potential_booking_id).exists():
                        self.booking_id = potential_booking_id
                        break
                else:
                    unique_suffix = str(uuid.uuid4())[:8].upper()
                    self.booking_id = f"{prefix}-{date_str}-{unique_suffix}"

        # Calculate estimated fee
        if self.expected_duration and not self.estimated_fee:
            settings = SystemSettings.load()
            self.estimated_fee = float(self.expected_duration * settings.price_per_minute)

        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        """Check if booking is upcoming"""
        return self.status == 'confirmed' and self.scheduled_arrival > timezone.now()

    @property
    def is_active(self):
        """Check if booking is currently active"""
        return self.status == 'active'

    @property
    def can_cancel(self):
        """Check if booking can be cancelled"""
        if self.status not in ['pending', 'confirmed']:
            return False
        # Can cancel up to 1 hour before scheduled arrival
        time_until_arrival = self.scheduled_arrival - timezone.now()
        return time_until_arrival.total_seconds() > 3600

    @property
    def time_until_arrival(self):
        """Get time until scheduled arrival"""
        if self.scheduled_arrival > timezone.now():
            delta = self.scheduled_arrival - timezone.now()
            hours = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "Arrived"

    def convert_to_session(self):
        """
        DEPRECATED: This method is no longer the primary way to create sessions from bookings.
        Sessions are now created as PENDING in confirm_arrival view.
        This method is kept for backward compatibility only.
        
        Convert booking to PENDING parking session (not active yet).
        Session will auto-activate when camera detects the vehicle.
        """
        if self.status != 'confirmed':
            return None

        # Create PENDING session (matching assign_slot workflow)
        session = ParkingSession.objects.create(
            vehicle_number=self.vehicle.plate_number,
            slot=self.slot,
            start_time=None,    # No start time yet - camera will set this
            status='pending'    # PENDING - waiting for camera detection
        )

        self.parking_session = session
        self.status = 'active'
        self.actual_arrival = timezone.now()
        self.save()

        # RESERVE the slot (do NOT mark as occupied yet - camera will do this)
        if self.slot:
            self.slot.is_reserved = True   # RESERVED
            self.slot.is_occupied = False  # NOT occupied yet
            self.slot.save()

        return session
