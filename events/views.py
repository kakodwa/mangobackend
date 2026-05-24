from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import F
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

import json
from .models import Event, Ticket, TicketCheckIn, EventTicketType,TicketItem
from .serializers import (
    EventSerializer,
    TicketSerializer,
    PurchaseTicketSerializer
)
from .utils import verify_qr_token


# =========================
# EVENT VIEWSET
# =========================
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    # =========================
    # PERMISSIONS
    # =========================
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'featured']:
            return [AllowAny()]

        return [IsAuthenticated()]

    # =========================
    # QUERYSET
    # =========================
    def get_queryset(self):

        queryset = Event.objects.filter(
            status='published'
        )

        # =========================
        # FILTER MY EVENTS
        # =========================
        mine = self.request.query_params.get("mine")

        if (
            mine == "true"
            and self.request.user.is_authenticated
        ):
            queryset = queryset.filter(
                organizer=self.request.user
            )

        # =========================
        # CATEGORY FILTER
        # =========================
        category = self.request.query_params.get(
            'category'
        )

        if category:
            queryset = queryset.filter(
                category_id=category
            )

        return queryset

    # =========================
    # CREATE EVENT
    # ========================
    def create(self, request, *args, **kwargs):
        print("\n🚀 CREATE HIT")
        print("REQUEST DATA:", request.data)
        print("FILES:", request.FILES)

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            print("\n❌ SERIALIZER ERRORS:")
            print(serializer.errors)
            return Response(serializer.errors, status=400)

        self.perform_create(serializer)

        print("\n✅ CREATE SUCCESS")

        return Response(serializer.data, status=201)

    # =========================
    # CREATE EVENT (DEBUG + SAFE)
    # =========================
    @transaction.atomic
    def perform_create(self, serializer):

        print("\n================ EVENT CREATE START ================")
        print("RAW REQUEST DATA:", self.request.data)

        raw_ticket_types = self.request.data.get("ticket_types", [])
        print("RAW ticket_types TYPE:", type(raw_ticket_types))
        print("RAW ticket_types VALUE:", raw_ticket_types)

        # =========================
        # FIX: if sent as string → convert to list
        # =========================
        ticket_types_data = raw_ticket_types

        if isinstance(raw_ticket_types, str):
            try:
                ticket_types_data = json.loads(raw_ticket_types)
                print("PARSED ticket_types:", ticket_types_data)
            except Exception as e:
                print("❌ ticket_types JSON parse error:", str(e))
                ticket_types_data = []

        # =========================
        # SAVE EVENT
        # =========================
        event = serializer.save(organizer=self.request.user)
        print("✅ EVENT CREATED:", event.id)

        # =========================
        # CREATE TICKET TYPES
        # =========================
        for t in ticket_types_data:
            try:
                print("➡ Creating ticket type:", t)

                EventTicketType.objects.create(
                    event=event,
                    name=t.get('name'),
                    price=t.get('price', 0),
                    total_seats=t.get('total_seats', 0),
                    available_seats=t.get('total_seats', 0)
                )

            except Exception as e:
                print("❌ ERROR CREATING TICKET TYPE:", e)

        print("================ EVENT CREATE END ================")

    # =========================
    # FEATURED EVENTS
    # =========================
    @action(detail=False, methods=['get'])
    def featured(self, request):
        events = Event.objects.filter(
            is_featured=True,
            status='published'
        )
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)

# =========================
# TICKET VIEWSET
# =========================
class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        queryset = (
            Ticket.objects.select_related(
            'event',
            'customer',).prefetch_related(
            'items',
            'items__ticket_type',).order_by('-purchased_at'))

        event_id = self.request.query_params.get("event")
        
        if event_id:
            return queryset.filter(
                event_id=event_id,
                event__organizer=self.request.user,
                )

        return queryset.filter(
            customer=self.request.user
            )


    # =====================================
    # PURCHASE TICKETS (CART SYSTEM)
    # =====================================
    @transaction.atomic
    @action(detail=False, methods=['post'])
    def purchase(self, request):

        print("\n========== PURCHASE DEBUG ==========")
        print("REQUEST DATA =>", request.data)
        print("USER =>", request.user)
        print("====================================\n")

        serializer = PurchaseTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event = serializer.validated_data['event']
        parsed_tickets = serializer.validated_data['parsed_tickets']

        total_amount = 0
        total_quantity = 0


        # =====================================
        # CALCULATE TOTALS
        # =====================================
        for item in parsed_tickets:
            ticket_type = item['ticket_type']
            quantity = item['quantity']

            subtotal = ticket_type.price * quantity
            total_amount += subtotal
            total_quantity += quantity

            
            # =====================================
            # ONLY VALIDATION (NO UPDATE)
            # =====================================
            if ticket_type.available_seats < quantity:
                return Response(
                    {"error": f"Not enough seats for {ticket_type.name}"},
                    status=400
                    )

        ticket = Ticket.objects.create(
            event=event,
            customer=request.user,
            ticket_type=None,
            quantity=total_quantity,
            total_amount=total_amount,
            payment_status='pending',
            )

        created_items = []

        # =====================================
        # CREATE ITEMS (NO SEAT DEDUCTION)
        # =====================================

        for item in parsed_tickets:
            ticket_type = item['ticket_type']
            quantity = item['quantity']
            subtotal = ticket_type.price * quantity

            ticket_item = TicketItem.objects.create(
                ticket=ticket,
                ticket_type=ticket_type,
                name_snapshot=ticket_type.name,
                price_snapshot=ticket_type.price,
                quantity=quantity,
                subtotal=subtotal,
                )

            created_items.append({
                "id": ticket_item.id,
                "ticket_type": ticket_type.name,
                "price": str(ticket_type.price),
                "quantity": quantity,
                "subtotal": str(subtotal),
                })


        return Response(
            {"message": "Tickets reserved. Proceed to payment.",
            "ticket": TicketSerializer(
                ticket,
                context={"request": request}
                ).data,
            "items": created_items,
            "summary": {
            "total_quantity": total_quantity,
            "total_amount": str(total_amount),
            }
            },
            status=status.HTTP_201_CREATED
            )

