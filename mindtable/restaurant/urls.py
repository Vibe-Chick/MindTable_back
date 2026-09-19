from django.urls import path

from .views import (
    RestaurantPreferenceAPIView,
    RestaurantRecommendationAPIView,
    RestaurantReserveAPIView,
)


urlpatterns = [
    path(
        "match/<str:match_id>/restaurants/preferences/",
        RestaurantPreferenceAPIView.as_view(),
        name="restaurant-preferences",
    ),

    path(
        "match/<str:match_id>/restaurants/",
        RestaurantRecommendationAPIView.as_view(),
        name="restaurant-recommendation",
    ),

    path(
        "match/<str:match_id>/reserve/",
        RestaurantReserveAPIView.as_view(),
        name="restaurant-reserve",
    ),
]