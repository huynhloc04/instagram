from locust import HttpUser, task, between, TaskSet, seq_task, constant
from random import choice
import uuid
import os


class PostCreationSequence(TaskSet):
    """Sequential tasks for post creation flow"""

    def on_start(self):
        self.image_id = None
        # Create a small test image for upload
        self.test_image_path = "test_image.jpg"
        with open(self.test_image_path, "wb") as f:
            f.write(b"fake image content")

    def on_stop(self):
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    @seq_task(1)
    def upload_image(self):
        """Upload an image before creating a post."""
        files = {
            "file": ("test_image.jpg", open(self.test_image_path, "rb"), "image/jpeg")
        }
        headers = self.parent.parent.get_headers()
        headers.pop("Content-Type", None)

        with self.client.post(
            "/api/v1/posts/upload",
            headers=headers,
            files=files,
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                self.image_id = response.json()["data"]["image_id"]
                return True
            response.failure(f"Upload image failed: {response.json()}")

    @seq_task(2)
    def create_post(self):
        """Create a new post using uploaded image."""
        if not self.image_id:
            return

        post_data = {
            "caption": "Created test post with uploaded image.",
            "image_id": self.image_id,
        }
        with self.client.post(
            "/api/v1/posts",
            json=post_data,
            headers=self.parent.parent.get_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                return True
            response.failure(f"Create post failed: {response.json()}")

    @seq_task(3)
    def stop(self):
        """Stop the sequence and return to parent."""
        self.interrupt()


class UserBehavior(TaskSet):
    """Main user behavior with weighted tasks"""

    tasks = {PostCreationSequence: 2}  # Weight for the post creation sequence

    def on_start(self):
        self.post_id = None

    @task(3)
    def view_feed(self):
        """View user feed - most common operation."""
        with self.client.get(
            "/api/v1/posts/news-feed",
            headers=self.parent.get_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                posts = response.json()["data"]["posts"]
                if posts and len(posts) > 0:
                    self.post_id = choice(posts)["id"]
                return True
            response.failure(f"Failed to get news feed: {response.json()}")

    @task(2)
    def like_post(self):
        """Like a random post."""
        if self.post_id:
            with self.client.post(
                f"/api/v1/posts/{self.post_id}/likes",
                headers=self.parent.get_headers(),
                catch_response=True,
            ) as like_response:
                if like_response.status_code in [200, 201]:
                    return True
                elif like_response.status_code == 409:
                    like_response.success()
                    return True
                else:
                    like_response.failure(f"Like post failed: {like_response.json()}")

    @task(1)
    def comment_on_post(self):
        """Comment on a post."""
        if self.post_id:
            comment_data = {"content": "Test comment from load testing"}
            with self.client.post(
                f"/api/v1/posts/{self.post_id}/comments",
                json=comment_data,
                headers=self.parent.get_headers(),
                catch_response=True,
            ) as response:
                if response.status_code in [200, 201]:
                    return True
                response.failure(f"Comment failed: {response.json()}")

    @task(1)
    def search_users(self):
        """Search for users."""
        self.client.get(
            "/api/v1/users/search?username=user",
            headers=self.parent.get_headers(),
            catch_response=True,
        )

    @task(1)
    def get_user_profile(self):
        """View user profile."""
        self.client.get(
            "/api/v1/users/me",
            headers=self.parent.get_headers(),
            catch_response=True,
        )


class InstagramUser(HttpUser):
    wait_time = between(1, 5)
    tasks = [UserBehavior]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_uuid = str(uuid.uuid4())[:8]

    def on_start(self):
        """Initialize user data and login on start."""
        self.token = None
        self.login_data = {"username": f"user_{self.user_uuid}", "password": "Test123!"}
        self.register()
        self.login()

    def register(self):
        """Register a new user."""
        register_data = {
            "email": f"{self.login_data['username']}_{self.user_uuid}@gmail.com",
            "password": self.login_data["password"],
            "username": f"user_{self.user_uuid}",
            "full_name": f"Test User {self.user_uuid}",
        }
        with self.client.post(
            "/api/v1/auth/register", json=register_data, catch_response=True
        ) as response:
            if response.status_code == 201:
                return True
            response.failure(f"Registration failed: {response.json()}")

    def login(self):
        """Login and store the token."""
        with self.client.post(
            "/api/v1/auth/login", json=self.login_data, catch_response=True
        ) as response:
            if response.status_code == 200:
                self.token = response.json()["data"]["access_token"]
                return True
            response.failure(f"Login failed: {response.json()}")

    def get_headers(self):
        """Get headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @task(2)
    def get_user_profile(self):
        """View user profile."""
        self.client.get(f"/api/v1/users/me", headers=self.get_headers())

    @task(1)
    def search_users(self):
        """Search for users."""
        self.client.get(
            "/api/v1/users/search?username=user", headers=self.get_headers()
        )

    @task(1)
    def update_profile(self):
        """Update user profile."""
        profile_data = {
            "bio": "Updated bio from load testing",
            "fullname": "Huynh Tan Loc.",
        }
        self.client.put(
            "/api/v1/users/me", json=profile_data, headers=self.get_headers()
        )
