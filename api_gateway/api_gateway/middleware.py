from django.utils.deprecation import MiddlewareMixin

class ApiGatewayMiddleware(MiddlewareMixin):
    """
    Middleware that marks requests passing through the API Gateway.
    This helps backend services recognize and trust requests coming from our gateway.
    """
    
    def process_request(self, request):
        # Add a marker in the request to identify it's coming from our trusted API gateway
        request.META['HTTP_X_API_GATEWAY'] = 'true'
        return None