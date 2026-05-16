# Django Lodge Booking API (MangoMart Hospitality)

This structure is designed to work with your existing custom User model and payment system.

---

# Features

* Lodge/Hotel listing
* Room management
* Amenities
* Room availability
* Booking system
* Check-in/check-out
* Booking statuses
* Guest count
* Pricing
* Reviews
* Image gallery
* Reservation management

---

# Recommended App Structure

```bash
apps/
 ├── hospitality/
 │     ├── models.py
 │     ├── serializers.py
 │     ├── views.py
 │     ├── urls.py
 │     ├── permissions.py
 │     ├── services.py
 │     └── utils.py
```

---

# models.py

```python
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
```

---

# serializers.py

```python
from rest_framework import serializers
from .models import Lodge, Room, Booking, LodgeImage, Review


class LodgeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LodgeImage
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'


class LodgeSerializer(serializers.ModelSerializer):
    images = LodgeImageSerializer(many=True, read_only=True)
    rooms = RoomSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Lodge
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = (
            'customer',
            'booking_reference',
            'total_nights',
            'subtotal',
            'total_amount',
        )
```

---

# utils.py

```python
import random
import string


def generate_booking_reference():
    return 'MM-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
```

---

# views.py

```python
from datetime import timedelta

from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Lodge, Room, Booking
from .serializers import (
    LodgeSerializer,
    RoomSerializer,
    BookingSerializer,
)
from .utils import generate_booking_reference


class LodgeViewSet(viewsets.ModelViewSet):
    queryset = Lodge.objects.filter(is_active=True)
    serializer_class = LodgeSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.filter(is_available=True)
    serializer_class = RoomSerializer
    permission_classes = [permissions.AllowAny]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user)

    def create(self, request, *args, **kwargs):
        room_id = request.data.get('room')
        check_in_date = request.data.get('check_in_date')
        check_out_date = request.data.get('check_out_date')

        room = Room.objects.get(id=room_id)

        overlapping_bookings = Booking.objects.filter(
            room=room,
            booking_status__in=['pending', 'confirmed'],
        ).filter(
            Q(check_in_date__lt=check_out_date) &
            Q(check_out_date__gt=check_in_date)
        )

        if overlapping_bookings.exists():
            return Response(
                {'error': 'Room is not available for selected dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from datetime import datetime

        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()

        total_nights = (check_out - check_in).days

        subtotal = room.price_per_night * total_nights
        service_fee = 0
        total_amount = subtotal + service_fee

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            customer=request.user,
            lodge=room.lodge,
            booking_reference=generate_booking_reference(),
            total_nights=total_nights,
            subtotal=subtotal,
            service_fee=service_fee,
            total_amount=total_amount,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel_booking(self, request, pk=None):
        booking = self.get_object()

        booking.booking_status = 'cancelled'
        booking.save()

        return Response({'message': 'Booking cancelled successfully'})
```

---

# urls.py

```python
from rest_framework.routers import DefaultRouter
from .views import LodgeViewSet, RoomViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'lodges', LodgeViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'bookings', BookingViewSet, basename='bookings')

urlpatterns = router.urls
```

---

# Main urls.py

```python
path('api/hospitality/', include('apps.hospitality.urls')),
```

---

# Recommended APIs

## Lodges

```bash
GET /api/hospitality/lodges/
POST /api/hospitality/lodges/
GET /api/hospitality/lodges/1/
```

---

## Rooms

```bash
GET /api/hospitality/rooms/
POST /api/hospitality/rooms/
```

---

## Bookings

```bash
GET /api/hospitality/bookings/
POST /api/hospitality/bookings/
POST /api/hospitality/bookings/1/cancel_booking/
```

---

# Recommended Future Features

## Important Next Features

* Availability calendar
* Seasonal pricing
* Discounts/promotions
* QR booking verification
* Mpamba/Airtel Money integration
* Lodge analytics dashboard
* Host payout tracking
* Refund handling
* Saved/favorite lodges
* Nearby lodges search
* Geo search
* Notifications
* Booking reminders

---

# Recommended Permissions

## customer

* create bookings
* review lodges

## property_owner

* create/manage lodges
* manage rooms
* view reservations

---

# Suggested User Types Update

Add hospitality owner support:

```python
USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('shop_owner', 'Shop Owner'),
    ('property_owner', 'Property Owner'),
    ('hospitality_owner', 'Hospitality Owner'),
    ('admin', 'Admin'),
)
```

---

# Recommended Booking Flow

1. User opens lodge
2. Select room
3. Select dates
4. Check availability
5. Make payment
6. Booking confirmed
7. Lodge owner notified
8. Customer receives booking reference

---

# Suggested Flutter Pages

* Lodge List Page
* Lodge Details Page
* Room Details Page
* Booking Checkout Page
* My Bookings Page
* Lodge Owner Dashboard
* Availability Calendar
* Booking Success Page

---

# Important Scaling Advice

Do NOT combine:

* products
* properties
* events
* lodges

in one database table.

Keep separate apps/modules:

```bash
apps/
 ├── marketplace/
 ├── properties/
 ├── hospitality/
 ├── events/
 └── payments/
```

This will help MangoMart scale properly in Malawi.
