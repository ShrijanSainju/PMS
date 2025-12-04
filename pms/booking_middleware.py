"""
Middleware for automatic booking slot reservation and expiration.
This runs periodically on requests to manage booking lifecycle without cron jobs.
"""
from django.utils import timezone
from datetime import timedelta
from .models import Booking, ParkingSession
import logging

logger = logging.getLogger(__name__)


class AutoReserveBookingSlotsMiddleware:
    """
    Middleware that automatically:
    1. Reserves slots for bookings when their time window starts (15 min before arrival)
    2. Expires bookings where customer didn't show up (30 min grace period)
    3. Frees slots from completed/cancelled/expired bookings
    
    Runs every 5 minutes to reduce overhead.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_check = None
    
    def __call__(self, request):
        # Only check every 5 minutes to reduce overhead
        now = timezone.now()
        
        if self.last_check is None or (now - self.last_check).total_seconds() > 300:
            try:
                self.reserve_upcoming_booking_slots(now)
                self.expire_missed_bookings(now)
                self.free_completed_booking_slots()
                self.last_check = now
            except Exception as e:
                logger.error(f"Error in AutoReserveBookingSlotsMiddleware: {e}")
        
        response = self.get_response(request)
        return response
    
    def reserve_upcoming_booking_slots(self, now):
        """
        Reserve slots for bookings whose time window is starting.
        Reserves 15 minutes before scheduled arrival to prevent conflicts.
        """
        grace_period = timedelta(minutes=15)
        
        # Find bookings that should be reserved now
        upcoming_bookings = Booking.objects.filter(
            status='confirmed',
            scheduled_arrival__lte=now + grace_period,  # Arriving soon or now
            scheduled_arrival__gte=now - timedelta(minutes=30)  # Not too old
        ).select_related('slot')
        
        reserved_count = 0
        
        for booking in upcoming_bookings:
            if booking.slot and not booking.slot.is_reserved and not booking.slot.is_occupied:
                # Check if there's an active session occupying this slot
                active_session = ParkingSession.objects.filter(
                    slot=booking.slot,
                    status__in=['pending', 'active']
                ).exclude(
                    vehicle_number=booking.vehicle.plate_number  # Exclude this booking's vehicle
                ).exists()
                
                if not active_session:
                    booking.slot.is_reserved = True
                    booking.slot.save()
                    reserved_count += 1
                    
                    logger.info(
                        f"Auto-reserved slot {booking.slot.slot_id} for booking {booking.booking_id} "
                        f"(scheduled: {booking.scheduled_arrival})"
                    )
        
        if reserved_count > 0:
            logger.info(f"Auto-reserved {reserved_count} slots for upcoming bookings")
    
    def expire_missed_bookings(self, now):
        """
        Expire bookings where customer didn't show up within grace period.
        Grace period: 30 minutes after scheduled arrival.
        """
        grace_period = timedelta(minutes=30)
        
        # Find bookings past their grace period
        expired_bookings = Booking.objects.filter(
            status='confirmed',
            scheduled_arrival__lt=now - grace_period,  # Past grace period
            actual_arrival__isnull=True  # Customer never arrived
        ).select_related('slot', 'customer', 'vehicle')
        
        expired_count = 0
        
        for booking in expired_bookings:
            # Expire the booking
            booking.status = 'expired'
            booking.save()
            
            # Free up the slot
            if booking.slot and booking.slot.is_reserved:
                # Make sure there's no active session using this slot
                active_session = ParkingSession.objects.filter(
                    slot=booking.slot,
                    status__in=['pending', 'active']
                ).exists()
                
                if not active_session:
                    booking.slot.is_reserved = False
                    booking.slot.save()
                    
                    logger.info(
                        f"Freed slot {booking.slot.slot_id} from expired booking {booking.booking_id}"
                    )
            
            expired_count += 1
            
            logger.warning(
                f"Auto-expired booking {booking.booking_id} - no-show for "
                f"{booking.scheduled_arrival} (vehicle: {booking.vehicle.plate_number})"
            )
        
        if expired_count > 0:
            logger.info(f"Auto-expired {expired_count} missed bookings")
    
    def free_completed_booking_slots(self):
        """
        Free slots from completed, cancelled, or expired bookings.
        Only frees if no active session is using the slot.
        """
        # Find stale bookings with reserved slots
        stale_bookings = Booking.objects.filter(
            status__in=['completed', 'cancelled', 'expired'],
            slot__is_reserved=True
        ).select_related('slot')
        
        freed_count = 0
        
        for booking in stale_bookings:
            if booking.slot:
                # Make sure no active session is using this slot
                active_session = ParkingSession.objects.filter(
                    slot=booking.slot,
                    status__in=['pending', 'active']
                ).exists()
                
                if not active_session:
                    booking.slot.is_reserved = False
                    booking.slot.save()
                    freed_count += 1
                    
                    logger.info(
                        f"Freed slot {booking.slot.slot_id} from {booking.get_status_display()} "
                        f"booking {booking.booking_id}"
                    )
        
        if freed_count > 0:
            logger.info(f"Freed {freed_count} slots from completed/cancelled bookings")
