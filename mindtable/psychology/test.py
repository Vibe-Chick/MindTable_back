# psychology/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .views import PsychologyProfileSaveAPIView


class PsychologyProfileSaveTests(TestCase):
    def test_save_profile(self):
        user = get_user_model().objects.create_user(username="tester", password="pw1234")

        factory = APIRequestFactory()
        request = factory.post(
            "/psychology/profile/save/",
            data={"q1": "...", "q2": "...", "q3": "...", "q4_choice": "..."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = PsychologyProfileSaveAPIView.as_view()(request)

        print(response.status_code, response.data)
        self.assertEqual(response.status_code, 200)
