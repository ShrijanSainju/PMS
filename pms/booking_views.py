from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

from .models import Booking, ParkingSlot, Vehicle, ParkingSession
from .forms import BookingForm
from .permissions import require_customer, require_staff_or_manager, require_approved_user

logger = logging.getLogger(__name__)


@require_customer
def my_bookings(request):
    """View all customer bookings"""
    bookings = Booking.objects.filter(
        customer=request.user
    ).select_related('vehicle', 'slot').order_by('-scheduled_arrival')
    
    # Categorize bookings
    upcoming = bookings.filter(status='confirmed', scheduled_arrival__gt=timezone.now())
    active = bookings.filter(status='active')
    past = bookings.filter(status__in=['completed', 'cancelled', 'expired']).order_by('-scheduled_arrival')[:10]
    
    context = {
        'bookings': bookings,
        'upcoming_bookings': upcoming,
        'active_bookings': active,
        'past_bookings': past,
        'total_bookings': bookings.count(),
    }
    
    return render(request, 'customer/my_bookings.html', context)


@require_customer
def create_booking(request):
    """Customer creates a new parking booking"""
    from .models import SystemSettings
    
    # Check if user has any active vehicles
    user_vehicles = Vehicle.objects.filter(owner=request.user, is_active=True)
    
    if not user_vehicles.exists():
        messages.warning(request, 'Please add a vehicle before making a booking.')
        return redirect('add_vehicle')
    
    if request.method == 'POST':
        form = BookingForm(request.user, request.POST)
        if form.is_valid():
            # Get the slot selected by customer BEFORE saving
            slot_id = form.cleaned_data.get('slot')
            try:
                selected_slot = ParkingSlot.objects.get(id=slot_id)
                
                # Verify slot is available
                if selected_slot.is_occupied:
                    messages.error(request, f'Slot {selected_slot.slot_id} is currently occupied. Please select another slot.')
                    return render(request, 'customer/create_booking.html', {
                        'form': form,
                        'user_vehicles': user_vehicles,
                        'available_slots_count': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
                        'settings': SystemSettings.load(),
                    })
                
                if selected_slot.is_reserved:
                    messages.error(request, f'Slot {selected_slot.slot_id} is already reserved. Please select another slot.')
                    return render(request, 'customer/create_booking.html', {
                        'form': form,
                        'user_vehicles': user_vehicles,
                        'available_slots_count': ParkingSlot.objects.filter(is_occupied=False, is_reserved=False).count(),
                        'settings': SystemSettings.load(),
                    })
                
                # Create booking instance without saving
                booking = form.save(commit=False)
                booking.customer = request.user
                booking.slot = selected_slot
                booking.status = 'confirmed'
                booking.save()
                
                # Reserve the slot
                selected_slot.is_reserved = True
                selected_slot.save()
                
                # Send confirmation
                try:
                    send_booking_confirmation(booking)
                except Exception as e:
                    logger.error(f"Failed to send booking confirmation: {e}")
                
                messages.success(request, f'Booking confirmed! Slot {selected_slot.slot_id} reserved for {booking.scheduled_arrival.strftime("%B %d, %Y at %I:%M %p")}')
                return redirect('booking_detail', booking_id=booking.id)
                
            except ParkingSlot.DoesNotExist:
                messages.error(request, 'Invalid slot selected. Please try again.')
    else:
        form = BookingForm(request.user)
    
    # Get availability info
    available_slots_count = ParkingSlot.objects.filter(
        is_occupied=False,
        is_reserved=False
    ).count()
    
    context = {
        'form': form,
        'user_vehicles': user_vehicles,
        'available_slots_count': available_slots_count,
        'settings': SystemSettings.load(),
    }
    
    return render(request, 'customer/create_booking.html', context)


@require_customer
def booking_detail(request, booking_id):
    """View booking details"""
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        customer=request.user
    )
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'customer/booking_detail.html', context)


@require_approved_user
def cancel_booking(request, booking_id):
    """Cancel a booking - accessible by customer (own bookings) or staff/manager (any booking)"""
    user_profile = getattr(request.user, 'userprofile', None)
    is_staff_or_manager = user_profile and user_profile.user_type in ['staff', 'manager']
    
    # Staff/manager can cancel any booking, customers only their own
    if is_staff_or_manager:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    if request.method == 'POST':
        if booking.can_cancel or is_staff_or_manager:
            booking.status = 'cancelled'
            booking.save()
            
            # Free up the slot
            if booking.slot:
                booking.slot.is_reserved = False
                booking.slot.save()
            
            # Send cancellation notification
            try:
                send_cancellation_notification(booking)
            except Exception as e:
                logger.error(f"Failed to send cancellation notification: {e}")
            
            messages.success(request, 'Booking cancelled successfully')
            
            # Redirect based on user type
            if is_staff_or_manager:
                return redirect('staff_bookings_list')
            else:
                return redirect('customer_bookings')
        else:
            if booking.status not in ['pending', 'confirmed']:
                messages.error(request, f'Cannot cancel a {booking.get_status_display()} booking')
            else:
                messages.error(request, 'Cannot cancel within 1 hour of scheduled arrival')
            return redirect('booking_detail', booking_id=booking.id)
    
    return render(request, 'customer/cancel_booking.html', {'booking': booking})


