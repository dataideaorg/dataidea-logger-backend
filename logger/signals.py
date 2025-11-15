from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EventLogMessage
from .notifications import send_error_notification_email


@receiver(post_save, sender=EventLogMessage)
def notify_on_error_log(sender, instance, created, **kwargs):
    """
    Signal handler that sends an email notification when an error or warning log is created.

    Args:
        sender: The model class (EventLogMessage)
        instance: The actual instance being saved
        created: Boolean; True if a new record was created
        **kwargs: Additional keyword arguments
    """
    if created and instance.level in ['error', 'warning']:
        # Send email notification for error and warning logs
        send_error_notification_email(instance)