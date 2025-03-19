from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
import csv
import datetime
import json
from collections import defaultdict
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
        return ApiKey.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """
        Handle updates to API keys (including is_active status changes)
        Only allows updating the name and is_active fields
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow updates to name and is_active fields
        data = {}
        if 'name' in request.data:
            data['name'] = request.data['name']
        if 'is_active' in request.data:
            data['is_active'] = request.data['is_active']
            
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

class EventLogMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return EventLogMessage.objects.filter(api_key__user=user)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        """
        Download event logs as CSV
        """
        user = request.user
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="event_logs_{timestamp}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'User ID', 'Message', 'Level', 'Timestamp', 'Metadata'])
        
        for log in queryset:
            writer.writerow([
                log.id,
                log.user_id,
                log.message,
                log.level,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.metadata
            ])
        
        return response

class LlmLogMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LlmLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return LlmLogMessage.objects.filter(api_key__user=user)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        """
        Download LLM logs as CSV
        """
        user = request.user
        queryset = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="llm_logs_{timestamp}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'User ID', 'Source', 'Query', 'Response', 'Timestamp', 'Metadata'])
        
        for log in queryset:
            writer.writerow([
                log.id,
                log.user_id,
                log.source,
                log.query,
                log.response,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.metadata
            ])
        
        return response

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_all_logs(request):
    """
    Download all logs (both event and LLM) as CSV files in a single response
    """
    user = request.user
    
    # Get user's logs
    event_logs = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs = LlmLogMessage.objects.filter(api_key__user=user)
    
    # Create the HttpResponse object with CSV content type
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="all_logs_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # Write event logs
    writer.writerow(['=== EVENT LOGS ==='])
    writer.writerow(['ID', 'User ID', 'Message', 'Level', 'Timestamp', 'Metadata'])
    
    for log in event_logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.message,
            log.level,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.metadata
        ])
    
    # Add a blank row between sections
    writer.writerow([])
    
    # Write LLM logs
    writer.writerow(['=== LLM LOGS ==='])
    writer.writerow(['ID', 'User ID', 'Source', 'Query', 'Response', 'Timestamp', 'Metadata'])
    
    for log in llm_logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.source,
            log.query,
            log.response,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.metadata
        ])
    
    return response

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
    api_keys_count = ApiKey.objects.filter(user=user, is_active=True).count()
    
    return Response({
        'total_event_logs': total_event_logs,
        'total_llm_logs': total_llm_logs,
        'logs_by_level': level_counts,
        'api_keys_count': api_keys_count
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_analytics_data(request):
    """
    Get analytics data for the logged-in user.
    Returns monthly log counts, LLM source distribution, and log level counts.
    """
    user = request.user
    
    # Get all logs for the user
    event_logs = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs = LlmLogMessage.objects.filter(api_key__user=user)
    
    # Calculate monthly log counts
    monthly_data = defaultdict(lambda: {"eventCount": 0, "llmCount": 0})
    
    for log in event_logs:
        month_year = log.timestamp.strftime("%Y-%m")
        monthly_data[month_year]["eventCount"] += 1
    
    for log in llm_logs:
        month_year = log.timestamp.strftime("%Y-%m")
        monthly_data[month_year]["llmCount"] += 1
    
    # Convert to list and sort by month
    monthly_logs = [
        {
            "month": month,
            "eventCount": data["eventCount"],
            "llmCount": data["llmCount"]
        }
        for month, data in sorted(monthly_data.items())
    ]
    
    # Get LLM sources distribution
    llm_sources = llm_logs.values('source').annotate(value=Count('id'))
    llm_sources_data = [
        {
            "name": source["source"] or "Unknown",
            "value": source["value"]
        }
        for source in llm_sources
    ]
    
    # Get log levels distribution
    log_levels = event_logs.values('level').annotate(count=Count('id'))
    log_levels_data = [
        {
            "level": level["level"],
            "count": level["count"]
        }
        for level in log_levels
    ]
    
    return Response({
        "monthly_logs": monthly_logs,
        "llm_sources": llm_sources_data,
        "log_levels": log_levels_data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_analytics_csv(request, data_type):
    """
    Download analytics data as CSV based on the specified type
    """
    user = request.user
    
    if data_type not in ["monthly", "sources", "levels", "all"]:
        return Response({"error": "Invalid data type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate filename with current date
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user.username}_analytics_{data_type}_{current_date}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Get all logs for the user
    event_logs = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs = LlmLogMessage.objects.filter(api_key__user=user)
    
    if data_type in ["monthly", "all"]:
        # Calculate monthly log counts
        monthly_data = defaultdict(lambda: {"eventCount": 0, "llmCount": 0})
        
        for log in event_logs:
            month_year = log.timestamp.strftime("%Y-%m")
            monthly_data[month_year]["eventCount"] += 1
        
        for log in llm_logs:
            month_year = log.timestamp.strftime("%Y-%m")
            monthly_data[month_year]["llmCount"] += 1
        
        # Write monthly data to CSV
        writer.writerow(["Month", "Event Logs", "LLM Logs", "Total Logs"])
        for month, data in sorted(monthly_data.items()):
            total = data["eventCount"] + data["llmCount"]
            writer.writerow([month, data["eventCount"], data["llmCount"], total])
    
    if data_type in ["sources", "all"] and data_type != "monthly":
        # Get LLM sources distribution
        llm_sources = llm_logs.values('source').annotate(count=Count('id'))
        
        # Write sources data to CSV
        writer.writerow(["Source", "Count"])
        for source in llm_sources:
            writer.writerow([source["source"] or "Unknown", source["count"]])
    
    if data_type in ["levels", "all"] and data_type not in ["monthly", "sources"]:
        # Get log levels distribution
        log_levels = event_logs.values('level').annotate(count=Count('id'))
        
        # Write levels data to CSV
        writer.writerow(["Level", "Count"])
        for level in log_levels:
            writer.writerow([level["level"], level["count"]])
    
    return response
