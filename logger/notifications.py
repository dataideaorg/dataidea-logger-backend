from django.conf import settings
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from .models import EmailNotificationPreference, EventLogMessage


def send_error_notification_email(log_message: EventLogMessage):
    """
    Send an email notification when an error log is received using Brevo API.

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

        # Configure Brevo API
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY

        # Create API instance
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Prepare email content
        subject = f'[{log_message.level.upper()}] {log_message.project.name} - Error Alert'

        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {'#dc2626' if log_message.level == 'error' else '#f59e0b'}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #4b5563; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">{log_message.level.upper()} Alert</h1>
                    <p style="margin: 5px 0 0 0;">{log_message.project.name}</p>
                </div>
                <div class="content">
                    <p>Hello {user.username},</p>
                    <p>An {log_message.level} log has been received for your project.</p>

                    <div class="detail-row">
                        <span class="label">Level:</span> {log_message.level.upper()}
                    </div>
                    <div class="detail-row">
                        <span class="label">Message:</span> {log_message.message}
                    </div>
                    <div class="detail-row">
                        <span class="label">User ID:</span> {log_message.user_id}
                    </div>
                    <div class="detail-row">
                        <span class="label">Timestamp:</span> {log_message.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </div>
                    <div class="detail-row">
                        <span class="label">Project:</span> {log_message.project.name}
                    </div>
                    {f'<div class="detail-row"><span class="label">Metadata:</span> {log_message.metadata}</div>' if log_message.metadata else ''}

                    <div class="footer">
                        <p>DATAIDEA Logger</p>
                        <p><a href="https://logger.dataidea.org/settings">Manage notification preferences</a></p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text_content = f"""
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

        # Create email object
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": preferences.email, "name": user.username}],
            sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "DATAIDEA Logger"},
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

        # Send email via Brevo API
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email notification sent to {preferences.email} for {log_message.level} log. Message ID: {api_response.message_id}")

    except ApiException as e:
        print(f"Brevo API error when sending email: {e}")
    except Exception as e:
        # Log the error but don't raise it to prevent disrupting the logging flow
        print(f"Failed to send email notification: {str(e)}")