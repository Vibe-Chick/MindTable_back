from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from matching.models import MatchTable

from .models import (
    RestaurantPreference,
    RestaurantRecommendation,
    RestaurantReservation,
)

from .services import restaurant_ai


# =========================================================
# 공통 선호 조건 계산
# =========================================================

def get_common_preferences(preferences):
    preferences = list(preferences)

    if not preferences:
        return None

    locations = [
        p.custom_location
        if p.location == "custom"
        else p.location
        for p in preferences
    ]

    prices = [
        p.price
        for p in preferences
    ]

    avoids = [
        p.avoid
        for p in preferences
        if p.avoid
    ]

    return {
        "location": locations[0] if locations else "",
        "price": prices[0] if prices else "mid",
        "avoid": avoids[0] if avoids else "",
    }


# =========================================================
# 식당 선호 조건 제출
#
# POST /api/match/<match_id>/restaurants/preferences/
#
# Request 예시
# {
#     "location": "custom",
#     "customLocation": "건대입구",
#     "price": "mid",
#     "avoid": "해산물"
# }
# =========================================================

class RestaurantPreferenceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        try:
            table = MatchTable.objects.get(
                match_id=match_id
            )

        except MatchTable.DoesNotExist:
            return Response(
                {
                    "detail": "매칭 테이블을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 해당 테이블 멤버인지 확인
        if not table.members.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "해당 테이블의 멤버가 아닙니다."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        location = request.data.get("location")

        custom_location = request.data.get(
            "customLocation",
            "",
        )

        price = request.data.get(
            "price",
            "mid",
        )

        avoid = request.data.get(
            "avoid",
            "",
        )

        if not location:
            return Response(
                {
                    "detail": "location이 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            location == "custom"
            and not custom_location
        ):
            return Response(
                {
                    "detail": "customLocation이 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if price not in ["low", "mid", "high"]:
            return Response(
                {
                    "detail": "price는 low, mid, high 중 하나여야 합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        RestaurantPreference.objects.update_or_create(
            table=table,
            user=request.user,
            defaults={
                "location": location,
                "custom_location": custom_location,
                "price": price,
                "avoid": avoid,
            },
        )

        submitted = (
            table.restaurant_preferences.count()
        )

        total = (
            table.members.count()
        )

        common = get_common_preferences(
            table.restaurant_preferences.all()
        )

        return Response(
            {
                "submitted": submitted,
                "total": total,
                "common": common,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# 식당 추천 결과 조회
#
# GET /api/match/<match_id>/restaurants/
#
# 아직 모두 제출하지 않았으면
#
# {
#     "status": "waiting",
#     "submitted": 2,
#     "total": 4,
#     ...
# }
#
# 모두 제출 + AI 결과가 있으면
#
# {
#     "status": "done",
#     ...
# }
# =========================================================

class RestaurantRecommendationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        try:
            table = MatchTable.objects.get(
                match_id=match_id
            )

        except MatchTable.DoesNotExist:
            return Response(
                {
                    "detail": "매칭 테이블을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not table.members.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "해당 테이블의 멤버가 아닙니다."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        preferences = (
            table.restaurant_preferences.all()
        )

        submitted = preferences.count()

        total = (
            table.members.count()
        )

        common = get_common_preferences(
            preferences
        )

        # -----------------------------------------
        # 아직 모든 멤버가 제출하지 않음
        # -----------------------------------------

        if submitted < total:
            return Response(
                {
                    "status": "waiting",
                    "submitted": submitted,
                    "total": total,
                    "common": common,
                    "source": None,
                    "restaurant": None,
                    "reason": None,
                },
                status=status.HTTP_200_OK,
            )

        # -----------------------------------------
        # 이미 추천 결과가 저장되어 있으면 반환
        # -----------------------------------------

        try:
            recommendation = (
                table.restaurant_recommendation
            )

            return Response(
                {
                    "status": "done",
                    "submitted": submitted,
                    "total": total,
                    "common": common,
                    "source": recommendation.source,
                    "restaurant": {
                        "id": (
                            recommendation.restaurant_id
                        ),
                        "name": recommendation.name,
                        "cuisine": (
                            recommendation.cuisine
                        ),
                        "walk": recommendation.walk,
                        "price": recommendation.price,
                        "discount": (
                            recommendation.discount
                        ),
                        "hue": recommendation.hue,
                        "lat": recommendation.lat,
                        "lng": recommendation.lng,
                    },
                    "reason": recommendation.reason,
                },
                status=status.HTTP_200_OK,
            )

        except RestaurantRecommendation.DoesNotExist:
            pass

        # -----------------------------------------
        # AI에 넘길 입력값 생성
        # -----------------------------------------

        ai_input = [
            {
                "userId": preference.user_id,
                "location": preference.location,
                "customLocation": (
                    preference.custom_location
                ),
                "price": preference.price,
                "avoid": preference.avoid,
            }
            for preference in preferences
        ]

        # -----------------------------------------
        # AI 식당 추천 호출
        # -----------------------------------------

        result = restaurant_ai(
            table=table,
            preferences=ai_input,
        )

        # 아직 AI 미구현
        if result is None:
            return Response(
                {
                    "status": "waiting",
                    "submitted": submitted,
                    "total": total,
                    "common": common,
                    "source": None,
                    "restaurant": None,
                    "reason": None,
                },
                status=status.HTTP_200_OK,
            )

        # -----------------------------------------
        # AI 응답 검증
        # -----------------------------------------

        restaurant = result.get(
            "restaurant"
        )

        if not restaurant:
            return Response(
                {
                    "detail": "AI 식당 추천 결과가 올바르지 않습니다."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        restaurant_id = restaurant.get("id")
        restaurant_name = restaurant.get("name")

        if not restaurant_id or not restaurant_name:
            return Response(
                {
                    "detail": "식당 id와 name이 필요합니다."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # -----------------------------------------
        # 추천 결과 DB 저장
        # -----------------------------------------

        recommendation = (
            RestaurantRecommendation.objects.create(
                table=table,

                restaurant_id=restaurant_id,

                name=restaurant_name,

                cuisine=restaurant.get(
                    "cuisine",
                    "",
                ),

                walk=restaurant.get(
                    "walk",
                    "",
                ),

                price=restaurant.get(
                    "price",
                    "",
                ),

                discount=restaurant.get(
                    "discount",
                    "",
                ),

                hue=restaurant.get(
                    "hue",
                    [],
                ),

                lat=restaurant.get(
                    "lat"
                ),

                lng=restaurant.get(
                    "lng"
                ),

                reason=result.get(
                    "reason",
                    "",
                ),

                source=result.get(
                    "source",
                    "",
                ),
            )
        )

        return Response(
            {
                "status": "done",
                "submitted": submitted,
                "total": total,
                "common": common,
                "source": recommendation.source,
                "restaurant": {
                    "id": (
                        recommendation.restaurant_id
                    ),
                    "name": recommendation.name,
                    "cuisine": (
                        recommendation.cuisine
                    ),
                    "walk": recommendation.walk,
                    "price": recommendation.price,
                    "discount": (
                        recommendation.discount
                    ),
                    "hue": recommendation.hue,
                    "lat": recommendation.lat,
                    "lng": recommendation.lng,
                },
                "reason": recommendation.reason,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# 식당 예약
#
# POST /api/match/<match_id>/reserve/
#
# Request
# {
#     "restaurantId": "r1"
# }
# =========================================================

class RestaurantReserveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id):
        restaurant_id = request.data.get(
            "restaurantId"
        )

        if not restaurant_id:
            return Response(
                {
                    "detail": "restaurantId가 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            table = MatchTable.objects.get(
                match_id=match_id
            )

        except MatchTable.DoesNotExist:
            return Response(
                {
                    "detail": "매칭 테이블을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 테이블 참가자 확인
        if not table.members.filter(
            id=request.user.id
        ).exists():
            return Response(
                {
                    "detail": "해당 테이블의 멤버가 아닙니다."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            restaurant = (
                RestaurantRecommendation.objects.get(
                    table=table,
                    restaurant_id=restaurant_id,
                )
            )

        except RestaurantRecommendation.DoesNotExist:
            return Response(
                {
                    "detail": "추천 식당을 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------------------
        # 예약 생성
        #
        # 현재는 실제 외부 예약 API 호출이 아니라
        # DB에 예약 정보를 저장하는 단계
        # -----------------------------------------

        reservation = (
            RestaurantReservation.objects.create(
                table=table,
                restaurant=restaurant,
                created_by=request.user,
            )
        )

        return Response(
            {
                "ok": True,
                "reservationId": (
                    reservation.reservation_id
                ),
            },
            status=status.HTTP_201_CREATED,
        )