@login_required
def check_availability_api(request):
    """API endpoint to check slot availability for a specific time"""
    if request.method == 'GET':
        try:
            arrival_str = request.GET.get('arrival')
            duration = int(request.GET.get('duration', 60))
            
            if not arrival_str:
                return JsonResponse({'error': 'Arrival time required'}, status=400)
            
            # Parse arrival time
            from datetime import datetime
            arrival = datetime.fromisoformat(arrival_str.replace('Z', '+00:00'))
            
            # Make timezone aware
            if timezone.is_naive(arrival):
                arrival = timezone.make_aware(arrival)
            
            # Find available slots
            available_slots = find_all_available_slots_for_time(arrival, duration)
            
            return JsonResponse({
                'available': len(available_slots) > 0,
                'count': len(available_slots),
                'slots': [slot.slot_id for slot in available_slots],
                'arrival': arrival.isoformat(),
                'duration': duration
            })
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'GET method required'}, status=405)


# Staff/Manager Views

@require_staff_or_manager
def staff_bookings_list(request):
    """Staff view of all bookings"""
    status_filter = request.GET.get('status', 'all')
    
    bookings_query = Booking.objects.all().select_related('customer', 'vehicle', 'slot')
    
    if status_filter != 'all':
        bookings = bookings_query.filter(status=status_filter)
    else:
        bookings = bookings_query
    
    # Today's bookings
    today = timezone.now().date()
    today_bookings = bookings_query.filter(scheduled_arrival__date=today)
    
    # Stats for the dashboard
    pending_count = bookings_query.filter(status='pending').count()
    confirmed_count = bookings_query.filter(status='confirmed').count()
    active_count = bookings_query.filter(status='active').count()
    today_count = today_bookings.count()
    
    # Upcoming bookings
    upcoming = bookings_query.filter(
        status='confirmed',
        scheduled_arrival__gt=timezone.now()
    ).order_by('scheduled_arrival')[:20]
    
    context = {
        'bookings': bookings.order_by('-scheduled_arrival')[:50],
        'today_bookings': today_bookings,
        'upcoming_bookings': upcoming,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'active_count': active_count,
        'today_count': today_count,
    }
    
    return render(request, 'staff/bookings_list.html', context)


@require_staff_or_manager
def confirm_arrival(request, booking_id):
    """Staff confirms customer arrival and converts booking to active session"""
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        if booking.status == 'confirmed':
            # Check if booking has a slot assigned
            if not booking.slot:
                messages.error(request, 'Cannot check in: No parking slot assigned to this booking')
                return redirect('staff_bookings_list')
            
            # Check if slot is already occupied
            if booking.slot.is_occupied:
                messages.error(request, f'Cannot check in: Slot {booking.slot.slot_id} is already occupied')
                return redirect('staff_bookings_list')
            
            try:
                session = booking.convert_to_session()
                if session:
                    messages.success(request, f'Customer checked in successfully! Session {session.session_id} started in slot {booking.slot.slot_id}.')
                    logger.info(f"Booking {booking.booking_id} converted to session {session.session_id} by {request.user.username}")
                    return redirect('staff_bookings_list')
                else:
                    messages.error(request, 'Failed to start parking session. Please try again.')
            except Exception as e:
                logger.error(f"Error converting booking {booking.booking_id} to session: {str(e)}")
                messages.error(request, f'Error starting session: {str(e)}')
        else:
            messages.error(request, f'Cannot check in a {booking.get_status_display()} booking. Only confirmed bookings can be checked in.')
        
        return redirect('staff_bookings_list')
    
    return render(request, 'staff/confirm_arrival.html', {'booking': booking})


# Helper Functions

def find_available_slot_for_time(arrival_time, duration_minutes):
    """Find a single available slot for specific time"""
    slots = find_all_available_slots_for_time(arrival_time, duration_minutes)
    return slots.first() if slots else None


