from django.contrib import admin

from .models import (
    RestaurantPreference,
    RestaurantRecommendation,
    RestaurantReservation,
)


@admin.register(RestaurantPreference)
class RestaurantPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "table",
        "user",
        "location",
        "custom_location",
        "price",
        "avoid",
        "created_at",
    )

    search_fields = (
        "table__match_id",
        "user__email",
        "location",
        "custom_location",
    )

    list_filter = (
        "price",
    )


@admin.register(RestaurantRecommendation)
class RestaurantRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "table",
        "restaurant_id",
        "name",
        "cuisine",
        "price",
        "source",
        "created_at",
    )

    search_fields = (
        "table__match_id",
        "restaurant_id",
        "name",
    )


@admin.register(RestaurantReservation)
class RestaurantReservationAdmin(admin.ModelAdmin):
    list_display = (
        "reservation_id",
        "table",
        "restaurant",
        "created_by",
        "created_at",
    )

    search_fields = (
        "reservation_id",
        "table__match_id",
        "created_by__email",
    )

    readonly_fields = (
        "reservation_id",
        "created_at",
    )