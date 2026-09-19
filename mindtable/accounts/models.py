from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)

    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    school_email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
    )

    school_name = models.CharField(
        max_length=100,
        blank=True,
    )

    is_school_verified = models.BooleanField(default=False)

    school_verified_at = models.DateTimeField(null=True, blank=True)


class SchoolEmailVerificationCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    email = models.EmailField()

    code = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)

    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.code}"