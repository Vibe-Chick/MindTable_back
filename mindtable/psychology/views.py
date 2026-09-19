from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PsychologyProfile, PsychologyQuestionProgress
from .serializers import PsychologyProfileSerializer


User = get_user_model()

class QuestionGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        progress, created = PsychologyQuestionProgress.objects.get_or_create(
            user=user
        )

        question_count = progress.question_count

        questions = [
            # "새로운 사람들과 만나는 것을 좋아하나요?",
            # "계획을 세우고 그대로 실행하는 편인가요?",
            # "스트레스를 받으면 주로 어떻게 해결하나요?",
            # "친구들과 있을 때 주로 어떤 역할을 하나요?",
            # "새로운 환경에 적응하는 데 시간이 얼마나 걸리나요?",
        ]

        question_index = question_count % len(questions)

        question = questions[question_index]

        progress.question_count += 1
        progress.save()

        return Response(
            {
                "question_number": progress.question_count,
                "question": question,
            }
        )
        
class CheckAnswerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        answer = request.data.get("answer")

        if not answer:
            return Response(
                {
                    "detail": "answer가 필요합니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "valid": True,
                "answer": answer,
            },
            status=status.HTTP_200_OK,
        )
        
class AnalyzeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        answers = request.data.get("answers", [])

        if not answers:
            return Response(
                {
                    "detail": "answers가 필요합니다.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = {
            "bigFive": {
                "openness": 0,
                "conscientiousness": 0,
                "extraversion": 0,
                "agreeableness": 0,
                "neuroticism": 0,
            },
            "interests": [],
            "summary": "",
        }

        return Response(
            result,
            status=status.HTTP_200_OK,
        )
        
class PsychologyProfileSaveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {
                    "detail": "사용자를 찾을 수 없습니다.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        big_five = request.data.get("bigFive", {})
        interests = request.data.get("interests", [])
        summary = request.data.get("summary", "")

        profile, created = PsychologyProfile.objects.update_or_create(
            user=user,
            defaults={
                "openness": big_five.get("openness", 0),
                "conscientiousness": big_five.get(
                    "conscientiousness",
                    0,
                ),
                "extraversion": big_five.get("extraversion", 0),
                "agreeableness": big_five.get("agreeableness", 0),
                "neuroticism": big_five.get("neuroticism", 0),
                "interests": interests,
                "summary": summary,
            },
        )

        serializer = PsychologyProfileSerializer(profile)

        return Response(
            serializer.data,
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )