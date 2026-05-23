from django.contrib import admin
from .models import (
    EventCategory,
    Event,
    EventTicketType,
    Ticket,
    EventImage,
    TicketCheckIn,
    TicketItem,
)


admin.site.register(TicketItem)


# =========================
# INLINE MODELS
# =========================
class EventTicketTypeInline(admin.TabularInline):
    model = EventTicketType
    extra = 1


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1


# =========================
# EVENT CATEGORY ADMIN
# =========================
@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


# =========================
# EVENT ADMIN
# =========================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'organizer',
        'category',
        'event_date',
        'city',
        'district',
        'status',
        'is_featured',
        'created_at',
    ]

    list_filter = [
        'status',
        'is_featured',
        'event_date',
        'category',
        'city',
    ]

    search_fields = [
        'title',
        'venue',
        'city',
        'district',
        'organizer__username',
    ]

    readonly_fields = ['created_at']

    inlines = [EventTicketTypeInline, EventImageInline]


# =========================
# EVENT TICKET TYPE ADMIN
# =========================
@admin.register(EventTicketType)
class EventTicketTypeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'event',
        'name',
        'price',
        'total_seats',
        'available_seats',
    ]

    list_filter = ['name']

    search_fields = ['event__title']


# =========================
# TICKET ADMIN
# =========================
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number',
        'event',
        'purchase_group',
        'customer',
        'ticket_type',
        'seat_number',
        'quantity',
        'total_amount',
        'payment_status',
        'purchased_at',
    ]

    list_filter = [
        'payment_status',
        'ticket_type',
        'purchased_at',
    ]

    search_fields = [
        'ticket_number',
        'customer__username',
        'event__title',
    ]

    readonly_fields = [
        'ticket_number',
        'qr_code',
        'purchased_at',
    ]


# =========================
# EVENT IMAGE ADMIN
# =========================
@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'event']


# =========================
# CHECK-IN ADMIN
# =========================
@admin.register(TicketCheckIn)
class TicketCheckInAdmin(admin.ModelAdmin):
    list_display = [
        'ticket',
        'is_checked_in',
        'checked_in_by',
        'checked_in_at',
    ]

    list_filter = ['is_checked_in', 'checked_in_at']

    search_fields = [
        'ticket__ticket_number',
        'ticket__customer__username',
        'ticket__event__title',
    ]

    readonly_fields = ['checked_in_at']