from django.contrib import admin
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt, PasswordResetRequest


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


# Customize admin site header
admin.site.site_header = "Parking Management System Admin"
admin.site.site_title = "PMS Admin"
admin.site.index_title = "Welcome to PMS Administration"
