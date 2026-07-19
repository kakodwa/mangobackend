# signals.py (inside your user/auth Django app)
from django.core.mail import send_mail
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Triggers automatically when a reset request is successfully validated.
    """
    # 1. Grab user details and generated OTP
    user_email = reset_password_token.user.email  #
    otp_code = reset_password_token.key  # 6-digit numeric token

    # 2. Compose the email template
    subject = "MalaTrade Password Reset OTP Code"
    message = (
        f"Hello {reset_password_token.user.first_name or reset_password_token.user.username},\n\n"
        f"You requested a password reset for your MalaTrade account.\n"
        f"Your 6-digit security OTP code is: {otp_code}\n\n"
        f"This code will expire in 24 hours. If you didn't request this, please ignore this email.\n\n"
        f"Best regards,\nMalaTrade Support Team"
    )

    # 3. Deliver the email
    send_mail(
    subject=subject,
    message=message,
    from_email="no-reply@malatrade.com",
    recipient_list=[user_email],
    fail_silently=False,)