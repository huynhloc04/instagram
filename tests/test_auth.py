import unittest
from random import randint

from app.v1 import create_app


class TestAuthApi(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.api_prefix = "api/v1"
        self.content_type = "application/json"
        random_val = randint(0, 1000)
        self.user_info = {
            "username": f"huynhdan_{random_val}",
            "password": f"DanH{random_val}@2001",
            "email": f"huynhdan{random_val}@gmail.com",
            "fullname": f"Dan Huynh {random_val}",
        }


    def tearDown(self):
        pass

    def test_authentication_apis(self):
        #   1. Register as new user
        registered_user = self.client.post(
            f"{self.api_prefix}/auth/register",
            content_type=self.content_type,
            json=self.user_info,
        )
        self.assertEqual(registered_user.json["status"], 201)

        #   2. Login with registered user
        login_user = self.client.post(
            f"{self.api_prefix}/auth/login",
            content_type=self.content_type,
            json={
                "username": self.user_info["username"],
                "password": self.user_info["password"]
            },
        )
        self.assertEqual(login_user.json["status"], 200)
        self.assertIn("access_token", login_user.json["data"])

        #   3. After login, get own profile
        access_token = login_user.json['data']['access_token']
        profile = self.client.get(
            f"{self.api_prefix}/users/profile",
            content_type=self.content_type,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.assertEqual(profile.json["status"], 200)
        self.assertIn("username", profile.json['data'])
        self.assertEqual(profile.json["data"]["username"], self.user_info["username"])
        


if __name__ == "__main__":
    unittest.main()
