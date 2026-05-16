from django.contrib import admin
from .models import Shop, ShopReview


class ShopReviewInline(admin.TabularInline):
    model = ShopReview
    extra = 0
    readonly_fields = ("customer", "rating", "comment", "created_at")


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "category",
        "status",
        "city",
        "district",
        "rating",
        "total_reviews",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "slug",
        "owner__first_name",
        "owner__last_name",
        "owner__phone_number",
        "category",
        "city",
        "district",
    )

    list_filter = (
        "status",
        "category",
        "city",
        "district",
        "is_active",
        "created_at",
    )

    ordering = ("-created_at",)

    prepopulated_fields = {"slug": ("name",)}

    autocomplete_fields = ("owner",)

    list_editable = ("status", "is_active")

    inlines = [ShopReviewInline]


@admin.register(ShopReview)
class ShopReviewAdmin(admin.ModelAdmin):
    list_display = (
        "shop",
        "customer",
        "rating",
        "created_at",
    )

    search_fields = (
        "shop__name",
        "customer__first_name",
        "customer__last_name",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    ordering = ("-created_at",)