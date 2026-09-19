from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PsychologyProfile, PsychologyQuestionProgress, PsychologyQuestionHistory, PsychologyAnalysisResult
from .serializers import PsychologyProfileSerializer
from .manual_question_test import generate_base_questions
from .manual_analyze_test import analyze_personality
User = get_user_model()

class QuestionGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        progress, created = PsychologyQuestionProgress.objects.get_or_create(
            user=user
        )
        question_count = progress.question_count
        question_list = generate_base_questions() 
        questions = question_list  

        
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
        question_id = request.data.get("questionId")
        question = request.data.get("question")
        answer = request.data.get("answer")

        if not question_id:
            return Response(
                {"detail": "questionId가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not question:
            return Response(
                {"detail": "question이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not answer:
            return Response(
                {"detail": "answer가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = PsychologyQuestionHistory.objects.create(
            user=request.user,
            question_id=question_id,
            question=question,
            answer=answer,
        )

        return Response(
            {
                "valid": True,
                "history_id": history.id,
                "questionId": history.question_id,
                "question": history.question,
                "answer": history.answer,
            },
            status=status.HTTP_201_CREATED,
        )
        
User = get_user_model()

class AnalyzeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {
                    "detail": "user_id가 필요합니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(
                email=user_id
            )

        except User.DoesNotExist:
            return Response(
                {
                    "detail": "사용자를 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        histories = PsychologyQuestionHistory.objects.filter(
            user=user
        ).order_by(
            "created_at"
        )

        if not histories.exists():
            return Response(
                {
                    "detail": "분석할 질문/답변 기록이 없습니다."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversations = [
            {
                "questionId": history.question_id,
                "question": history.question,
                "answer": history.answer,
            }
            for history in histories
        ]

        # result = bigfive(conversations)
        result =  analyze_personality(user_id, conversations)

        PsychologyAnalysisResult.objects.create(
            user=user,
            openness=result["bigFive"]["openness"],
            conscientiousness=result["bigFive"]["conscientiousness"],
            extraversion=result["bigFive"]["extraversion"],
            agreeableness=result["bigFive"]["agreeableness"],
            neuroticism=result["bigFive"]["neuroticism"],
            interests=result.get(
                "interests",
                [],
            ),
            summary=result.get(
                "summary",
                "",
            ),
            valid=result.get(
                "valid",
                True,
            ),
            insufficient=result.get(
                "insufficient",
                [],
            ),
        )

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
                    "detail": "사용자를 찾을 수 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        analysis = PsychologyAnalysisResult.objects.filter(
            user=user,
            valid=True,
        ).order_by("-created_at").first()

        if analysis is None:
            return Response(
                {
                    "detail": "해당 사용자의 분석 결과가 없습니다."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        profile, created = PsychologyProfile.objects.update_or_create(
            user=user,
            defaults={
                "openness": analysis.openness,
                "conscientiousness": analysis.conscientiousness,
                "extraversion": analysis.extraversion,
                "agreeableness": analysis.agreeableness,
                "neuroticism": analysis.neuroticism,
                "interests": analysis.interests,
                "summary": analysis.summary,
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