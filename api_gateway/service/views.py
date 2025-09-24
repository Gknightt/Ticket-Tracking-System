from django.shortcuts import render
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Service

# Serializer for the Service model
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'system', 'service', 'base_url']

# ViewSet for the Service model
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    # Custom action to retrieve all service mappings
    @action(detail=False, methods=['get'])
    def mappings(self, request):
        services = self.get_queryset()
        mappings = {f"{service.system}/{service.service}": service.base_url for service in services}
        return Response(mappings)

@method_decorator(csrf_exempt, name='dispatch')
class AddServiceView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            system = data.get('system')
            service = data.get('service')
            base_url = data.get('base_url')

            if not system or not service or not base_url:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            service_entry, created = Service.objects.get_or_create(
                system=system, service=service, defaults={"base_url": base_url}
            )

            if not created:
                service_entry.base_url = base_url
                service_entry.save()

            return JsonResponse({"message": "Service added/updated successfully"}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class GetServiceMappingsView(View):
    def get(self, request):
        services = Service.objects.all()
        mappings = {f"{service.system}/{service.service}": service.base_url for service in services}
        return JsonResponse(mappings, status=200)
