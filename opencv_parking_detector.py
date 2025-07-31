import cv2
import requests

# API endpoint (change this if you're hosting Django somewhere else)
API_URL = 'http://127.0.0.1:8000/api/update-slot/'

# Define parking slot coordinates (x, y, w, h)
parking_slots = [
    (60, 0, 150, 56),
    (60, 56, 150, 56),
    (60, 112, 150, 56),
    (60, 168, 150, 56),
    (60, 224, 150, 56),
    (60, 280, 150, 56),
    (60, 336, 150, 56),
]

occupancy_threshold = 0.1

def send_status(slot_number, status):
    # Convert status to boolean and create proper slot_id
    slot_id = f"P{slot_number:02d}"  # Format as P01, P02, etc.
    is_occupied = (status == "occupied")

    data = {
        "slot_id": slot_id,
        "is_occupied": is_occupied
    }
    try:
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            print(f"[✓] Slot {slot_id}: {'Occupied' if is_occupied else 'Vacant'}")
        else:
            print(f"[!] Failed to send Slot {slot_id}: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[!] Exception sending Slot {slot_id}: {e}")

# Load video
cap = cv2.VideoCapture('parking_lot.mp4')

while True:
    ret, frame = cap.read()
    if not ret:
        break

    for idx, (x, y, w, h) in enumerate(parking_slots):
        slot = frame[y:y+h, x:x+w]

        # Convert to grayscale
        gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Calculate white pixel ratio
        non_zero = cv2.countNonZero(edges)
        total_pixels = w * h
        ratio = non_zero / total_pixels

        status = "Occupied" if ratio > occupancy_threshold else "Vacant"

        # Send data to API
        send_status(idx + 1, status)

        # Optional: visualize
        color = (0, 0, 255) if status == 'Occupied' else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, status, (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imshow('Parking Lot Detection', frame)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
