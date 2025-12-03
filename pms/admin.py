from django.contrib import admin
from .models import ParkingSlot, ParkingSession, UserProfile, LoginAttempt, PasswordResetRequest, Booking, SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('price_per_minute', 'updated_at', 'updated_by')
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_id', 'is_occupied', 'is_reserved', 'timestamp')
    list_filter = ('is_occupied', 'is_reserved')
    search_fields = ('slot_id',)
    readonly_fields = ('timestamp',)


@admin.register(ParkingSession)
class ParkingSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'vehicle_number', 'slot', 'status', 'start_time', 'end_time', 'fee', 'duration_display')
    list_filter = ('status', 'start_time', 'end_time')
    search_fields = ('vehicle_number', 'session_id', 'slot__slot_id')
    readonly_fields = ('session_id', 'created_at', 'duration_display', 'calculated_fee')
    date_hierarchy = 'start_time'
    list_editable = ('fee',)  # Allow editing fee directly in list view
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'vehicle_number', 'slot', 'status', 'created_at')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration_display')
        }),
        ('Revenue', {
            'fields': ('calculated_fee', 'fee'),
            'description': 'Calculated fee is auto-computed. You can manually override the actual fee charged.'
        }),
    )
    
    actions = ['recalculate_fees', 'mark_as_completed', 'export_revenue_report']
    
    def duration_display(self, obj):
        """Display session duration"""
        if obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            return f"{int(hours)}h {int(minutes)}m"
        return "N/A"
    duration_display.short_description = 'Duration'
    
    def calculated_fee(self, obj):
        """Show auto-calculated fee"""
        if obj.start_time and obj.end_time:
            return f"₹{obj.calculate_fee():.2f}"
        return "N/A"
    calculated_fee.short_description = 'Auto-Calculated Fee'
    
    def recalculate_fees(self, request, queryset):
        """Recalculate fees for selected sessions"""
        count = 0
        for session in queryset:
            if session.start_time and session.end_time:
                session.fee = session.calculate_fee()
                session.save()
                count += 1
        self.message_user(request, f'Recalculated fees for {count} session(s).')
    recalculate_fees.short_description = 'Recalculate fees for selected sessions'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected sessions as completed"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'Marked {updated} session(s) as completed.')
    mark_as_completed.short_description = 'Mark selected as completed'
    
    def export_revenue_report(self, request, queryset):
        """Export revenue report for selected sessions"""
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="revenue_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Session ID', 'Vehicle', 'Slot', 'Start Time', 'End Time', 'Duration (min)', 'Fee', 'Status'])
        
        total_revenue = 0
        for session in queryset:
            duration = 0
            if session.start_time and session.end_time:
                duration = int((session.end_time - session.start_time).total_seconds() / 60)
            
            writer.writerow([
                session.session_id,
                session.vehicle_number,
                session.slot.slot_id,
                session.start_time.strftime('%Y-%m-%d %H:%M') if session.start_time else '',
                session.end_time.strftime('%Y-%m-%d %H:%M') if session.end_time else '',
                duration,
                f"{session.fee:.2f}" if session.fee else '0.00',
                session.status
            ])
            
            if session.fee:
                total_revenue += session.fee
        
        writer.writerow([])
        writer.writerow(['TOTAL REVENUE', '', '', '', '', '', f"{total_revenue:.2f}", ''])
        
        self.message_user(request, f'Exported {queryset.count()} sessions. Total Revenue: ₹{total_revenue:.2f}')
        return response
    export_revenue_report.short_description = 'Export revenue report (CSV)'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('slot')


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
