from django.contrib import admin
from .models import ApiKey, LogMessage

@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'key', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(LogMessage)
class LogMessageAdmin(admin.ModelAdmin):
    list_display = ('level', 'message_preview', 'api_key', 'timestamp')
    list_filter = ('level', 'timestamp', 'api_key')
    search_fields = ('message', 'api_key__name', 'api_key__user__username')
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
