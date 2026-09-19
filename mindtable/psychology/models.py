from django.conf import settings
from django.db import models


class PsychologyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="psychology_profile",
    )

    openness = models.FloatField(default=0)
    conscientiousness = models.FloatField(default=0)
    extraversion = models.FloatField(default=0)
    agreeableness = models.FloatField(default=0)
    neuroticism = models.FloatField(default=0)

    interests = models.JSONField(default=list, blank=True)

    summary = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} Psychology Profile"
    
class PsychologyQuestionProgress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="psychology_question_progress",
    )

    question_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.question_count}"
    
class PsychologyQuestionHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="psychology_question_histories",
    )

    question_id = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.question_id}"
    
class PsychologyAnalysisResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="psychology_analysis_results",
    )

    openness = models.IntegerField()
    conscientiousness = models.IntegerField()
    extraversion = models.IntegerField()
    agreeableness = models.IntegerField()
    neuroticism = models.IntegerField()

    interests = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True)

    valid = models.BooleanField(default=True)
    insufficient = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - Analysis {self.id}"