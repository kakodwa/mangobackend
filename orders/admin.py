from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("total_price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "status",
        "total_amount",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "order_number",
        "customer__first_name",
        "customer__last_name",
        "customer__phone_number",
    
    )

    list_filter = (
        "status",
        "created_at",
    )

    ordering = ("-created_at",)

    inlines = [OrderItemInline]

    list_editable = ("status",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
        "total_price",
    )

    search_fields = (
        "order__order_number",
        "product__name",
    )

    list_filter = (
        "product",
    )

    autocomplete_fields = ("order", "product")