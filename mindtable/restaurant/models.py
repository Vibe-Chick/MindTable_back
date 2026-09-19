from django.conf import settings
from django.db import models


class RestaurantPreference(models.Model):
    PRICE_CHOICES = (
        ("low", "저렴"),
        ("mid", "보통"),
        ("high", "비쌈"),
    )

    table = models.ForeignKey(
        "matching.MatchTable",
        on_delete=models.CASCADE,
        related_name="restaurant_preferences",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restaurant_preferences",
    )

    location = models.CharField(
        max_length=100,
    )

    custom_location = models.CharField(
        max_length=255,
        blank=True,
    )

    price = models.CharField(
        max_length=20,
        choices=PRICE_CHOICES,
        default="mid",
    )

    avoid = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["table", "user"],
                name="unique_restaurant_preference_per_user",
            )
        ]

    def __str__(self):
        return f"{self.table.match_id} - {self.user}"
    
class RestaurantRecommendation(models.Model):
    table = models.OneToOneField(
        "matching.MatchTable",
        on_delete=models.CASCADE,
        related_name="restaurant_recommendation",
    )

    restaurant_id = models.CharField(
        max_length=100,
    )

    name = models.CharField(
        max_length=255,
    )

    cuisine = models.CharField(
        max_length=100,
        blank=True,
    )

    walk = models.CharField(
        max_length=100,
        blank=True,
    )

    price = models.CharField(
        max_length=20,
        blank=True,
    )

    discount = models.CharField(
        max_length=255,
        blank=True,
    )

    hue = models.JSONField(
        default=list,
        blank=True,
    )

    lat = models.FloatField(
        null=True,
        blank=True,
    )

    lng = models.FloatField(
        null=True,
        blank=True,
    )

    reason = models.TextField(
        blank=True,
    )

    source = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.table.match_id} - {self.name}"
    
class RestaurantReservation(models.Model):
    reservation_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
    )

    table = models.ForeignKey(
        "matching.MatchTable",
        on_delete=models.CASCADE,
        related_name="restaurant_reservations",
    )

    restaurant = models.ForeignKey(
        RestaurantRecommendation,
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="restaurant_reservations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and not self.reservation_id:
            self.reservation_id = f"rsv-{self.pk:04d}"

            super().save(
                update_fields=["reservation_id"]
            )

    def __str__(self):
        return self.reservation_id