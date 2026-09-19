from django.urls import path

from .views import (
    GoogleLoginView,
    SchoolEmailVerificationConfirmView,
    SchoolEmailVerificationRequestView,
)


urlpatterns = [
    path("auth/google/", GoogleLoginView.as_view(), name="google-login"),
    path(
        "auth/school/send-code/",
        SchoolEmailVerificationRequestView.as_view(),
        name="school-send-code",
    ),
    path(
        "auth/school/verify-code/",
        SchoolEmailVerificationConfirmView.as_view(),
        name="school-verify-code",
    ),
]