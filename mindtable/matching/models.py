from django.conf import settings
from django.db import models
from django.utils import timezone


class MatchTable(models.Model):
    STATUS_CHOICES = (
        ("open", "모집 중"),
        ("done", "모집 완료"),
        ("cancelled", "취소"),
    )

    match_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
    )

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_match_tables",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_match_tables",
        blank=True,
    )

    meal_at = models.DateTimeField()

    capacity = models.PositiveIntegerField()

    same_school_only = models.BooleanField(
        default=False,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    reason = models.TextField(
        null=True,
        blank=True,
    )

    scores = models.JSONField(
        null=True,
        blank=True,
    )

    tiebreakers = models.JSONField(
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # 먼저 DB에 저장해서 pk를 만든다.
        super().save(*args, **kwargs)

        # 새 객체이고 match_id가 아직 없으면 자동 생성
        if is_new and not self.match_id:
            date = timezone.localdate().strftime("%Y%m%d")

            self.match_id = f"m_{date}_{self.pk:04d}"

            super().save(
                update_fields=["match_id"]
            )

    def __str__(self):
        return self.match_id or f"MatchTable {self.pk}"