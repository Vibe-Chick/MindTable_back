from django.urls import path

from .views import (
    AnalyzeAPIView,
    CheckAnswerAPIView,
    QuestionGenerateAPIView,
    PsychologyProfileSaveAPIView,
)

urlpatterns = [
    path(
        "psychology/questions/",
        QuestionGenerateAPIView.as_view(),
    ),
    path(
        "psychology/check-answer/",
        CheckAnswerAPIView.as_view(),
    ),
    path(
        "psychology/analyze/",
        AnalyzeAPIView.as_view(),
    ),
    path(
        "users/<int:user_id>/profile/",
        PsychologyProfileSaveAPIView.as_view(),
    ),
]