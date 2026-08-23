import random
import string
from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from django.db.models import F

from delivery.models import Delivery
from products.models import Product, ProductVariant 
from payments.core.escrow import EscrowService
from orders.models import SellerOrder
from payments.models import CommissionRate


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class OrderService:

    @staticmethod
    def process_order(payment, company_wallet):

        order = payment.order

        with transaction.atomic():

            # ========================================================
            # 1. STOCK DEDUCTION (HANDLES VARIANTS AND GLOBAL POOL)
            # ========================================================
            for item in order.items.select_related("product", "product_variant"):
                
                if item.product_variant:
                    # Deduct stock from specific variant row
                    updated = ProductVariant.objects.filter(
                        id=item.product_variant.id,
                        stock__gte=item.quantity
                    ).update(stock=F("stock") - item.quantity)

                    if updated == 0:
                        raise Exception(f"Out of stock for selected option on: {item.product.name}")
                else:
                    # Fallback: deduct from main product stock
                    updated = Product.objects.filter(
                        id=item.product.id,
                        stock__gte=item.quantity
                    ).update(stock=F("stock") - item.quantity)

                    if updated == 0:
                        raise Exception(f"Out of stock {item.product.name}")

            order.status = "confirmed"
            order.save()

            # =========================
            # 2. GROUP ITEMS BY SELLER
            # =========================
            sellers = defaultdict(list)

            for item in order.items.select_related("product__shop__owner"):
                seller = item.product.shop.owner
                sellers[seller].append(item)

            # =========================
            # 3. CREATE SELLER ORDERS
            # =========================
            seller_orders = []

            for seller, items in sellers.items():

                subtotal = sum(i.total_price for i in items)

                seller_order = SellerOrder.objects.create(
                    order=order,
                    seller=seller,
                    subtotal=subtotal,
                )

                seller_orders.append(seller_order)

                # Create delivery per seller
                Delivery.objects.create(
                    order=order,
                    seller=seller,
                    status="pending",
                    customer_latitude=order.delivery_latitude,
                    customer_longitude=order.delivery_longitude,
                    delivery_address=order.delivery_address,
                    delivery_phone_number=order.delivery_phone_number,
                    delivery_code=generate_code()
                )

            # ========================================================
            # 4. HOLD ESCROW PER SELLER (DYNAMIC ADMIN COMMISSION)
            # ========================================================
            # Pull global order commission rate configured by admin
            global_rates = CommissionRate.get_rates()
            order_commission = global_rates.order_commission

            for seller_order in seller_orders:
                EscrowService.hold(
                    payment=payment,
                    beneficiary=seller_order.seller,
                    amount=seller_order.subtotal,
                    commission_rate=order_commission,
                    escrow_type="order"
                )