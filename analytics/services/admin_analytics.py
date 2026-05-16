from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from users.models import User
from orders.models import Order
from payments.models import Payment
from delivery.models import Delivery
from wallet.models import WalletTransaction


def get_admin_dashboard_stats():
    return {
        "users": get_user_stats(),
        "orders": get_order_stats(),
        "revenue": get_revenue_stats(),
        "deliveries": get_delivery_stats(),
        "wallet": get_wallet_stats(),
    }


# ---------------- USERS ----------------
def get_user_stats():
    return {
        "total": User.objects.count(),
        "customers": User.objects.filter(user_type="customer").count(),
        "shop_owners": User.objects.filter(user_type="shop_owner").count(),
        "property_owners": User.objects.filter(user_type="property_owner").count(),
    }


# ---------------- ORDERS ----------------
def get_order_stats():
    return {
        "total": Order.objects.count(),
        "pending": Order.objects.filter(status="pending").count(),
        "processing": Order.objects.filter(status="processing").count(),
        "delivered": Order.objects.filter(status="delivered").count(),
        "cancelled": Order.objects.filter(status="cancelled").count(),
    }


# ---------------- REVENUE ----------------
def get_revenue_stats():
    today = timezone.now()
    last_30_days = today - timedelta(days=30)

    total_revenue = Payment.objects.filter(status="completed").aggregate(
        total=Sum("amount")
    )["total"] or 0

    monthly_revenue = Payment.objects.filter(
        status="completed",
        created_at__gte=last_30_days
    ).aggregate(total=Sum("amount"))["total"] or 0

    return {
        "total_revenue": total_revenue,
        "last_30_days": monthly_revenue,
    }


# ---------------- DELIVERY ----------------
def get_delivery_stats():
    return {
        "total": Delivery.objects.count(),
        "delivered": Delivery.objects.filter(status="delivered").count(),
        "failed": Delivery.objects.filter(status="failed").count(),
        "in_progress": Delivery.objects.exclude(status__in=["delivered", "failed"]).count(),
    }


# ---------------- WALLET ----------------
def get_wallet_stats():
    return {
        "transactions": WalletTransaction.objects.count(),
        "credits": WalletTransaction.objects.filter(transaction_type="credit").count(),
        "debits": WalletTransaction.objects.filter(transaction_type="debit").count(),
    }