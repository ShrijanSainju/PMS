"""
Enhanced OpenCV Parking Detector with Django Integration
Features:
- Configurable detection parameters
- Multiple detection algorithms
- Automatic slot assignment
- Error handling and retry logic
- Real-time status updates
- Configuration management
"""

import cv2
import numpy as np
import requests
import json
import time
import threading
import logging
import argparse
from datetime import datetime
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parking_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParkingDetector:
    def __init__(self, config_file='detector_config.yaml'):
        self.config = self.load_config(config_file)
        self.api_url = self.config['api']['base_url']
        self.update_endpoint = f"{self.api_url}/api/update-slot/"
        self.session_endpoint = f"{self.api_url}/api/parking-sessions/"
        
        # Detection parameters
        self.occupancy_threshold = self.config['detection']['occupancy_threshold']
        self.update_interval = self.config['detection']['update_interval']
        self.detection_method = self.config['detection']['method']
        
        # Parking slots configuration
        self.parking_slots = self.config['parking_slots']
        
        # State tracking
        self.last_sent = {}
        self.slot_states = {}
        self.session = requests.Session()
        self.session.timeout = self.config['api']['timeout']
        
        # Video capture
        self.cap = None
        self.frame_count = 0
        
        # Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=self.config['detection']['var_threshold']
        )
        
        logger.info("Parking detector initialized")

    def load_config(self, config_file):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return self.get_default_config()

    def get_default_config(self):
        """Return default configuration"""
        return {
            'api': {
                'base_url': 'http://127.0.0.1:8000',
                'timeout': 5,
                'retry_attempts': 3,
                'retry_delay': 1
            },
            'detection': {
                'method': 'hybrid',  # 'edge', 'background', 'hybrid'
                'occupancy_threshold': 0.1,
                'update_interval': 2,
                'var_threshold': 50,
                'min_contour_area': 500
            },
            'video': {
                'source': 'parking_lot.mp4',  # or 0 for webcam
                'fps': 30,
                'resize_width': 640,
                'resize_height': 480
            },
            'parking_slots': [
                {'id': 'A1', 'coords': [60, 0, 150, 57], 'zone': 'A'},
                {'id': 'A2', 'coords': [60, 56, 150, 57], 'zone': 'A'},
                {'id': 'A3', 'coords': [60, 115, 150, 59], 'zone': 'A'},
                {'id': 'A4', 'coords': [60, 175, 150, 59], 'zone': 'A'},
                {'id': 'A5', 'coords': [60, 235, 150, 59], 'zone': 'A'},
                {'id': 'A6', 'coords': [60, 295, 150, 59], 'zone': 'A'},
                {'id': 'A7', 'coords': [60, 355, 150, 59], 'zone': 'A'},
                {'id': 'B1', 'coords': [212, 0, 150, 57], 'zone': 'B'},
                {'id': 'B2', 'coords': [212, 56, 150, 57], 'zone': 'B'},
                {'id': 'B3', 'coords': [212, 115, 150, 59], 'zone': 'B'},
                {'id': 'B4', 'coords': [212, 175, 150, 59], 'zone': 'B'},
                {'id': 'B5', 'coords': [212, 235, 150, 59], 'zone': 'B'},
                {'id': 'B6', 'coords': [212, 295, 150, 59], 'zone': 'B'},
                {'id': 'B7', 'coords': [212, 355, 150, 59], 'zone': 'B'},
            ]
        }

    def initialize_video_capture(self):
        """Initialize video capture"""
        video_source = self.config['video']['source']
        
        # Try to convert to int for webcam
        try:
            video_source = int(video_source)
        except ValueError:
            pass
        
        self.cap = cv2.VideoCapture(video_source)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {video_source}")
            return False
        
        # Set video properties
        self.cap.set(cv2.CAP_PROP_FPS, self.config['video']['fps'])
        
        logger.info(f"Video capture initialized: {video_source}")
        return True

    def detect_occupancy_edge(self, slot_roi):
        """Edge detection based occupancy detection"""
        gray = cv2.cvtColor(slot_roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        non_zero = cv2.countNonZero(edges)
        total_pixels = slot_roi.shape[0] * slot_roi.shape[1]
        ratio = non_zero / total_pixels
        return ratio > self.occupancy_threshold

    def detect_occupancy_background(self, slot_roi):
        """Background subtraction based occupancy detection"""
        fg_mask = self.bg_subtractor.apply(slot_roi)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check if any significant contour exists
        for contour in contours:
            if cv2.contourArea(contour) > self.config['detection']['min_contour_area']:
                return True
        
        return False

    def detect_occupancy_hybrid(self, slot_roi):
        """Hybrid detection combining edge and background subtraction"""
        edge_result = self.detect_occupancy_edge(slot_roi)
        bg_result = self.detect_occupancy_background(slot_roi)
        
        # Use OR logic - if either method detects occupancy, consider it occupied
        return edge_result or bg_result

    def detect_occupancy(self, slot_roi):
        """Main occupancy detection method"""
        method = self.detection_method
        
        if method == 'edge':
            return self.detect_occupancy_edge(slot_roi)
        elif method == 'background':
            return self.detect_occupancy_background(slot_roi)
        elif method == 'hybrid':
            return self.detect_occupancy_hybrid(slot_roi)
        else:
            logger.warning(f"Unknown detection method: {method}, using edge detection")
            return self.detect_occupancy_edge(slot_roi)

    def send_slot_update(self, slot_id, is_occupied):
        """Send slot status update to Django API with retry logic"""
        data = {
            "slot_id": slot_id,
            "is_occupied": is_occupied,
            "timestamp": datetime.now().isoformat(),
            "detector_id": "opencv_enhanced"
        }
        
        for attempt in range(self.config['api']['retry_attempts']):
            try:
                response = self.session.post(self.update_endpoint, json=data)
                
                if response.status_code == 200:
                    logger.debug(f"Successfully updated slot {slot_id}: {'Occupied' if is_occupied else 'Vacant'}")
                    return True
                else:
                    logger.warning(f"API returned status {response.status_code} for slot {slot_id}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1} failed for slot {slot_id}: {e}")
                
                if attempt < self.config['api']['retry_attempts'] - 1:
                    time.sleep(self.config['api']['retry_delay'])
        
        logger.error(f"Failed to update slot {slot_id} after {self.config['api']['retry_attempts']} attempts")
        return False

    def send_async_update(self, slot_id, is_occupied):
        """Send update in background thread"""
        def task():
            self.send_slot_update(slot_id, is_occupied)
        
        threading.Thread(target=task, daemon=True).start()

    def should_update_slot(self, slot_id, is_occupied):
        """Check if slot status should be updated"""
        now = time.time()
        
        # Always update if state changed
        if slot_id in self.slot_states and self.slot_states[slot_id] != is_occupied:
            return True
        
        # Update periodically even if state hasn't changed
        if slot_id not in self.last_sent or now - self.last_sent[slot_id] > self.update_interval:
            return True
        
        return False

    def process_frame(self, frame):
        """Process a single frame for parking detection"""
        # Resize frame if configured
        if 'resize_width' in self.config['video'] and 'resize_height' in self.config['video']:
            frame = cv2.resize(frame, (
                self.config['video']['resize_width'],
                self.config['video']['resize_height']
            ))
        
        detection_results = []
        
        for slot_config in self.parking_slots:
            slot_id = slot_config['id']
            x, y, w, h = slot_config['coords']
            
            # Extract slot ROI
            slot_roi = frame[y:y+h, x:x+w]
            
            # Detect occupancy
            is_occupied = self.detect_occupancy(slot_roi)
            
            # Update if necessary
            if self.should_update_slot(slot_id, is_occupied):
                self.send_async_update(slot_id, is_occupied)
                self.last_sent[slot_id] = time.time()
            
            # Update state tracking
            self.slot_states[slot_id] = is_occupied
            
            # Store result for visualization
            detection_results.append({
                'slot_id': slot_id,
                'coords': (x, y, w, h),
                'is_occupied': is_occupied,
                'zone': slot_config.get('zone', 'Unknown')
            })
        
        return detection_results

    def draw_detections(self, frame, detection_results):
        """Draw detection results on frame"""
        for result in detection_results:
            slot_id = result['slot_id']
            x, y, w, h = result['coords']
            is_occupied = result['is_occupied']
            zone = result['zone']
            
            # Choose color based on occupancy
            color = (0, 0, 255) if is_occupied else (0, 255, 0)  # Red for occupied, Green for vacant
            status = 'Occupied' if is_occupied else 'Vacant'
            
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw slot ID and status
            label = f"{slot_id}: {status}"
            cv2.putText(frame, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw zone indicator
            cv2.putText(frame, f"Zone {zone}", (x, y + h + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw frame info
        info_text = f"Frame: {self.frame_count} | Method: {self.detection_method}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def run(self, show_video=True):
        """Main detection loop"""
        if not self.initialize_video_capture():
            return
        
        logger.info("Starting parking detection...")
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame, restarting video...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
                    continue
                
                self.frame_count += 1
                
                # Process frame
                detection_results = self.process_frame(frame)
                
                # Draw results if video display is enabled
                if show_video:
                    self.draw_detections(frame, detection_results)
                    cv2.imshow('Enhanced Parking Detection', frame)
                    
                    # Check for quit key
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Log status periodically
                if self.frame_count % 300 == 0:  # Every 10 seconds at 30 FPS
                    occupied_count = sum(1 for r in detection_results if r['is_occupied'])
                    total_slots = len(detection_results)
                    logger.info(f"Status: {occupied_count}/{total_slots} slots occupied")
        
        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        logger.info("Cleanup completed")

def main():
    parser = argparse.ArgumentParser(description='Enhanced Parking Detector')
    parser.add_argument('--config', default='detector_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--no-video', action='store_true',
                       help='Run without video display')
    
    args = parser.parse_args()
    
    detector = ParkingDetector(args.config)
    detector.run(show_video=not args.no_video)

if __name__ == "__main__":
    main()
