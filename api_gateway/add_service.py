#!/usr/bin/env python

import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_gateway.settings")
django.setup()

from service.models import Service

# Service data to add
service_data = {
    "system": "TTS",
    "service": "Ticket",
    "base_url": "http://localhost:8004"
}

# Create or update service record
service, created = Service.objects.get_or_create(
    system=service_data["system"], 
    service=service_data["service"],
    defaults={"base_url": service_data["base_url"]}
)

if created:
    print(f"Service {service_data['system']}/{service_data['service']} created successfully")
else:
    service.base_url = service_data["base_url"]
    service.save()
    print(f"Service {service_data['system']}/{service_data['service']} updated successfully")

# List all services for verification
print("\nCurrent services in database:")
for service in Service.objects.all():
    print(f"ID: {service.id}, System: {service.system}, Service: {service.service}, URL: {service.base_url}")