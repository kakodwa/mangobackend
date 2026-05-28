from datetime import timedelta

from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.core.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import timedelta
import json
import random
import string
from .permissions import IsHospitalityOwner
from django.core import signing

from .models import Lodge, Room, Booking, Amenity
from .serializers import (
    LodgeSerializer,
    RoomSerializer,
    BookingSerializer,
    AmenitySerializer
)


from django.core.signing import (
    TimestampSigner,
    BadSignature,
    SignatureExpired,
)

signer = TimestampSigner()

def verify_booking_qr(token, max_age=86400):
    try:
        value = signer.unsign(token, max_age=max_age)
        data = json.loads(value)
        return data

    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return None


def generate_booking_reference():

    return 'BK-' + ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=8,
        )
    )


class AmenityViewSet(ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer


class LodgeViewSet(viewsets.ModelViewSet):
    # queryset = Lodge.objects.filter(is_active=True)
    serializer_class = LodgeSerializer

    def get_queryset(self):

        # Public users can only see active lodges
        if self.action in ['list', 'retrieve']:
            return Lodge.objects.filter(is_active=True)

        # Authenticated users can only manage their own lodges
        return Lodge.objects.filter(
            owner=self.request.user
        )

    def get_permissions(self):

        # Anyone can view lodges
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]

        # Any authenticated user can create/update/delete
        return [permissions.IsAuthenticated()]

    # =========================
    # FULL CREATE DEBUG
    # =========================
    def create(self, request, *args, **kwargs):
        print("\n🔥 CREATE REQUEST DEBUG")
        print("DATA:", request.data)
        print("FILES:", request.FILES)

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("\n❌ SERIALIZER ERRORS:", serializer.errors)

            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        print("\n✅ CREATED SUCCESSFULLY")
        return Response(serializer.data,status=status.HTTP_201_CREATED)

    # =========================
    # FULL UPDATE DEBUG
    # =========================
    def update(self, request, *args, **kwargs):

        print("\n🔥 ===== UPDATE REQUEST DEBUG =====")
        print("DATA:", request.data)
        print("FILES:", request.FILES)
        print("CONTENT TYPE:", request.content_type)

        partial = kwargs.pop('partial', False)

        # Only owner can update because of get_queryset()
        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        if not serializer.is_valid():

            print("\n❌ UPDATE ERRORS ❌")
            print(serializer.errors)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        print("✅ LODGE UPDATED:", instance.id)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):

        user = self.request.user

        print("\n🔥 ===== LODGE CREATE DEBUG =====")
        print("🔥 USER:", user)
        print("🔥 USER TYPE:", getattr(user, "user_type", None))

        lodge = serializer.save(owner=user)

        print("✅ CREATED:", lodge.id)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def my_lodges(self, request):

        try:
            print("=== MY LODGES DEBUG START ===")
            print("User:", request.user)
            print("Authenticated:", request.user.is_authenticated)

            lodges = Lodge.objects.filter(
                owner=request.user
            ).order_by('-created_at')

            print("Lodges found:", lodges.count())

            serializer = self.get_serializer(
                lodges,
                many=True,
                context={"request": request}
            )

            print("Serialization successful")
            print("=== MY LODGES DEBUG END ===")

            return Response(serializer.data)

        except Exception as e:

            print("Error:", str(e))

        return Response(
            {"detail": "Failed to load lodges"},
            status=500
        )


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.filter(is_available=True)
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve','availability']:
            return [permissions.AllowAny()]
        return [IsHospitalityOwner()]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("❌ VALIDATION ERROR:", serializer.errors)
            return Response(serializer.errors, status=400)

        self.perform_create(serializer)

        print("✅ ROOM CREATED:", serializer.data)

        return Response(serializer.data, status=201)

   
    @action(detail=True,methods=['get'],permission_classes=[permissions.AllowAny],authentication_classes=[])
    def availability(self, request, pk=None):


        bookings = Booking.objects.filter(
            room_id=pk,
            booking_status__in=['confirmed',]# 'checked_in'
        )

        booked_dates = []

        for booking in bookings:
            current = booking.check_in_date

            while current <= booking.check_out_date:
                booked_dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)

        return Response({
            "booked_dates": booked_dates
        })


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action in ["owner", "check_in", "scan_qr", "cancel_booking"]:
            return Booking.objects.filter(lodge__owner=user)

        return Booking.objects.filter(customer=user)

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

        serializer.is_valid(raise_exception=False)
        if not serializer.is_valid():
            print("❌ SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

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


    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def owner(self, request):
        user = request.user

        bookings = Booking.objects.filter(lodge__owner=user)

        serializer = self.get_serializer(bookings, many=True)
        print(serializer.data)
        return Response(serializer.data)


    @action(detail=False, methods=['post'])
    def scan_qr(self, request):
        qr_token = request.data.get("qr_data")

        if not qr_token:
            return Response({"error": "QR code required"}, status=400)

        data = verify_booking_qr(qr_token)

        if not data:
            return Response({"error": "Invalid or expired QR code"}, status=400)

        booking_id = data.get("booking_id")

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=404)

        booking.mark_checked_in(request.user)

        return Response({
            "message": "Check-in successful",
            "booking_reference": booking.booking_reference,
            "room_number": booking.room.room_number,
            "booking_status": booking.booking_status,})

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        try:
            booking = self.get_object()

            booking.mark_checked_in(request.user)
            return Response({
                "message": "Checked in successfully",
                "status": booking.booking_status
                })

        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def cancel_booking(self, request, pk=None):
        booking = self.get_object()

        booking.booking_status = 'cancelled'
        booking.save()

        return Response({'message': 'Booking cancelled successfully'})