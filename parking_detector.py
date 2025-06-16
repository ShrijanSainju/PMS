# import cv2
# import requests

# # Load the video
# cap = cv2.VideoCapture('parking_lot.mp4')

# # Define parking slot coordinates (x, y, w, h)
# parking_slots = [
#     (60, 0, 150, 57), (60, 56, 150, 57), (60, 115, 150, 59),
#     (60, 175, 150, 59), (60, 235, 150, 59), (60, 295, 150, 59),
#     (60, 355, 150, 59), (212, 0, 150, 57), (212, 56, 150, 57),
#     (212, 115, 150, 59), (212, 175, 150, 59), (212, 235, 150, 59),
#     (212, 295, 150, 59), (212, 355, 150, 59),
# ]

# # Threshold ratio to decide occupancy
# occupancy_threshold = 0.1  # tune this

# # Send status to Django API
# def update_parking_slot_status(slot_id, is_occupied):
#     url = "http://127.0.0.1:8000/api/update-slot/"
#     data = {
#         "slot_id": slot_id,
#         "is_occupied": is_occupied
#     }
#     try:
#         response = requests.post(url, json=data)
#         if response.status_code != 200:
#             print(f"[ERROR] Failed to update slot {slot_id}: {response.text}")
#     except Exception as e:
#         print(f"[EXCEPTION] {e}")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     for idx, (x, y, w, h) in enumerate(parking_slots):
#         row = 'A' if idx < 7 else 'B'
#         num = (idx % 7) + 1
#         slot_id = f"{row}{num}"

#         # Crop and process
#         slot = frame[y:y+h, x:x+w]
#         gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
#         edges = cv2.Canny(gray, 50, 150)
#         non_zero = cv2.countNonZero(edges)

#         total_pixels = w * h
#         is_occupied = non_zero > total_pixels * occupancy_threshold
#         status = 'Occupied' if is_occupied else 'Vacant'

#         update_parking_slot_status(slot_id, is_occupied)

#         # Draw
#         color = (0, 0, 255) if is_occupied else (0, 255, 0)
#         cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
#         cv2.putText(frame, status, (x, y - 5),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

#     cv2.imshow('Parking Detection', frame)

#     if cv2.waitKey(25) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()




import cv2
import requests
import threading
import time

# Load the video
cap = cv2.VideoCapture('parking_lot.mp4')

# Define parking slot coordinates
parking_slots = [
    (60, 0, 150, 57), (60, 56, 150, 57), (60, 115, 150, 59),
    (60, 175, 150, 59), (60, 235, 150, 59), (60, 295, 150, 59),
    (60, 355, 150, 59), (212, 0, 150, 57), (212, 56, 150, 57),
    (212, 115, 150, 59), (212, 175, 150, 59), (212, 235, 150, 59),
    (212, 295, 150, 59), (212, 355, 150, 59),
]

occupancy_threshold = 0.1
update_interval = 2  # seconds
last_sent = {}

# Send in background thread
def send_async(slot_id, is_occupied):
    def task():
        try:
            response = requests.post("http://127.0.0.1:8000/api/update-slot/",
                                     json={"slot_id": slot_id, "is_occupied": is_occupied})
            if response.status_code != 200:
                print(f"[ERROR] {slot_id}: {response.text}")
        except Exception as e:
            print(f"[EXCEPTION] {slot_id}: {e}")
    threading.Thread(target=task, daemon=True).start()

while True:
    ret, frame = cap.read()
    if not ret:
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
        status = 'Occupied' if is_occupied else 'Vacant'

        # Limit API update
        now = time.time()
        if slot_id not in last_sent or now - last_sent[slot_id] > update_interval:
            send_async(slot_id, is_occupied)
            last_sent[slot_id] = now

        # Draw
        color = (0, 0, 255) if is_occupied else (0, 255, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(frame, status, (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imshow('Parking Detection', frame)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
