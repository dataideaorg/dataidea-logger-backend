from django.contrib import admin
from .models import ApiKey, EventLogMessage, LlmLogMessage

@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'key', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(EventLogMessage)
class EventLogMessageAdmin(admin.ModelAdmin):
    list_display = ('level', 'message_preview', 'api_key', 'timestamp')
    list_filter = ('level', 'timestamp', 'api_key')
    search_fields = ('message', 'api_key__name', 'api_key__user__username')
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(LlmLogMessage)
class LlmLogMessageAdmin(admin.ModelAdmin):
    list_display = ('source', 'query_preview', 'api_key', 'timestamp')
    list_filter = ('source', 'timestamp', 'api_key')
    search_fields = ('query', 'api_key__name', 'api_key__user__username')

    def query_preview(self, obj):
        return obj.query[:50] + '...' if len(obj.query) > 50 else obj.query
    query_preview.short_description = 'Query'