from rest_framework import serializers

from .models import PsychologyProfile


class PsychologyProfileSerializer(serializers.ModelSerializer):
    bigFive = serializers.SerializerMethodField()

    class Meta:
        model = PsychologyProfile
        fields = [
            "bigFive",
            "interests",
            "summary",
            "created_at",
            "updated_at",
        ]

    def get_bigFive(self, obj):
        return {
            "openness": obj.openness,
            "conscientiousness": obj.conscientiousness,
            "extraversion": obj.extraversion,
            "agreeableness": obj.agreeableness,
            "neuroticism": obj.neuroticism,
        }