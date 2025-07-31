"""
Security middleware for the Parking Management System
"""

import logging
import time
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .security import get_client_ip, log_security_event, check_suspicious_activity

logger = logging.getLogger(__name__)

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to handle various security concerns
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming requests for security checks"""
        
        # Get client IP
        ip = get_client_ip(request)
        
        # Check for suspicious activity
        if check_suspicious_activity(request):
            # Block suspicious IPs temporarily
            block_key = f"blocked_ip:{ip}"
            if cache.get(block_key):
                return JsonResponse({
                    'error': 'Access temporarily blocked due to suspicious activity'
                }, status=403)
            else:
                # Block for 1 hour
                cache.set(block_key, True, 3600)
        
        # Check for common attack patterns in URLs
        suspicious_patterns = [
            'admin/admin',
            'wp-admin',
            'phpmyadmin',
            '.env',
            'config.php',
            'shell.php',
            '../',
            '..\\',
            '<script',
            'javascript:',
            'eval(',
            'union select',
            'drop table',
            'insert into',
            'delete from'
        ]
        
        path_lower = request.path.lower()
        query_lower = request.META.get('QUERY_STRING', '').lower()
        
        for pattern in suspicious_patterns:
            if pattern in path_lower or pattern in query_lower:
                log_security_event(request, 'suspicious_url', {
                    'pattern': pattern,
                    'path': request.path,
                    'query': request.META.get('QUERY_STRING', '')
                })
                return JsonResponse({
                    'error': 'Invalid request'
                }, status=400)
        
        # Check for oversized requests
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                content_length = int(content_length)
                max_size = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB default
                if content_length > max_size:
                    log_security_event(request, 'oversized_request', {
                        'content_length': content_length,
                        'max_allowed': max_size
                    })
                    return JsonResponse({
                        'error': 'Request too large'
                    }, status=413)
            except ValueError:
                pass
        
        # Rate limiting for API endpoints
        if request.path.startswith('/api/'):
            rate_limit_key = f"api_rate_limit:{ip}"
            current_requests = cache.get(rate_limit_key, 0)
            
            # Allow 100 requests per minute for API endpoints
            if current_requests >= 100:
                log_security_event(request, 'api_rate_limit_exceeded', {
                    'requests_count': current_requests
                })
                return JsonResponse({
                    'error': 'API rate limit exceeded',
                    'retry_after': 60
                }, status=429)
            
            cache.set(rate_limit_key, current_requests + 1, 60)
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing responses to add security headers"""
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for HTML responses
        if response.get('Content-Type', '').startswith('text/html'):
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: blob:; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response['Content-Security-Policy'] = csp_policy
        
        # Add CORS headers for API responses
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
            response['Access-Control-Max-Age'] = '3600'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log requests for security monitoring
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Log incoming requests"""
        request.start_time = time.time()
        
        # Log sensitive endpoints
        sensitive_paths = ['/admin/', '/api/', '/staff/', '/manager/']
        
        if any(request.path.startswith(path) for path in sensitive_paths):
            ip = get_client_ip(request)
            user = getattr(request, 'user', None)
            username = user.username if user and user.is_authenticated else 'anonymous'

            logger.info(f"Request: {request.method} {request.path} from {ip} (user: {username})")
    
    def process_response(self, request, response):
        """Log response information"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 5.0:  # Requests taking more than 5 seconds
                ip = get_client_ip(request)
                logger.warning(f"Slow request: {request.method} {request.path} "
                             f"took {duration:.2f}s from {ip}")
            
            # Log error responses
            if response.status_code >= 400:
                ip = get_client_ip(request)
                user = getattr(request, 'user', None)
                username = user.username if user and user.is_authenticated else 'anonymous'
                logger.warning(f"Error response: {response.status_code} for "
                             f"{request.method} {request.path} from {ip} (user: {username})")
        
        return response


class IPWhitelistMiddleware(MiddlewareMixin):
    """
    Middleware to restrict access to certain IPs for admin endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check IP whitelist for admin endpoints"""
        if not self.whitelist:
            return None
        
        # Only apply to admin endpoints
        if not request.path.startswith('/admin/'):
            return None
        
        ip = get_client_ip(request)
        
        # Check if IP is in whitelist
        if ip not in self.whitelist:
            log_security_event(request, 'admin_access_denied', {
                'ip': ip,
                'path': request.path
            })
            return JsonResponse({
                'error': 'Access denied from this IP address'
            }, status=403)
        
        return None


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to enhance session security
    """
    
    def process_request(self, request):
        """Check session security"""
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            # Check for session hijacking
            session_ip = request.session.get('ip_address')
            current_ip = get_client_ip(request)
            
            if session_ip and session_ip != current_ip:
                log_security_event(request, 'session_ip_mismatch', {
                    'session_ip': session_ip,
                    'current_ip': current_ip,
                    'user': user.username if user else 'unknown'
                })
                
                # Force logout for security
                from django.contrib.auth import logout
                logout(request)
                return JsonResponse({
                    'error': 'Session security violation. Please log in again.'
                }, status=401)
            
            # Store IP in session if not present
            if not session_ip:
                request.session['ip_address'] = current_ip
        
        return None
