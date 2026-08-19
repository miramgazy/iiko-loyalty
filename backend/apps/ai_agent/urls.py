from django.urls import path
from apps.ai_agent.views import ChatWithAgentView

urlpatterns = [
    path('organizations/<int:organization_id>/chat/', ChatWithAgentView.as_view(), name='ai_chat'),
]
