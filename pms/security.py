"""
Security utilities for the Parking Management System
"""

import re
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_rate_limited(request, action):
    """Check if request is rate limited - DISABLED FOR TESTING"""
    # Rate limiting disabled for testing
    return False


def validate_vehicle_number(vehicle_number):
    """Validate vehicle number format"""
    if not vehicle_number:
        return False, "Vehicle number is required"
    
    # Remove spaces and convert to uppercase
    vehicle_number = vehicle_number.strip().upper()
    
    # Basic validation - alphanumeric with hyphens
    if not re.match(r'^[A-Z0-9\-\s]{3,15}$', vehicle_number):
        return False, "Invalid vehicle number format"
    
    # Check for minimum meaningful content
    if len(vehicle_number.replace('-', '').replace(' ', '')) < 3:
        return False, "Vehicle number too short"
    
    return True, vehicle_number


def validate_slot_id(slot_id):
    """Validate slot ID format"""
    if not slot_id:
        return False, "Slot ID is required"
    
    # Basic validation - alphanumeric
    if not re.match(r'^[A-Z0-9]{1,10}$', slot_id.upper()):
        return False, "Invalid slot ID format"
    
    return True, slot_id.upper()


def log_security_event(request, event_type, details=None):
    """Log security-related events - DISABLED FOR TESTING"""
    # Security event logging disabled for testing
    pass

