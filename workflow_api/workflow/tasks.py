from celery import shared_task
from workflow.models import Workflows
from workflow.serializers import WorkflowDetailSerializer
from workflow_api.celery import app  # Your Celery instance
import logging

logger = logging.getLogger(__name__)

@shared_task(name="workflow.send_to_consumer") 
def send_to_consumer(workflow_id):
    try:
        workflow = Workflows.objects.get(workflow_id=workflow_id)
        serializer = WorkflowDetailSerializer(workflow)
        serialized_data = serializer.data
        # Send to the consumer task in `task_service` via the queue
        app.send_task(
            "receive_workflow",  # ← Remove "workflow.tasks." prefix
            kwargs={"payload": {"workflow": serialized_data}},
            queue="workflow_send_queue"
        )
        logger.info(f"Dispatched workflow {workflow_id} to consumer")

    except Workflows.DoesNotExist:
        logger.error(f"Workflow with ID {workflow_id} does not exist")



@shared_task(name="workflow.send_hello")
def send_hello():
    app.send_task(
        "receive_hello",
        kwargs={"payload": {"message": "Hello"}},
        queue="workflow_send_queue"
    )