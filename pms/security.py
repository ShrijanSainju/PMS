"""
Security utilities for the Parking Management System
"""

import hashlib
import time
import logging
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
import re

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMIT_SETTINGS = {
    'api_calls': {
        'limit': 1000,  # requests per window
        'window': 3600,  # 1 hour in seconds
    },
    'login_attempts': {
        'limit': 5,  # attempts per window
        'window': 900,  # 15 minutes in seconds
    },
    'slot_updates': {
        'limit': 1000,  # updates per window
        'window': 3600,  # 1 hour in seconds
    }
}

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_rate_limit_key(request, action):
    """Generate cache key for rate limiting"""
    ip = get_client_ip(request)
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    return f"rate_limit:{action}:{ip}:{user_id}"

def is_rate_limited(request, action):
    """Check if request is rate limited"""
    if action not in RATE_LIMIT_SETTINGS:
        return False
    
    config = RATE_LIMIT_SETTINGS[action]
    key = get_rate_limit_key(request, action)
    
    # Get current count
    current_count = cache.get(key, 0)
    
    if current_count >= config['limit']:
        logger.warning(f"Rate limit exceeded for {action} from {get_client_ip(request)}")
        return True
    
    # Increment counter
    cache.set(key, current_count + 1, config['window'])
    return False

def rate_limit(action):
    """Decorator for rate limiting views"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if is_rate_limited(request, action):
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': RATE_LIMIT_SETTINGS[action]['window']
                }, status=429)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

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

def sanitize_input(value, max_length=100):
    """Sanitize user input"""
    if not value:
        return ""
    
    # Convert to string and strip whitespace
    value = str(value).strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r']
    for char in dangerous_chars:
        value = value.replace(char, '')
    
    return value

def log_security_event(request, event_type, details=None):
    """Log security-related events"""
    ip = get_client_ip(request)
    user = request.user.username if request.user.is_authenticated else 'anonymous'
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    log_data = {
        'event_type': event_type,
        'ip': ip,
        'user': user,
        'user_agent': user_agent,
        'timestamp': timezone.now().isoformat(),
        'details': details or {}
    }
    
    logger.warning(f"Security Event: {event_type} from {ip} (user: {user})")
    
    # Store in cache for monitoring
    cache_key = f"security_events:{ip}:{int(time.time() // 3600)}"  # Hourly buckets
    events = cache.get(cache_key, [])
    events.append(log_data)
    cache.set(cache_key, events, 3600)  # Keep for 1 hour

def check_suspicious_activity(request):
    """Check for suspicious activity patterns"""
    ip = get_client_ip(request)
    
    # Check for too many security events in the last hour
    cache_key = f"security_events:{ip}:{int(time.time() // 3600)}"
    events = cache.get(cache_key, [])
    
    if len(events) > 10:  # More than 10 security events per hour
        log_security_event(request, 'suspicious_activity', {
            'event_count': len(events),
            'reason': 'Too many security events'
        })
        return True
    
    return False

def require_api_key(view_func):
    """Decorator to require API key for certain endpoints"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
        
        if not api_key:
            log_security_event(request, 'missing_api_key')
            return JsonResponse({'error': 'API key required'}, status=401)
        
        # Validate API key (in production, store these securely)
        valid_keys = getattr(settings, 'API_KEYS', ['opencv_detector_key_2024'])
        
        if api_key not in valid_keys:
            log_security_event(request, 'invalid_api_key', {'provided_key': api_key[:10] + '...'})
            return JsonResponse({'error': 'Invalid API key'}, status=401)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def validate_session_data(data):
    """Validate session-related data"""
    errors = []
    
    # Validate vehicle number
    if 'vehicle_number' in data:
        valid, result = validate_vehicle_number(data['vehicle_number'])
        if not valid:
            errors.append(f"Vehicle number: {result}")
        else:
            data['vehicle_number'] = result
    
    # Validate slot ID
    if 'slot_id' in data:
        valid, result = validate_slot_id(data['slot_id'])
        if not valid:
            errors.append(f"Slot ID: {result}")
        else:
            data['slot_id'] = result
    
    # Validate boolean fields
    boolean_fields = ['is_occupied', 'is_reserved']
    for field in boolean_fields:
        if field in data:
            if isinstance(data[field], str):
                data[field] = data[field].lower() in ['true', '1', 'yes']
            elif not isinstance(data[field], bool):
                errors.append(f"{field}: Must be a boolean value")
    
    return len(errors) == 0, errors, data

def secure_headers(view_func):
    """Decorator to add security headers"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CORS headers for API endpoints
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
        
        return response
    return wrapper

def monitor_failed_logins(username, ip):
    """Monitor and track failed login attempts"""
    cache_key = f"failed_logins:{ip}:{username}"
    attempts = cache.get(cache_key, 0)
    attempts += 1
    
    # Lock account after 5 failed attempts for 15 minutes
    if attempts >= 5:
        lockout_key = f"account_locked:{username}"
        cache.set(lockout_key, True, 900)  # 15 minutes
        logger.warning(f"Account {username} locked due to failed login attempts from {ip}")
    
    cache.set(cache_key, attempts, 900)  # Track for 15 minutes
    return attempts

def is_account_locked(username):
    """Check if account is locked due to failed login attempts"""
    lockout_key = f"account_locked:{username}"
    return cache.get(lockout_key, False)

def clear_failed_logins(username, ip):
    """Clear failed login attempts after successful login"""
    cache_key = f"failed_logins:{ip}:{username}"
    lockout_key = f"account_locked:{username}"
    cache.delete(cache_key)
    cache.delete(lockout_key)
