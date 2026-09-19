from django.contrib import admin

from .models import (
    PsychologyProfile,
    PsychologyQuestionProgress,
    PsychologyQuestionHistory,
    PsychologyAnalysisResult,
)


@admin.register(PsychologyProfile)
class PsychologyProfileAdmin(admin.ModelAdmin):
    list_display = (
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

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(PsychologyQuestionProgress)
class PsychologyQuestionProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "question_count",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(PsychologyQuestionHistory)
class PsychologyQuestionHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "question_id",
        "question",
        "answer",
        "created_at",
    )

    search_fields = (
        "user__email",
        "question_id",
        "question",
        "answer",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )
    
@admin.register(PsychologyAnalysisResult)
class PsychologyAnalysisResultAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
        "valid",
        "created_at",
    )

    search_fields = (
        "user__email",
        "summary",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-created_at",
    )