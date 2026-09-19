import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from google.auth.transport import requests
from google.oauth2 import id_token

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from .models import SchoolEmailVerificationCode


User = get_user_model()

SCHOOL_CODE_EXPIRY_MINUTES = 10


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

        except ValueError as e:
            print("Google token verify error:", str(e))
            return Response(
                {"error": "유효하지 않은 Google 토큰입니다.",
                 "detail": str(e),
                },
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


class SchoolEmailVerificationRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        school_email = request.data.get("school_email")

        if not school_email:
            return Response(
                {"error": "school_email이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            User.objects.filter(school_email=school_email)
            .exclude(pk=request.user.pk)
            .exists()
        ):
            return Response(
                {"error": "이미 다른 계정에서 인증된 학교 이메일입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = f"{random.randint(0, 999999):06d}"

        SchoolEmailVerificationCode.objects.create(
            user=request.user,
            email=school_email,
            code=code,
        )

        send_mail(
            subject="[MindTable] 학교 이메일 인증 코드",
            message=f"인증 코드: {code} ({SCHOOL_CODE_EXPIRY_MINUTES}분 이내에 입력해주세요.)",
            from_email=None,
            recipient_list=[school_email],
        )

        return Response(
            {"message": "인증 코드가 발송되었습니다."},
            status=status.HTTP_200_OK,
        )


class SchoolEmailVerificationConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")

        if not code:
            return Response(
                {"error": "code가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification = (
            SchoolEmailVerificationCode.objects.filter(
                user=request.user,
                code=code,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not verification:
            return Response(
                {"error": "유효하지 않은 인증 코드입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = verification.created_at + timezone.timedelta(
            minutes=SCHOOL_CODE_EXPIRY_MINUTES
        )

        if timezone.now() > expires_at:
            return Response(
                {"error": "인증 코드가 만료되었습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        verification.is_used = True
        verification.save(update_fields=["is_used"])

        request.user.school_email = verification.email
        request.user.is_school_verified = True
        request.user.school_verified_at = timezone.now()
        request.user.save(
            update_fields=["school_email", "is_school_verified", "school_verified_at"]
        )

        return Response(
            {
                "message": "학교 인증이 완료되었습니다.",
                "school_email": request.user.school_email,
                "is_school_verified": request.user.is_school_verified,
            },
            status=status.HTTP_200_OK,
        )