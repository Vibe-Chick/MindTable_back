# psychology/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import PsychologyProfileSaveAPIView


class PsychologyProfileSaveTests(TestCase):
    def test_save_profile(self):
        user = get_user_model().objects.create_user(username="tester", password="pw1234")

        # AI 모듈이 넘겨줄 값이라고 가정하고 임의로 채운 입력.
        # (ai_engine.profile.extract_profile()이 실제로 반환하는 모양에 맞춤:
        #  self_report_vector 5축 -> bigFive, interest_tags -> interests)
        factory = APIRequestFactory()
        request = factory.post(
            "/psychology/profile/save/",
            data={
                "bigFive": {
                    "openness": 4,
                    "conscientiousness": 3,
                    "extraversion": 2,
                    "agreeableness": 4,
                    "neuroticism": 3,
                },
                "interests": ["등산", "음악"],
                "summary": "임의 테스트 입력",
            },
            format="json",
        )
        force_authenticate(request, user=user)

        # PsychologyProfileSaveAPIView.post(self, request, user_id)라
        # user_id를 여기서 직접 넘겨야 한다(실제 서비스에선 URL 경로로 들어옴).
        response = PsychologyProfileSaveAPIView.as_view()(request, user_id=user.id)

        print(response.status_code, response.data)
        self.assertIn(response.status_code, (200, 201))
