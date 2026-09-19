from django.contrib import admin

from .models import PsychologyProfile


@admin.register(PsychologyProfile)
class PsychologyProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
        "updated_at",
    )

    search_fields = (
        "user__email",
    )