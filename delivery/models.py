from django.db import models
from users.models import User
from orders.models import Order
from payments.models import EscrowWallet

class DeliveryPerson(models.Model):

    # =========================
    # IDENTIFICATION
    # =========================
    id_number = models.CharField(
        max_length=30,
        unique=True
    )

    full_name = models.CharField(max_length=100)

    phone_number = models.CharField(max_length=20, unique=True)
    alternative_phone = models.CharField(max_length=20, null=True, blank=True)

    # =========================
    # VEHICLE INFO
    # =========================
    vehicle_number = models.CharField(max_length=20,null=True, blank=True)
    vehicle_type = models.CharField(max_length=50,null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)

    # =========================
    # STATUS
    # =========================
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('busy', 'Busy'),
            ('inactive', 'Inactive')
        ],
        default='active'
    )

    # =========================
    # PERFORMANCE
    # =========================
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_deliveries = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.id_number})"


class Delivery(models.Model):
    DELIVERY_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    seller = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    delivery_person = models.ForeignKey(DeliveryPerson, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='pending')
    
    # Tracking
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_address = models.TextField(null=True,blank=True)
    delivery_phone_number = models.TextField(max_length="100",null=True,blank=True)


    pickup_latitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    pickup_longitude = models.DecimalField(max_digits=9,decimal_places=6,null=True,blank=True)
    
    delivery_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    escrow_released = models.BooleanField(default=False)

    customer_delivery_code = models.CharField(max_length=6,null=True,blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Delivery for Order {self.order.order_number}"

    @property
    def escrow(self):
        return EscrowWallet.objects.filter(order=self.order,seller=self.seller,status="held").first()


class DeliveryRating(models.Model):
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='rating')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'customer'})
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for Delivery {self.delivery.id} - {self.rating}★"
