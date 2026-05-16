from django.contrib import admin
from .models import Product, ProductImage, ProductReview,Banner,AppVersion,Favorite




admin.site.register(AppVersion)
admin.site.register(Banner)
admin.site.register(Favorite)
 

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ("customer", "rating", "comment", "created_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "shop",
        "price",
        "stock",
        "is_active",
        "rating",
        "total_reviews",
        "created_at",
    )

    search_fields = (
        "name",
        "sku",
        "slug",
        "shop__name",
    )

    list_filter = (
        "is_active",
        "shop",
        "created_at",
        "discount_percentage",
    )

    ordering = ("-created_at",)

    prepopulated_fields = {"slug": ("name",)}

    autocomplete_fields = ("shop",)

    list_editable = ("price", "stock", "is_active")

    inlines = [ProductImageInline, ProductReviewInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "is_primary",
        "created_at",
    )

    search_fields = (
        "product__name",
    )

    list_filter = (
        "is_primary",
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "customer",
        "rating",
        "created_at",
    )

    search_fields = (
        "product__name",
        "customer__first_name",
        "customer__last_name",
    )

    list_filter = (
        "rating",
        "created_at",
    )