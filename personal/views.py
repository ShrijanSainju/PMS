
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

from .models import ParkingSlot
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
def update_slot(request):
    slot_id = request.data.get('slot_id')
    is_occupied = request.data.get('is_occupied')

    if slot_id is None or is_occupied is None:
        return Response({"error": "Missing data"}, status=400)

    slot, created = ParkingSlot.objects.get_or_create(slot_id=slot_id)

    # Ignore sensor vacancy if a slot is reserved (car might be on its way)
    if slot.is_reserved and not is_occupied:
        return Response({"message": f"Slot {slot_id} is reserved; ignoring vacancy signal."})

    # Otherwise, update and clear reservation if car has arrived
    slot.is_occupied = is_occupied
    if is_occupied:
        slot.is_reserved = False
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
