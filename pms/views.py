
import cv2
import requests
import time
import logging
from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from .models import ParkingSlot, ParkingSession, Vehicle, Booking
from .serializers import ParkingSlotSerializer
from .decorators import require_staff_or_manager, require_approved_user
from .permissions import require_staff_or_manager, require_approved_user
import json
# Configure logging
logger = logging.getLogger(__name__)

# Import consolidated views from modular structure
from .dashboard_views import (
    home_screen_view, navbar, manager_dashboard, adminbase,
    dashboard_view, dashboard_analytics_api, live_stats_api
)
from .auth_views import manager_logout_view

# def login_redirect_view(request):
#     if request.user.is_superuser:
#         return redirect('/adminbase/')
#     elif request.user.groups.filter(name='Staff').exists():
#         return redirect('/staff/dashboard/')
#     elif request.user.groups.filter(name='Security').exists():
#         return redirect('/security/dashboard/')
#     else:
#         return redirect('/home/')
    
# def admin_logout_view(request):
#     logout(request)
#     return redirect('manager/logout')

# =======
#     return render(request, 'admin/adminbase.html',{})



# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from .models import ParkingSlot
# from .serializers import ParkingSlotSerializer



# @api_view(['POST'])
# def update_slot(request):
#     slot_id = request.data.get('slot_id')
#     is_occupied = request.data.get('is_occupied')

#     if slot_id is None or is_occupied is None:
#         return Response({"error": "Missing data"}, status=400)

#     slot, created = ParkingSlot.objects.get_or_create(slot_id=slot_id)
#     slot.is_occupied = is_occupied
#     slot.save()
#     return Response({"message": f"Updated slot {slot_id} to {'Occupied' if is_occupied else 'Vacant'}"})



# from rest_framework import viewsets


# class ParkingSlotViewSet(viewsets.ModelViewSet):
#     queryset = ParkingSlot.objects.all()
#     serializer_class = ParkingSlotSerializer




# from django.shortcuts import render
# from django.http import JsonResponse
# from .models import ParkingSlot

# def dashboard_view(request):
#     return render(request, 'admin/dashboard.html')


# def slot_status_api(request):
#     slots = ParkingSlot.objects.all().order_by('slot_id')
#     data = [
#         {
#             'slot_id': slot.slot_id,
#             'is_occupied': slot.is_occupied,
#             'timestamp': slot.timestamp,
#         }
#         for slot in slots
#     ]
#     return JsonResponse(data, safe=False)


# import cv2
# from django.http import StreamingHttpResponse
# import time

# # Camera Feed Generator



# def gen_frames():
#     cap = cv2.VideoCapture('parking_lot.mp4')  # or use 0 for webcam

#     parking_slots = [
#         (60, 0, 150, 57), (60, 56, 150, 57), (60, 115, 150, 59),
#         (60, 175, 150, 59), (60, 235, 150, 59), (60, 295, 150, 59),
#         (60, 355, 150, 59), (212, 0, 150, 57), (212, 56, 150, 57),
#         (212, 115, 150, 59), (212, 175, 150, 59), (212, 235, 150, 59),
#         (212, 295, 150, 59), (212, 355, 150, 59),
#     ]

#     occupancy_threshold = 0.1

#     while True:
#         success, frame = cap.read()
#         if not success:
#             break

#         for idx, (x, y, w, h) in enumerate(parking_slots):
#             row = 'A' if idx < 7 else 'B'
#             num = (idx % 7) + 1
#             slot_id = f"{row}{num}"

#             slot = frame[y:y+h, x:x+w]
#             gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
#             edges = cv2.Canny(gray, 50, 150)
#             non_zero = cv2.countNonZero(edges)
#             total_pixels = w * h
#             is_occupied = non_zero > total_pixels * occupancy_threshold

#             color = (0, 0, 255) if is_occupied else (0, 255, 0)
#             label = "Occupied" if is_occupied else "Vacant"
#             cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
#             cv2.putText(frame, label, (x, y - 5),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#         time.sleep(1 / 30) 

# def video_feed(request):
#     return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
# >>>>>>> Stashed changes

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets

from .models import ParkingSlot, ParkingSession
from .serializers import ParkingSlotSerializer
import cv2
import time

# --- Standard Views ---

def home_screen_view(request):
    print(request.headers)
    return render(request, 'manager/homepage.html', {})

def navbar(request):
    return render(request, 'manager/navbar.html', {})

def admin_dashboard(request):
    return render(request, 'manager/admin_dashboard.html', {})

def adminbase(request):
    return render(request, 'manager/adminbase.html', {})

def admin_logout_view(request):
    logout(request)
    return redirect('manager/logout')

# --- Login Views ---

def staff_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='Staff').exists():
            login(request, user)
            return redirect('/staff/dashboard/')
        else:
            messages.error(request, 'Invalid credentials or not a staff member')
    return render(request, 'staff_login.html')

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.groups.filter(name='Admin').exists():
            login(request, user)
            return redirect('/manager/dashboard/')
        else:
            messages.error(request, 'Invalid credentials or not an admin member')
    return render(request, 'admin_login.html')

def login_redirect_view(request):
    if request.user.is_superuser:
        return redirect('/adminbase/')
    elif request.user.groups.filter(name='Staff').exists():
        return redirect('/staff/dashboard/')
    elif request.user.groups.filter(name='Security').exists():
        return redirect('/security/dashboard/')
    else:
        return redirect('/home/')

# --- API and Dashboard Views ---

