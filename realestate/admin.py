from django.contrib import admin
from .models import Property, PropertyImage, PropertyUnlock


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class PropertyUnlockInline(admin.TabularInline):
    model = PropertyUnlock
    extra = 0
    readonly_fields = ("customer", "unlock_fee", "unlocked_at")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "property_type",
        "status",
        "price",
        "city",
        "district",
        "is_publicly_visible",
        "view_count",
        "created_at",
    )

    search_fields = (
        "title",
        "address",
        "city",
        "district",
        "owner__first_name",
        "owner__last_name",
        "owner__phone_number",
    )

    list_filter = (
        "property_type",
        "status",
        "city",
        "district",
        "is_publicly_visible",
        "created_at",
    )

    ordering = ("-created_at",)

    prepopulated_fields = {"slug": ("title",)}

    autocomplete_fields = ("owner",)

    list_editable = ("status", "is_publicly_visible")

    inlines = [PropertyImageInline, PropertyUnlockInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = (
        "property",
        "is_primary",
        "created_at",
    )

    search_fields = (
        "property__title",
        "property__city",
    )

    list_filter = (
        "is_primary",
        "created_at",
    )


@admin.register(PropertyUnlock)
class PropertyUnlockAdmin(admin.ModelAdmin):
    list_display = (
        "property",
        "customer",
        "unlock_fee",
        "unlocked_at",
    )

    search_fields = (
        "property__title",
        "customer__first_name",
        "customer__last_name",
    )

    list_filter = (
        "unlocked_at",
    )

    ordering = ("-unlocked_at",)