from django.db import models
from django.utils.text import slugify
import uuid
from users.models import User
from shops.models import Shop

class Product(models.Model):

    CATEGORY_ELECTRONICS = 'Electronics'
    CATEGORY_FASHION = 'Fashion'
    CATEGORY_GROCERIES = 'Groceries'
    CATEGORY_HOME = 'Home'
    CATEGORY_BEAUTY = 'Beauty'

    CATEGORY_CHOICES = [
        (CATEGORY_ELECTRONICS, 'Electronics'),
        (CATEGORY_FASHION, 'Fashion'),
        (CATEGORY_GROCERIES, 'Groceries'),
        (CATEGORY_HOME, 'Home'),
        (CATEGORY_BEAUTY, 'Beauty'),
    ]


    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/')

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_ELECTRONICS
    )
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(default=0)
    
    # Inventory
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
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
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(shop=self.shop, slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"


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


# models.py
class Banner(models.Model):
    title = models.CharField(max_length=255,blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='banners/')
    url = models.URLField(blank=True, null=True)  # 👈 NEW FIELD
    is_active = models.BooleanField(default=True)
    cta_text = models.CharField(max_length=50,default="Learn more")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AppVersion(models.Model):
    version = models.CharField(max_length=20)
    force_update = models.BooleanField(default=False)
    maintenance_mode = models.BooleanField(default=False)  # NEW
    message = models.TextField(blank=True, null=True)       # NEW
    update_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.version
