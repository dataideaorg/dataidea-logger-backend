from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import EmailNotificationPreference, EventLogMessage


def send_error_notification_email(log_message: EventLogMessage):
    """
    Send an email notification when an error log is received.

    Args:
        log_message: The EventLogMessage instance that triggered the notification
    """
    try:
        # Get the user from the API key
        user = log_message.api_key.user

        # Check if user has email notification preferences
        try:
            preferences = EmailNotificationPreference.objects.get(user=user)
        except EmailNotificationPreference.DoesNotExist:
            # No preferences set, skip sending email
            return

        # Check if notifications are enabled
        if not preferences.enabled:
            return

        # Check if we should notify for this log level
        if log_message.level == 'error' and not preferences.notify_on_error:
            return
        if log_message.level == 'warning' and not preferences.notify_on_warning:
            return

        # Only send for error and warning levels
        if log_message.level not in ['error', 'warning']:
            return

        # Prepare email content
        subject = f'[{log_message.level.upper()}] {log_message.project.name} - Error Alert'

        # Plain text message
        message = f"""
Hello {user.username},

An {log_message.level} log has been received for your project: {log_message.project.name}

Details:
- Level: {log_message.level.upper()}
- Message: {log_message.message}
- User ID: {log_message.user_id}
- Timestamp: {log_message.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- Project: {log_message.project.name}

Metadata: {log_message.metadata if log_message.metadata else 'None'}

---
DATAIDEA Logger
https://logger.dataidea.org

To manage your notification preferences, visit: https://logger.dataidea.org/settings
        """

        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[preferences.email],
            fail_silently=True,  # Don't raise exceptions if email fails
        )

        print(f"Email notification sent to {preferences.email} for {log_message.level} log")

    except Exception as e:
        # Log the error but don't raise it to prevent disrupting the logging flow
        print(f"Failed to send email notification: {str(e)}")