@api_view(['POST'])
@csrf_exempt  # Allow OpenCV detector to call this endpoint
def update_slot(request):
    slot_id = request.data.get('slot_id')
    is_occupied = request.data.get('is_occupied')

    if slot_id is None or is_occupied is None:
        return Response({"error": "Missing data"}, status=400)

    # Convert to boolean in case it's sent as string
    is_occupied = str(is_occupied).lower() in ['true', '1']

    slot, created = ParkingSlot.objects.get_or_create(slot_id=slot_id)

    if slot.is_reserved and not is_occupied:
        return Response({"message": f"Slot {slot_id} is reserved; ignoring vacancy signal."})

    # Handle camera detection for reserved slots
    if slot.is_reserved and is_occupied:
        session = ParkingSession.objects.filter(slot=slot, status='pending').last()
        
        if session:
            # AUTO-ACTIVATE SESSION (same behavior for both walk-in and bookings)
            session.status = 'active'
            if session.start_time is None:
                session.start_time = timezone.now()
            session.save()
            
            # Update slot to occupied
            slot.is_occupied = True
            slot.is_reserved = False
            slot.save()
            
            # If this is a booking-related session, update booking camera detection
            try:
                booking = Booking.objects.get(parking_session=session, status='active')
                if not booking.camera_detected:
                    booking.camera_detected = True
                    booking.camera_detected_at = timezone.now()
                    booking.save()
                    logger.info(f"Camera detected and auto-activated session for booking {booking.booking_id}")
            except Booking.DoesNotExist:
                # This is a walk-in session (not from booking)
                logger.info(f"Camera detected and auto-activated walk-in session {session.session_id}")
            
            return Response({
                "message": f"Vehicle detected in slot {slot_id}. Session {session.session_id} auto-activated.",
                "session_id": session.session_id,
                "auto_activated": True
            })

    # Update occupancy
    slot.is_occupied = is_occupied
    slot.save()

    return Response({"message": f"Updated slot {slot_id} to {'Occupied' if is_occupied else 'Vacant'}"})


