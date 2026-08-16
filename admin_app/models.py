# models.py
from django.db import models

class SMSQueue(models.Model):
    STATUS_CHOICES = (
        ('QUEUED', 'Queued'),
        ('PROCESSING', 'Processing'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    )

    phone_number = models.CharField(max_length=20, help_text="Formatted as +265XXXXXXXXX")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='QUEUED')
    error_log = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sms_queue'
        ordering = ['created_at']

    def __str__(self):
        return f"SMS to {self.phone_number} [{self.status}]"