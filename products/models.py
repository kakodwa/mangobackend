from django.db import models
from django.utils.text import slugify
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.storage import default_storage
from .utils import process_and_compress_image  
import uuid
from users.models import User
from shops.models import Shop
from mangohub.models import Review


class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/')

    category = models.CharField(max_length=50, default='Fashion')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(default=0)

    aliexpress_url = models.URLField(blank=True, null=True)
    
    # Inventory
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews = GenericRelation(Review)
    total_reviews = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('shop', 'slug')

    def __str__(self):
        return f"{self.name} - {self.shop.name}"

    def save(self, *args, **kwargs):
        # 1. Slug Handling
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(shop=self.shop, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # 2. SKU Handling
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        # 3. Image Optimization (Square: 1000x1000)
        if self.image and not getattr(self, '_image_processed', False):
            try:
                if default_storage.exists(self.image.name):
                    processed_file = process_and_compress_image(
                        self.image,
                        ratio_type="square",
                        target_width=1000
                        )

                    if processed_file:
                        self.image = processed_file
                        self._image_processed = True

            except FileNotFoundError:
                print(f"Missing image file: {self.image.name}")

            except Exception as e:
                print(f"Skipping compression: {e}")

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # CRITICAL FIX: Only compress if it's a freshly uploaded file payload object instance
        if self.image and hasattr(self.image, 'file') and not getattr(self, '_image_processed', False):
            try:
                processed_file = process_and_compress_image(self.image, ratio_type="square", target_width=800)
                if processed_file:
                    self.image = processed_file
                    self._image_processed = True
            except Exception as e:
                print(f"Skipping compression: {e}")

        super().save(*args, **kwargs)


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'customer')

    def __str__(self):
        return f"{self.product.name} - {self.rating}★"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')


class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/')
    url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    cta_text = models.CharField(max_length=50, default="Learn more")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else "banner"

    def save(self, *args, **kwargs):
        # CRITICAL FIX: Only compress if it's a freshly uploaded file payload object instance
        if self.image and hasattr(self.image, 'file') and not getattr(self, '_image_processed', False):
            try:
                processed_file = process_and_compress_image(self.image, ratio_type="landscape", target_width=1400)
                if processed_file:
                    self.image = processed_file
                    self._image_processed = True
            except Exception as e:
                print(f"Skipping compression: {e}")

        super().save(*args, **kwargs)


class AppVersion(models.Model):
    version = models.CharField(max_length=20)
    force_update = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    update_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.version


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    cj_variant_id = models.CharField(max_length=100, unique=True, db_index=True, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    attributes = models.JSONField(default=dict, blank=True)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weight_g = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.attributes}"