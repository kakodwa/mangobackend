# signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_rest_passwordreset.signals import reset_password_token_created

User = get_user_model()


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Triggers automatically whenever a new User record is created in the DB.
    """
    # Only execute on initial creation, not on subsequent user updates
    if created:
        user_email = instance.email
        
        # Skip sending if user has no email address configured
        if not user_email:
            return

        user_name = instance.first_name or instance.username

        subject = "Welcome to MalaTrade!"
        context = {
            'user_name': user_name,
        }

        # Render HTML template
        html_message = render_to_string('emails/welcome_email.html', context)

        # Plain text fallback
        plain_message = (
            f"Hello {user_name},\n\n"
            f"Welcome to MalaTrade! Thank you for joining our platform.\n"
            f"Your account is ready to go.\n\n"
            f"Best regards,\nMalaTrade Support Team"
        )

        # Send Email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email="support@malatrade.com",
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )


# ... your existing password_reset_token_created receiver below ...