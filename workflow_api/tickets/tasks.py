from celery import shared_task
from tickets.models import WorkflowTicket
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError
from django.conf import settings
import requests
from urllib.parse import urlparse, urljoin
import os
from django.db import transaction

@shared_task(name='tickets.tasks.receive_ticket')
def receive_ticket(ticket_data):
    import traceback
    try:
        # ✅ Map incoming fields to model fields
        field_mapping = {
            'id': 'original_ticket_id',
            'ticket_number': 'ticket_number',
            'sub_category': 'sub_category',
        }
        
        # Apply field mapping
        for old_key, new_key in field_mapping.items():
            if old_key in ticket_data:
                ticket_data[new_key] = ticket_data.pop(old_key)

        # ✅ Parse datetime fields
        datetime_fields = ['submit_date', 'update_date', 'fetched_at']
        for field in datetime_fields:
            if isinstance(ticket_data.get(field), str):
                try:
                    dt = parse_datetime(ticket_data[field])
                    ticket_data[field] = make_aware(dt) if dt and dt.tzinfo is None else dt
                except Exception:
                    ticket_data[field] = None

        # ✅ Parse date fields
        date_fields = ['scheduled_date', 'expected_return_date', 'performance_start_date', 'performance_end_date']
        for field in date_fields:
            if isinstance(ticket_data.get(field), str):
                try:
                    ticket_data[field] = datetime.fromisoformat(ticket_data[field]).date()
                except Exception:
                    ticket_data[field] = None

        # ✅ Parse duration fields
        for dur_field in ['response_time', 'resolution_time']:
            if isinstance(ticket_data.get(dur_field), str):
                try:
                    h, m, s = map(float, ticket_data[dur_field].split(':'))
                    ticket_data[dur_field] = timedelta(hours=h, minutes=m, seconds=s)
                except Exception:
                    ticket_data[dur_field] = None

        # ✅ Handle decimal fields
        if ticket_data.get('requested_budget'):
            try:
                ticket_data['requested_budget'] = float(ticket_data['requested_budget'])
            except (ValueError, TypeError):
                ticket_data['requested_budget'] = None

        # ✅ Ensure JSON fields have proper defaults
        if 'dynamic_data' not in ticket_data or ticket_data['dynamic_data'] is None:
            ticket_data['dynamic_data'] = {}
        if 'attachments' not in ticket_data or ticket_data['attachments'] is None:
            ticket_data['attachments'] = []
        if 'cost_items' not in ticket_data or ticket_data['cost_items'] is None:
            ticket_data['cost_items'] = None

        # ✅ Filter allowed fields for the updated model
        allowed_fields = {
            'ticket_id', 'original_ticket_id', 'ticket_number', 'source_service',
            'employee', 'employee_cookie_id',
            'subject', 'category', 'subcategory', 'sub_category', 'description', 
            'scheduled_date', 'submit_date', 'update_date', 'assigned_to',
            'priority', 'status', 'department',
            'asset_name', 'serial_number', 'location', 'expected_return_date', 'issue_type', 'other_issue',
            'performance_start_date', 'performance_end_date',
            'approved_by', 'rejected_by', 'cost_items', 'requested_budget', 'fiscal_year', 'department_input',
            'dynamic_data', 'attachments',
            'response_time', 'resolution_time', 'time_closed', 'rejection_reason',
            'is_task_allocated', 'fetched_at'
        }
        ticket_data = {k: v for k, v in ticket_data.items() if k in allowed_fields}

        # ✅ Validate required fields
        required_fields = ['subject']
        missing = [field for field in required_fields if not ticket_data.get(field)]
        if missing:
            return {
                "status": "error",
                "type": "validation_error",
                "errors": {field: "This field is required." for field in missing}
            }

        # ✅ Validate attachments exist
        validated_attachments = []
        for att in ticket_data.get("attachments", []):
            file_url = att.get("file")
            if not file_url:
                continue
            try:
                # Extract the path after /media/
                relative_path = urlparse(file_url).path.split("/media/")[1]
                abs_path = os.path.join(settings.MEDIA_ROOT, os.path.normpath(relative_path))

                # Ensure destination directory exists
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)

                # Skip downloading if the file already exists
                if os.path.exists(abs_path):
                    print(f"✅ File already exists: {abs_path}")
                else:
                    print(f"📥 Downloading: {file_url}")
                    response = requests.get(file_url)
                    if response.status_code == 200:
                        with open(abs_path, "wb") as f:
                            f.write(response.content)
                        print(f"✅ Stored: {abs_path}")
                    else:
                        print(f"❌ Failed to download: {file_url} (status {response.status_code})")
                        continue  # skip this attachment

                # Attach the new internal file URL
                validated_attachments.append({
                    "file": urljoin(settings.BASE_URL, f"/media/{relative_path.replace(os.sep, '/')}")
                })

            except Exception as e:
                print(f"❌ Error processing attachment {file_url}: {e}")
                continue

        ticket_data["attachments"] = validated_attachments

        # ✅ Create and save with explicit transaction
        with transaction.atomic():
            # Use update_or_create to handle duplicates based on original_ticket_id or ticket_number
            lookup_fields = {}
            if ticket_data.get('original_ticket_id'):
                lookup_fields['original_ticket_id'] = ticket_data['original_ticket_id']
            elif ticket_data.get('ticket_number'):
                lookup_fields['ticket_number'] = ticket_data['ticket_number']
            
            if lookup_fields:
                ticket, created = WorkflowTicket.objects.update_or_create(
                    **lookup_fields,
                    defaults=ticket_data
                )
                action = "created" if created else "updated"
            else:
                ticket = WorkflowTicket(**ticket_data)
                ticket.full_clean()
                ticket.save()
                action = "created"
            
            # Force a database query to verify the save worked
            saved_ticket = WorkflowTicket.objects.get(pk=ticket.pk)
            print(f"✅ Verified ticket {action} with ID: {saved_ticket.pk}")

        return {"status": "success", "ticket_id": ticket.ticket_id or ticket.original_ticket_id, "action": action}

    except ValidationError as ve:
        return {
            "status": "error",
            "type": "validation_error",
            "errors": ve.message_dict
        }

    except Exception as e:
        return {
            "status": "error",
            "type": "exception",
            "error": str(e),
            "trace": traceback.format_exc()
        }


# tickets/tasks.py

import json

@shared_task(name="send_ticket_status")
def send_ticket_status(ticket_id, status):
    data = {
        "ticket_number": ticket_id,
        "new_status": status
    }
    json_data = json.dumps(data)
    print("Sending to queue:", json_data)
    return json_data
