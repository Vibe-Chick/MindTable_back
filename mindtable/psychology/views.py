from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class QuestionGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        questions = [
            {
                "id": "q1",
                "type": "open",
                "trait": "extraversion",
                "title": (
                    "낯선 사람들이랑 있을 때랑 혼자 있을 때, "
                    "에너지가 언제 더 차오르는 편이야?"
                ),
                "hint": (
                    "정답은 없어, 최근 예시 들어서 "
                    "편하게 적어줘"
                ),
            },
            {
                "id": "q2",
                "type": "open",
                "trait": "openness",
                "title": (
                    "요즘 새롭게 관심 생긴 주제나 "
                    "해본 경험 있어?"
                ),
                "hint": (
                    "아주 작은 거라도 좋아. "
                    "왜 끌렸는지도 알려줘"
                ),
            },
            {
                "id": "q3",
                "type": "open",
                "trait": "agreeableness",
                "title": (
                    "낯선 사람들이랑 대화하다가 "
                    "어색해지는 느낌은 어떻게 풀어가는 편이야?"
                ),
                "hint": "너만의 대화 스타일이 궁금해",
            },
            {
                "id": "q4",
                "type": "choice",
                "trait": "calibration",
                "title": (
                    "마지막으로, 그룹 안에 있을 때 "
                    "너는 어느 쪽에 더 가까워?"
                ),
                "hint": "정답 없어, 더 편한 쪽으로 골라줘",
                "options": [
                    {
                        "value": "leader",
                        "label": "이끄는 역할이 편해",
                    },
                    {
                        "value": "harmonizer",
                        "label": "분위기 맞추는 게 편해",
                    },
                ],
            },
        ]

        return Response({
            "questions": questions
        }) 
class CheckAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question_id = request.data.get("questionId")
        question = request.data.get("question")
        answer = request.data.get("answer")

        if not question_id:
            return Response(
                {"error": "questionId가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not question:
            return Response(
                {"error": "question이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not answer:
            return Response(
                {"error": "answer가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO:
        # 나중에 AI 모델에게 question + answer를 전달
        # AI가 답변의 충분성을 판단하도록 변경

        if len(answer.strip()) < 15:
            return Response({
                "needFollowUp": True,
                "followUpQuestion":
                    "조금 더 구체적인 상황이나 경험을 말해줄 수 있어?",
            })

        return Response({
            "needFollowUp": False,
            "followUpQuestion": None,
        })

class AnalyzeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        answers = request.data.get("answers")
        follow_ups = request.data.get("followUps", [])

        if not answers:
            return Response(
                {"error": "answers가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO:
        # answers와 follow_ups를 실제 AI 모델에 전달
        # AI 결과로 아래 값을 생성해야 함

        result = {
            "bigFive": {
                "openness": 4,
                "conscientiousness": 3,
                "extraversion": 4,
                "agreeableness": 3,
                "neuroticism": 2,
            },
            "interests": [
                "필름카메라",
                "클라이밍",
                "전시 보기",
            ],
            "summary":
                "낯가림은 있지만 얘기 시작하면 잘 안 멈추는 타입",
        }

        return Response(result)
    
from .models import PsychologyProfile
from .serializers import PsychologyProfileSerializer


class PsychologyProfileSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):

        if request.user.id != user_id:
            return Response(
                {
                    "error":
                        "다른 사용자의 프로필을 수정할 수 없습니다."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        big_five = request.data.get("bigFive")
        interests = request.data.get("interests", [])
        summary = request.data.get("summary")

        if not big_five:
            return Response(
                {"error": "bigFive가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_traits = [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ]

        for trait in required_traits:
            if trait not in big_five:
                return Response(
                    {
                        "error":
                            f"bigFive.{trait} 값이 필요합니다."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not summary:
            return Response(
                {"error": "summary가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, created = (
            PsychologyProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    "openness":
                        big_five["openness"],
                    "conscientiousness":
                        big_five["conscientiousness"],
                    "extraversion":
                        big_five["extraversion"],
                    "agreeableness":
                        big_five["agreeableness"],
                    "neuroticism":
                        big_five["neuroticism"],
                    "interests": interests,
                    "summary": summary,
                },
            )
        )

        serializer = PsychologyProfileSerializer(profile)

        return Response(
            {
                "created": created,
                "profile": serializer.data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )
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