def find_all_available_slots_for_time(arrival_time, duration_minutes):
    """Find all available slots for specific time period"""
    end_time = arrival_time + timedelta(minutes=duration_minutes)
    
    # Get slots that are already booked during this time
    conflicting_bookings = Booking.objects.filter(
        Q(status__in=['confirmed', 'active']) &
        (
            # Booking starts during our time
            Q(scheduled_arrival__lt=end_time, scheduled_arrival__gte=arrival_time) |
            # Booking ends during our time
            Q(scheduled_arrival__lt=arrival_time, 
              scheduled_arrival__gte=arrival_time - timedelta(hours=3))
        )
    ).values_list('slot_id', flat=True)
    
    # Find available slots
    available_slots = ParkingSlot.objects.exclude(
        id__in=conflicting_bookings
    ).filter(
        is_occupied=False
    )
    
    return available_slots


def send_booking_confirmation(booking):
    """Send email confirmation for booking"""
    subject = f'Parking Booking Confirmed - {booking.booking_id}'
    message = f"""
Dear {booking.customer.get_full_name() or booking.customer.username},

Your parking booking has been confirmed!

Booking Details:
- Booking ID: {booking.booking_id}
- Vehicle: {booking.vehicle.plate_number} ({booking.vehicle.display_name})
- Parking Slot: {booking.slot.slot_id}
- Scheduled Arrival: {booking.scheduled_arrival.strftime('%B %d, %Y at %I:%M %p')}
- Expected Duration: {booking.expected_duration} minutes
- Estimated Fee: ₹{booking.estimated_fee}

Important:
- Please arrive within 30 minutes of your scheduled time
- Your booking will expire if you don't arrive within this window
- You can cancel up to 1 hour before your scheduled arrival

Thank you for using our Parking Management System!

Best regards,
PMS Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.customer.email],
            fail_silently=False,
        )
        logger.info(f"Booking confirmation sent to {booking.customer.email}")
    except Exception as e:
        logger.error(f"Failed to send booking confirmation email: {e}")
        raise


def send_cancellation_notification(booking):
    """Send cancellation notification"""
    subject = f'Booking Cancelled - {booking.booking_id}'
    message = f"""
Dear {booking.customer.get_full_name() or booking.customer.username},

Your parking booking has been cancelled.

Cancelled Booking:
- Booking ID: {booking.booking_id}
- Vehicle: {booking.vehicle.plate_number}
- Scheduled Arrival: {booking.scheduled_arrival.strftime('%B %d, %Y at %I:%M %p')}

You can make a new booking anytime.

Thank you for using our Parking Management System!

Best regards,
PMS Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.customer.email],
            fail_silently=False,
        )
        logger.info(f"Cancellation notification sent to {booking.customer.email}")
    except Exception as e:
        logger.error(f"Failed to send cancellation notification: {e}")


def check_expired_bookings():
    """Check and expire bookings that customer didn't show up for (run as cron job)"""
    now = timezone.now()
    grace_period = timedelta(minutes=30)
    
    expired = Booking.objects.filter(
        status='confirmed',
        scheduled_arrival__lt=now - grace_period,
        actual_arrival__isnull=True
    )
    
    for booking in expired:
        booking.status = 'expired'
        booking.save()
        
        # Free up the slot
        if booking.slot:
            booking.slot.is_reserved = False
            booking.slot.save()
        
        logger.info(f"Booking {booking.booking_id} expired (no-show)")
    
    return expired.count()


def send_booking_reminders():
    """Send reminders 30 minutes before arrival (run as cron job)"""
    now = timezone.now()
    reminder_window_start = now + timedelta(minutes=25)
    reminder_window_end = now + timedelta(minutes=35)
    
    upcoming_bookings = Booking.objects.filter(
        status='confirmed',
        scheduled_arrival__gte=reminder_window_start,
        scheduled_arrival__lte=reminder_window_end
    )
    
    for booking in upcoming_bookings:
        subject = f'Reminder: Parking Booking in 30 Minutes - {booking.booking_id}'
        message = f"""
Dear {booking.customer.get_full_name() or booking.customer.username},

This is a reminder that your parking booking is in 30 minutes:

- Slot: {booking.slot.slot_id}
- Arrival Time: {booking.scheduled_arrival.strftime('%I:%M %p')}
- Vehicle: {booking.vehicle.plate_number}

Please arrive on time to avoid cancellation.

Best regards,
PMS Team
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [booking.customer.email],
                fail_silently=True,
            )
            logger.info(f"Reminder sent for booking {booking.booking_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder for booking {booking.booking_id}: {e}")
    
    return upcoming_bookings.count()
