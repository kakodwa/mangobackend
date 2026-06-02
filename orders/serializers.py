from rest_framework import serializers
from .models import Order, OrderItem
from decimal import Decimal, ROUND_HALF_UP
from products.serializers import ProductSerializer
from delivery.serializers import DeliverySerializer
from orders.models import SellerOrder
from payments.models import EscrowWallet


class SellerOrderSerializer(serializers.ModelSerializer):

    customer_paid = serializers.SerializerMethodField()
    escrow_status = serializers.SerializerMethodField()
    escrow_amount = serializers.SerializerMethodField()
    seller_amount = serializers.SerializerMethodField()
    commission = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()   # ✅ ADD THIS

    class Meta:
        model = SellerOrder
        fields = [
            "id",
            "order",
            "seller",
            "subtotal",
            "customer_paid",
            "escrow_status",
            "escrow_amount",
            "seller_amount",
            "commission",
            "delivery_status",
            "items",   # ✅ IMPORTANT
            "created_at",
        ]

    def get_items(self, obj):
        items = obj.order.items.filter(product__shop__owner=obj.seller)

        return [
            {
                "id": i.id,
                "product_name": i.product.name,
                "product_image": i.product.image.url if i.product.image else "",
                "quantity": i.quantity,
                "total_price": i.total_price,
            }
            for i in items
        ]

    def get_customer_paid(self, obj):
        return obj.order.status != "pending"

    def get_escrow_status(self, obj):
        escrow = EscrowWallet.objects.filter(payment__order=obj.order,beneficiary=obj.seller).first()
        return escrow.status if escrow else None

    def get_escrow_amount(self, obj):
        escrow = EscrowWallet.objects.filter(payment__order=obj.order,beneficiary=obj.seller).first()
        return escrow.amount if escrow else Decimal("0.00")

    def get_commission(self, obj):
        return (obj.subtotal * Decimal("10")) / Decimal("100")

    def get_seller_amount(self, obj):
        return obj.subtotal - self.get_commission(obj)

    def get_delivery_status(self, obj):
        delivery = obj.order.deliveries.filter(seller=obj.seller).first()
        return delivery.status if delivery else "pending"


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

    seller_orders = SellerOrderSerializer(many=True, read_only=True)  # ✅ ADD THIS

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
            'seller_orders',   # ✅ MUST BE HERE
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