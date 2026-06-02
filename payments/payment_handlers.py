from decimal import Decimal
from collections import defaultdict

from django.db import transaction
from django.db.models import F

from products.models import Product
from delivery.models import Delivery
from wallet.models import (
    Wallet,
    WalletTransaction,
    CompanyWalletTransaction
)
from events.models import EventTicketType


# =========================================================
# ORDER HANDLER (MULTI-VENDOR SUPPORT)
# =========================================================
def handle_order(payment, company_wallet):

    with transaction.atomic():

        order = payment.order

        # -------------------------
        # STOCK DEDUCTION
        # -------------------------
        for item in order.items.select_related("product"):

            updated = Product.objects.filter(
                id=item.product.id,
                stock__gte=item.quantity
            ).update(
                stock=F("stock") - item.quantity
            )

            if updated == 0:
                raise Exception(
                    f"Not enough stock for {item.product.name}"
                )

        order.status = "confirmed"
        order.save()

        Delivery.objects.create(
            order=order,
            status="pending",
            customer_latitude=order.delivery_latitude,
            customer_longitude=order.delivery_longitude,
            delivery_address=order.delivery_address,
            delivery_phone_number=order.delivery_phone_number,
            delivery_code=generate_code()
        )

        commission_rate = Decimal("10.00")

        seller_totals = defaultdict(Decimal)

        for item in order.items.select_related(
            "product",
            "product__shop",
            "product__shop__owner"
        ):
            seller = item.product.shop.owner
            seller_totals[seller] += item.total_price

        company_total_commission = Decimal("0.00")

        for seller, subtotal in seller_totals.items():

            seller_wallet, _ = Wallet.objects.get_or_create(
                user=seller
            )

            commission = (subtotal * commission_rate) / Decimal("100")
            seller_amount = subtotal - commission

            company_total_commission += commission

            seller_before = seller_wallet.balance

            seller_wallet.balance += seller_amount
            seller_wallet.total_earnings += seller_amount
            seller_wallet.save()

            WalletTransaction.objects.create(
                wallet=seller_wallet,
                transaction_type="credit",
                source="order_payment",
                amount=seller_amount,
                transaction_rate=commission_rate,
                balance_before=seller_before,
                balance_after=seller_wallet.balance,
                reference=payment.payment_reference,
                description=f"Order {order.order_number}"
            )

        company_before = company_wallet.balance

        company_wallet.balance += company_total_commission
        company_wallet.total_earnings += company_total_commission
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source="order_commission",
            amount=company_total_commission,
            transaction_rate=commission_rate,
            balance_before=company_before,
            balance_after=company_wallet.balance,
            reference=payment.payment_reference,
            description=f"Commission from order {order.order_number}"
        )


# =========================================================
# PROPERTY UNLOCK HANDLER
# =========================================================
def handle_property_unlock(payment, company_wallet):

    with transaction.atomic():

        unlock = payment.property_unlock

        unlock.is_unlocked = True
        unlock.save()

        owner = unlock.property.owner

        owner_wallet, _ = Wallet.objects.get_or_create(
            user=owner
        )

        commission_rate = Decimal("15.00")

        owner_amount = payment.amount * (
            Decimal("1") - (commission_rate / Decimal("100"))
        )

        company_amount = payment.amount * (
            commission_rate / Decimal("100")
        )

        owner_before = owner_wallet.balance

        owner_wallet.balance += owner_amount
        owner_wallet.total_earnings += owner_amount
        owner_wallet.save()

        WalletTransaction.objects.create(
            wallet=owner_wallet,
            transaction_type="credit",
            source="property_unlock",
            amount=owner_amount,
            transaction_rate=commission_rate,
            balance_before=owner_before,
            balance_after=owner_wallet.balance,
            reference=payment.payment_reference,
            description=f"Property unlock #{unlock.id}"
        )

        company_before = company_wallet.balance

        company_wallet.balance += company_amount
        company_wallet.total_earnings += company_amount
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source="property_unlock_commission",
            amount=company_amount,
            transaction_rate=commission_rate,
            balance_before=company_before,
            balance_after=company_wallet.balance,
            reference=payment.payment_reference,
            description=f"Commission from property unlock #{unlock.id}"
        )