@api_view(['POST'])
@require_staff_or_manager
def auto_assign_slot(request):
    """Automatically assign the best available slot to a vehicle"""
    from .security import validate_vehicle_number, log_security_event, is_rate_limited

    # Apply rate limiting
    if is_rate_limited(request, 'api_calls'):
        return Response({"error": "Rate limit exceeded"}, status=429)

    vehicle_number = request.data.get('vehicle_number')
    zone_preference = request.data.get('zone_preference', 'A')

    if not vehicle_number:
        log_security_event(request, 'invalid_auto_assign', {'missing_vehicle_number': True})
        return Response({"error": "Vehicle number is required"}, status=400)

    # Validate vehicle number
    valid, result = validate_vehicle_number(vehicle_number)
    if not valid:
        log_security_event(request, 'invalid_auto_assign', {'invalid_vehicle_number': vehicle_number})
        return Response({"error": f"Invalid vehicle number: {result}"}, status=400)

    vehicle_number = result

    # Check if vehicle already has an active session
    existing_session = ParkingSession.objects.filter(
        vehicle_number=vehicle_number,
        status__in=['pending', 'active']
    ).first()

    if existing_session:
        return Response({
            "error": f"Vehicle {vehicle_number} already has an active session",
            "existing_slot": existing_session.slot.slot_id,
            "session_status": existing_session.status
        }, status=409)

    try:
        # Find available slots, preferring the specified zone
        available_slots = ParkingSlot.objects.filter(
            is_occupied=False,
            is_reserved=False
        ).order_by('slot_id')

        # Filter by zone preference if specified
        if zone_preference:
            preferred_slots = [slot for slot in available_slots if slot.slot_id.startswith(zone_preference)]
            if preferred_slots:
                available_slots = preferred_slots

        if not available_slots:
            return Response({"error": "No available slots"}, status=404)

        # Assign the first available slot
        assigned_slot = available_slots[0]
        assigned_slot.is_reserved = True
        assigned_slot.save()

        # Create a pending session
        session = ParkingSession.objects.create(
            vehicle_number=vehicle_number,
            slot=assigned_slot,
            status='pending'
        )

        logger.info(f"Auto-assigned slot {assigned_slot.slot_id} to vehicle {vehicle_number} by user {request.user.username}")

        return Response({
            "message": f"Slot {assigned_slot.slot_id} assigned to {vehicle_number}",
            "slot_id": assigned_slot.slot_id,
            "session_id": session.id,
            "zone": assigned_slot.slot_id[0] if assigned_slot.slot_id else "Unknown",
            "assigned_by": request.user.username,
            "timestamp": timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in auto-assignment for {vehicle_number}: {str(e)}")
        log_security_event(request, 'auto_assign_error', {'error': str(e), 'vehicle_number': vehicle_number})
        return Response({"error": "Internal server error"}, status=500)


@api_view(['GET'])
@require_approved_user
def get_available_slots(request):
    """Get list of available slots with zone information"""
    zone = request.GET.get('zone')

    available_slots = ParkingSlot.objects.filter(
        is_occupied=False,
        is_reserved=False
    ).order_by('slot_id')

    if zone:
        available_slots = available_slots.filter(slot_id__startswith=zone)

    slots_data = []
    for slot in available_slots:
        slots_data.append({
            'slot_id': slot.slot_id,
            'zone': slot.slot_id[0] if slot.slot_id else "Unknown",
            'last_updated': slot.timestamp.isoformat()
        })

    return Response({
        'available_slots': slots_data,
        'total_count': len(slots_data),
        'zones': list(set([slot['zone'] for slot in slots_data]))
    })


@require_staff_or_manager
def security_dashboard(request):
    """Security monitoring dashboard for administrators"""

    return render(request, 'manager/security_dashboard.html')


@api_view(['GET'])
@require_staff_or_manager
def security_events_api(request):
    """API endpoint for security events"""

    from .security import get_client_ip
    from django.core.cache import cache

    # Get security events from cache
    ip = get_client_ip(request)

    events = []
    # Get recent events (simplified - no hourly breakdown)
    events_key = f"security_events:{ip}"
    events = cache.get(events_key, [])

    # Sort by timestamp
    events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return Response({
        'events': events[:100],  # Return last 100 events
        'total_count': len(events),
        'last_updated': timezone.now().isoformat()
    })


@api_view(['POST'])
@require_staff_or_manager
def security_action_api(request):
    """API endpoint for security actions"""

    action = request.data.get('action')

    if action == 'clear_logs':
        # Clear security logs
        from django.core.cache import cache
        cache.clear()
        logger.info(f"Security logs cleared by {request.user.username}")
        return Response({"message": "Security logs cleared"})

    elif action == 'emergency_lockdown':
        # Implement emergency lockdown
        cache.set('emergency_lockdown', True, 3600)  # 1 hour lockdown
        logger.critical(f"Emergency lockdown initiated by {request.user.username}")
        return Response({"message": "Emergency lockdown activated"})

    elif action == 'export_report':
        # Generate security report
        # This would typically generate a PDF or CSV file
        logger.info(f"Security report requested by {request.user.username}")
        return Response({"message": "Security report generation started"})

    else:
        return Response({"error": "Invalid action"}, status=400)




class ParkingSlotViewSet(viewsets.ModelViewSet):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer

def dashboard_view(request):
    """Redirect to role-based dashboard - this should use the one from dashboard_views.py"""
    from .dashboard_views import dashboard_view as role_based_dashboard
    return role_based_dashboard(request)

def slot_status_api(request):
    """API endpoint for getting slot status - accessible to all logged-in users"""
    # Check if user is authenticated - return JSON error for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    slots = ParkingSlot.objects.all().order_by('slot_id')
    data = []
    now = timezone.now()
    upcoming_window = timedelta(minutes=30)  # Show bookings arriving within 30 minutes

    for slot in slots:
        # Check for pending/active session for this slot
        session = ParkingSession.objects.filter(slot=slot, status__in=['pending', 'active']).last()
        session_status = session.status if session else None
        vehicle_number = session.vehicle_number if session else None
        session_start = session.start_time if session else None

        # Check for upcoming bookings (arriving within 30 minutes)
        upcoming_booking = Booking.objects.filter(
            slot=slot,
            status='confirmed',
            scheduled_arrival__gte=now,
            scheduled_arrival__lte=now + upcoming_window
        ).order_by('scheduled_arrival').first()

        # Calculate when occupied slot will be free
        estimated_free_time = None
        if slot.is_occupied and session and session.start_time:
            # Try to find related booking for duration
            related_booking = Booking.objects.filter(
                slot=slot,
                status='active',
                parking_session=session
            ).first()
            
            if related_booking and related_booking.expected_duration:
                estimated_free_time = (session.start_time + timedelta(minutes=related_booking.expected_duration)).isoformat()

        # Try to find user information for the vehicle
        user_info = None
        vehicle_info = None
        if vehicle_number:
            try:
                from .models import Vehicle
                vehicle_info = Vehicle.objects.filter(
                    plate_number=vehicle_number,
                    is_active=True
                ).select_related('owner', 'owner__userprofile').first()

                if vehicle_info and vehicle_info.owner:
                    user_profile = getattr(vehicle_info.owner, 'userprofile', None)
                    user_info = {
                        'name': vehicle_info.owner.get_full_name() or vehicle_info.owner.username,
                        'email': vehicle_info.owner.email,
                        'phone': user_profile.phone_number if user_profile else None,
                        'user_type': user_profile.get_user_type_display() if user_profile else 'Unknown'
                    }
            except:
                pass

        slot_data = {
            'id': slot.id,
            'slot_id': slot.slot_id,
            'is_occupied': slot.is_occupied,
            'is_reserved': slot.is_reserved,
            'session_status': session_status,
            'vehicle_number': vehicle_number,
            'session_start': session_start.isoformat() if session_start else None,
            'timestamp': slot.timestamp.isoformat(),
            'estimated_free_time': estimated_free_time,
            'upcoming_booking': {
                'booking_id': upcoming_booking.booking_id,
                'scheduled_arrival': upcoming_booking.scheduled_arrival.isoformat(),
                'vehicle': upcoming_booking.vehicle.plate_number if upcoming_booking.vehicle else None,
                'customer': upcoming_booking.customer.get_full_name() or upcoming_booking.customer.username,
                'minutes_until_arrival': int((upcoming_booking.scheduled_arrival - now).total_seconds() / 60)
            } if upcoming_booking else None,
            'user_info': user_info,
            'vehicle_info': {
                'make': vehicle_info.make if vehicle_info else None,
                'model': vehicle_info.model if vehicle_info else None,
                'year': vehicle_info.year if vehicle_info else None,
                'color': vehicle_info.color if vehicle_info else None,
                'type': vehicle_info.get_vehicle_type_display() if vehicle_info else None
            } if vehicle_info else None
        }

        data.append(slot_data)

    return JsonResponse(data, safe=False)


@login_required
def check_slot_availability(request):
    """API endpoint to check if a slot is available for a specific time window"""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET method required'}, status=405)
    
    slot_id = request.GET.get('slot_id')
    scheduled_arrival_str = request.GET.get('scheduled_arrival')
    expected_duration = request.GET.get('expected_duration')
    
    # Validate parameters
    if not all([slot_id, scheduled_arrival_str, expected_duration]):
        return JsonResponse({
            'available': False,
            'error': 'Missing required parameters: slot_id, scheduled_arrival, expected_duration'
        }, status=400)
    
    try:
        # Parse inputs
        slot = ParkingSlot.objects.get(id=slot_id)
        scheduled_arrival = timezone.datetime.fromisoformat(scheduled_arrival_str.replace('Z', '+00:00'))
        expected_duration = int(expected_duration)
        scheduled_departure = scheduled_arrival + timedelta(minutes=expected_duration)
        
        # Check if slot is currently occupied (for immediate bookings)
        if slot.is_occupied and scheduled_arrival <= timezone.now():
            return JsonResponse({
                'available': False,
                'reason': 'Slot is currently occupied',
                'slot_id': slot.slot_id
            })
        
        # Check for time-based conflicts
        time_conflicts = []
        for booking in Booking.objects.filter(slot=slot, status__in=['confirmed', 'active']):
            booking_end = booking.scheduled_arrival + timedelta(minutes=booking.expected_duration)
            # Check if time windows overlap
            if not (booking_end <= scheduled_arrival or booking.scheduled_arrival >= scheduled_departure):
                time_conflicts.append({
                    'booking_id': booking.id,
                    'start': booking.scheduled_arrival.isoformat(),
                    'end': booking_end.isoformat(),
                    'vehicle': booking.vehicle.plate_number if booking.vehicle else None
                })
        
        if time_conflicts:
            return JsonResponse({
                'available': False,
                'reason': 'Time slot conflict',
                'conflicts': time_conflicts,
                'slot_id': slot.slot_id
            })
        
        # Slot is available
        return JsonResponse({
            'available': True,
            'slot_id': slot.slot_id,
            'message': f'Slot {slot.slot_id} is available from {scheduled_arrival.strftime("%b %d, %I:%M %p")} to {scheduled_departure.strftime("%I:%M %p")}'
        })
        
    except ParkingSlot.DoesNotExist:
        return JsonResponse({
            'available': False,
            'error': 'Slot not found'
        }, status=404)
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'available': False,
            'error': f'Invalid parameter format: {str(e)}'
        }, status=400)


