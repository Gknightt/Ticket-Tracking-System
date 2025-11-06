from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import StepInstance
from .serializers import StepInstanceSerializer
from .services import EmployeeService
from authentication import JWTCookieAuthentication, TTSSystemPermission


class StepInstanceView(ListAPIView):
    """
    Main view for listing step instances with employee information populated.
    """
    serializer_class = StepInstanceSerializer

    def get_queryset(self):
        queryset = StepInstance.objects.all()

        task_id = self.request.query_params.get('task_id')
        user_id = self.request.query_params.get('user_id')

        if task_id:
            queryset = queryset.filter(task_id=task_id)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Sort by latest created
        queryset = queryset.order_by('-created_at')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to populate employee information before returning response.
        Optimized to batch employee info requests.
        """
        response = super().list(request, *args, **kwargs)
        
        print(f"list: Response status code: {response.status_code}")
        
        # Process each step instance to populate employee information
        if response.status_code == 200:
            # Handle both paginated and non-paginated responses
            step_instances_data = []
            if 'results' in response.data:
                step_instances_data = response.data['results']
            elif isinstance(response.data, list):
                step_instances_data = response.data
            else:
                return response
            
            # Use the EmployeeService to handle employee info fetching
            employee_service = EmployeeService(request)
            
            # Collect all employee_cookie_ids that need fetching
            tickets_needing_employee_info = []
            employee_cookie_ids_to_fetch = set()
            
            for step_instance_data in step_instances_data:
                task_data = step_instance_data.get('task')
                if task_data and 'ticket' in task_data:
                    ticket_data = task_data['ticket']
                    
                    # Check if employee is null but employee_cookie_id exists
                    if ticket_data.get('employee') is None and ticket_data.get('employee_cookie_id'):
                        print(f"list: Ticket {ticket_data.get('id')} needs employee info for cookie_id: {ticket_data.get('employee_cookie_id')}")
                        tickets_needing_employee_info.append({
                            'step_instance_data': step_instance_data,
                            'ticket_data': ticket_data,
                            'employee_cookie_id': ticket_data.get('employee_cookie_id')
                        })
                        employee_cookie_ids_to_fetch.add(ticket_data.get('employee_cookie_id'))
            
            print(f"list: Found {len(tickets_needing_employee_info)} tickets needing employee info")
            print(f"list: Unique employee_cookie_ids to fetch: {employee_cookie_ids_to_fetch}")
            
            # Fetch all employee info in one batch request
            if employee_cookie_ids_to_fetch:
                employee_info_map = employee_service.fetch_multiple_employees_info(employee_cookie_ids_to_fetch)
                print(f"list: Received employee_info_map: {employee_info_map}")
                
                # Update tickets with fetched employee info
                for ticket_info in tickets_needing_employee_info:
                    employee_cookie_id = ticket_info['employee_cookie_id']
                    # Convert to string to match the JSON response key format
                    employee_info = employee_info_map.get(str(employee_cookie_id))
                    ticket_id = ticket_info['ticket_data'].get('id')
                    
                    print(f"list: Processing ticket {ticket_id} with employee_cookie_id {employee_cookie_id}")
                    print(f"list: Looking up employee info with key: '{employee_cookie_id}' (string version)")
                    print(f"list: Employee info for cookie_id {employee_cookie_id}: {employee_info}")
                    
                    if employee_info:
                        # Update the database record
                        try:
                            step_instance = StepInstance.objects.get(
                                step_instance_id=ticket_info['step_instance_data']['step_instance_id']
                            )
                            ticket = step_instance.task_id.ticket
                            
                            print(f"list: Before update - ticket {ticket.id} employee field: {ticket.employee}")
                            ticket.employee = employee_info
                            ticket.save(update_fields=['employee'])
                            print(f"list: After update - ticket {ticket.id} employee field: {ticket.employee}")
                            
                            # Update the response data
                            print(f"list: Before response update - ticket_data employee: {ticket_info['ticket_data'].get('employee')}")
                            ticket_info['ticket_data']['employee'] = employee_info
                            print(f"list: After response update - ticket_data employee: {ticket_info['ticket_data'].get('employee')}")
                            
                        except Exception as e:
                            print(f"list: Error updating ticket {ticket_id}: {e}")
                            # Still update the response data even if database update fails
                            ticket_info['ticket_data']['employee'] = employee_info
                            print(f"list: Updated response data only for ticket {ticket_id}")
                    else:
                        print(f"list: No employee info found for cookie_id {employee_cookie_id}")
                        print(f"list: Available keys in employee_info_map: {list(employee_info_map.keys())}")
                
                print(f"list: Successfully processed {len(employee_info_map)} employee records")
        
        return response


class SecureStepInstanceDetailView(RetrieveAPIView):
    """
    Secure view for retrieving a specific step instance by step_instance_id.
    Only accessible if the authenticated user is assigned to the step instance.
    """
    serializer_class = StepInstanceSerializer
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [TTSSystemPermission]
    lookup_field = 'step_instance_id'
    lookup_url_kwarg = 'step_instance_id'

    def get_queryset(self):
        return StepInstance.objects.all()

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve method to check user authorization and populate employee information.
        """
        try:
            step_instance_id = kwargs.get('step_instance_id')
            
            # Get the step instance
            try:
                step_instance = StepInstance.objects.get(step_instance_id=step_instance_id)
            except StepInstance.DoesNotExist:
                return JsonResponse(
                    {'error': 'Step instance not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if the authenticated user is authorized to view this step instance
            authenticated_user_id = request.user.user_id
            step_instance_user_id = step_instance.user_id
            
            if str(authenticated_user_id) != str(step_instance_user_id):
                return JsonResponse(
                    {
                        'error': 'No authorization to handle this ticket',
                        'message': f'This step instance is assigned to a different user'
                    }, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Serialize the step instance
            serializer = self.get_serializer(step_instance)
            response_data = serializer.data

            # Populate employee information if needed
            task_data = response_data.get('task')
            if task_data and 'ticket' in task_data:
                ticket_data = task_data['ticket']
                
                # Check if employee is null but employee_cookie_id exists
                if ticket_data.get('employee') is None and ticket_data.get('employee_cookie_id'):
                    employee_service = EmployeeService(request)
                    employee_cookie_id = ticket_data.get('employee_cookie_id')
                    
                    # Fetch employee info
                    employee_info_map = employee_service.fetch_multiple_employees_info({employee_cookie_id})
                    employee_info = employee_info_map.get(str(employee_cookie_id))
                    
                    if employee_info:
                        # Update the database record
                        try:
                            ticket = step_instance.task_id.ticket
                            ticket.employee = employee_info
                            ticket.save(update_fields=['employee'])
                            
                            # Update the response data
                            ticket_data['employee'] = employee_info
                            
                        except Exception as e:
                            print(f"Error updating ticket employee info: {e}")
                            # Still update the response data even if database update fails
                            ticket_data['employee'] = employee_info

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )