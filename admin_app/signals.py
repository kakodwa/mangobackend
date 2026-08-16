# admin_app/signals.py
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created

from admin_app.models import SMSQueue

User = get_user_model()




@receiver(post_save, sender=User)
def send_sms_on_user_creation(sender, instance, created, **kwargs):
    if not created:
        return

    phone_number = getattr(instance, 'phone_number', None)
    if not phone_number:
        return

    username = instance.username or instance.first_name or "User"
    user_email = instance.email

    # Clear stale tokens and generate a fresh setup token
    ResetPasswordToken.objects.filter(user=instance).delete()
    token = ResetPasswordToken.objects.create(user=instance)
    otp_code = token.key

    # Format compact identifier string
    if user_email and "@" in user_email and not user_email.endswith(".local"):
        id_str = f"User: {username} | Email: {user_email}"
    else:
        id_str = f"User: {username}"

    # Strict SMS length: ~120–150 chars (under 160 limit)
    sms_text = (
        f"MalaTrade account created. {id_str}. "
        f"OTP: {otp_code}. "
        f"Open app > Login screen > tap 'Forgot Password' to set password.www.malatrade.com"
    )

    SMSQueue.objects.create(
        phone_number=phone_number,
        message=sms_text,
        status='QUEUED'
    )

# =====================================================================
# 2. SELF-SERVICE RESET FLOW (Under 160 Chars)
# =====================================================================
@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Fires on standard app reset request. Sends compact OTP SMS.
    """
    user = reset_password_token.user
    user_email = user.email
    phone_number = getattr(user, 'phone_number', None)
    otp_code = reset_password_token.key
    user_name = user.first_name or user.username

    # 1. Send Email Notification
    if user_email and "@" in user_email and not user_email.endswith(".local"):
        subject = "MalaTrade Password Reset OTP Code"
        context = {'user_name': user_name, 'otp_code': otp_code}
        html_message = render_to_string('emails/password_reset_email.html', context)
        plain_message = f"Hello {user_name},\nYour 6-digit security OTP code is: {otp_code}"

        send_mail(
            subject=subject,
            message=plain_message,
            from_email="support@malatrade.com",
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=True,
        )

    # 2. Queue SMS OTP (~65 characters total)
    if phone_number and not getattr(instance, 'is_registration', False):
        sms_text = f"MalaTrade OTP: {otp_code}. Use this code to reset your password. Do not share."
        SMSQueue.objects.create(
            phone_number=phone_number,
            message=sms_text,
            status='QUEUED'
        )