from django.db import models
from users.models import User
from products.models import Product
from shops.models import Shop
from decimal import Decimal

class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    order_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', limit_choices_to={'user_type': 'customer'})
    
    
    # Status
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,default=Decimal('0.00'))
    
    # Delivery
    delivery_address = models.TextField()
    delivery_phone_number = models.TextField(max_length="100",null=True,blank=True)
    delivery_latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,default=0.0)
    delivery_longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True,default=0.0)
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class SellerOrder(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="seller_orders")
    seller = models.ForeignKey(User, on_delete=models.CASCADE)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ],
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
