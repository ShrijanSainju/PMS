
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

# @api_view(['POST'])
# def update_slot(request):
#     slot_id = request.data.get('slot_id')
#     is_occupied = request.data.get('is_occupied')

#     if slot_id is None or is_occupied is None:
#         return Response({"error": "Missing data"}, status=400)

#     # Convert to boolean in case it's sent as string
#     is_occupied = str(is_occupied).lower() in ['true', '1']

#     slot, created = ParkingSlot.objects.get_or_create(slot_id=slot_id)

#     if slot.is_reserved and not is_occupied:
#         return Response({"message": f"Slot {slot_id} is reserved; ignoring vacancy signal."})

#     # Activate session if car has arrived and slot was reserved
#     if slot.is_reserved and is_occupied:
#         session = ParkingSession.objects.filter(slot=slot, status='pending').last()
#         if session:
#             session.status = 'active'
#             session.save()
#         slot.is_reserved = False  # Clear reservation

#     # Update occupancy
#     slot.is_occupied = is_occupied
#     slot.save()

#     return Response({"message": f"Updated slot {slot_id} to {'Occupied' if is_occupied else 'Vacant'}"})


from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ParkingSlot, ParkingSession
from .permissions import require_approved_user, require_staff_or_manager
import json

@api_view(['POST'])
@csrf_exempt  # Allow OpenCV detector to call this endpoint
def update_slot(request):
    from .security import (
        rate_limit, validate_session_data, secure_headers,
        require_api_key, log_security_event
    )

    # Apply rate limiting (skip for video feed detector)
    detector_id = request.data.get('detector_id', '')
    if request.path.startswith('/api/') and detector_id != 'video_feed':
        from .security import is_rate_limited
        if is_rate_limited(request, 'slot_updates'):
            return Response({"error": "Rate limit exceeded"}, status=429)

    # Validate API key for external requests
    api_key = request.headers.get('X-API-Key') or request.data.get('api_key')
    if api_key:
        from .security import require_api_key
        # This is an external request, validate API key
        valid_keys = getattr(settings, 'API_KEYS', [])
        if api_key not in valid_keys:
            log_security_event(request, 'invalid_api_key', {'provided_key': api_key[:10] + '...'})
            return Response({"error": "Invalid API key"}, status=401)

    # Get and validate input data
    data = {
        'slot_id': request.data.get('slot_id'),
        'is_occupied': request.data.get('is_occupied'),
        'detector_id': request.data.get('detector_id', 'unknown'),
        'timestamp': request.data.get('timestamp')
    }

    # Validate required fields
    if data['slot_id'] is None or data['is_occupied'] is None:
        log_security_event(request, 'invalid_slot_update', {'missing_fields': True})
        return Response({"error": "Missing required fields: slot_id, is_occupied"}, status=400)

    # Validate and sanitize data
    valid, errors, clean_data = validate_session_data(data)
    if not valid:
        log_security_event(request, 'invalid_slot_update', {'validation_errors': errors})
        return Response({"error": "Validation failed", "details": errors}, status=400)

    slot_id = clean_data['slot_id']
    is_occupied = clean_data['is_occupied']
    detector_id = clean_data['detector_id']

    try:
        slot, created = ParkingSlot.objects.get_or_create(slot_id=slot_id)

        # Store previous state for change detection
        previous_state = slot.is_occupied

        if slot.is_reserved and not is_occupied:
            return Response({"message": f"Slot {slot_id} is reserved; ignoring vacancy signal."})

        # Handle vehicle entry (vacant -> occupied)
        if not previous_state and is_occupied:
            # Check if there's a pending session for this slot
            pending_session = ParkingSession.objects.filter(slot=slot, status='pending').last()

            if pending_session:
                # Activate the pending session
                pending_session.status = 'active'
                if pending_session.start_time is None:
                    pending_session.start_time = timezone.now()
                pending_session.save()
                slot.is_reserved = False
                logger.info(f"Activated pending session for {pending_session.vehicle_number} in slot {slot_id}")
            else:
                # Create a new session for unknown vehicle
                unknown_session = ParkingSession.objects.create(
                    vehicle_number=f"UNKNOWN-{slot_id}-{int(timezone.now().timestamp())}",
                    slot=slot,
                    status='active',
                    start_time=timezone.now()
                )
                logger.info(f"Created new session for unknown vehicle in slot {slot_id}")

        # Handle vehicle exit (occupied -> vacant)
        elif previous_state and not is_occupied:
            # End any active session for this slot
            active_session = ParkingSession.objects.filter(slot=slot, status='active').last()

            if active_session:
                active_session.end_time = timezone.now()
                active_session.status = 'completed'
                active_session.fee = active_session.calculate_fee()
                active_session.save()
                logger.info(f"Completed session for {active_session.vehicle_number} in slot {slot_id}, fee: ₹{active_session.fee}")

        # Update occupancy
        slot.is_occupied = is_occupied
        slot.save()

        # Log the update
        logger.info(f"Slot {slot_id} updated to {'Occupied' if is_occupied else 'Vacant'} by {detector_id}")

        return Response({
            "message": f"Updated slot {slot_id} to {'Occupied' if is_occupied else 'Vacant'}",
            "previous_state": previous_state,
            "new_state": is_occupied,
            "detector_id": detector_id,
            "timestamp": timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error updating slot {slot_id}: {str(e)}")
        log_security_event(request, 'slot_update_error', {'error': str(e), 'slot_id': slot_id})
        return Response({"error": "Internal server error"}, status=500)


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

    return render(request, 'admin/security_dashboard.html')


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
    return render(request, 'admin/dashboard.html')

@require_approved_user
def slot_status_api(request):
    slots = ParkingSlot.objects.all().order_by('slot_id')
    data = []

    for slot in slots:
        # Check for pending/active session for this slot
        session = ParkingSession.objects.filter(slot=slot, status__in=['pending', 'active']).last()
        session_status = session.status if session else None
        vehicle_number = session.vehicle_number if session else None
        session_start = session.start_time if session else None

        data.append({
            'slot_id': slot.slot_id,
            'is_occupied': slot.is_occupied,
            'is_reserved': slot.is_reserved,
            'session_status': session_status,
            'vehicle_number': vehicle_number,
            'session_start': session_start.isoformat() if session_start else None,
            'timestamp': slot.timestamp.isoformat(),
        })

    return JsonResponse(data, safe=False)


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
    cap = cv2.VideoCapture('parking_lot.mp4')  # Change to 0 for webcam

    parking_slots = [
        (60, 0, 150, 57), (60, 56, 150, 57), (60, 115, 150, 59),
        (60, 175, 150, 59), (60, 235, 150, 59), (60, 295, 150, 59),
        (60, 355, 150, 59), (212, 0, 150, 57), (212, 56, 150, 57),
        (212, 115, 150, 59), (212, 175, 150, 59), (212, 235, 150, 59),
        (212, 295, 150, 59), (212, 355, 150, 59),
    ]

    occupancy_threshold = 0.1
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
                    # Only update if slot is not reserved (reserved slots shouldn't be auto-updated)
                    if not db_slot.is_reserved:
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

                # Use current database status for display
                db_status = db_slot.is_occupied
                color = (0, 0, 255) if db_status else (0, 255, 0)
                label = f"{slot_id}: {'Occupied' if db_status else 'Vacant'}"

                # Show detection vs database mismatch
                if is_occupied != db_status:
                    color = (0, 255, 255)  # Yellow for mismatch
                    label += " (MISMATCH)"

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
                return render(request, 'staff/assign_slot.html', {
                    'form': form,
                    'error': f"Vehicle {vehicle_number} already has an ongoing session (Slot {existing_session.slot.slot_id}).",
                    'available_slots': [],
                    'zones': []
                })

            # Try to use the auto-assignment API for better slot selection
            try:
                import requests
                api_url = request.build_absolute_uri('/api/auto-assign/')
                response = requests.post(api_url, json={
                    'vehicle_number': vehicle_number,
                    'zone_preference': zone_preference
                }, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    slot_id = data['slot_id']
                    session_id = data['session_id']

                    # Get the session and slot objects
                    session = ParkingSession.objects.get(id=session_id)
                    slot = session.slot

                    return render(request, 'staff/assign_success.html', {
                        'session': session,
                        'slot': slot,
                        'auto_assigned': True,
                        'zone': data.get('zone', 'Unknown'),
                        'message': f"Slot {slot_id} automatically assigned to {vehicle_number}"
                    })
                else:
                    error_data = response.json()
                    error_message = error_data.get('error', 'Failed to assign slot automatically')

            except Exception as e:
                error_message = f"Auto-assignment failed: {str(e)}"
                logger.warning(f"Auto-assignment API failed: {e}")

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
                return render(request, 'staff/assign_slot.html', {
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

            logger.info(f"Manually assigned slot {available_slot.slot_id} to vehicle {vehicle_number}")

            return render(request, 'staff/assign_success.html', {
                'session': session,
                'slot': available_slot,
                'auto_assigned': False,
                'zone': available_slot.slot_id[0] if available_slot.slot_id else 'Unknown',
                'message': f"Slot {available_slot.slot_id} assigned to {vehicle_number}"
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

    return render(request, 'staff/assign_slot.html', {
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

        slot.is_occupied = False
        slot.save()

        return render(request, 'staff/end_success.html', {'session': session})
    else:
        return render(request, 'staff/end_success.html', {'error': 'No active session found.'})


@require_approved_user
def history_log(request):
    sessions = ParkingSession.objects.all().order_by('-start_time')
    return render(request, 'admin/history.html', {'sessions': sessions})


from django.utils.timezone import now
from django.db.models import Case, When, Value, IntegerField

@require_approved_user
def lookup_session(request):
    session = None
    elapsed_time = None
    price = None
    price_per_minute = 2  # Change this to match your pricing logic

    if request.method == 'POST':
        form = LookupForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']

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

            if session and session.start_time:
                if session.status in ['pending', 'active']:
                    end = now()
                else:
                    end = session.end_time or now()

                elapsed = end - session.start_time
                elapsed_minutes = int(elapsed.total_seconds() // 60)
                elapsed_time = str(elapsed).split('.')[0]  # Format HH:MM:SS
                price = elapsed_minutes * price_per_minute
    else:
        form = LookupForm()

    return render(request, 'customer/lookup.html', {
        'form': form,
        'session': session,
        'elapsed_time': elapsed_time,
        'price': price,
    })


from django.shortcuts import render
from django.utils import timezone
from .models import ParkingSlot, ParkingSession

@require_staff_or_manager
def end_session_by_vehicle(request):
    message = ''
    selected_session = None
    active_sessions = ParkingSession.objects.filter(status='active')

    if request.method == 'POST':
        vehicle_number = request.POST.get('vehicle_number')
        session = active_sessions.filter(vehicle_number=vehicle_number).last()

        if session:
            now_time = timezone.now()  # Use a single consistent timestamp
            session.end_time = now_time
            session.status = 'completed'
            session.fee = session.calculate_fee()
            session.save()

            # Update slot to vacant
            session.slot.is_occupied = False
            session.slot.save()

            selected_session = session
        else:
            message = "No active session found for this vehicle."

    return render(request, 'staff/end_session_by_vehicle.html', {
        'active_sessions': active_sessions,
        'selected_session': selected_session,
        'message': message,
    })

