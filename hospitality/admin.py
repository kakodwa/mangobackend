from django.contrib import admin
from .models import (
    Amenity,
    Lodge,
    LodgeImage,
    Room,
    Booking,
    Review,
)


# =========================
# INLINE MODELS
# =========================

class LodgeImageInline(admin.TabularInline):
    model = LodgeImage
    extra = 1


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


# =========================
# AMENITY ADMIN
# =========================

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )

    search_fields = (
        'name',
    )


# =========================
# LODGE ADMIN
# =========================

@admin.register(Lodge)
class LodgeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'lodge_type',
        'owner',
        'district',
        'city',
        'phone_number',
        'is_verified',
        'is_active',
        'created_at',
    )

    list_filter = (
        'lodge_type',
        'district',
        'city',
        'is_verified',
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'city',
        'district',
        'owner__username',
        'owner__email',
        'phone_number',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    autocomplete_fields = (
        'owner',
    )

    filter_horizontal = (
        'amenities',
    )

    inlines = [
        LodgeImageInline,
        RoomInline,
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'owner',
                'name',
                'lodge_type',
                'description',
            )
        }),

        ('Contact Information', {
            'fields': (
                'phone_number',
                'email',
            )
        }),

        ('Location', {
            'fields': (
                'address',
                'city',
                'district',
                'latitude',
                'longitude',
            )
        }),

        ('Booking Information', {
            'fields': (
                'check_in_time',
                'check_out_time',
            )
        }),

        ('Amenities', {
            'fields': (
                'amenities',
            )
        }),

        ('Status', {
            'fields': (
                'is_verified',
                'is_active',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


# =========================
# LODGE IMAGE ADMIN
# =========================

@admin.register(LodgeImage)
class LodgeImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'lodge',
        'is_primary',
        'created_at',
    )

    list_filter = (
        'is_primary',
        'created_at',
    )

    search_fields = (
        'lodge__name',
    )


# =========================
# ROOM ADMIN
# =========================

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'lodge',
        'room_number',
        'room_type',
        'price_per_night',
        'capacity',
        'is_available',
        'created_at',
    )

    list_filter = (
        'room_type',
        'is_available',
        'has_wifi',
        'has_tv',
        'has_ac',
        'has_breakfast',
    )

    search_fields = (
        'lodge__name',
        'room_number',
        'title',
    )

    readonly_fields = (
        'created_at',
    )

    autocomplete_fields = (
        'lodge',
    )

    fieldsets = (
        ('Room Information', {
            'fields': (
                'lodge',
                'room_type',
                'room_number',
                'title',
                'description',
            )
        }),

        ('Pricing', {
            'fields': (
                'price_per_night',
            )
        }),

        ('Capacity', {
            'fields': (
                'capacity',
                'total_rooms',
            )
        }),

        ('Features', {
            'fields': (
                'has_wifi',
                'has_tv',
                'has_ac',
                'has_breakfast',
            )
        }),

        ('Availability', {
            'fields': (
                'is_available',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
            )
        }),
    )


# =========================
# BOOKING ADMIN
# =========================

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'booking_reference',
        'customer',
        'lodge',
        'room',
        'check_in_date',
        'check_out_date',
        'total_amount',
        'booking_status',
        'payment_status',
        'created_at',
    )

    list_filter = (
        'booking_status',
        'payment_status',
        'created_at',
        'check_in_date',
        'check_out_date',
    )

    search_fields = (
        'booking_reference',
        'customer__username',
        'customer__email',
        'lodge__name',
    )

    readonly_fields = (
        'booking_reference',
        'subtotal',
        'service_fee',
        'total_amount',
        'total_nights',
        'created_at',
        'updated_at',
    )

    autocomplete_fields = (
        'customer',
        'lodge',
        'room',
    )

    fieldsets = (
        ('Booking Information', {
            'fields': (
                'booking_reference',
                'customer',
                'lodge',
                'room',
            )
        }),

        ('Stay Information', {
            'fields': (
                'check_in_date',
                'check_out_date',
                'adults',
                'children',
                'total_nights',
            )
        }),

        ('Pricing', {
            'fields': (
                'subtotal',
                'service_fee',
                'total_amount',
            )
        }),

        ('Status', {
            'fields': (
                'booking_status',
                'payment_status',
            )
        }),

        ('Additional Information', {
            'fields': (
                'special_requests',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )


# =========================
# REVIEW ADMIN
# =========================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'lodge',
        'rating',
        'created_at',
    )

    list_filter = (
        'rating',
        'created_at',
    )

    search_fields = (
        'customer__username',
        'lodge__name',
        'comment',
    )

    readonly_fields = (
        'created_at',
    )

    autocomplete_fields = (
        'customer',
        'lodge',
    )