from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('shop_owner', 'Shop Owner'),
        ('property_owner', 'Property Owner'),
        ('hospitality_owner', 'Hospitality Owner'),
        ('event_organizer', 'Event Organizer'),
        ('admin', 'Admin'),
    )

    phone_regex = RegexValidator(
        regex=r'^\+?[1-9]\d{7,14}$',
        message='Enter a valid international phone number (e.g. +265881234567)'
    )

    email = models.EmailField(unique=True)

    phone_number = models.CharField(
        max_length=17,
        blank=True,
        validators=[phone_regex]
    )

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='customer'
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True
    )

    bio = models.TextField(blank=True)

    # ======================
    # NEW SIMPLE FIELDS
    # ======================

    gender = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    district = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"


class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='address')
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.user.username} - {self.city}"
