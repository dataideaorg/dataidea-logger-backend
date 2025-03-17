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

class LogMessage(models.Model):
    api_key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name='log_messages')
    message = models.TextField()
    query = models.TextField(blank=True, null=True, help_text="The query that was sent")
    response = models.TextField(blank=True, null=True, help_text="The response that was received")
    level = models.CharField(max_length=20, default='info', 
                            choices=[('info', 'Info'), ('warning', 'Warning'), 
                                    ('error', 'Error'), ('debug', 'Debug')])
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.level}: {self.message[:50]}..."

    class Meta:
        ordering = ['-timestamp']
