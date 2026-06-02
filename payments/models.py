from django.db import models
from users.models import User
from orders.models import Order
from events.models import Ticket
from realestate.models import Property

class Payment(models.Model):


    PAYMENT_PURPOSE_CHOICES = (
    ('order', 'Order Payment'),
    ('property_unlock', 'Property Unlock'),
    ('wallet_topup', 'Wallet Topup'),
    ('booking','booking'),
    ('ticket', 'ticket'),
    )


    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_reference = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    purpose = models.CharField(max_length=30,choices=PAYMENT_PURPOSE_CHOICES,default='order')
    payment_method = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # PayChangu Details
    paychangu_transaction_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    
    # Generic relations
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    property_unlock = models.ForeignKey('realestate.PropertyUnlock', on_delete=models.CASCADE, related_name='payment', null=True, blank=True)
    booking = models.ForeignKey('hospitality.Booking',null=True,blank=True,on_delete=models.CASCADE)
    ticket_purchase = models.ForeignKey('events.Ticket',null=True,blank=True,on_delete=models.SET_NULL)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.payment_reference}"


class PaymentWebhook(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='webhooks')
    webhook_data = models.JSONField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook for {self.payment.payment_reference}"




class EscrowWallet(models.Model):


    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,null=True, blank=True
    )

    beneficiary = models.ForeignKey(
        User,
        on_delete=models.CASCADE,null=True, blank=True
    )

    escrow_type = models.CharField(
        max_length=30,
        default='order',
        choices=[
            ("order", "Order"),
            ("booking", "Booking"),
            ("ticket", "Ticket"),
            ("property_unlock", "Property Unlock"),
        ]
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,null=True, blank=True
    )

    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("held", "Held"),
            ("released", "Released"),
            ("refunded", "Refunded")
        ],
        default="held"
    )