from io import BytesIO

import qrcode
from django.core.files import File
from django.db import models
from django.utils.text import slugify

from users.models import User
from mangohub.models import Review
from django.contrib.contenttypes.fields import GenericRelation


class Shop(models.Model):
    SHOP_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shops'
    )

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)

    description = models.TextField()

    logo = models.ImageField(upload_to='shop_logos/')
    banner = models.ImageField(
        upload_to='shop_banners/',
        blank=True,
        null=True
    )

    category = models.CharField(max_length=100)

    # QR
    qr_code = models.ImageField(
        upload_to="shop_qr/",
        blank=True,
        null=True,
    )

    qr_scan_count = models.PositiveIntegerField(default=0)

    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    # Contact
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    # Status
    status = models.CharField(
        max_length=20,
        choices=SHOP_STATUS_CHOICES,
        default='pending'
    )

    is_active = models.BooleanField(default=True)

    # Reviews
    reviews = GenericRelation(Review)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    total_reviews = models.IntegerField(default=0)

    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def generate_qr(self):
        """
        Generates a QR code only once pointing to a public tracking endpoint.
        """
        backend_domain = "https://mangobackend-yayy.onrender.com" 
        qr_url = f"{backend_domain}/qr/shop/{self.id}/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        image = qr.make_image(fill_color="#000000", back_color="#FFFFFF")

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        
        # 🔥 THE CRITICAL FIX: Rewind the buffer pointer to the beginning!
        buffer.seek(0)
        
        filename = f"shop_{self.id}.png"
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        is_new = self.pk is None

        # 1. Commit regular data values to database first
        super().save(*args, **kwargs)

        # 2. Safely trigger file stream compilation downstream
        if is_new and not self.qr_code:
            self.generate_qr()
            # Use super().save to directly update fields, bypassing endless recursion loops
            super().save(update_fields=["qr_code"])


class ShopReview(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'customer'})
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shop', 'customer')

    def __str__(self):
        return f"{self.shop.name} - {self.rating}★"