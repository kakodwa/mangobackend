from django.db import models
from users.models import User
from django.utils.text import slugify
from mangohub.models import Review
from django.contrib.contenttypes.fields import GenericRelation
from products.utils import process_and_compress_image
import uuid

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('land', 'Land'),
        ('commercial', 'Commercial'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    )

    LISTING_PURPOSE_CHOICES = (
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', limit_choices_to={'user_type': 'property_owner'})
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    listing_purpose = models.CharField(max_length=10, choices=LISTING_PURPOSE_CHOICES, default='sale')
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Location & GPS
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    
    # Property Details
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    size_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Pricing
    price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='MWK')
    
    # Access Control
    is_publicly_visible = models.BooleanField(default=False)
    unlock_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    view_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews = GenericRelation(Review)
    total_reviews = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"

        super().save(*args, **kwargs)


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.property.title}"

    def save(self, *args, **kwargs):
        # Image Optimization (Landscape 16:9 for clean real-estate showcase layout)
        if self.image and not getattr(self, '_image_processed', False):
            processed_file = process_and_compress_image(self.image, ratio_type="landscape", target_width=1200)
            if processed_file:
                self.image = processed_file
                self._image_processed = True

        super().save(*args, **kwargs)


class PropertyUnlock(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='unlocks')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_properties', limit_choices_to={'user_type': 'customer'})
    unlock_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_unlocked = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('property', 'customer')

    def __str__(self):
        return f"{self.customer.username} unlocked {self.property.title}"