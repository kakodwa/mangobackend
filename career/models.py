import os
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Custom cPanel storage fallback for production
cpanel_storage = FileSystemStorage(
    location="/home/malanxux/public_html/media",
    base_url="https://www.malatrade.com/media/"
)
selected_storage = FileSystemStorage() if settings.DEBUG else cpanel_storage

def cv_upload_path(instance, filename):
    return os.path.join('uploads', 'cvs', filename)


class Vacancy(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, help_text="URL friendly identifier (e.g., marketing-ambassador)")
    description = models.TextField(help_text="Role details and duties")
    responsibilities = models.TextField(blank=True, help_text="Enter key responsibilities")
    qualifications = models.TextField(blank=True, help_text="Enter key requirements/qualifications")
    locations = models.CharField(max_length=255, default="Lilongwe, Blantyre, Mzuzu, Zomba, Mangochi")
    is_active = models.BooleanField(default=True, help_text="Check to keep position open")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Vacancies"  # 👈 Corrected attribute name

    def __str__(self):
        return self.title

class JobApplication(models.Model):
    LOCATION_CHOICES = [
        ('Lilongwe', 'Lilongwe'),
        ('Blantyre', 'Blantyre'),
        ('Mzuzu', 'Mzuzu'),
        ('Zomba', 'Zomba'),
        ('Mangochi', 'Mangochi'),
        ('Other', 'Other'),
    ]

    # Link application to a specific Vacancy
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    cv_file = models.FileField(upload_to=cv_upload_path, storage=selected_storage)
    cover_letter = models.TextField(blank=True, null=True)

    # Communication Checkboxes
    opt_in_future_vacancies = models.BooleanField(
        default=False,
        verbose_name="Notify me about future job vacancies at MalaTrade"
    )
    opt_in_announcements_products = models.BooleanField(
        default=False,
        verbose_name="Receive news, announcements, and featured products from MalaTrade"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        position_title = self.vacancy.title if self.vacancy else "General Application"
        return f"{self.full_name} - {position_title}"