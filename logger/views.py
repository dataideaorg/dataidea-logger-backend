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
from .models import ApiKey, EventLogMessage, LlmLogMessage, Project
from .serializers import (
    ApiKeySerializer, 
    EventLogMessageSerializer, EventLogMessageCreateSerializer,
    LlmLogMessageSerializer, LlmLogMessageCreateSerializer,
    ProjectSerializer
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

class EventLogMessageViewSet(viewsets.ModelViewSet):
    serializer_class = EventLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'delete', 'head', 'options']  # Only allow GET, DELETE
    
    def get_queryset(self):
        user = self.request.user
        queryset = EventLogMessage.objects.filter(api_key__user=user)
        
        # Filter by project if project ID is provided in query params
        project_id = self.request.query_params.get('project')
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                queryset = queryset.filter(project=project)
            except Project.DoesNotExist:
                # If project doesn't exist or doesn't belong to user, return empty queryset
                return EventLogMessage.objects.none()
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a single event log entry
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "status": "success", 
            "message": "Log entry deleted successfully"
        }, status=status.HTTP_200_OK)
    
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

class LlmLogMessageViewSet(viewsets.ModelViewSet):
    serializer_class = LlmLogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'delete', 'head', 'options']  # Only allow GET, DELETE
    
    def get_queryset(self):
        user = self.request.user
        queryset = LlmLogMessage.objects.filter(api_key__user=user)
        
        # Filter by project if project ID is provided in query params
        project_id = self.request.query_params.get('project')
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
                queryset = queryset.filter(project=project)
            except Project.DoesNotExist:
                # If project doesn't exist or doesn't belong to user, return empty queryset
                return LlmLogMessage.objects.none()
        
        return queryset
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a single LLM log entry
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "status": "success", 
            "message": "Log entry deleted successfully"
        }, status=status.HTTP_200_OK)
    
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
    
    # Filter by project if project ID is provided
    project_id = request.query_params.get('project')
    filename_project = ""
    
    if project_id:
        try:
            project = Project.objects.get(id=project_id, user=user)
            event_logs = event_logs.filter(project=project)
            llm_logs = llm_logs.filter(project=project)
            filename_project = f"_{project.name}"
        except Project.DoesNotExist:
            # If project doesn't exist or doesn't belong to user, return error
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Create the HttpResponse object with CSV content type
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="all_logs{filename_project}_{timestamp}.csv"'
    
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
    """
    Create a new event log entry.
    
    You can specify the project either by:
    1. Providing the 'project' field with the project ID (number)
    2. Providing the 'project_name' field with the project name (string)
    
    If a project with the given name doesn't exist, it will be created automatically.
    """
    serializer = EventLogMessageCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_llm_log(request):
    """
    Create a new LLM log entry.
    
    You can specify the project either by:
    1. Providing the 'project' field with the project ID (number)
    2. Providing the 'project_name' field with the project name (string)
    
    If a project with the given name doesn't exist, it will be created automatically.
    """
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
    project_id = request.query_params.get('project_id')
    
    # Get all logs for the user, optionally filtered by project
    event_logs_query = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs_query = LlmLogMessage.objects.filter(api_key__user=user)
    
    if project_id:
        try:
            project = Project.objects.get(id=project_id, user=user)
            event_logs_query = event_logs_query.filter(project=project)
            llm_logs_query = llm_logs_query.filter(project=project)
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    event_logs = event_logs_query.all()
    llm_logs = llm_logs_query.all()
    
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
    llm_sources = llm_logs_query.values('source').annotate(value=Count('id'))
    llm_sources_data = [
        {
            "name": source["source"] or "Unknown",
            "value": source["value"]
        }
        for source in llm_sources
    ]
    
    # Get log levels distribution
    log_levels = event_logs_query.values('level').annotate(count=Count('id'))
    log_levels_data = [
        {
            "level": level["level"],
            "count": level["count"]
        }
        for level in log_levels
    ]
    
    # Get project distribution (when not filtered by project)
    projects_data = []
    if not project_id:
        event_projects = event_logs_query.values('project').annotate(count=Count('id'))
        llm_projects = llm_logs_query.values('project').annotate(count=Count('id'))
        
        # Combine counts
        project_counts = defaultdict(int)
        for entry in event_projects:
            project_counts[entry['project']] += entry['count']
        
        for entry in llm_projects:
            project_counts[entry['project']] += entry['count']
        
        # Get project details and add to response
        for project_id, count in project_counts.items():
            try:
                project = Project.objects.get(id=project_id)
                projects_data.append({
                    "id": project.id,
                    "name": project.name,
                    "count": count
                })
            except Project.DoesNotExist:
                # Skip if project doesn't exist
                continue
    
    return Response({
        "monthly_logs": monthly_logs,
        "llm_sources": llm_sources_data,
        "log_levels": log_levels_data,
        "projects": projects_data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_analytics_csv(request, data_type):
    """
    Download analytics data as CSV based on the specified type
    """
    user = request.user
    project_id = request.query_params.get('project_id')
    
    if data_type not in ["monthly", "sources", "levels", "projects", "all"]:
        return Response({"error": "Invalid data type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate filename with current date
    current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{user.username}_analytics_{data_type}"
    if project_id:
        try:
            project = Project.objects.get(id=project_id, user=user)
            filename += f"_{project.name}"
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    filename += f"_{current_date}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Get filtered logs
    event_logs_query = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs_query = LlmLogMessage.objects.filter(api_key__user=user)
    
    if project_id:
        project = Project.objects.get(id=project_id, user=user)
        event_logs_query = event_logs_query.filter(project=project)
        llm_logs_query = llm_logs_query.filter(project=project)
    
    event_logs = event_logs_query.all()
    llm_logs = llm_logs_query.all()
    
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
        llm_sources = llm_logs_query.values('source').annotate(count=Count('id'))
        
        # Write sources data to CSV
        writer.writerow(["Source", "Count"])
        for source in llm_sources:
            writer.writerow([source["source"] or "Unknown", source["count"]])
    
    if data_type in ["levels", "all"] and data_type not in ["monthly", "sources"]:
        # Get log levels distribution
        log_levels = event_logs_query.values('level').annotate(count=Count('id'))
        
        # Write levels data to CSV
        writer.writerow(["Level", "Count"])
        for level in log_levels:
            writer.writerow([level["level"], level["count"]])
    
    if data_type in ["projects", "all"] and not project_id and data_type not in ["monthly", "sources", "levels"]:
        # Get project distribution
        event_projects = EventLogMessage.objects.filter(api_key__user=user).values('project__name', 'project').annotate(count=Count('id'))
        llm_projects = LlmLogMessage.objects.filter(api_key__user=user).values('project__name', 'project').annotate(count=Count('id'))
        
        # Combine counts
        project_counts = defaultdict(lambda: {"name": "", "event_count": 0, "llm_count": 0})
        
        for entry in event_projects:
            project_id = entry['project']
            project_counts[project_id]["name"] = entry['project__name']
            project_counts[project_id]["event_count"] = entry['count']
        
        for entry in llm_projects:
            project_id = entry['project']
            project_counts[project_id]["name"] = entry['project__name']
            project_counts[project_id]["llm_count"] = entry['count']
        
        # Write projects data to CSV
        writer.writerow(["Project", "Event Logs", "LLM Logs", "Total Logs"])
        for project_id, data in project_counts.items():
            total = data["event_count"] + data["llm_count"]
            writer.writerow([data["name"], data["event_count"], data["llm_count"], total])
    
    return response

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        # Add log counts to the response
        data['event_log_count'] = EventLogMessage.objects.filter(project=instance).count()
        data['llm_log_count'] = LlmLogMessage.objects.filter(project=instance).count()
        data['log_count'] = data['event_log_count'] + data['llm_log_count']
        
        return Response(data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Add log counts to each project
        for project_data in data:
            project_id = project_data['id']
            project_data['event_log_count'] = EventLogMessage.objects.filter(project_id=project_id).count()
            project_data['llm_log_count'] = LlmLogMessage.objects.filter(project_id=project_id).count()
            project_data['log_count'] = project_data['event_log_count'] + project_data['llm_log_count']
        
        return Response(data)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_all_logs(request):
    """
    Delete all logs (both event and LLM) for the authenticated user.
    Optionally filter by project using the 'project' query parameter.
    """
    user = request.user
    
    # Get user's logs
    event_logs = EventLogMessage.objects.filter(api_key__user=user)
    llm_logs = LlmLogMessage.objects.filter(api_key__user=user)
    
    # Filter by project if project ID is provided
    project_id = request.query_params.get('project')
    project_name = ""
    
    if project_id:
        try:
            project = Project.objects.get(id=project_id, user=user)
            event_logs = event_logs.filter(project=project)
            llm_logs = llm_logs.filter(project=project)
            project_name = project.name
        except Project.DoesNotExist:
            # If project doesn't exist or doesn't belong to user, return error
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Count logs before deletion
    event_count = event_logs.count()
    llm_count = llm_logs.count()
    total_count = event_count + llm_count
    
    # Delete logs
    event_logs.delete()
    llm_logs.delete()
    
    # Prepare success message
    message = f"Successfully deleted {total_count} logs"
    if project_id:
        message += f" from project '{project_name}'"
    
    return Response({
        "status": "success",
        "message": message,
        "deleted_count": {
            "event_logs": event_count,
            "llm_logs": llm_count,
            "total": total_count
        }
    }, status=status.HTTP_200_OK)
