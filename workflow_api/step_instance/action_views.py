from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import StepInstance
from action.serializers import ActionSerializer
from step.models import StepTransition


class AvailableActionsView(APIView):
    """
    View to get available actions for a step instance.
    """
    def get(self, request, step_instance_id):
        try:
            instance = StepInstance.objects.get(step_instance_id=step_instance_id)
        except StepInstance.DoesNotExist:
            return Response({'detail': 'StepInstance not found'}, status=status.HTTP_404_NOT_FOUND)

        current_step = instance.step_transition_id.to_step_id
        transitions = StepTransition.objects.filter(from_step_id=current_step)
        actions = [t.action_id for t in transitions if t.action_id]

        serializer = ActionSerializer(actions, many=True)
        return Response(serializer.data)