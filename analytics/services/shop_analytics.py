from django.db.models import Sum, Count
from orders.models import Order, OrderItem
from products.models import Product


def get_shop_dashboard_stats(user):
    products = Product.objects.filter(shop__owner=user)

    order_items = OrderItem.objects.filter(product__shop__owner=user)

    total_revenue = order_items.aggregate(
        total=Sum("total_price")
    )["total"] or 0

    top_products = (
        order_items.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    orders = Order.objects.filter(items__product__shop__owner=user).distinct()

    return {
        "products": {
            "total": products.count(),
        },

        "orders": {
            "total": orders.count(),
            "pending": orders.filter(status="pending").count(),
            "delivered": orders.filter(status="delivered").count(),
        },

        "sales": {
            "total_revenue": total_revenue,
            "top_products": list(top_products),
        },
    }