from rest_framework import serializers
from .models import Payment, PaymentWebhook
from orders.models import Order
from hospitality.models import Booking
from realestate.models import PropertyUnlock
from events.models import Ticket
import uuid


# =====================================================
# PAYMENT SERIALIZER
# =====================================================
class PaymentSerializer(serializers.ModelSerializer):

    order_number = serializers.CharField(
        source='order.order_number',
        read_only=True
    )

    purpose_display = serializers.CharField(
        source='get_purpose_display',
        read_only=True
    )

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    payment_method_display = serializers.SerializerMethodField()
    property_title = serializers.SerializerMethodField()
    ticket_event = serializers.SerializerMethodField()

    class Meta:
        model = Payment

        fields = [
            'id',
            'payment_reference',
            'amount',

            'purpose',
            'purpose_display',

            'payment_method',
            'payment_method_display',

            'status',
            'status_display',

            # relations
            'order',
            'order_number',

            'property_unlock',
            'property_title',

            'booking',

            'ticket_purchase',     # ✅ NEW
            'ticket_event',        # ✅ NEW DISPLAY

            'paychangu_transaction_id',
            'paid_at',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'payment_reference',
            'paychangu_transaction_id',
            'paid_at',
            'created_at'
        ]

    # ---------------------------------------
    def get_payment_method_display(self, obj):

        methods = {
            "airtel_money": "Airtel Money",
            "tnm_mpamba": "TNM Mpamba",
            "visa_card": "Visa Card",
        }

        return methods.get(obj.payment_method, obj.payment_method)

    # ---------------------------------------
    def get_property_title(self, obj):
        if obj.property_unlock:
            return obj.property_unlock.property.title
        return None

    # ---------------------------------------
    def get_ticket_event(self, obj):
        if obj.ticket_purchase:
            return obj.ticket_purchase.event.title
        return None


# =====================================================
# PAYMENT INITIATE SERIALIZER
# =====================================================
class PaymentInitiateSerializer(serializers.Serializer):

    order_id = serializers.IntegerField(required=False, allow_null=True)
    property_unlock_id = serializers.IntegerField(required=False, allow_null=True)
    booking_id = serializers.IntegerField(required=False, allow_null=True)
    ticket_purchase_id = serializers.IntegerField(required=False, allow_null=True)  # ✅ NEW

    payment_method = serializers.CharField()

    # -------------------------------------------------
    def create(self, validated_data):

        user = self.context['request'].user
        payment_reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"

        order = None
        property_unlock = None
        booking = None
        ticket_purchase = None

        amount = None
        payment_purpose = None

        # ================= ORDER =================
        if validated_data.get('order_id'):
            order = Order.objects.get(id=validated_data['order_id'])
            payment_purpose = "order"
            amount = order.total_amount

        # ================= PROPERTY =================
        elif validated_data.get('property_unlock_id'):
            property_unlock = PropertyUnlock.objects.get(
                id=validated_data['property_unlock_id']
            )
            payment_purpose = "property_unlock"
            amount = property_unlock.property.unlock_fee

        # ================= BOOKING =================
        elif validated_data.get('booking_id'):
            booking = Booking.objects.get(
                id=validated_data['booking_id']
            )
            payment_purpose = "booking"
            amount = booking.total_amount

        # ================= TICKETS (NEW) =================
        elif validated_data.get('ticket_purchase_id'):
            ticket_purchase = Ticket.objects.get(
                id=validated_data['ticket_purchase_id']
            )

            payment_purpose = "ticket"

            # ticket total price
            amount = ticket_purchase.total_amount

        else:
            raise serializers.ValidationError(
                "Provide order_id, property_unlock_id, booking_id, or ticket_purchase_id"
            )

        # ================= CREATE PAYMENT =================
        payment = Payment.objects.create(
            user=user,
            order=order,
            property_unlock=property_unlock,
            booking=booking,
            ticket_purchase=ticket_purchase,   # ✅ NEW

            amount=amount,
            purpose=payment_purpose,
            payment_method=validated_data['payment_method'],
            payment_reference=payment_reference,
            status='pending'
        )

        return payment


# =====================================================
# WEBHOOK SERIALIZER
# =====================================================
class PaymentWebhookSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentWebhook
        fields = [
            'id',
            'payment',
            'webhook_data',
            'processed',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'payment',
            'created_at'
        ]