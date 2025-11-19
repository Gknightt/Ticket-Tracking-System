"""
Performance Logging Middleware for Django
Tracks response times, status codes, and request details
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from django.utils.deprecation import MiddlewareMixin

# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_dir / 'performance.log',
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger('performance')


class PerformanceLoggingMiddleware(MiddlewareMixin):
    """
    Django middleware to log request/response performance metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.metrics_file = log_dir / 'metrics.json'
        self.metrics = self.load_metrics()
    
    def load_metrics(self):
        """Load existing metrics from file"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")
        
        return {
            'requests': [],
            'summary': {
                'total_requests': 0,
                'total_errors': 0,
                'average_response_time': 0,
                'start_time': datetime.now().isoformat()
            }
        }
    
    def save_metrics(self):
        """Save metrics to file"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def process_request(self, request):
        """Mark request start time"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log response metrics"""
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # Convert to ms
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration': round(duration, 2),
                'ip': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')
            }
            
            # Log to file
            logger.info(json.dumps(log_entry))
            
            # Update metrics
            self.update_metrics(log_entry)
            
            # Console output
            color = self.get_color_for_status(response.status_code)
            reset = '\033[0m'
            print(
                f"{log_entry['timestamp']} | {color}{response.status_code}{reset} | "
                f"{duration:.0f}ms | {request.method} {request.path}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def update_metrics(self, entry):
        """Update metrics summary"""
        self.metrics['requests'].append(entry)
        self.metrics['summary']['total_requests'] += 1
        
        if entry['status_code'] >= 400:
            self.metrics['summary']['total_errors'] += 1
        
        # Calculate average response time
        total_time = sum(req['duration'] for req in self.metrics['requests'])
        self.metrics['summary']['average_response_time'] = round(
            total_time / len(self.metrics['requests']), 2
        )
        
        # Keep only last 10000 requests in memory
        if len(self.metrics['requests']) > 10000:
            self.metrics['requests'] = self.metrics['requests'][-10000:]
        
        # Save metrics every 100 requests
        if self.metrics['summary']['total_requests'] % 100 == 0:
            self.save_metrics()
    
    def get_color_for_status(self, status_code):
        """Return ANSI color code for status"""
        if status_code >= 500:
            return '\033[31m'  # Red
        if status_code >= 400:
            return '\033[33m'  # Yellow
        if status_code >= 300:
            return '\033[36m'  # Cyan
        if status_code >= 200:
            return '\033[32m'  # Green
        return '\033[0m'  # Reset
