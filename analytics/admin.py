# analytics/admin.py

from django.contrib import admin
from .models import AppEvent


@admin.register(AppEvent)
class AppEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_name",
        "device_type",
        "latitude",
        "longitude",
        "timestamp",
    )

    list_filter = (
        "event_name",
        "device_type",
        "timestamp",
    )

    search_fields = (
        "event_name",
        "device_type",
    )

    readonly_fields = (
        "timestamp",
    )

    ordering = ("-timestamp",)