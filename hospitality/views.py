from datetime import timedelta

from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from .utils import generate_booking_reference
from .permissions import IsHospitalityOwner


from .models import Lodge, Room, Booking, Amenity
from .serializers import (
    LodgeSerializer,
    RoomSerializer,
    BookingSerializer,
    AmenitySerializer
)


class AmenityViewSet(ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer


class LodgeViewSet(viewsets.ModelViewSet):
    queryset = Lodge.objects.filter(is_active=True)
    serializer_class = LodgeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsHospitalityOwner()]

    # =========================
    # FULL CREATE DEBUG
    # =========================
    def create(self, request, *args, **kwargs):

        print("\n🔥 ===== CREATE REQUEST DEBUG =====")
        print("🔥 DATA:", request.data)
        print("🔥 FILES:", request.FILES)
        print("🔥 CONTENT TYPE:", request.content_type)

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():

            print("\n❌ SERIALIZER ERRORS ❌")
            print(serializer.errors)
            print("❌ ==================\n")

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)

        print("\n✅ SERIALIZER VALID\n")

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        user = self.request.user

        print("\n🔥 ===== LODGE CREATE DEBUG =====")
        print("🔥 USER:", user)
        print("🔥 USER TYPE:", user.user_type)

        lodge = serializer.save(owner=user)

        print("✅ CREATED:", lodge.id)


    @action(detail=False, methods=['get'], permission_classes=[IsHospitalityOwner])
    def my_lodges(self, request):
        try:
            print("=== MY LODGES DEBUG START ===")
            print("User:", request.user)
            print("Authenticated:", request.user.is_authenticated)

            lodges = Lodge.objects.filter(owner=request.user).order_by('-created_at')
            print("Lodges found:", lodges.count())

            serializer = self.get_serializer(lodges, many=True, context={"request": request})
            print("Serialization successful")
            print("=== MY LODGES DEBUG END ===")
            return Response(serializer.data)
        except Exception as e:
            print("Error:", str(e))
           

        return Response({"detail": "Failed to load lodges"}, status=500)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.filter(is_available=True)
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
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