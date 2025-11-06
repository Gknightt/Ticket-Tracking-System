from django.urls import path
from .views import StepInstanceView
from .action_views import AvailableActionsView
from .trigger_views import TriggerNextStepView
from .simple_views import SimpleStepInstanceView

urlpatterns = [
    path('<str:step_instance_id>/actions/', AvailableActionsView.as_view()),
    # path('<str:step_instance_id>/', TriggerNextStepView.as_view()),
    path('<uuid:step_instance_id>/', TriggerNextStepView.as_view()),
    path('list/', StepInstanceView.as_view()),
    path('simple/', SimpleStepInstanceView.as_view()),
]