# =========================
# TICKET VALIDATION (QR SCAN)
# =========================
class TicketValidationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def validate_ticket(self, request):

        ticket_number = request.data.get('ticket_number')

        try:
            ticket = Ticket.objects.get(
                ticket_number=ticket_number,
                payment_status='paid'
            )
        except Ticket.DoesNotExist:
            return Response(
                {"valid": False, "message": "Invalid ticket"},
                status=400
            )

        checkin, created = TicketCheckIn.objects.get_or_create(ticket=ticket)

        if checkin.is_checked_in:
            return Response(
                {"valid": False, "message": "Ticket already used"},
                status=400
            )

        checkin.is_checked_in = True
        checkin.checked_in_by = request.user
        checkin.save()

        return Response({
            "valid": True,
            "message": "Ticket verified successfully",
            "event": ticket.event.title,
            "seat": ticket.seat_number,
            "type": ticket.ticket_type.name if ticket.ticket_type else "Regular"
        })


# =========================
# QR CHECK-IN API
# =========================
class TicketCheckInAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # =========================
            # 1. GET QR CODE
            # =========================
            qr_token = request.data.get("qr_code")

            if not qr_token:
                return Response({
                    "status": "error",
                    "message": "QR code required",
                }, status=400)

            print("🔍 QR TOKEN:", qr_token)

            # =========================
            # 2. VERIFY QR TOKEN
            # =========================
            data = verify_qr_token(qr_token)

            print("📦 DECODED DATA:", data)

            if not data:
                return Response({
                    "status": "error",
                    "message": "Invalid or expired QR code",
                }, status=400)

            ticket_number = data.get("ticket_number")
            event_id = data.get("event_id")

            print("🎟 TICKET:", ticket_number)
            print("🎫 EVENT:", event_id)

            if not ticket_number or not event_id:
                return Response({
                    "status": "error",
                    "message": "Invalid QR payload",
                }, status=400)

            # =========================
            # 3. FETCH TICKET
            # =========================
            ticket = get_object_or_404(
                Ticket,
                ticket_number=ticket_number,
                event_id=event_id,
                payment_status='paid',
                event__status='published'
            )

            # =========================
            # 4. CHECK EVENT DATE
            # =========================
            event = ticket.event
            today = timezone.now().date()

            if event.event_date > today:
                return Response({
                    "status": "error",
                    "message": "Event has not started yet",
                    "data": {
                        "event": event.title,
                        "date": str(event.event_date)
                    }
                }, status=400)

            # =========================
            # 5. CHECK-IN LOGIC
            # =========================
            checkin, created = TicketCheckIn.objects.get_or_create(
                ticket=ticket
            )

            if checkin.is_checked_in:
                return Response({
                    "status": "error",
                    "message": "Ticket already checked in",
                    "data": {
                        "ticket": ticket_number,
                        "event": event.title,
                        "checked_in_at": str(checkin.checked_in_at) if checkin.checked_in_at else None
                    }
                }, status=400)

            # =========================
            # 6. MARK CHECK-IN
            # =========================
            checkin.is_checked_in = True
            checkin.checked_in_by = request.user
            checkin.checked_in_at = timezone.now()
            checkin.save()

            # =========================
            # 7. SUCCESS RESPONSE
            # =========================
            return Response({
                "status": "success",
                "message": "Check-in successful",

                "data": {
                "ticket_number": data.get("ticket_number"),
                "event_title": data.get("event_title"),
                "attendee_name": data.get("attendee_name"),
                "ticket_items": data.get("ticket_items", []),

                "checked_in_at": str(checkin.checked_in_at),
                "seat": ticket.seat_number,
                "type": ticket.ticket_type.name if ticket.ticket_type else "Regular", }
                })

        except Exception as e:
            print("❌ CHECK-IN ERROR:", str(e))

            return Response({
                "status": "error",
                "message": "Internal server error during check-in"
            }, status=500)