@require_approved_user
def slot_status_sync_api(request):
    """API to check for mismatches between detection and database"""
    slots = ParkingSlot.objects.all().order_by('slot_id')

    # Get detection results from the latest frame (if available)
    detection_results = request.GET.get('detection_data')

    sync_data = []
    total_mismatches = 0

    for slot in slots:
        slot_data = {
            'slot_id': slot.slot_id,
            'db_status': slot.is_occupied,
            'db_reserved': slot.is_reserved,
            'last_updated': slot.timestamp.isoformat(),
            'mismatch': False,
            'detection_status': None
        }

        # If detection data is provided, compare with database
        if detection_results:
            try:
                detection_data = json.loads(detection_results)
                for detection in detection_data:
                    if detection['slot_id'] == slot.slot_id:
                        slot_data['detection_status'] = detection['is_occupied']
                        slot_data['mismatch'] = detection['is_occupied'] != slot.is_occupied
                        if slot_data['mismatch']:
                            total_mismatches += 1
                        break
            except (json.JSONDecodeError, KeyError):
                pass

        sync_data.append(slot_data)

    return JsonResponse({
        'slots': sync_data,
        'total_mismatches': total_mismatches,
        'sync_timestamp': timezone.now().isoformat()
    })


# dashboard_analytics_api is imported from dashboard_views.py


# live_stats_api is imported from dashboard_views.py

# --- Video Streaming Logic ---
from django.http import StreamingHttpResponse

def gen_frames():
    cap = cv2.VideoCapture(0
                           )  # Change to 0 for webcam 1 for droidcam 2 for droidcam2 'parking_lot.mp4' for dummy video

    parking_slots = [
        (60, 0, 150, 57), (60, 56, 150, 57), (60, 115, 150, 59),
        (60, 175, 150, 59), (60, 235, 150, 59), (60, 295, 150, 59),
        (60, 355, 150, 59), (212, 0, 150, 57), (212, 56, 150, 57),
        (212, 115, 150, 59), (212, 175, 150, 59), (212, 235, 150, 59),
        (212, 295, 150, 59), (212, 355, 150, 59),
    ]

    occupancy_threshold = 0.03 #0.1
    last_update = {}  # Track last update time for each slot to avoid too frequent updates

    while True:
        success, frame = cap.read()
        if not success:
            break

        current_time = timezone.now()

        for idx, (x, y, w, h) in enumerate(parking_slots):
            row = 'A' if idx < 7 else 'B'
            num = (idx % 7) + 1
            slot_id = f"{row}{num}"

            slot = frame[y:y+h, x:x+w]
            gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            non_zero = cv2.countNonZero(edges)
            total_pixels = w * h
            is_occupied = non_zero > total_pixels * occupancy_threshold

            # Get or create database slot
            try:
                db_slot, created = ParkingSlot.objects.get_or_create(
                    slot_id=slot_id,
                    defaults={'is_occupied': is_occupied, 'is_reserved': False}
                )

                # Update database if detection differs and enough time has passed
                time_since_last_update = (current_time - last_update.get(slot_id, current_time - timedelta(seconds=10))).total_seconds()

                if db_slot.is_occupied != is_occupied and time_since_last_update > 1:  # Update every 1 second max
                    # Don't update reserved slots to vacant (false vacancy signals)
                    if not (db_slot.is_reserved and not is_occupied):
                        # Call the API endpoint instead of directly updating database
                        try:
                            import requests
                            api_url = 'http://127.0.0.1:8000/api/update-slot/'
                            data = {
                                'slot_id': slot_id,
                                'is_occupied': is_occupied,
                                'detector_id': 'video_feed'
                            }
                            response = requests.post(api_url, json=data, timeout=1)
                            if response.status_code == 200:
                                last_update[slot_id] = current_time
                                print(f"[VIDEO FEED] API Updated {slot_id}: {'Occupied' if is_occupied else 'Vacant'}")
                            else:
                                print(f"[VIDEO FEED] API Error {slot_id}: {response.status_code}")
                        except Exception as api_error:
                            # Fallback to direct database update if API fails
                            db_slot.is_occupied = is_occupied
                            db_slot.save()
                            last_update[slot_id] = current_time
                            print(f"[VIDEO FEED] Direct DB Updated {slot_id}: {'Occupied' if is_occupied else 'Vacant'} (API failed: {api_error})")
                    else:
                        print(f"[VIDEO FEED] Ignoring vacancy signal for reserved slot {slot_id}")

                # Simple three-state color coding: Green=Vacant, Yellow=Reserved, Red=Occupied
                if db_slot.is_reserved and not db_slot.is_occupied:
                    color = (0, 255, 255)  # Yellow for reserved
                    label = f"{slot_id}: Reserved"
                elif db_slot.is_occupied:
                    color = (0, 0, 255)  # Red for occupied
                    label = f"{slot_id}: Occupied"
                else:
                    color = (0, 255, 0)  # Green for vacant
                    label = f"{slot_id}: Vacant"

            except Exception as e:
                # Fallback to detection if there's any database error
                color = (0, 0, 255) if is_occupied else (0, 255, 0)
                label = f"{slot_id}: {'Occupied' if is_occupied else 'Vacant'} (DB ERROR)"
                print(f"[VIDEO FEED] Database error for {slot_id}: {e}")

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(1 / 30)

def video_feed(request):
    return StreamingHttpResponse(gen_frames(), content_type='multipart/x-mixed-replace; boundary=frame')



from django.shortcuts import render
from .models import ParkingSlot, ParkingSession
from .forms import VehicleEntryForm

from django.utils import timezone

