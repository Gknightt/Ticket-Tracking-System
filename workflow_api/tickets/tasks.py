from celery import shared_task
from tickets.models import WorkflowTicket
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ValidationError

@shared_task(name='tickets.tasks.receive_ticket')
def receive_ticket(ticket_data):
    import traceback
    try:
        # ✅ Normalize sub_category -> subcategory
        if 'sub_category' in ticket_data:
            ticket_data['subcategory'] = ticket_data.pop('sub_category')

        # ✅ Parse date and datetime fields if they exist
        if isinstance(ticket_data.get('opened_on'), str):
            try:
                ticket_data['opened_on'] = datetime.fromisoformat(ticket_data['opened_on']).date()
            except Exception:
                ticket_data['opened_on'] = None

        if isinstance(ticket_data.get('fetched_at'), str):
            try:
                dt = parse_datetime(ticket_data['fetched_at'])
                ticket_data['fetched_at'] = make_aware(dt) if dt and dt.tzinfo is None else dt
            except Exception:
                ticket_data['fetched_at'] = None

        for dur_field in ['response_time', 'resolution_time']:
            if isinstance(ticket_data.get(dur_field), str):
                try:
                    h, m, s = map(float, ticket_data[dur_field].split(':'))
                    ticket_data[dur_field] = timedelta(hours=h, minutes=m, seconds=s)
                except Exception:
                    ticket_data[dur_field] = None

        # ✅ Only keep allowed fields to prevent model crash
        allowed_fields = {
            'ticket_id', 'subject', 'customer', 'priority', 'status', 'opened_on', 'sla',
            'description', 'department', 'position', 'fetched_at', 'category', 'subcategory',
            'original_ticket_id', 'source_service', 'attachments', 'is_task_allocated',
            'submit_date', 'update_date', 'response_time', 'resolution_time', 'time_closed', 'rejection_reason'
        }
        ticket_data = {k: v for k, v in ticket_data.items() if k in allowed_fields}

        # ✅ Ensure required fields exist
        required_fields = ['ticket_id', 'category', 'subcategory']
        missing = [field for field in required_fields if not ticket_data.get(field)]
        if missing:
            return {
                "status": "error",
                "type": "validation_error",
                "errors": {field: "This field is required." for field in missing}
            }

        # ✅ Create and save
        ticket = WorkflowTicket(**ticket_data)
        ticket.full_clean()
        ticket.save()

        return {"status": "success", "ticket_id": ticket.ticket_id}

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
