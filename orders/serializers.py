from rest_framework import serializers
from .models import Order, OrderItem, SellerOrder
from decimal import Decimal, ROUND_HALF_UP
from products.serializers import ProductSerializer
from delivery.serializers import DeliverySerializer
from payments.models import EscrowWallet
from shops.models import Shop


class SellerOrderSerializer(serializers.ModelSerializer):

    shop_id = serializers.SerializerMethodField()
    shop_name = serializers.SerializerMethodField()
    shop_logo = serializers.SerializerMethodField()

    customer_paid = serializers.SerializerMethodField()
    escrow_status = serializers.SerializerMethodField()
    escrow_amount = serializers.SerializerMethodField()
    seller_amount = serializers.SerializerMethodField()
    commission = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = SellerOrder
        fields = [
            "id",
            "order",
            "seller",
            "shop_id",       
            "shop_name",    
            "shop_logo",   
            "subtotal",
            "customer_paid",
            "escrow_status",
            "escrow_amount",
            "seller_amount",
            "commission",
            "delivery_status",
            "items",
            "created_at",
        ]

    # =========================================================================
    # ROBUST SHOP RESOLUTION HELPERS
    # =========================================================================
    def _get_seller_shop(self, obj):
        """
        Safely locates the Shop instance for the seller.
        Tries direct model access first, then falls back to a query by owner.
        """
        try:
            if hasattr(obj.seller, 'shop'):
                return obj.seller.shop
            return Shop.objects.filter(owner=obj.seller).first()
        except Exception:
            return None

    def get_shop_id(self, obj):
        shop = self._get_seller_shop(obj)
        return shop.id if shop else None

    def get_shop_name(self, obj):
        shop = self._get_seller_shop(obj)
        if shop and getattr(shop, 'name', None):
            return shop.name
        return "Official Store"

    def get_shop_logo(self, obj):
        shop = self._get_seller_shop(obj)
        if shop and getattr(shop, 'logo', None) and shop.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(shop.logo.url)
            return shop.logo.url
        return None

    # =========================================================================
    # EXISTING BUSINESS LOGIC RESOLVERS
    # =========================================================================
    def get_items(self, obj):
        items = obj.order.items.filter(product__shop__owner=obj.seller)

        return [
            {
                "id": i.id,
                "product_name": i.product.name,
                "product_image": i.product.image.url if i.product.image else "",
                "variant_attributes": i.product_variant.attributes if i.product_variant else {},
                "quantity": i.quantity,
                "total_price": i.total_price,
            }
            for i in items
        ]

    def get_customer_paid(self, obj):
        return obj.order.status != "pending"

    def get_escrow_status(self, obj):
        escrow = EscrowWallet.objects.filter(payment__order=obj.order, beneficiary=obj.seller).first()
        return escrow.status if escrow else None

    def get_escrow_amount(self, obj):
        escrow = EscrowWallet.objects.filter(payment__order=obj.order, beneficiary=obj.seller).first()
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


# =========================================================================
# ORDER ITEM SERIALIZER
# =========================================================================
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    product_variant = serializers.SerializerMethodField()
    product_variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_id',
            'product_variant',
            'product_variant_id',
            'quantity',
            'unit_price',
            'total_price'
        ]
        read_only_fields = ['id', 'unit_price', 'total_price']

    def get_product_variant(self, obj):
        if obj.product_variant:
            return obj.product_variant.attributes 
        return None


# =========================================================================
# PARENT ORDER SERIALIZER
# =========================================================================
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    seller_orders = SellerOrderSerializer(many=True, read_only=True)

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
            'seller_orders',
            'created_at'
        ]


# =========================================================================
# ORDER CREATE SERIALIZER
# =========================================================================
class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True)
    delivery_address = serializers.CharField()
    lat = serializers.FloatField(required=False, allow_null=True)
    lng = serializers.FloatField(required=False, allow_null=True)
    delivery_phone = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        from .models import Order, OrderItem
        from products.models import Product, ProductVariant
        from decimal import Decimal

        user = self.context['request'].user
        items_data = self.initial_data.get('items', [])

        lat = round6(validated_data.pop('lat', None))
        lng = round6(validated_data.pop('lng', None))
        phone = validated_data.pop('delivery_phone', None)

        order = Order.objects.create(
            order_number=f"ORD-{user.id}-{Order.objects.count() + 1}",
            customer=user,
            delivery_address=validated_data['delivery_address'],
            delivery_latitude=lat,
            delivery_longitude=lng,
            delivery_phone_number=phone,
            subtotal=0,
            total_amount=0
        )

        subtotal = Decimal('0.00')

        for item in items_data:
            product = Product.objects.get(id=item['product_id'])
            qty = int(item['quantity'])

            if product.shop.owner == user:
                raise serializers.ValidationError(
                    f"You cannot order your own product: {product.name}"
                )

            variant_attributes = item.get('variant_attributes')
            variant = None
            
            if variant_attributes:
                variant = ProductVariant.objects.filter(
                    product=product,
                    attributes=variant_attributes
                ).first()

            unit_price = product.price
            total_price = unit_price * qty
            subtotal += total_price

            OrderItem.objects.create(
                order=order,
                product=product,
                product_variant=variant,
                quantity=qty,
                unit_price=unit_price,
                total_price=total_price
            )

        order.subtotal = subtotal
        order.total_amount = subtotal
        order.save()

        return order