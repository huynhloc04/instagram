from unittest import TestCase

from app.v1 import create_app


class TestPostAPIs(TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.client()
        self.api_prefix = "api/v1"
        self.content_type = "application/json"
        self.user_info = {
            "username": "nguyensuy",
            "password": "SuyNT@2001",
        }

    def tearDown(self):
        pass

    def test_create_post(self):

        #   1. Login
        user = self.client.post(
            f"{self.api_prefix}/auth/login",
            content_type=self.content_type,
            json=self.login_info,
        )
        self.assertEqual(user.json["status"], 200)
        self.assertIn("access_token", user.json["data"])

        #   2. Create post
