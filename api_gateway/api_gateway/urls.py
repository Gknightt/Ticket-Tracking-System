"""
URL configuration for api_gateway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
import requests
import json
from django.core.exceptions import ObjectDoesNotExist
from service.models import Service

def forward_request(request, system, service, query):
    try:
        # Fetch the service mapping from the database
        service_mapping = Service.objects.get(system=system, service=service)
        target_url = f"{service_mapping.base_url}/{query}"
        
        # Print debug information
        print(f"Forwarding request to: {target_url}")
        print(f"Method: {request.method}")
        print(f"Query params: {request.GET}")

        # Forward the request to the target service
        headers = {key: value for key, value in request.headers.items() if key not in ['Host', 'Content-Length']}
        
        # Add CSRF-related headers to bypass CSRF protection on backend services
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Add X-CSRFToken header for Django backend services
            csrf_token = request.META.get('CSRF_COOKIE', '')
            if csrf_token:
                headers['X-CSRFToken'] = csrf_token
            
            # Add additional headers to help Django recognize this as a safe request
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            # Tell backend services that this request is from the trusted API gateway
            headers['X-API-Gateway'] = 'true'
        
        # Handle request body for different content types
        body = request.body
        
        # Make the request to the target service
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body,
            params=request.GET
        )
        
        # Print debug info about the response
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content: {response.content[:100]}...")  # Print first 100 chars
        
        # Try to parse the response as JSON
        try:
            json_response = response.json()
            return JsonResponse(json_response, status=response.status_code, safe=False)
        except ValueError:
            # If the response is not JSON, return the raw content
            return HttpResponse(response.content, status=response.status_code, content_type=response.headers.get('Content-Type', 'text/plain'))
            
    except ObjectDoesNotExist:
        return JsonResponse({"error": f"Service not found for {system}/{service}"}, status=404)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "error": "Service request failed", 
            "details": str(e),
            "target_url": f"{service_mapping.base_url}/{query}" if 'service_mapping' in locals() else "Unknown"
        }, status=500)
    except Exception as e:
        import traceback
        return JsonResponse({
            "error": "Unexpected error", 
            "details": str(e),
            "traceback": traceback.format_exc()
        }, status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('service/', include('service.urls')),
    # Add the API proxy paths
    path('api/<str:system>/<str:service>/<path:query>', forward_request, name='forward-request-api'),
    # Add support for the TTS/Ticket/api/tickets/ format
    path('<str:system>/<str:service>/<path:query>', forward_request, name='forward-request-direct'),
]
