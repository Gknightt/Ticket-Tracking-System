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

        # Forward all headers from the original request except Host and Content-Length
        # This will include X-CSRFToken if sent by the frontend
        headers = {key: value for key, value in request.headers.items() 
                  if key.lower() not in ['host', 'content-length']}
        
        # Simply pass through all cookies from the original request
        cookies = request.COOKIES
        
        # Handle request body 
        body = request.body
        
        # Make the request to the target service
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            cookies=cookies,  # Forward the original cookies as-is
            data=body,
            params=request.GET,
            allow_redirects=False  # Don't follow redirects, let the client handle them
        )
        
        # Print debug info about the response
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Create Django response object
        if response.headers.get('Content-Type', '').startswith('application/json'):
            # For JSON responses
            try:
                json_response = response.json()
                django_response = JsonResponse(json_response, status=response.status_code, safe=False)
            except ValueError:
                # If JSON parsing fails, fall back to raw response
                django_response = HttpResponse(
                    response.content, 
                    status=response.status_code,
                    content_type=response.headers.get('Content-Type', 'text/plain')
                )
        else:
            # For non-JSON responses
            django_response = HttpResponse(
                response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'text/plain')
            )
        
        # Copy all headers from the backend response to our Django response
        # Skip certain headers that would be set by Django automatically
        skip_headers = {'content-length', 'content-encoding', 'transfer-encoding', 'connection',
                       'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te',
                       'trailers', 'upgrade', 'content-type'}
        
        for header, value in response.headers.items():
            if header.lower() not in skip_headers:
                django_response[header] = value
        
        # Forward all cookies from the backend response
        for cookie in response.cookies.items():
            cookie_name, cookie_value = cookie
            cookie_dict = requests.utils.dict_from_cookiejar(response.cookies)
            cookie_obj = response.cookies.get(cookie_name)
            
            # Get all cookie attributes
            django_response.set_cookie(
                key=cookie_name,
                value=cookie_value,
                max_age=cookie_obj.get('max-age'),
                expires=cookie_obj.get('expires'),
                path=cookie_obj.get('path', '/'),
                domain=cookie_obj.get('domain'),
                secure=cookie_obj.get('secure', False),
                httponly=cookie_obj.get('httponly', False),
                samesite=cookie_obj.get('samesite', 'Lax')
            )
        
        return django_response
            
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
