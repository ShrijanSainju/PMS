
# from django.contrib.auth import authenticate, login,logout
# from django.shortcuts import render, redirect
# from django.contrib import messages

# # Create your views here.

# def home_screen_view(request):
#     print(request.headers)
#     return render(request, 'manager/homepage.html', {})

# def navbar(request):
#     return render(request, 'manager/navbar.html', {})

# def admin_dashboard(request):
#     return render(request, 'manager/admin_dashboard.html', {})

# def adminbase(request):
# <<<<<<< Updated upstream
#     return render(request, 'manager/adminbase.html', {})


# # --- Staff Login View ---

# def staff_login_view(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None and user.groups.filter(name='Staff').exists():
#             login(request, user)
#             return redirect('/staff/dashboard/')
#         else:
#             messages.error(request, 'Invalid credentials or not a staff member')
#     return render(request, 'staff_login.html')

# def admin_login_view(request):
#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None and user.groups.filter(name='Admin').exists():
#             login(request, user)
#             return redirect('/manager/dashboard/')
#         else:
#             messages.error(request, 'Invalid credentials or not a admin member')
#     return render(request, 'admin_login.html')


# # --- Login Redirect Logic ---

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
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, StreamingHttpResponse

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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ParkingSlot, ParkingSession

@api_view(['POST'])
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

    # Activate session if car has arrived and slot was reserved
    if slot.is_reserved and is_occupied:
        session = ParkingSession.objects.filter(slot=slot, status='pending').last()
        if session:
            session.status = 'active'
            if session.start_time is None:
                session.start_time = timezone.now()
            session.save()
        slot.is_reserved = False  # Clear reservation

    # Update occupancy
    slot.is_occupied = is_occupied
    slot.save()

    return Response({"message": f"Updated slot {slot_id} to {'Occupied' if is_occupied else 'Vacant'}"})




class ParkingSlotViewSet(viewsets.ModelViewSet):
    queryset = ParkingSlot.objects.all()
    serializer_class = ParkingSlotSerializer

def dashboard_view(request):
    return render(request, 'admin/dashboard.html')

def slot_status_api(request):
    slots = ParkingSlot.objects.all().order_by('slot_id')
    data = [
        {
            'slot_id': slot.slot_id,
            'is_occupied': slot.is_occupied,
            'is_reserved': slot.is_reserved,
            'timestamp': slot.timestamp,
        }
        for slot in slots
    ]
    return JsonResponse(data, safe=False)

# --- Video Streaming Logic ---

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

    while True:
        success, frame = cap.read()
        if not success:
            break

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

            color = (0, 0, 255) if is_occupied else (0, 255, 0)
            label = "Occupied" if is_occupied else "Vacant"
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

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

def assign_slot(request):
    if request.method == 'POST':
        form = VehicleEntryForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']

            # Find first slot that is not reserved and not occupied
            available_slot = ParkingSlot.objects.filter(is_reserved=False, is_occupied=False).order_by('slot_id').first()
            if not available_slot:
                return render(request, 'staff/assign_slot.html', {
                    'form': form,
                    'error': "No available slots at the moment."
                })

            # Create session with 'pending' status
            session = ParkingSession.objects.create(
                vehicle_number=vehicle_number,
                slot=available_slot,
                status='pending'
            )

            # Reserve the slot (do not mark occupied yet)
            available_slot.is_reserved = True
            available_slot.save()

            return render(request, 'staff/success.html', {'session': session})

    else:
        form = VehicleEntryForm()
    
    return render(request, 'staff/assign_slot.html', {'form': form})



from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import ParkingSlot, ParkingSession
from .forms import VehicleEntryForm, LookupForm

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


def history_log(request):
    sessions = ParkingSession.objects.all().order_by('-start_time')
    return render(request, 'admin/history.html', {'sessions': sessions})


from django.utils.timezone import now
from django.db.models import Case, When, Value, IntegerField

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

