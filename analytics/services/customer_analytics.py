from orders.models import Order
from payments.models import Payment
from wallet.models import Wallet


def get_customer_dashboard_stats(user):
    return {
        "orders": {
            "total": Order.objects.filter(customer=user).count(),
            "delivered": Order.objects.filter(customer=user, status="delivered").count(),
        },

        "payments": {
            "total_spent": Payment.objects.filter(
                user=user,
                status="completed"
            ).aggregate(total=Sum("amount"))["total"] or 0,
        },

        "wallet": get_wallet(user),
    }


def get_wallet(user):
    wallet = Wallet.objects.filter(user=user).first()

    if not wallet:
        return {
            "balance": 0,
            "earned": 0,
            "withdrawn": 0,
        }

    return {
        "balance": wallet.balance,
        "earned": wallet.total_earnings,
        "withdrawn": wallet.total_withdrawn,
    }