from django.shortcuts import render

from django.conf import settings
from django.contrib.auth import get_user_model

from google.auth.transport import requests
from google.oauth2 import id_token

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class GoogleLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        google_token = request.data.get("credential")

        if not google_token:
            return Response(
                {"error": "Google credential이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = id_token.verify_oauth2_token(
                google_token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )

        except ValueError:
            return Response(
                {"error": "유효하지 않은 Google 토큰입니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        picture = idinfo.get("picture", "")
        email_verified = idinfo.get("email_verified", False)

        if not email or not email_verified:
            return Response(
                {"error": "인증된 Google 이메일이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": name,
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.first_name,
                    "picture": picture,
                    "google_id": google_id,
                },
                "created": created,
            },
            status=status.HTTP_200_OK,
        )