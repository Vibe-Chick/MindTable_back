from django.contrib import admin

from .models import MatchTable


@admin.register(MatchTable)
class MatchTableAdmin(admin.ModelAdmin):
    list_display = (
        "match_id",
        "host",
        "meal_at",
        "capacity",
        "member_count",
        "same_school_only",
        "status",
        "created_at",
    )

    search_fields = (
        "match_id",
        "host__email",
    )

    list_filter = (
        "status",
        "same_school_only",
    )

    filter_horizontal = (
        "members",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "현재 인원"