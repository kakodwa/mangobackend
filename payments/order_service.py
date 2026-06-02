from decimal import Decimal
from collections import defaultdict
from django.db import transaction
from django.db.models import F

from products.models import Product
from delivery.models import SellerDelivery
from wallet.models import Wallet, WalletTransaction
from core.escrow import EscrowService


class OrderService:

    @staticmethod
    def process_order(payment):

        order = payment.order

        with transaction.atomic():

            # 1. stock deduction
            for item in order.items.select_related("product"):
                updated = Product.objects.filter(
                    id=item.product.id,
                    stock__gte=item.quantity
                ).update(stock=F("stock") - item.quantity)

                if updated == 0:
                    raise Exception(f"Out of stock {item.product.name}")

            order.status = "confirmed"
            order.save()

            # 2. create seller deliveries (IMPORTANT FIX)
            sellers = defaultdict(list)

            for item in order.items.select_related("product__shop__owner"):
                seller = item.product.shop.owner
                sellers[seller].append(item)

            for seller, items in sellers.items():

                SellerDelivery.objects.create(
                    order=order,
                    seller=seller,
                    status="pending",
                    delivery_code=OrderService.generate_code()
                )

            # 3. HOLD MONEY IN ESCROW
            EscrowService.hold(order, payment.amount)

    @staticmethod
    def generate_code():
        import random, string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))