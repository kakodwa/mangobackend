from rest_framework import serializers
from .models import Order, OrderItem
from decimal import Decimal, ROUND_HALF_UP
from products.serializers import ProductSerializer
from delivery.serializers import DeliverySerializer



def round6(value):
    if value is None:
        return None
    return Decimal(value).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP
    )


# =========================
# ORDER ITEM SERIALIZER
# =========================
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_id',
            'quantity',
            'unit_price',
            'total_price'
        ]
        read_only_fields = ['id', 'unit_price', 'total_price']



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)

    delivery = DeliverySerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_name',
            'customer_id',
            'status',
            'subtotal',
            'shipping_fee',
            'tax',
            'total_amount',
            'delivery_address',
            'delivery_latitude',
            'delivery_longitude',

            'delivery',

            'items',
            'created_at'
        ]


# =========================
# ORDER CREATE SERIALIZER
# =========================
class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True)
    delivery_address = serializers.CharField()

    # GPS (frontend names)

    lat = serializers.FloatField(required=False, allow_null=True)
    lng = serializers.FloatField(required=False, allow_null=True)

    # PHONE (frontend name)
    delivery_phone = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        from .models import Order, OrderItem
        from products.models import Product
        from decimal import Decimal

        user = self.context['request'].user
        items_data = validated_data['items']

        # =========================
        # EXTRACT EXTRA FIELDS
        # ========================

        lat = round6(validated_data.pop('lat', None))
        lng = round6(validated_data.pop('lng', None))
        phone = validated_data.pop('delivery_phone', None)

        # =========================
        # CREATE ORDER
        # =========================
        order = Order.objects.create(
            order_number=f"ORD-{user.id}-{Order.objects.count() + 1}",
            customer=user,
            delivery_address=validated_data['delivery_address'],

            # ✅ GPS MAP
            delivery_latitude=lat,
            delivery_longitude=lng,

            # ✅ PHONE MAP
            delivery_phone_number=phone,

            subtotal=0,
            total_amount=0
        )

        subtotal = Decimal('0.00')

        # =========================
        # CREATE ITEMS
        # =========================
        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            qty = item['quantity']

            if product.shop.owner == user:
                raise serializers.ValidationError(
                    f"You cannot order your own product: {product.name}"
                )

            unit_price = product.price
            total_price = unit_price * qty

            subtotal += total_price

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price
            )

        # =========================
        # FINAL TOTALS
        # =========================
        order.subtotal = subtotal
        order.total_amount = subtotal
        order.save()

        return order