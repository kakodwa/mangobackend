from django.db.models import Sum
from realestate.models import Property, PropertyUnlock


def get_property_dashboard_stats(user):
    properties = Property.objects.filter(owner=user)

    unlocks = PropertyUnlock.objects.filter(property__owner=user)

    total_unlock_income = unlocks.aggregate(
        total=Sum("unlock_fee")
    )["total"] or 0

    most_viewed = properties.order_by("-view_count")[:5]

    return {
        "properties": {
            "total": properties.count(),
            "available": properties.filter(status="available").count(),
            "sold": properties.filter(status="sold").count(),
        },

        "views": {
            "total": sum(p.view_count for p in properties),
        },

        "revenue": {
            "unlock_income": total_unlock_income,
        },

        "top_properties": [
            {
                "title": p.title,
                "views": p.view_count
            }
            for p in most_viewed
        ],
    }