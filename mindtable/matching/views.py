from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MatchTable
# from .services import ai


User = get_user_model()


# =========================================================
# 사용자 정보 관련 함수
# =========================================================

def get_user_name(user):
    return (
        getattr(user, "name", None)
        or getattr(user, "username", "")
    )


def get_user_school(user):
    return getattr(user, "school", "")


def get_user_major(user):
    return getattr(user, "major", "")


def get_user_interests(user):
    """
    PsychologyProfile이 존재하면 interests 가져오기
    없으면 빈 배열 반환
    """
    try:
        return user.psychology_profile.interests
    except Exception:
        return []


def user_data(user, host=None):
    return {
        "id": user.id,
        "name": get_user_name(user),
        "major": get_user_major(user),
        "school": get_user_school(user),
        "interests": get_user_interests(user),
        "isHost": (
            user.id == host.id
            if host is not None
            else False
        ),
    }


# =========================================================
# slot -> datetime 변환
#
# 예:
# 2026-09-30-lunch
# 2026-09-30-dinner
# =========================================================

def convert_slot_to_datetime(slot):
    date_string, meal_type = slot.rsplit("-", 1)

    if meal_type == "lunch":
        time_string = "12:00:00"

    elif meal_type == "dinner":
        time_string = "18:30:00"

    else:
        raise ValueError("지원하지 않는 시간대입니다.")

    meal_at = datetime.fromisoformat(
        f"{date_string}T{time_string}"
    )

    return timezone.make_aware(meal_at)


# =========================================================
# 매칭 신청
#
# POST /api/match/request/
#
# Request
#
# {
#     "userId": 12,
#     "slots": ["2026-09-30-lunch"],
#     "sameSchoolOnly": false,
#     "capacity": 4
# }
# =========================================================

class MatchRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("userId")
        slots = request.data.get("slots", [])
        same_school_only = request.data.get(
            "sameSchoolOnly",
            False,
        )
        capacity = request.data.get("capacity")

        # -------------------------
        # userId 검사
        # -------------------------

        if user_id is None:
            return Response(
                {
                    "detail": "userId가 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(
                id=user_id
            )

        except User.DoesNotExist:
            return Response(
                {
                    "detail": "사용자를 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------
        # slots 검사
        # -------------------------

        if not isinstance(slots, list):
            return Response(
                {
                    "detail": "slots는 배열이어야 합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not slots:
            return Response(
                {
                    "detail": "slots가 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------
        # capacity 검사
        # -------------------------

        if capacity is None:
            return Response(
                {
                    "detail": "capacity가 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            capacity = int(capacity)

        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "capacity는 숫자여야 합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if capacity < 2:
            return Response(
                {
                    "detail": "capacity는 최소 2 이상이어야 합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 현재는 첫 번째 slot 사용
        slot = slots[0]

        try:
            meal_at = convert_slot_to_datetime(
                slot
            )

        except ValueError as e:
            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------
        # 테이블 생성
        # -------------------------

        table = MatchTable.objects.create(
            host=user,
            meal_at=meal_at,
            capacity=capacity,
            same_school_only=same_school_only,
            status="open",
        )

        # 방 만든 사람은 자동 참가
        table.members.add(user)

        return Response(
            {
                "userId": user.id,
                "slots": slots,
                "sameSchoolOnly": same_school_only,
                "capacity": capacity,
                "matchId": table.match_id,
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# 매칭 결과 조회
#
# GET /api/match/<match_id>/
# =========================================================

class MatchResultAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):

        try:
            table = MatchTable.objects.get(
                match_id=match_id
            )

        except MatchTable.DoesNotExist:
            return Response(
                {
                    "detail": "테이블을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        members = []

        for member in table.members.all():

            member_info = user_data(
                member,
                table.host,
            )

            members.append(
                member_info
            )

        result = {
            "id": table.match_id,
            "hostId": table.host_id,
            "mealAt": table.meal_at.isoformat(),
            "capacity": table.capacity,
            "sameSchoolOnly": table.same_school_only,
            "members": members,
            "reason": table.reason,
            "scores": table.scores,
            "tiebreakers": table.tiebreakers,
        }

        return Response(
            {
                "status": table.status,
                "result": result,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# 열린 테이블 목록
#
# GET /api/match/open/
# =========================================================

class OpenMatchTableAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        tables = MatchTable.objects.filter(
            status="open"
        ).order_by(
            "meal_at"
        )

        result = []

        for table in tables:

            result.append(
                {
                    "id": table.match_id,

                    "mealAt": (
                        table.meal_at.isoformat()
                    ),

                    "capacity": table.capacity,

                    "memberCount": (
                        table.members.count()
                    ),

                    "sameSchoolOnly": (
                        table.same_school_only
                    ),

                    "host": {
                        "name": get_user_name(
                            table.host
                        ),

                        "school": get_user_school(
                            table.host
                        ),

                        "major": get_user_major(
                            table.host
                        ),
                    },

                    "joined": (
                        table.members
                        .filter(
                            id=request.user.id
                        )
                        .exists()
                    ),
                }
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


# =========================================================
# 테이블 참가 신청
#
# POST /api/match/<match_id>/join/
#
# Body
# {}
# =========================================================

class MatchJoinAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):

        try:
            table = MatchTable.objects.get(
                match_id=match_id
            )

        except MatchTable.DoesNotExist:
            return Response(
                {
                    "detail": "테이블을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------
        # 이미 마감
        # -------------------------

        if table.status != "open":
            return Response(
                {
                    "detail": "이미 마감된 테이블입니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------
        # 이미 참가
        # -------------------------

        if table.members.filter(
            id=request.user.id
        ).exists():

            return Response(
                {
                    "detail": "이미 참여한 테이블입니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------
        # 정원 검사
        # -------------------------

        if table.members.count() >= table.capacity:

            return Response(
                {
                    "detail": "정원이 가득 찼습니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------
        # 같은 학교 옵션
        # -------------------------

        if table.same_school_only:

            host_school = get_user_school(
                table.host
            )

            user_school = get_user_school(
                request.user
            )

            if host_school != user_school:

                return Response(
                    {
                        "detail": (
                            "같은 학교 사용자만 "
                            "신청할 수 있습니다."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # -------------------------
        # 참가
        # -------------------------

        table.members.add(
            request.user
        )

        member_count = table.members.count()

        # -------------------------
        # 정원 마감
        # -------------------------

        if member_count >= table.capacity:

            table.status = "done"

            table.save(
                update_fields=[
                    "status",
                ]
            )

        return Response(
            {
                "status": table.status,
                "memberCount": member_count,
                "capacity": table.capacity,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# AI 추천 테이블
#
# GET /api/match/<match_id>/recommend/
# =========================================================

class MatchRecommendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):

        # -------------------------
        # 열린 테이블 조회
        # -------------------------

        tables = MatchTable.objects.filter(
            status="open"
        ).exclude(
            members=request.user
        )

        # -------------------------
        # AI 추천
        #
        # services.py의 ai() 사용
        # -------------------------

        recommendations = ai(
            user=request.user,
            tables=tables,
        )

        # AI 아직 구현 안 됨
        if recommendations is None:

            return Response(
                [],
                status=status.HTTP_200_OK,
            )

        result = []

        for recommendation in recommendations:

            table = recommendation["table"]

            result.append(
                {
                    "id": table.match_id,

                    "mealAt": (
                        table.meal_at.isoformat()
                    ),

                    "capacity": table.capacity,

                    "memberCount": (
                        table.members.count()
                    ),

                    "sameSchoolOnly": (
                        table.same_school_only
                    ),

                    "host": {
                        "name": get_user_name(
                            table.host
                        ),

                        "school": get_user_school(
                            table.host
                        ),

                        "major": get_user_major(
                            table.host
                        ),
                    },

                    "joined": (
                        table.members
                        .filter(
                            id=request.user.id
                        )
                        .exists()
                    ),

                    "fit": recommendation.get(
                        "fit"
                    ),

                    "fitReason": recommendation.get(
                        "fitReason",
                        "",
                    ),

                    "sharedInterests": (
                        recommendation.get(
                            "sharedInterests",
                            [],
                        )
                    ),
                }
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )