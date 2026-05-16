from django.contrib import admin
from .models import DeliveryPerson, Delivery, DeliveryRating

admin.site.register(DeliveryPerson)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "delivery_person",
        "status",
        "picked_up_at",
        "delivered_at",
        "created_at",
    )

    search_fields = (
        "order__order_number",
    )

    list_filter = (
        "status",
        "created_at",
        "picked_up_at",
        "delivered_at",
    )



@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = (
        "delivery",
        "customer",
        "rating",
        "created_at",
    )

    search_fields = (
        "customer__first_name",
        "customer__last_name",
        "delivery__order__order_number",
    )

    list_filter = (
        "rating",
        "created_at",
    )