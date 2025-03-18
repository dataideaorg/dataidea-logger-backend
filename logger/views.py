from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.db.models import Count
from .models import ApiKey, EventLogMessage, LlmLogMessage
from .serializers import (
    ApiKeySerializer, 
    EventLogMessageSerializer, EventLogMessageCreateSerializer,
    LlmLogMessageSerializer, LlmLogMessageCreateSerializer
)

# Create your views here.

class ApiKeyViewSet(viewsets.ModelViewSet):
    serializer_class = ApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ApiKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EventLogMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return EventLogMessage.objects.filter(api_key__user=user)

class LlmLogMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LlmLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return LlmLogMessage.objects.filter(api_key__user=user)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_event_log(request):
    serializer = EventLogMessageCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_llm_log(request):
    serializer = LlmLogMessageCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_stats(request):
    """
    Get usage statistics for the authenticated user
    """
    user = request.user
    
    # Get total logs count
    total_event_logs = EventLogMessage.objects.filter(api_key__user=user).count()
    total_llm_logs = LlmLogMessage.objects.filter(api_key__user=user).count()
    
    # Get event logs by level
    logs_by_level = EventLogMessage.objects.filter(api_key__user=user).values('level').annotate(count=Count('id'))
    level_counts = {
        'info': 0,
        'warning': 0,
        'error': 0,
        'debug': 0
    }
    
    for item in logs_by_level:
        level_counts[item['level']] = item['count']
    
    # Get API keys count
    api_keys_count = ApiKey.objects.filter(user=user).count()
    
    return Response({
        'total_event_logs': total_event_logs,
        'total_llm_logs': total_llm_logs,
        'logs_by_level': level_counts,
        'api_keys_count': api_keys_count
    })
