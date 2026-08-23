from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Sends automated weekly HTML emails to active users.'

    def handle(self, *args, **options):
        # Fetch active users who have an email set
        users = User.objects.filter(is_active=True).exclude(email='')

        if not users.exists():
            self.stdout.write(self.style.WARNING('No active users found.'))
            return

        subject = "Your Weekly Summary from MalaTrade"
        success_count = 0

        for user in users:
            # Render HTML content with dynamic context
            context = {'user': user}
            html_message = render_to_string('emails/weekly_newsletter.html', context)
            plain_message = strip_tags(html_message)  # Fallback for plain-text email clients

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                success_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to send to {user.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully sent {success_count} HTML emails.'))