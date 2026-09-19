from django.urls import path

from .views import (
    AnalyzeAPIView,
    CheckAnswerAPIView,
    PsychologyProfileSaveAPIView,
    QuestionGenerateAPIView,
)

urlpatterns = [
    path(
        "psychology/questions/",
        QuestionGenerateAPIView.as_view(),
        name="psychology-questions",
    ),
    path(
        "psychology/check-answer/",
        CheckAnswerAPIView.as_view(),
        name="psychology-check-answer",
    ),
    path(
        "psychology/analyze/",
        AnalyzeAPIView.as_view(),
        name="psychology-analyze",
    ),
    path(
        "users/<int:user_id>/profile/",
        PsychologyProfileSaveAPIView.as_view(),
        name="psychology-profile-save",
    ),
]