import requests
from django.conf import settings


class EmployeeService:
    """
    Service class to handle employee information fetching from auth service.
    """
    
    def __init__(self, request):
        self.request = request
    
    def get_client_jwt_token(self):
        """
        Extract JWT token from client request (cookies or Authorization header).
        """
        # Try to get token from Authorization header first
        auth_header = self.request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Try to get token from cookies
        access_token = self.request.COOKIES.get('access_token')
        if access_token:
            return access_token
            
        return None

    def fetch_employee_info(self, employee_cookie_id):
        """
        Fetch employee information from auth service using employee_cookie_id.
        Uses the client's JWT token for authentication.
        """
        if not employee_cookie_id:
            print("fetch_employee_info: employee_cookie_id is None")
            return None
            
        try:
            # Get JWT token from client request
            token = self.get_client_jwt_token()
            if not token:
                print("fetch_employee_info: No JWT token found in client request")
                return None
            
            # Get auth service URL from settings
            auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://localhost:8001')
            if not auth_service_url:
                print("fetch_employee_info: AUTH_SERVICE_URL not configured in settings")
                return None
            
            # Make request to auth service
            url = f"{auth_service_url}/api/v1/tts/user-info/{employee_cookie_id}/"
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            }
            
            print(f"fetch_employee_info: Making request to {url}")
            print(f"fetch_employee_info: Using client JWT token (first 20 chars): {token[:20]}...")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"fetch_employee_info: Received successful response: {response.json()}")
                return response.json()
            elif response.status_code == 404:
                print(f"fetch_employee_info: User not found for employee_cookie_id: {employee_cookie_id}")
                return None
            else:
                print(f"fetch_employee_info: Auth service returned status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("fetch_employee_info: Timeout when calling auth service")
            return None
        except requests.exceptions.RequestException as e:
            print(f"fetch_employee_info: Error calling auth service: {e}")
            return None
        except Exception as e:
            print(f"fetch_employee_info: Unexpected error when fetching employee info: {e}")
            return None

    def fetch_multiple_employees_info(self, employee_cookie_ids):
        """
        Fetch employee information for multiple employee_cookie_ids.
        Tries batch request first, falls back to individual requests if batch endpoint is not available.
        """
        if not employee_cookie_ids:
            return {}
            
        try:
            # Get JWT token from client request
            token = self.get_client_jwt_token()
            if not token:
                print("fetch_multiple_employees_info: No JWT token found in client request")
                return {}
            
            # Get auth service URL from settings
            auth_service_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://localhost:8001')
            if not auth_service_url:
                print("fetch_multiple_employees_info: AUTH_SERVICE_URL not configured in settings")
                return {}
            
            # Try batch request first
            try:
                url = f"{auth_service_url}/api/v1/tts/users-info/"
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                }
                
                payload = {
                    'employee_cookie_ids': list(employee_cookie_ids)
                }
                
                print(f"fetch_multiple_employees_info: Trying batch request to {url} for {len(employee_cookie_ids)} employees")
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"fetch_multiple_employees_info: Batch request successful, received data for {len(result)} employees")
                    return result  # Expected format: {employee_cookie_id: employee_data, ...}
                elif response.status_code == 404:
                    print("fetch_multiple_employees_info: Batch endpoint not found, falling back to individual requests")
                    return self._fetch_employees_individually(employee_cookie_ids, token, auth_service_url)
                else:
                    print(f"fetch_multiple_employees_info: Batch request failed with status {response.status_code}: {response.text}")
                    print("fetch_multiple_employees_info: Falling back to individual requests")
                    return self._fetch_employees_individually(employee_cookie_ids, token, auth_service_url)
                    
            except requests.exceptions.RequestException as e:
                print(f"fetch_multiple_employees_info: Batch request failed with error: {e}")
                print("fetch_multiple_employees_info: Falling back to individual requests")
                return self._fetch_employees_individually(employee_cookie_ids, token, auth_service_url)
                
        except Exception as e:
            print(f"fetch_multiple_employees_info: Unexpected error: {e}")
            return {}

    def _fetch_employees_individually(self, employee_cookie_ids, token, auth_service_url):
        """
        Fallback method to fetch employee information using individual requests.
        """
        employee_info_map = {}
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        print(f"_fetch_employees_individually: Making {len(employee_cookie_ids)} individual requests")
        
        for employee_cookie_id in employee_cookie_ids:
            try:
                url = f"{auth_service_url}/api/v1/tts/user-info/{employee_cookie_id}/"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    employee_info_map[employee_cookie_id] = response.json()
                elif response.status_code == 404:
                    print(f"_fetch_employees_individually: User not found for employee_cookie_id: {employee_cookie_id}")
                else:
                    print(f"_fetch_employees_individually: Failed to fetch employee {employee_cookie_id}: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"_fetch_employees_individually: Error fetching employee {employee_cookie_id}: {e}")
                continue
        
        print(f"_fetch_employees_individually: Successfully fetched {len(employee_info_map)} employees")
        return employee_info_map