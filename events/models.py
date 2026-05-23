import uuid
import io
import qrcode
import json

from django.db import models
from users.models import User
from django.core.files.base import ContentFile
from django.core.signing import TimestampSigner

signer = TimestampSigner()


# =========================
# EVENT CATEGORY
# =========================
class EventCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# =========================
# EVENT MODEL
# =========================
class Event(models.Model):
    EVENT_STATUS = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='events'
    )

    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    venue = models.CharField(max_length=255)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    # ================= GPS =================
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    banner = models.ImageField(upload_to='event_banners/')

    status = models.CharField(
        max_length=20,
        choices=EVENT_STATUS,
        default='draft'
    )

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return self.title

    # ================= OPTIONAL HELPERS =================
    def get_total_seats(self):
        return sum(t.total_seats for t in self.ticket_types.all())

    def get_available_seats(self):
        return sum(t.available_seats for t in self.ticket_types.all())


# =========================
# TICKET TYPES (VIP / REGULAR / VVIP)
# =========================
class EventTicketType(models.Model):
    SEAT_TYPE = (
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('vvip', 'VVIP'),
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='ticket_types'
    )

    name = models.CharField(max_length=50, choices=SEAT_TYPE)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    total_seats = models.PositiveIntegerField()
    available_seats = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.event.title} - {self.name}"




# =========================
# TICKET MODEL
# =========================
class Ticket(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    purchase_group = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    ticket_number = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    # ================= TICKET TYPE =================
    ticket_type = models.ForeignKey(
        EventTicketType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ================= SEAT =================
    seat_number = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    qr_code = models.ImageField(
        upload_to='ticket_qrcodes/',
        blank=True,
        null=True
    )

    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.event.title}"

    # ================= QR DATA =================
    def get_signed_qr_data(self):
        payload = {
            "ticket_number": str(self.ticket_number),
            #"event_id": self.event.id,
            "event_title": self.event.title,
            "ticket_items": [
            {
            "name": item.name_snapshot,
            "type": item.ticket_type.name if item.ticket_type else None,
            "quantity": item.quantity
            }
            for item in self.items.select_related("ticket_type")
            ],
            "attendee_name": self.customer.get_full_name()
            or self.customer.username,
        }

        json_payload = json.dumps(payload)
        return signer.sign(json_payload)

    # ================= QR GENERATION =================
    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(self.get_signed_qr_data())
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')

        file_name = f"ticket_{self.ticket_number}.png"

        self.qr_code.save(
            file_name,
            ContentFile(buffer.getvalue()),
            save=False
        )

    # ================= AUTO QR ON PAYMENT =================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        is_paid_now = False

        if not is_new:
            old = Ticket.objects.get(pk=self.pk)

            if old.payment_status != 'paid' and self.payment_status == 'paid':
                is_paid_now = True

        super().save(*args, **kwargs)

        if is_paid_now and not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])



class TicketItem(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='items')

    ticket_type = models.ForeignKey(EventTicketType, null=True, blank=True, on_delete=models.SET_NULL)

    name_snapshot = models.CharField(max_length=50)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField()

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


# =========================
# EVENT IMAGES
# =========================
class EventImage(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='event_images/')


# =========================
# CHECK-IN SYSTEM
# =========================
class TicketCheckIn(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE
    )

    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    checked_in_at = models.DateTimeField(auto_now_add=True)

    is_checked_in = models.BooleanField(default=False)

    def mark_checked_in(self, user):
        if self.is_checked_in:
            return False

        self.is_checked_in = True
        self.checked_in_by = user
        self.save()
        return True