@require_staff_or_manager
def assign_slot(request):
    # Determine template based on user role
    user_profile = getattr(request.user, 'userprofile', None)
    is_manager = user_profile and user_profile.user_type == 'manager'
    template_prefix = 'manager' if is_manager else 'staff'

    if request.method == 'POST':
        form = VehicleEntryForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']
            zone_preference = request.POST.get('zone_preference', 'A')

            # Check if vehicle already has a pending or active session
            existing_session = ParkingSession.objects.filter(
                vehicle_number=vehicle_number,
                status__in=['pending', 'active']
            ).first()

            if existing_session:
                return render(request, f'{template_prefix}/assign_slot.html', {
                    'form': form,
                    'error': f"Vehicle {vehicle_number} already has an ongoing session (Slot {existing_session.slot.slot_id}).",
                    'available_slots': [],
                    'zones': []
                })

            # Try to use auto-assignment logic for better slot selection
            try:
                # Validate vehicle number (basic validation)
                if not vehicle_number or len(vehicle_number.strip()) < 2:
                    error_message = "Invalid vehicle number"
                else:
                    vehicle_number = vehicle_number.strip().upper()

                    # Find available slots, preferring the specified zone
                    available_slots = ParkingSlot.objects.filter(
                        is_occupied=False,
                        is_reserved=False
                    ).order_by('slot_id')

                    # Filter by zone preference if specified
                    if zone_preference and zone_preference != '':
                        preferred_slots = [slot for slot in available_slots if slot.slot_id.startswith(zone_preference)]
                        if preferred_slots:
                            available_slots = preferred_slots

                    if not available_slots:
                        error_message = "No available slots"
                    else:
                        # Assign the first available slot
                        assigned_slot = available_slots[0]
                        assigned_slot.is_reserved = True
                        assigned_slot.save()

                        # Create a pending session
                        session = ParkingSession.objects.create(
                            vehicle_number=vehicle_number,
                            slot=assigned_slot,
                            status='pending'
                        )

                        # Try to find the vehicle owner
                        vehicle_owner = None
                        vehicle_info = None
                        try:
                            from .models import Vehicle
                            vehicle_info = Vehicle.objects.filter(
                                plate_number=vehicle_number,
                                is_active=True
                            ).select_related('owner', 'owner__userprofile').first()

                            if vehicle_info:
                                vehicle_owner = vehicle_info.owner
                        except:
                            pass

                        return render(request, f'{template_prefix}/assign_success.html', {
                            'session': session,
                            'slot': assigned_slot,
                            'auto_assigned': True,
                            'zone': assigned_slot.slot_id[0] if assigned_slot.slot_id else 'Unknown',
                            'message': f"Slot {assigned_slot.slot_id} automatically assigned to {vehicle_number}",
                            'vehicle_owner': vehicle_owner,
                            'vehicle_info': vehicle_info,
                        })

            except Exception as e:
                error_message = f"Auto-assignment failed: {str(e)}"
                logger.warning(f"Auto-assignment failed: {e}")

            # Fallback to manual assignment if auto-assignment fails
            available_slots = ParkingSlot.objects.filter(
                is_occupied=False,
                is_reserved=False
            ).order_by('slot_id')

            # Prefer slots in the requested zone
            if zone_preference:
                zone_slots = [slot for slot in available_slots if slot.slot_id.startswith(zone_preference)]
                if zone_slots:
                    available_slots = zone_slots

            if not available_slots:
                return render(request, f'{template_prefix}/assign_slot.html', {
                    'form': form,
                    'error': error_message if 'error_message' in locals() else 'No available slots at the moment.',
                    'available_slots': [],
                    'zones': []
                })

            # Manual assignment
            available_slot = available_slots[0]

            # Create session with 'pending' status
            session = ParkingSession.objects.create(
                vehicle_number=vehicle_number,
                slot=available_slot,
                status='pending'
            )

            # Reserve the slot (do not mark occupied yet)
            available_slot.is_reserved = True
            available_slot.save()

            # Try to find the vehicle owner
            vehicle_owner = None
            vehicle_info = None
            try:
                from .models import Vehicle
                vehicle_info = Vehicle.objects.filter(
                    plate_number=vehicle_number,
                    is_active=True
                ).select_related('owner', 'owner__userprofile').first()

                if vehicle_info:
                    vehicle_owner = vehicle_info.owner
            except:
                pass

            logger.info(f"Manually assigned slot {available_slot.slot_id} to vehicle {vehicle_number}")

            return render(request, f'{template_prefix}/assign_success.html', {
                'session': session,
                'slot': available_slot,
                'auto_assigned': False,
                'zone': available_slot.slot_id[0] if available_slot.slot_id else 'Unknown',
                'message': f"Slot {available_slot.slot_id} assigned to {vehicle_number}",
                'vehicle_owner': vehicle_owner,
                'vehicle_info': vehicle_info,
            })

    else:
        form = VehicleEntryForm()

        # Get available slots for display
        try:
            import requests
            api_url = request.build_absolute_uri('/api/available-slots/')
            response = requests.get(api_url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                available_slots = data.get('available_slots', [])
                zones = data.get('zones', [])
            else:
                available_slots = []
                zones = []
        except Exception as e:
            logger.warning(f"Failed to fetch available slots: {e}")
            available_slots = []
            zones = []

    return render(request, f'{template_prefix}/assign_slot.html', {
        'form': form,
        'available_slots': available_slots,
        'zones': zones
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import ParkingSlot, ParkingSession
from .forms import VehicleEntryForm, LookupForm

@require_staff_or_manager
def end_session(request, slot_id):
    slot = get_object_or_404(ParkingSlot, slot_id=slot_id)
    session = ParkingSession.objects.filter(slot=slot, status='active').last()

    if session:
        session.end_time = timezone.now()
        session.status = 'completed'
        session.fee = session.calculate_fee()
        session.save()

        # Clear both occupied and reserved flags
        slot.is_occupied = False
        slot.is_reserved = False
        slot.save()

        # Also complete any related booking
        try:
            booking = Booking.objects.get(parking_session=session, status='active')
            booking.status = 'completed'
            booking.actual_departure = timezone.now()
            booking.save()
        except Booking.DoesNotExist:
            pass

        return render(request, 'staff/end_success.html', {'session': session})
    else:
        return render(request, 'staff/end_success.html', {'error': 'No active session found.'})


@require_staff_or_manager
def activate_pending_session(request, session_id):
    """
    Manually activate a pending parking session.
    For walk-in sessions: Used when camera detection fails or for manual override.
    For booking sessions: Provides dual confirmation (camera + staff) before activation.
    """
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    session = get_object_or_404(ParkingSession, session_id=session_id, status='pending')
    
    # Check if this is a booking-related session
    try:
        booking = Booking.objects.get(parking_session=session, status='active')
        # Booking session - check for dual confirmation
        if not booking.camera_detected:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Camera has not detected the vehicle yet. Please wait for camera confirmation.',
                    'requires_camera': True
                })
            else:
                from django.contrib import messages
                messages.warning(request, 'Camera has not detected the vehicle yet. Please wait for camera confirmation before activating.')
                return redirect('staff_bookings_list')
        
        # Camera detected AND staff confirming - activate session
        logger.info(f"Dual confirmation completed for booking {booking.booking_id}. Activating session {session.session_id}.")
        
    except Booking.DoesNotExist:
        # Walk-in session - no dual confirmation required
        logger.info(f"Manual activation of walk-in session {session.session_id}.")
        pass
    
    # Activate the session
    session.status = 'active'
    if session.start_time is None:
        session.start_time = timezone.now()
    session.save()
    
    # Update slot status
    session.slot.is_reserved = False
    session.slot.is_occupied = True
    session.slot.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        return JsonResponse({
            'success': True,
            'message': f'Session {session.session_id} activated successfully',
            'session_id': session.session_id,
            'vehicle_number': session.vehicle_number,
            'slot_id': session.slot.slot_id,
            'start_time': session.start_time.isoformat()
        })
    else:
        # Regular request - redirect back
        from django.contrib import messages
        messages.success(request, f'Session {session.session_id} activated successfully!')
        try:
            booking = Booking.objects.get(parking_session=session)
            return redirect('staff_bookings_list')
        except Booking.DoesNotExist:
            return redirect('unified-parking-management')


@require_approved_user
def history_log(request):
    """
    History view that shows:
    - All sessions for staff/manager
    - Only user's own vehicle sessions for customers
    """
    user_profile = getattr(request.user, 'userprofile', None)
    is_customer = user_profile and user_profile.user_type == 'customer'
    
    if is_customer:
        # For customers, only show their own vehicle sessions
        from .models import Vehicle
        customer_vehicles = Vehicle.objects.filter(owner=request.user, is_active=True)
        customer_plate_numbers = list(customer_vehicles.values_list('plate_number', flat=True))
        
        sessions = ParkingSession.objects.filter(
            vehicle_number__in=customer_plate_numbers
        ).order_by('-start_time') if customer_plate_numbers else ParkingSession.objects.none()
    else:
        # For staff/manager, show all sessions
        sessions = ParkingSession.objects.all().order_by('-start_time')

    # Enhance sessions with user information
    enhanced_sessions = []
    for session in sessions:
        session_data = {
            'session': session,
            'user_info': None,
            'vehicle_info': None
        }

        # Try to find user information for the vehicle
        try:
            from .models import Vehicle
            vehicle_info = Vehicle.objects.filter(
                plate_number=session.vehicle_number,
                is_active=True
            ).select_related('owner', 'owner__userprofile').first()

            if vehicle_info and vehicle_info.owner:
                session_data['vehicle_info'] = vehicle_info
                user_profile = getattr(vehicle_info.owner, 'userprofile', None)
                session_data['user_info'] = {
                    'name': vehicle_info.owner.get_full_name() or vehicle_info.owner.username,
                    'email': vehicle_info.owner.email,
                    'phone': user_profile.phone_number if user_profile else None,
                    'user_type': user_profile.get_user_type_display() if user_profile else 'Unknown'
                }
        except:
            pass

        enhanced_sessions.append(session_data)

    # Use different templates for customer vs staff/manager
    template = 'customer/parking_history.html' if is_customer else 'manager/history.html'
    return render(request, template, {
        'enhanced_sessions': enhanced_sessions,
        'is_customer': is_customer
    })


from django.utils.timezone import now
from django.db.models import Case, When, Value, IntegerField

# @require_approved_user
def lookup_session(request):
    session = None
    elapsed_time = None
    price = None
    from .models import SystemSettings
    settings = SystemSettings.load()
    price_per_minute = float(settings.price_per_minute)
    vehicle_owner = None
    vehicle_info = None
    all_sessions = None

    if request.method == 'POST':
        form = LookupForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']

            # Get the most relevant session (active > pending > recent completed)
            session = (
                ParkingSession.objects
                .filter(vehicle_number=vehicle_number)
                .annotate(
                    status_priority=Case(
                        When(status='active', then=Value(1)),
                        When(status='pending', then=Value(2)),
                        When(status='completed', then=Value(3)),
                        default=Value(4),
                        output_field=IntegerField()
                    )
                )
                .order_by('status_priority', '-start_time')
                .first()
            )

            # Get all sessions for this vehicle (for history)
            all_sessions = ParkingSession.objects.filter(
                vehicle_number=vehicle_number
            ).order_by('-start_time')[:10]  # Last 10 sessions

            # Try to find the vehicle owner from registered vehicles
            try:
                from .models import Vehicle
                vehicle_info = Vehicle.objects.filter(
                    plate_number=vehicle_number,
                    is_active=True
                ).select_related('owner', 'owner__userprofile').first()

                if vehicle_info:
                    vehicle_owner = vehicle_info.owner
            except:
                # If Vehicle model doesn't exist or other error, continue without owner info
                pass

            if session and session.start_time:
                # Use the duration property from the model
                elapsed_time = session.duration
                
                # Calculate price
                if session.status in ['pending', 'active']:
                    end = now()
                else:
                    end = session.end_time or now()
                
                elapsed = end - session.start_time
                elapsed_minutes = int(elapsed.total_seconds() // 60)
                price = elapsed_minutes * price_per_minute
    else:
        form = LookupForm()

    return render(request, 'customer/lookup.html', {
        'form': form,
        'session': session,
        'elapsed_time': elapsed_time,
        'price': price,
        'vehicle_owner': vehicle_owner,
        'vehicle_info': vehicle_info,
        'all_sessions': all_sessions,
    })


@require_staff_or_manager
def unified_parking_management(request):
    """Unified interface for vehicle registry, session lookup, and slot assignment"""
    # Determine user role and template prefix
    user_profile = getattr(request.user, 'userprofile', None)
    is_manager = user_profile and user_profile.user_type == 'manager'
    template_prefix = 'manager' if is_manager else 'staff'

    # Get URL parameters
    action = request.GET.get('action', 'registry')  # registry, lookup, assign
    search_query = request.GET.get('search', '')
    filter_status = request.GET.get('status', 'all')
    vehicle_lookup = request.GET.get('vehicle', '')

    # Initialize context
    context = {
        'action': action,
        'search_query': search_query,
        'filter_status': filter_status,
        'vehicle_lookup': vehicle_lookup,
        'is_manager': is_manager,
    }

    # Handle different actions
    if action == 'assign':
        # Handle slot assignment
        if request.method == 'POST':
            form = VehicleEntryForm(request.POST)
            if form.is_valid():
                vehicle_number = form.cleaned_data['vehicle_number']
                zone_preference = request.POST.get('zone_preference', 'A')

                # Check if vehicle already has a pending or active session
                existing_session = ParkingSession.objects.filter(
                    vehicle_number=vehicle_number,
                    status__in=['pending', 'active']
                ).first()

                if existing_session:
                    context.update({
                        'form': form,
                        'assign_error': f"Vehicle {vehicle_number} already has an ongoing session (Slot {existing_session.slot.slot_id}).",
                        'available_slots': [],
                        'zones': []
                    })
                else:
                    # Implement auto-assignment logic directly
                    try:
                        # Validate vehicle number (basic validation)
                        if not vehicle_number or len(vehicle_number.strip()) < 2:
                            context['assign_error'] = "Invalid vehicle number"
                        else:
                            vehicle_number = vehicle_number.strip().upper()

                            # Find available slots, preferring the specified zone
                            available_slots = ParkingSlot.objects.filter(
                                is_occupied=False,
                                is_reserved=False
                            ).order_by('slot_id')

                            # Filter by zone preference if specified
                            if zone_preference and zone_preference != '':
                                preferred_slots = [slot for slot in available_slots if slot.slot_id.startswith(zone_preference)]
                                if preferred_slots:
                                    available_slots = preferred_slots

                            if not available_slots:
                                context['assign_error'] = "No available slots"
                            else:
                                # Assign the first available slot
                                assigned_slot = available_slots[0]
                                assigned_slot.is_reserved = True
                                assigned_slot.save()

                                # Create a pending session
                                session = ParkingSession.objects.create(
                                    vehicle_number=vehicle_number,
                                    slot=assigned_slot,
                                    status='pending'
                                )

                                # Try to find vehicle owner
                                vehicle_owner = None
                                vehicle_info = None
                                try:
                                    vehicle_info = Vehicle.objects.filter(
                                        plate_number=vehicle_number,
                                        is_active=True
                                    ).select_related('owner', 'owner__userprofile').first()
                                    if vehicle_info:
                                        vehicle_owner = vehicle_info.owner
                                except:
                                    pass

                                context.update({
                                    'assignment_success': True,
                                    'assigned_session': session,
                                    'assigned_slot': assigned_slot,
                                    'vehicle_owner': vehicle_owner,
                                    'vehicle_info': vehicle_info,
                                    'assignment_message': f"Slot {assigned_slot.slot_id} assigned to {vehicle_number}"
                                })

                                logger.info(f"Assigned slot {assigned_slot.slot_id} to vehicle {vehicle_number} by user {request.user.username}")
                    except Exception as e:
                        context['assign_error'] = f"Assignment failed: {str(e)}"
                        logger.error(f"Error in slot assignment for {vehicle_number}: {str(e)}")
        else:
            form = VehicleEntryForm()

        # Get available slots and zones for assignment
        available_slots = ParkingSlot.objects.filter(is_occupied=False, is_reserved=False)
        # Extract zones (first character of slot_id) manually
        zones = set()
        for slot in available_slots:
            if slot.slot_id:
                zones.add(slot.slot_id[0])
        context.update({
            'form': form,
            'available_slots': available_slots,
            'zones': sorted(zones)
        })

    elif action == 'lookup':
        # Handle session lookup
        session = None
        all_sessions = None
        vehicle_owner = None
        vehicle_info = None
        elapsed_time = None
        current_price = None

        if request.method == 'POST' or vehicle_lookup:
            lookup_vehicle = request.POST.get('vehicle_number', vehicle_lookup)
            if lookup_vehicle:
                # Get the most relevant session
                from django.db.models import Case, When, Value, IntegerField
                session = (
                    ParkingSession.objects
                    .filter(vehicle_number=lookup_vehicle)
                    .annotate(
                        status_priority=Case(
                            When(status='active', then=Value(1)),
                            When(status='pending', then=Value(2)),
                            When(status='completed', then=Value(3)),
                            default=Value(4),
                            output_field=IntegerField()
                        )
                    )
                    .order_by('status_priority', '-start_time')
                    .first()
                )

                # Calculate elapsed time and price for active session
                if session and session.status == 'active' and session.start_time:
                    from .models import SystemSettings
                    settings = SystemSettings.load()
                    
                    # Calculate elapsed time
                    now = timezone.now()
                    elapsed = now - session.start_time
                    hours = int(elapsed.total_seconds() // 3600)
                    minutes = int((elapsed.total_seconds() % 3600) // 60)
                    elapsed_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                    
                    # Calculate current price
                    total_minutes = int(elapsed.total_seconds() / 60)
                    current_price = float(settings.price_per_minute) * total_minutes
                
                elif session and session.status == 'completed':
                    # For completed sessions, show total duration and fee
                    if session.start_time and session.end_time:
                        elapsed = session.end_time - session.start_time
                        hours = int(elapsed.total_seconds() // 3600)
                        minutes = int((elapsed.total_seconds() % 3600) // 60)
                        elapsed_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                    
                    if session.fee:
                        current_price = float(session.fee)

                # Get all sessions for history
                all_sessions = ParkingSession.objects.filter(
                    vehicle_number=lookup_vehicle
                ).order_by('-start_time')[:10]

                # Try to find vehicle owner
                try:
                    vehicle_info = Vehicle.objects.filter(
                        plate_number=lookup_vehicle,
                        is_active=True
                    ).select_related('owner', 'owner__userprofile').first()
                    if vehicle_info:
                        vehicle_owner = vehicle_info.owner
                except:
                    pass

        from .forms import LookupForm
        lookup_form = LookupForm(initial={'vehicle_number': vehicle_lookup})
        context.update({
            'lookup_form': lookup_form,
            'lookup_session': session,
            'lookup_all_sessions': all_sessions,
            'lookup_vehicle_owner': vehicle_owner,
            'lookup_vehicle_info': vehicle_info,
            'lookup_elapsed_time': elapsed_time,
            'lookup_current_price': current_price,
        })

    else:  # action == 'registry' (default)
        # Handle vehicle registry
        vehicles = Vehicle.objects.filter(is_active=True).select_related(
            'owner', 'owner__userprofile'
        ).order_by('plate_number')

        # Apply search filter
        if search_query:
            vehicles = vehicles.filter(
                Q(plate_number__icontains=search_query) |
                Q(owner__first_name__icontains=search_query) |
                Q(owner__last_name__icontains=search_query) |
                Q(owner__email__icontains=search_query) |
                Q(make__icontains=search_query) |
                Q(model__icontains=search_query)
            )

        # Enhance vehicles with current parking status
        enhanced_vehicles = []
        for vehicle in vehicles:
            current_session = ParkingSession.objects.filter(
                vehicle_number=vehicle.plate_number,
                status__in=['pending', 'active']
            ).select_related('slot').first()
            
            # Check for active bookings
            current_booking = Booking.objects.filter(
                vehicle=vehicle,
                status__in=['confirmed', 'active']
            ).select_related('slot').first()

            recent_sessions = ParkingSession.objects.filter(
                vehicle_number=vehicle.plate_number
            ).order_by('-start_time')[:5]

            # Determine current status (prioritize session over booking)
            if current_session:
                if current_session.status == 'active':
                    parking_status = 'Currently Parked'
                    status_class = 'success'
                    status_detail = f"Slot {current_session.slot.slot_id}"
                else:
                    parking_status = 'Reserved'
                    status_class = 'warning'
                    status_detail = f"Slot {current_session.slot.slot_id}"
            elif current_booking:
                if current_booking.status == 'active':
                    parking_status = 'Currently Parked'
                    status_class = 'success'
                    status_detail = f"Slot {current_booking.slot.slot_id if current_booking.slot else 'TBD'}"
                else:
                    parking_status = 'Reserved (Booking)'
                    status_class = 'warning'
                    status_detail = f"Slot {current_booking.slot.slot_id if current_booking.slot else 'TBD'}"
            else:
                parking_status = 'Not Parked'
                status_class = 'secondary'
                status_detail = 'Available'

            user_profile = getattr(vehicle.owner, 'userprofile', None)

            vehicle_data = {
                'vehicle': vehicle,
                'owner': vehicle.owner,
                'user_profile': user_profile,
                'current_session': current_session,
                'current_booking': current_booking,
                'recent_sessions': recent_sessions,
                'parking_status': parking_status,
                'status_class': status_class,
                'status_detail': status_detail,
                'total_sessions': ParkingSession.objects.filter(
                    vehicle_number=vehicle.plate_number
                ).count()
            }

            # Apply status filter
            if filter_status == 'parked' and parking_status != 'Currently Parked':
                continue
            elif filter_status == 'available' and parking_status != 'Not Parked':
                continue
            elif filter_status == 'reserved' and 'Reserved' not in parking_status:
                continue

            enhanced_vehicles.append(vehicle_data)

        # Get summary statistics
        total_vehicles = Vehicle.objects.filter(is_active=True).count()
        parked_vehicles = ParkingSession.objects.filter(status='active').count()
        reserved_sessions = ParkingSession.objects.filter(status='pending').count()
        reserved_bookings = Booking.objects.filter(status='confirmed').count()
        reserved_vehicles = reserved_sessions + reserved_bookings
        available_vehicles = total_vehicles - parked_vehicles - reserved_vehicles

        context.update({
            'enhanced_vehicles': enhanced_vehicles,
            'total_vehicles': total_vehicles,
            'parked_vehicles': parked_vehicles,
            'reserved_vehicles': reserved_vehicles,
            'available_vehicles': available_vehicles,
        })

    return render(request, f'{template_prefix}/unified_parking_management.html', context)


from django.shortcuts import render
from django.utils import timezone
from .models import ParkingSlot, ParkingSession

@require_staff_or_manager
def end_session_by_vehicle(request):
    message = ''
    selected_session = None
    vehicle_owner = None
    vehicle_info = None

    # Get active sessions with enhanced user information
    active_sessions_raw = ParkingSession.objects.filter(status='active').select_related('slot')
    enhanced_active_sessions = []

    for session in active_sessions_raw:
        session_data = {
            'session': session,
            'user_info': None,
            'vehicle_info': None
        }

        # Try to find user information for each active session
        try:
            from .models import Vehicle
            vehicle_info_obj = Vehicle.objects.filter(
                plate_number=session.vehicle_number,
                is_active=True
            ).select_related('owner', 'owner__userprofile').first()

            if vehicle_info_obj and vehicle_info_obj.owner:
                session_data['vehicle_info'] = vehicle_info_obj
                user_profile = getattr(vehicle_info_obj.owner, 'userprofile', None)
                session_data['user_info'] = {
                    'name': vehicle_info_obj.owner.get_full_name() or vehicle_info_obj.owner.username,
                    'email': vehicle_info_obj.owner.email,
                    'phone': user_profile.phone_number if user_profile else None,
                    'user_type': user_profile.get_user_type_display() if user_profile else 'Unknown'
                }
        except:
            pass

        enhanced_active_sessions.append(session_data)

    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number')
        session = active_sessions_raw.filter(vehicle_number=vehicle_number).last()

        if session:
            # Try to find the vehicle owner
            try:
                from .models import Vehicle
                vehicle_info = Vehicle.objects.filter(
                    plate_number=vehicle_number,
                    is_active=True
                ).select_related('owner', 'owner__userprofile').first()

                if vehicle_info:
                    vehicle_owner = vehicle_info.owner
            except:
                pass

            now_time = timezone.now()  # Use a single consistent timestamp
            session.end_time = now_time
            session.status = 'completed'
            session.fee = session.calculate_fee()
            session.save()

            # Update slot to vacant - clear both flags
            session.slot.is_occupied = False
            session.slot.is_reserved = False
            session.slot.save()

            # Also complete any related booking
            try:
                booking = Booking.objects.get(parking_session=session, status='active')
                booking.status = 'completed'
                booking.actual_departure = now_time
                booking.save()
            except Booking.DoesNotExist:
                pass

            selected_session = session
        else:
            message = "No active session found for this vehicle."

    return render(request, 'staff/end_session_by_vehicle.html', {
        'enhanced_active_sessions': enhanced_active_sessions,
        'active_sessions': active_sessions_raw,  # Keep for backward compatibility
        'selected_session': selected_session,
        'message': message,
        'vehicle_owner': vehicle_owner,
        'vehicle_info': vehicle_info,
    })

