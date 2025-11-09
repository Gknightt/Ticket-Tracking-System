from rest_framework import serializers
from .models import Steps, StepTransition
from role.models import Roles


class StepSerializer(serializers.ModelSerializer):
    is_initialized = serializers.SerializerMethodField()
    class Meta:
        model = Steps
        fields = (
            "step_id",
            "workflow_id",
            "role_id", 
            "name", 
            "description",
            "is_initialized",
            "created_at", 
            "updated_at",
            "instruction"
        )
    def get_is_initialized(self, obj):
        return StepTransition.objects.filter(to_step_id=obj).exists()


class StepTransitionSerializer(serializers.ModelSerializer):
    from_step_id = serializers.SlugRelatedField(
        queryset=Steps.objects.all(),
        allow_null=True,
        slug_field='step_id'
    )
    to_step_id = serializers.SlugRelatedField(
        queryset=Steps.objects.all(),
        slug_field='step_id',
        allow_null=True,
        required=False
    )

    class Meta:
        model = StepTransition
        fields = [
            'transition_id',
            'workflow_id',
            'from_step_id', 
            'to_step_id',
        ]
        read_only_fields = ['transition_id']

    def validate(self, attrs):
        frm = attrs.get('from_step_id') or getattr(self.instance, 'from_step_id', None)
        to = attrs.get('to_step_id') or getattr(self.instance, 'to_step_id', None)
        workflow_id = attrs.get('workflow_id') or getattr(self.instance, 'workflow_id', None)

        if not frm and not to:
            raise serializers.ValidationError("At least one of from_step_id or to_step_id must be provided.")

        if frm and to and frm.pk == to.pk:
            raise serializers.ValidationError("from_step_id and to_step_id must be different.")

        if frm and to and frm.workflow_id != to.workflow_id:
            raise serializers.ValidationError("from_step_id and to_step_id must belong to the same workflow.")

        # Constraint 1: Only one from_step = null per workflow
        if not frm:
            existing = StepTransition.objects.filter(workflow_id=workflow_id, from_step_id__isnull=True)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError("A StepTransition with from_step = null already exists for this workflow.")

        return attrs

    def update(self, instance, validated_data):
        # Constraint 2: Disallow updating from_step if it's null
        new_from_step = validated_data.get('from_step_id')
        if instance.from_step_id is None and new_from_step is not None:
            raise serializers.ValidationError("Cannot modify from_step_id of the start transition (from_step = null).")

        instance.from_step_id = validated_data.get('from_step_id', instance.from_step_id)
        instance.to_step_id = validated_data.get('to_step_id', instance.to_step_id)
        instance.workflow_id = validated_data.get('workflow_id', instance.workflow_id)

        instance.full_clean()
        instance.save()
        return instance