# =========================================================
# BOOKING HANDLER
# =========================================================
def handle_booking(payment, company_wallet):

    with transaction.atomic():

        booking = payment.booking

        if not booking:
            raise Exception("Booking not linked to payment")

        if booking.payment_status == "paid":
            return

        booking.booking_status = "confirmed"
        booking.payment_status = "paid"
        booking.save()

        owner = booking.room.lodge.owner

        owner_wallet, _ = Wallet.objects.get_or_create(user=owner)

        commission_rate = Decimal("10.00")

        owner_amount = payment.amount * (
            Decimal("1") - (commission_rate / Decimal("100"))
        )

        company_amount = payment.amount * (
            commission_rate / Decimal("100")
        )

        owner_before = owner_wallet.balance

        owner_wallet.balance += owner_amount
        owner_wallet.total_earnings += owner_amount
        owner_wallet.save()

        WalletTransaction.objects.create(
            wallet=owner_wallet,
            transaction_type="credit",
            source="booking_payment",
            amount=owner_amount,
            transaction_rate=commission_rate,
            balance_before=owner_before,
            balance_after=owner_wallet.balance,
            reference=payment.payment_reference,
            description=f"Booking #{booking.id}"
        )

        company_before = company_wallet.balance

        company_wallet.balance += company_amount
        company_wallet.total_earnings += company_amount
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source="booking_commission",
            amount=company_amount,
            transaction_rate=commission_rate,
            balance_before=company_before,
            balance_after=company_wallet.balance,
            reference=payment.payment_reference,
            description=f"Commission from booking #{booking.id}"
        )


# =========================================================
# TICKET HANDLER
# =========================================================
def handle_ticket(payment, company_wallet):

    with transaction.atomic():

        ticket = payment.ticket_purchase

        if not ticket:
            raise Exception("Ticket not linked to payment")

        if ticket.payment_status == "paid":
            return

        event = ticket.event

        # -------------------------
        # SEAT DEDUCTION
        # -------------------------
        for item in ticket.items.select_related("ticket_type"):

            updated = EventTicketType.objects.filter(
                id=item.ticket_type.id,
                available_seats__gte=item.quantity
            ).update(
                available_seats=F("available_seats") - item.quantity
            )

            if updated == 0:
                raise Exception(
                    f"Not enough seats for {item.ticket_type.name}"
                )

        ticket.payment_status = "paid"
        ticket.save()

        organizer = event.organizer

        organizer_wallet, _ = Wallet.objects.get_or_create(
            user=organizer
        )

        commission_rate = Decimal("10.00")

        organizer_amount = payment.amount * (
            Decimal("1") - (commission_rate / Decimal("100"))
        )

        company_amount = payment.amount * (
            commission_rate / Decimal("100")
        )

        before = organizer_wallet.balance

        organizer_wallet.balance += organizer_amount
        organizer_wallet.total_earnings += organizer_amount
        organizer_wallet.save()

        WalletTransaction.objects.create(
            wallet=organizer_wallet,
            transaction_type="credit",
            source="ticket_payment",
            amount=organizer_amount,
            transaction_rate=commission_rate,
            balance_before=before,
            balance_after=organizer_wallet.balance,
            reference=payment.payment_reference,
            description=f"Ticket sale - {event.title}"
        )

        company_before = company_wallet.balance

        company_wallet.balance += company_amount
        company_wallet.total_earnings += company_amount
        company_wallet.save()

        CompanyWalletTransaction.objects.create(
            wallet=company_wallet,
            transaction_type="credit",
            source="ticket_commission",
            amount=company_amount,
            transaction_rate=commission_rate,
            balance_before=company_before,
            balance_after=company_wallet.balance,
            reference=payment.payment_reference,
            description=f"Commission from ticket {event.title}"
        )


# =========================================================
# WALLET TOPUP
# =========================================================
def handle_wallet_topup(payment):

    with transaction.atomic():

        wallet, _ = Wallet.objects.get_or_create(
            user=payment.user
        )

        before = wallet.balance

        wallet.balance += payment.amount
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="credit",
            source="wallet_topup",
            amount=payment.amount,
            transaction_rate=Decimal("0.00"),
            balance_before=before,
            balance_after=wallet.balance,
            reference=payment.payment_reference,
            description="Wallet Topup"
        )