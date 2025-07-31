#!/usr/bin/env python3
"""
Unified Parking Detection Service
Ensures consistency between camera feed and database status
"""

import cv2
import requests
import time
import threading
import json
from datetime import datetime

class UnifiedParkingDetector:
    def __init__(self):
        self.api_url = "http://127.0.0.1:8000/api/update-slot/"
        self.status_url = "http://127.0.0.1:8000/api/slot-status/"
        
        # Standardized parking slot coordinates (matching views.py)
        self.parking_slots = [
            {"id": "A1", "coords": (60, 0, 150, 57)},
            {"id": "A2", "coords": (60, 56, 150, 57)},
            {"id": "A3", "coords": (60, 115, 150, 59)},
            {"id": "A4", "coords": (60, 175, 150, 59)},
            {"id": "A5", "coords": (60, 235, 150, 59)},
            {"id": "A6", "coords": (60, 295, 150, 59)},
            {"id": "A7", "coords": (60, 355, 150, 59)},
            {"id": "B1", "coords": (212, 0, 150, 57)},
            {"id": "B2", "coords": (212, 56, 150, 57)},
            {"id": "B3", "coords": (212, 115, 150, 59)},
            {"id": "B4", "coords": (212, 175, 150, 59)},
            {"id": "B5", "coords": (212, 235, 150, 59)},
            {"id": "B6", "coords": (212, 295, 150, 59)},
            {"id": "B7", "coords": (212, 355, 150, 59)},
        ]
        
        self.occupancy_threshold = 0.1
        self.update_interval = 1.0  # Update every second
        self.last_sent = {}
        self.slot_states = {}
        self.db_states = {}
        
        # Start background thread to sync with database
        self.sync_thread = threading.Thread(target=self.sync_with_database, daemon=True)
        self.sync_thread.start()
    
    def sync_with_database(self):
        """Periodically sync with database to get current slot states"""
        while True:
            try:
                response = requests.get(self.status_url, timeout=5)
                if response.status_code == 200:
                    slots_data = response.json()
                    for slot_data in slots_data:
                        slot_id = slot_data['slot_id']
                        self.db_states[slot_id] = {
                            'is_occupied': slot_data['is_occupied'],
                            'is_reserved': slot_data['is_reserved'],
                            'session_status': slot_data.get('session_status'),
                            'vehicle_number': slot_data.get('vehicle_number'),
                            'timestamp': slot_data.get('timestamp')
                        }
                else:
                    print(f"[WARNING] Failed to sync with database: {response.status_code}")
            except Exception as e:
                print(f"[ERROR] Database sync error: {e}")
            
            time.sleep(2)  # Sync every 2 seconds
    
    def detect_occupancy(self, slot_roi):
        """Detect if a parking slot is occupied using edge detection"""
        gray = cv2.cvtColor(slot_roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        non_zero = cv2.countNonZero(edges)
        total_pixels = slot_roi.shape[0] * slot_roi.shape[1]
        ratio = non_zero / total_pixels
        return ratio > self.occupancy_threshold
    
    def send_slot_update(self, slot_id, is_occupied):
        """Send slot status update to Django API"""
        data = {
            "slot_id": slot_id,
            "is_occupied": is_occupied,
            "detector_id": "unified_detector",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(self.api_url, json=data, timeout=5)
            if response.status_code == 200:
                print(f"[✓] {slot_id}: {'Occupied' if is_occupied else 'Vacant'}")
                return True
            else:
                print(f"[!] Failed to update {slot_id}: {response.status_code}")
                return False
        except Exception as e:
            print(f"[!] Exception updating {slot_id}: {e}")
            return False
    
    def should_update_slot(self, slot_id, detected_status):
        """Determine if slot status should be updated"""
        now = time.time()
        
        # Always update if detection differs from database
        if slot_id in self.db_states:
            db_status = self.db_states[slot_id]['is_occupied']
            if detected_status != db_status:
                print(f"[MISMATCH] {slot_id}: Detected={detected_status}, DB={db_status}")
                return True
        
        # Update if state changed from last detection
        if slot_id in self.slot_states and self.slot_states[slot_id] != detected_status:
            return True
        
        # Periodic update even if no change (heartbeat)
        if slot_id not in self.last_sent or now - self.last_sent[slot_id] > self.update_interval * 5:
            return True
        
        return False
    
    def process_frame(self, frame):
        """Process a single frame and return annotated frame with detection results"""
        detection_results = []
        
        for slot_config in self.parking_slots:
            slot_id = slot_config['id']
            x, y, w, h = slot_config['coords']
            
            # Extract slot ROI
            slot_roi = frame[y:y+h, x:x+w]
            
            # Detect occupancy
            detected_status = self.detect_occupancy(slot_roi)
            
            # Get database status
            db_status = None
            db_info = ""
            if slot_id in self.db_states:
                db_status = self.db_states[slot_id]['is_occupied']
                vehicle = self.db_states[slot_id].get('vehicle_number', '')
                if vehicle:
                    db_info = f" ({vehicle})"
            
            # Update database if necessary
            if self.should_update_slot(slot_id, detected_status):
                success = self.send_slot_update(slot_id, detected_status)
                if success:
                    self.last_sent[slot_id] = time.time()
            
            # Update local state tracking
            self.slot_states[slot_id] = detected_status
            
            # Determine display color and label
            if db_status is not None:
                # Use database status for display
                display_status = db_status
                if detected_status != db_status:
                    color = (0, 255, 255)  # Yellow for mismatch
                    label = f"{slot_id}: MISMATCH{db_info}"
                else:
                    color = (0, 0, 255) if display_status else (0, 255, 0)
                    label = f"{slot_id}: {'OCC' if display_status else 'VAC'}{db_info}"
            else:
                # Fallback to detection if no database info
                display_status = detected_status
                color = (128, 128, 128)  # Gray for no DB data
                label = f"{slot_id}: {'OCC' if display_status else 'VAC'} (NO DB)"
            
            # Draw rectangle and label
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Store detection result
            detection_results.append({
                'slot_id': slot_id,
                'detected_status': detected_status,
                'db_status': db_status,
                'display_status': display_status,
                'mismatch': detected_status != db_status if db_status is not None else False
            })
        
        return frame, detection_results
    
    def run_detection(self, video_source='parking_lot.mp4'):
        """Run the main detection loop"""
        print(f"[INFO] Starting unified parking detection on {video_source}")
        
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            print(f"[ERROR] Could not open video source: {video_source}")
            return
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[INFO] End of video or failed to read frame")
                    break
                
                # Process frame
                annotated_frame, results = self.process_frame(frame)
                
                # Display frame (optional)
                cv2.imshow('Unified Parking Detection', annotated_frame)
                
                # Print summary every 30 frames
                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    mismatches = sum(1 for r in results if r['mismatch'])
                    print(f"[INFO] Frame {frame_count}, FPS: {fps:.1f}, Mismatches: {mismatches}")
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(1/30)  # Limit to ~30 FPS
                
        except KeyboardInterrupt:
            print("[INFO] Detection stopped by user")
        finally:
            cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = UnifiedParkingDetector()
    detector.run_detection()
