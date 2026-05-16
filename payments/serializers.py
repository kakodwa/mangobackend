from rest_framework import serializers
from .models import Payment, PaymentWebhook
from orders.models import Order
from realestate.models import PropertyUnlock
import uuid

#Mobile Money (initialize charge)
#Card (redirect checkout URL)
#Verify + Webhook confirmation

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

            'order',
            'order_number',

            'property_unlock',
            'property_title',

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

    def get_payment_method_display(self, obj):

        methods = {
            "airtel_money": "Airtel Money",
            "tnm_mpamba": "TNM Mpamba",
            "visa_card": "Visa Card",
        }

        return methods.get(
            obj.payment_method,
            obj.payment_method
        )

    def get_property_title(self, obj):

        if obj.property_unlock:
            return obj.property_unlock.property.title

        return None

class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=False, allow_null=True)
    property_unlock_id = serializers.IntegerField(required=False, allow_null=True)
    payment_method = serializers.CharField()

    def create(self, validated_data):
        user = self.context['request'].user
        payment_reference = f"PAY-{uuid.uuid4().hex[:8].upper()}"

        order = None
        property_unlock = None
        amount = None
        payment_purpose = None

        #PRODUCT PAYMENT
        if validated_data.get('order_id'):
            order = Order.objects.get(id=validated_data['order_id'])
            payment_purpose = "order"
            amount = order.total_amount

        #PROPERTY PAYMENT
        elif validated_data.get('property_unlock_id'):
            property_unlock = PropertyUnlock.objects.get(
                id=validated_data['property_unlock_id']
                )
            payment_purpose = "property_unlock"
            amount = property_unlock.property.unlock_fee # or property_unlock.amount depending on your model 

        else:
            raise serializers.ValidationError(
                "Either order_id or property_unlock_id is required"
                )

        payment = Payment.objects.create(
            user=user,
            order=order,
            property_unlock=property_unlock,
            amount=amount,
            purpose = payment_purpose,
            payment_method=validated_data['payment_method'],
            payment_reference=payment_reference,
            status='pending'
            )

        return payment

class PaymentWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentWebhook
        fields = ['id', 'payment', 'webhook_data', 'processed', 'created_at']
        read_only_fields = ['id', 'payment', 'created_at']