# signals.py
from django.core.mail import send_mail
from django.dispatch import receiver
from django.template.loader import render_to_string
from django_rest_passwordreset.signals import reset_password_token_created

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Triggers automatically when a reset request is successfully validated.
    """
    user_email = reset_password_token.user.email
    otp_code = reset_password_token.key
    user_name = reset_password_token.user.first_name or reset_password_token.user.username

    subject = "MalaTrade Password Reset OTP Code"

    # Context data passed into the HTML template
    context = {
        'user_name': user_name,
        'otp_code': otp_code,
    }

    # Render HTML template
    html_message = render_to_string('emails/password_reset_email.html', context)

    # Plain text fallback for non-HTML email clients
    plain_message = (
        f"Hello {user_name},\n\n"
        f"You requested a password reset for your MalaTrade account.\n"
        f"Your 6-digit security OTP code is: {otp_code}\n\n"
        f"This code will expire in 24 hours. If you didn't request this, please ignore this email.\n\n"
        f"Best regards,\nMalaTrade Support Team"
    )

    # Deliver the email with both plain text and HTML versions
    send_mail(
        subject=subject,
        message=plain_message,
        from_email="support@malatrade.com",
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )