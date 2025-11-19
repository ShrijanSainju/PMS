from django.contrib import admin
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt, PasswordResetRequest, Booking


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_id', 'is_occupied', 'is_reserved', 'timestamp')
    list_filter = ('is_occupied', 'is_reserved')
    search_fields = ('slot_id',)
    readonly_fields = ('timestamp',)


@admin.register(ParkingSession)
class ParkingSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'vehicle_number', 'slot', 'status', 'start_time', 'end_time', 'fee')
    list_filter = ('status', 'start_time', 'end_time')
    search_fields = ('vehicle_number', 'session_id', 'slot__slot_id')
    readonly_fields = ('session_id',)
    date_hierarchy = 'start_time'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'phone_number', 'email_verified', 'created_at')
    list_filter = ('user_type', 'email_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'success', 'timestamp')
    list_filter = ('success', 'timestamp')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'vehicle', 'slot', 'scheduled_arrival', 'status', 'estimated_fee')
    list_filter = ('status', 'scheduled_arrival', 'created_at')
    search_fields = ('booking_id', 'customer__username', 'customer__email', 'vehicle__plate_number')
    readonly_fields = ('booking_id', 'created_at', 'updated_at', 'estimated_fee')
    date_hierarchy = 'scheduled_arrival'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'customer', 'vehicle', 'slot', 'status')
        }),
        ('Schedule', {
            'fields': ('scheduled_arrival', 'expected_duration', 'actual_arrival', 'actual_departure')
        }),
        ('Session & Payment', {
            'fields': ('parking_session', 'estimated_fee')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'vehicle', 'slot', 'parking_session')


# Customize admin site header
admin.site.site_header = "Parking Management System Admin"
admin.site.site_title = "PMS Admin"
admin.site.index_title = "Welcome to PMS Administration"
