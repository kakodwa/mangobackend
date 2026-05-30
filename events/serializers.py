from rest_framework import serializers
from .models import (
    Event,
    EventCategory,
    Ticket,
    EventImage,
    EventTicketType,
    TicketItem
)


# =========================
# CATEGORY
# =========================
class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = '__all__'


# =========================
# EVENT IMAGES
# =========================
class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = ['id', 'image']


# =========================
# TICKET TYPE (VIP / REGULAR / VVIP)
# =========================
class EventTicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTicketType
        fields = [
            'id',
            'event',
            'name',
            'price',
            'total_seats',
            'available_seats'
        ]


# =========================
# EVENT SERIALIZER
# =========================
class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(
        source='organizer.get_full_name',
        read_only=True
    )

    images = EventImageSerializer(many=True, read_only=True)
    ticket_types = EventTicketTypeSerializer(many=True,read_only=True)
    organizer_phone_number = serializers.CharField(
        source='organizer.phone_number',
        read_only=True
    )

    class Meta:
        model = Event
        fields = [
            'id',
            'organizer',
            'organizer_name',
            'category',

            'title',
            'description',

            'organizer_phone_number',

            'venue',
            'district',
            'city',

            'latitude',
            'longitude',

            'ticket_types',

            'event_date',
            'start_time',
            'end_time',

            'banner',

            'status',
            'is_featured',

            'images',
            'created_at',
        ]


        read_only_fields = [
            'organizer',
            'available_tickets',
            'created_at'
        ]

class TicketItemSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)

    class Meta:
        model = TicketItem
        fields = [
            'ticket_type_name',
            'quantity',
            'subtotal'
        ]


# =========================
# TICKET SERIALIZER
# =========================
class TicketSerializer(serializers.ModelSerializer):
    items = TicketItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(
        source='customer.get_full_name',
        read_only=True
    )

    event_title = serializers.CharField(
        source='event.title',
        read_only=True
    )

    # NEW: ticket type info
    ticket_type_name = serializers.CharField(
        source='ticket_type.name',
        read_only=True
    )

    # QR CODE
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',

            'event',
            'event_title',

            'customer',
            'customer_name',

            # NEW
            'ticket_type',
            'ticket_type_name',
            'seat_number',

            'quantity',
            'total_amount',
            'payment_status',

            'items',

            'qr_code',
            'purchased_at',
        ]

        read_only_fields = [
            'customer',
            'ticket_number',
            'total_amount',
            'purchased_at',
        ]

    def get_qr_code(self, obj):
        request = self.context.get('request')

        if obj.qr_code:
            return request.build_absolute_uri(obj.qr_code.url)

        return None


# =========================
# PURCHASE TICKET
# =========================
class TicketItemInputSerializer(serializers.Serializer):
    ticket_type_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(min_value=1)




class PurchaseTicketSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    tickets = TicketItemInputSerializer(many=True)

    def validate(self, attrs):
        from .models import Event, EventTicketType

        event_id = attrs.get('event_id')
        tickets = attrs.get('tickets')

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found")

        parsed_tickets = []

        for item in tickets:
            ticket_type = None

            if item.get("ticket_type_id"):
                try:
                    ticket_type = EventTicketType.objects.get(
                        id=item["ticket_type_id"],
                        event=event
                    )
                except EventTicketType.DoesNotExist:
                    raise serializers.ValidationError("Invalid ticket type")

                if ticket_type.available_seats < item["quantity"]:
                    raise serializers.ValidationError(
                        f"Not enough seats for {ticket_type.name}"
                    )

            parsed_tickets.append({
                "ticket_type": ticket_type,
                "quantity": item["quantity"]
            })

        attrs["event"] = event
        attrs["parsed_tickets"] = parsed_tickets

        return attrs