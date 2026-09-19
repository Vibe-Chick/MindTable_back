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


class SchoolVerification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school_verification",
    )

    school_email = models.EmailField(unique=True)

    school_name = models.CharField(
        max_length=100,
        blank=True,
    )

    verified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.school_email}"


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