from django.urls import path

from .views import (
    MatchJoinAPIView,
    MatchRecommendAPIView,
    MatchRequestAPIView,
    MatchResultAPIView,
    OpenMatchTableAPIView,
)


urlpatterns = [
    path(
        "match/request/",
        MatchRequestAPIView.as_view(),
        name="match-request",
    ),

    path(
        "match/open/",
        OpenMatchTableAPIView.as_view(),
        name="match-open",
    ),

    path(
        "match/<str:match_id>/join/",
        MatchJoinAPIView.as_view(),
        name="match-join",
    ),

    path(
        "match/<str:match_id>/recommend/",
        MatchRecommendAPIView.as_view(),
        name="match-recommend",
    ),

    path(
        "match/<str:match_id>/",
        MatchResultAPIView.as_view(),
        name="match-result",
    ),
]