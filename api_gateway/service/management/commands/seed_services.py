from django.core.management.base import BaseCommand
from service.models import Service

class Command(BaseCommand):
    help = 'Seeds the database with initial service endpoints for the TTS system'

    def handle(self, *args, **kwargs):
        # Define all services in the TTS system
        services = [
            # User Service endpoints
            {
                'system': 'TTS',
                'service': 'User',
                'base_url': 'http://user-service:8000'
            },
            # Ticket Service endpoints
            {
                'system': 'TTS',
                'service': 'Ticket',
                'base_url': 'http://ticket_service:7000'
            },
            # Workflow Service endpoints
            {
                'system': 'TTS',
                'service': 'Workflow',
                'base_url': 'http://workflow_api:8000'
            }
        ]

        # Create or update each service
        for service_data in services:
            service, created = Service.objects.get_or_create(
                system=service_data['system'],
                service=service_data['service'],
                defaults={'base_url': service_data['base_url']}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created service: {service.system}/{service.service} -> {service.base_url}"
                ))
            else:
                # Update the URL if it exists but is different
                if service.base_url != service_data['base_url']:
                    old_url = service.base_url
                    service.base_url = service_data['base_url']
                    service.save()
                    self.stdout.write(self.style.WARNING(
                        f"Updated service: {service.system}/{service.service} from {old_url} to {service.base_url}"
                    ))
                else:
                    self.stdout.write(self.style.NOTICE(
                        f"Service already exists: {service.system}/{service.service} -> {service.base_url}"
                    ))
        
        # Verification
        self.stdout.write(self.style.SUCCESS(f"Total services in database: {Service.objects.count()}"))