from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Lodge(models.Model):
    LODGE_TYPE_CHOICES = (
        ('hotel', 'Hotel'),
        ('lodge', 'Lodge'),
        ('guest_house', 'Guest House'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('resort', 'Resort'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lodges'
    )

    name = models.CharField(max_length=255)
    lodge_type = models.CharField(max_length=30, choices=LODGE_TYPE_CHOICES)
    description = models.TextField()

    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    check_in_time = models.TimeField(default='14:00')
    check_out_time = models.TimeField(default='10:00')

    amenities = models.ManyToManyField(Amenity, blank=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class LodgeImage(models.Model):
    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(upload_to='lodges/')
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lodge.name} Image"


class Room(models.Model):
    ROOM_TYPE_CHOICES = (
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
        ('family', 'Family'),
        ('deluxe', 'Deluxe'),
    )

    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='rooms'
    )

    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    room_number = models.CharField(max_length=50)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    capacity = models.PositiveIntegerField(default=1)
    total_rooms = models.PositiveIntegerField(default=1)

    has_wifi = models.BooleanField(default=False)
    has_tv = models.BooleanField(default=False)
    has_ac = models.BooleanField(default=False)
    has_breakfast = models.BooleanField(default=False)

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lodge', 'room_number')

    def __str__(self):
        return f"{self.lodge.name} - {self.room_number}"


class Booking(models.Model):
    BOOKING_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    booking_reference = models.CharField(max_length=20, unique=True)

    check_in_date = models.DateField()
    check_out_date = models.DateField()

    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    total_nights = models.PositiveIntegerField(default=1)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    booking_status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    special_requests = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.booking_reference


class Review(models.Model):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lodge_reviews'
    )

    lodge = models.ForeignKey(
        Lodge,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'lodge')

    def __str__(self):
        return f"{self.lodge.name} - {self.rating}"