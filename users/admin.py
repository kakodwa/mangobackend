from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "phone_number",
        "user_type",
        "is_verified",
        "is_active",
        "date_joined",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
    )

    list_filter = (
        "user_type",
        "is_verified",
        "is_active",
    )

    ordering = ("-date_joined",)

    list_editable = (
        "is_verified",
        "is_active",
        "user_type",
    )

    fieldsets = (
    (None, {
        "fields": ("username", "password")
    }),
    ("Personal Info", {
        "fields": (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "profile_picture",
            "bio",
            "user_type",
            "is_verified",
        )
    }),
    ("Permissions", {
        "fields": (
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
    }),
    ("Important dates", {
        "fields": ("last_login",)  # ❌ ONLY this
    }),
)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "city",
        "district",
        "is_default",
        "latitude",
        "longitude",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "city",
        "district",
    )

    list_filter = (
        "city",
        "district",
        "is_default",
    )

    ordering = ("-created_at",)