from delivery.models import Delivery
from django.db import transaction
from products.models import Product, ProductVariant # ✅ Critical: Added ProductVariant import
from django.db.models import F
from collections import defaultdict
from payments.core.escrow import EscrowService
from orders.models import SellerOrder
from decimal import Decimal
import random
import string


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class OrderService:

    @staticmethod
    def process_order(payment, company_wallet):

        order = payment.order

        with transaction.atomic():

            # ========================================================
            # 1. STOCK DEDUCTION (UPDATED TO HANDLE VARIANTS CORRECTLY)
            # ========================================================
            # ✅ Added product_variant to select_related to optimize DB queries
            for item in order.items.select_related("product", "product_variant"):
                
                if item.product_variant:
                    # 🔹 If a variant was purchased, deduct stock from that specific variant row
                    updated = ProductVariant.objects.filter(
                        id=item.product_variant.id,
                        stock__gte=item.quantity
                    ).update(stock=F("stock") - item.quantity)

                    if updated == 0:
                        raise Exception(f"Out of stock for selected option on: {item.product.name}")
                else:
                    # 🔹 Fallback: if no variant is attached, deduct from global product pool
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

                # create delivery per seller
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

            # =========================
            # 4. HOLD ESCROW PER SELLER
            # =========================
            for seller_order in seller_orders:
                EscrowService.hold(
                    payment=payment,
                    beneficiary=seller_order.seller,
                    amount=seller_order.subtotal,
                    commission_rate=10,
                    escrow_type="order"
                )