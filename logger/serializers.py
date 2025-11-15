from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ApiKey, EventLogMessage, LlmLogMessage, Project, EmailNotificationPreference

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'key', 'name', 'created_at', 'is_active']
        read_only_fields = ['id', 'key', 'created_at']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'project_type', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at']

# Event Log Serializers
class EventLogMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLogMessage
        fields = ['id', 'project', 'user_id', 'message', 'level', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class EventLogMessageCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.UUIDField(write_only=True)
    project_name = serializers.CharField(required=False, write_only=True, help_text="Name of the project. If provided, the system will use or create a project with this name rather than requiring a project ID.")
    project = serializers.PrimaryKeyRelatedField(required=False, queryset=Project.objects.all(), help_text="Project ID. Only required if project_name is not provided.")

    class Meta:
        model = EventLogMessage
        fields = ['api_key', 'project', 'project_name', 'user_id', 'message', 'level', 'metadata']

    def validate(self, data):
        # Remove project_name from data if project is directly provided
        if 'project' in data and 'project_name' in data:
            del data['project_name']
            return data

        # If neither project nor project_name is provided, raise validation error
        if 'project' not in data and 'project_name' not in data:
            raise serializers.ValidationError("Either 'project' (ID) or 'project_name' must be provided")

        # If project_name is provided, get or create the project
        if 'project_name' in data and 'api_key' in data:
            api_key = data['api_key']
            project_name = data.pop('project_name')

            try:
                project = Project.objects.get(user=api_key.user, name=project_name, is_active=True)
            except Project.DoesNotExist:
                # Create a new project with the given name and type 'activity'
                project = Project.objects.create(
                    user=api_key.user,
                    name=project_name,
                    project_type='activity',
                    is_active=True
                )

            data['project'] = project

        return data
    
    def validate_api_key(self, value):
        try:
            api_key = ApiKey.objects.get(key=value, is_active=True)
            return api_key
        except ApiKey.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive API key")
    
    def create(self, validated_data):
        api_key = validated_data.pop('api_key')
        log_message = EventLogMessage.objects.create(api_key=api_key, **validated_data)
        return log_message

# LLM Log Serializers
class LlmLogMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LlmLogMessage
        fields = ['id', 'project', 'user_id', 'source', 'query', 'response', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class LlmLogMessageCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.UUIDField(write_only=True)
    project_name = serializers.CharField(required=False, write_only=True, help_text="Name of the project. If provided, the system will use or create a project with this name rather than requiring a project ID.")
    project = serializers.PrimaryKeyRelatedField(required=False, queryset=Project.objects.all(), help_text="Project ID. Only required if project_name is not provided.")

    class Meta:
        model = LlmLogMessage
        fields = ['api_key', 'project', 'project_name', 'user_id', 'source', 'query', 'response', 'metadata']

    def validate(self, data):
        # Remove project_name from data if project is directly provided
        if 'project' in data and 'project_name' in data:
            del data['project_name']
            return data

        # If neither project nor project_name is provided, raise validation error
        if 'project' not in data and 'project_name' not in data:
            raise serializers.ValidationError("Either 'project' (ID) or 'project_name' must be provided")

        # If project_name is provided, get or create the project
        if 'project_name' in data and 'api_key' in data:
            api_key = data['api_key']
            project_name = data.pop('project_name')

            try:
                project = Project.objects.get(user=api_key.user, name=project_name, is_active=True)
            except Project.DoesNotExist:
                # Create a new project with the given name and type 'llm'
                project = Project.objects.create(
                    user=api_key.user,
                    name=project_name,
                    project_type='llm',
                    is_active=True
                )

            data['project'] = project

        return data
    
    def validate_api_key(self, value):
        try:
            api_key = ApiKey.objects.get(key=value, is_active=True)
            return api_key
        except ApiKey.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive API key")
    
    def create(self, validated_data):
        api_key = validated_data.pop('api_key')
        log_message = LlmLogMessage.objects.create(api_key=api_key, **validated_data)
        return log_message


# Email Notification Preference Serializer
class EmailNotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailNotificationPreference
        fields = ['id', 'email', 'enabled', 'notify_on_error', 'notify_on_warning', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at'] 