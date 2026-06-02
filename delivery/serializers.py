from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import Delivery, DeliveryPerson
from payments.models import EscrowWallet
from payments.serializers import EscrowWalletSerializer 
from orders.models import OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
        ]



# =========================
# DELIVERY PERSON SERIALIZER
# =========================
class DeliveryPersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryPerson
        fields = [
            'id',
            'id_number',

            # identity
            'full_name',
            'phone_number',
            'alternative_phone',

            # vehicle
            'vehicle_number',
            'vehicle_type',
            'license_number',

            # status
            'status',

            # performance
            'rating',
            'total_deliveries',

            'created_at'
        ]

# =========================
# DELIVERY READ SERIALIZER
# (USED BY FLUTTER SCREENS)


class DeliverySerializer(serializers.ModelSerializer):

    delivery_person = DeliveryPersonSerializer(read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    customer_delivery_code = serializers.CharField(read_only=True)
    escrow = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            'id',
            'order_number',
            'items',
            'delivery_code',
            'status',
            'delivery_person',
            'pickup_latitude',
            'pickup_longitude',
            'customer_latitude',
            'customer_longitude',
            'delivery_address',
            'escrow',
            'customer_delivery_code',
            'delivery_phone_number',
            'created_at',
            'picked_up_at',
            'delivered_at',
        ]

    def get_items(self, obj):
        order = getattr(obj, "order", None)
        if not order:
            return []

        return OrderItemSerializer(
            order.items.filter(product__shop__owner=obj.seller),
            many=True
        ).data

    def get_escrow(self, obj):
        if not getattr(obj, "order", None):
            return []

        qs = EscrowWallet.objects.filter(payment__order=obj.order)

        if getattr(obj, "seller", None):
            qs = qs.filter(beneficiary=obj.seller)

        return EscrowWalletSerializer(qs, many=True).data

# =========================
# ASSIGN DELIVERY PERSON
# =========================
class AssignDeliverySerializer(serializers.Serializer):

    # ======================
    # DELIVERY PERSON INFO
    # ======================
    id_number = serializers.CharField()
    full_name = serializers.CharField()
    phone_number = serializers.CharField()

    alternative_phone = serializers.CharField(
        required=False,
        allow_blank=True
    )

    vehicle_number = serializers.CharField(required=False, allow_blank=True)
    vehicle_type = serializers.CharField(required=False, allow_blank=True)
    license_number = serializers.CharField(required=False, allow_blank=True)

    # ======================
    # PICKUP GPS
    # ======================
    pickup_latitude = serializers.FloatField()
    pickup_longitude = serializers.FloatField()

    # ======================
    # ROUND GPS AUTOMATICALLY
    # ======================
    def validate(self, attrs):

        attrs["pickup_latitude"] = float(
        Decimal(str(attrs["pickup_latitude"]))
        .quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        )

        attrs["pickup_longitude"] = float(
        Decimal(str(attrs["pickup_longitude"]))
        .quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        )

        return attrs

    # ======================
    # CORE ASSIGN LOGIC
    # ======================
    def update(self, delivery, validated_data):

        driver, created = DeliveryPerson.objects.get_or_create(
            id_number=validated_data["id_number"],
            defaults={
                "full_name": validated_data["full_name"],
                "phone_number": validated_data["phone_number"],
                "alternative_phone": validated_data.get("alternative_phone", ""),
                "vehicle_number": validated_data.get("vehicle_number", ""),
                "vehicle_type": validated_data.get("vehicle_type", ""),
                "license_number": validated_data.get("license_number", ""),
            }
        )

        # If driver exists → optionally update info
        if not created:
            driver.full_name = validated_data["full_name"]
            driver.phone_number = validated_data["phone_number"]
            driver.alternative_phone = validated_data.get("alternative_phone", "")
            driver.vehicle_number = validated_data.get("vehicle_number", "")
            driver.vehicle_type = validated_data.get("vehicle_type", "")
            driver.license_number = validated_data.get("license_number", "")
            driver.save()

        # LINK DRIVER TO DELIVERY
        delivery.delivery_person = driver

        # SAVE GPS
        delivery.pickup_latitude = validated_data["pickup_latitude"]
        delivery.pickup_longitude = validated_data["pickup_longitude"]

        delivery.status = "assigned"
        delivery.save()

        return delivery

# =========================
# DELIVERY STATUS UPDATE
# (USED BY RIDER)
# =========================
class DeliveryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            'status',
            'pickup_latitude',
            'pickup_longitude'
        ]