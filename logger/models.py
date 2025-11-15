from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class ApiKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
class Project(models.Model):
    PROJECT_TYPE_CHOICES = [
        ('activity', 'Activity Event Logs'),
        ('llm', 'LLM Event Logs'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPE_CHOICES,
        default='activity',
        help_text="Type of logs this project will handle"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']

class EventLogMessage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='event_log_messages')
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='event_log_messages')
    user_id = models.CharField(max_length=100, help_text="The user id of the user who made the request")
    message = models.TextField(help_text="The log message")
    level = models.CharField(max_length=20, default='info', 
                            choices=[('info', 'Info'), ('warning', 'Warning'), 
                                    ('error', 'Error'), ('debug', 'Debug')])
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.level}: {self.message[:50]}..."

    class Meta:
        ordering = ['-timestamp']


class LlmLogMessage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='llm_log_messages')
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='llm_log_messages')
    user_id = models.CharField(max_length=100, help_text="The user id of the user who made the request")
    source = models.TextField(help_text="The which model or service the log message is from")
    query = models.TextField(blank=True, null=True, help_text="The query that was sent")
    response = models.TextField(blank=True, null=True, help_text="The response that was received")
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.source}: {self.query[:50]}..."

    class Meta:
        ordering = ['-timestamp']


class EmailNotificationPreference(models.Model):
    """User preferences for email notifications when error logs are received"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_notification_preference')
    email = models.EmailField(help_text="Email address to send notifications to")
    enabled = models.BooleanField(default=True, help_text="Enable/disable email notifications")
    notify_on_error = models.BooleanField(default=True, help_text="Send email when error logs are received")
    notify_on_warning = models.BooleanField(default=False, help_text="Send email when warning logs are received")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.email} ({'enabled' if self.enabled else 'disabled'})"

    class Meta:
        verbose_name = "Email Notification Preference"
        verbose_name_plural = "Email Notification Preferences"

