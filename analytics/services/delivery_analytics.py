from delivery.models import Delivery, DeliveryPerson


def get_delivery_dashboard_stats(user):
    deliveries = Delivery.objects.all()

    return {
        "deliveries": {
            "total": deliveries.count(),
            "delivered": deliveries.filter(status="delivered").count(),
            "failed": deliveries.filter(status="failed").count(),
            "in_transit": deliveries.filter(status="in_transit").count(),
        },

        "drivers": {
            "total": DeliveryPerson.objects.count(),
            "active": DeliveryPerson.objects.filter(status="active").count(),
            "busy": DeliveryPerson.objects.filter(status="busy").count(),
        },
    }