from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from apps.core.models import Organization
from apps.accounts.permissions import IsOrgEmployee
from apps.ai_agent.services import LLMService

class ChatWithAgentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrgEmployee]

    def post(self, request, organization_id, *args, **kwargs):
        org = get_object_or_404(Organization, id=organization_id)
        
        # Check module availability
        if not org.is_ai_agent_enabled:
            return Response({"error": "Module 'ai_agent' is not enabled for this organization"}, status=status.HTTP_403_FORBIDDEN)
            
        messages = request.data.get('messages', [])
        if not messages or not isinstance(messages, list):
            return Response({"error": "Payload 'messages' must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Clean history to prevent malicious system injection
        cleaned_history = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role in ["user", "assistant"] and content:
                cleaned_history.append({"role": role, "content": content})
                
        service = LLMService(org)
        response_text = service.run_chat(cleaned_history)
        
        return Response({"response": response_text})
