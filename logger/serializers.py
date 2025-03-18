from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ApiKey, EventLogMessage, LlmLogMessage

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'key', 'name', 'created_at', 'is_active']
        read_only_fields = ['id', 'key', 'created_at']

# Event Log Serializers
class EventLogMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventLogMessage
        fields = ['id', 'user_id', 'message', 'level', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class EventLogMessageCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = EventLogMessage
        fields = ['api_key', 'user_id', 'message', 'level', 'metadata']
    
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
        fields = ['id', 'user_id', 'source', 'query', 'response', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class LlmLogMessageCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = LlmLogMessage
        fields = ['api_key', 'user_id', 'source', 'query', 'response', 'metadata']
    
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