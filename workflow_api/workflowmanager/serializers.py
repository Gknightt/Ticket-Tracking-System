from rest_framework import serializers


from workflow.models import Workflows

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflows
        fields = '__all__'

from step.models import Steps, StepTransition

class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Steps
        fields = '__all__'

class StepTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepTransition
        fields = '__all__'
