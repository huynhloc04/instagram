from locust import HttpUser, task, between
from random import choice
import uuid


class InstagramUser(HttpUser):
    wait_time = between(1, 5)  # Random wait between tasks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate a longer unique ID for each user to avoid conflicts
        self.user_uuid = str(uuid.uuid4())[:8]  # Increased from 4 to 8 characters

    def on_start(self):
        """Initialize user data and login on start."""
        self.token = None
        self.login_data = {"username": f"user_{self.user_uuid}", "password": "Test123!"}
        # Register user first
        self.register()
        # Then login
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
            if response.status_code == 201:  # Successfully created
                return True
            # elif response.status_code == 409:  # Conflict - user exists
            #     # Mark as success since we can proceed with login
            #     response.success()
            #     return True
            # elif response.status_code == 400:  # Bad request - might be validation
            #     response.success()  # Don't mark as failure since we can proceed
            #     return True
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

    @task(3)
    def view_feed(self):
        """View user feed - most common operation."""
        self.client.get("/api/v1/posts/news-feed", headers=self.get_headers())

    @task(2)
    def create_post(self):
        """Create a new post."""
        post_data = {
            "caption": "Created test post.",
            "image_id": 1,
        }
        with self.client.post(
            "/api/v1/posts",
            json=post_data,
            headers=self.get_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                return True
            response.failure(f"Create post failed: {response.json()}")

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

    @task(2)
    def like_post(self):
        """Like a random post."""
        # First get some posts
        with self.client.get(
            "/api/v1/posts/news-feed", headers=self.get_headers(), catch_response=True
        ) as response:
            if response.status_code == 200:
                posts = response.json()["data"]["posts"]
                if posts and len(posts) > 0:
                    post_id = choice(posts)["id"]
                    # Try to like the post
                    with self.client.post(
                        f"/api/v1/posts/{post_id}/likes",
                        headers=self.get_headers(),
                        catch_response=True,
                    ) as like_response:
                        if like_response.status_code in [200, 201]:  # Success
                            return True
                        elif like_response.status_code == 409:  # Already liked
                            like_response.success()  # Mark as success since it's an expected condition
                            return True
                        else:
                            like_response.failure(
                                f"Like post failed: {like_response.json()}"
                            )
            else:
                response.failure(f"Failed to get news feed: {response.json()}")

    @task(1)
    def comment_on_post(self):
        """Comment on a random post."""
        # First get some posts
        with self.client.get(
            "/api/v1/posts/news-feed", headers=self.get_headers(), catch_response=True
        ) as response:
            if response.status_code == 200:
                posts = response.json()["data"]["posts"]
                if posts and len(posts) > 0:
                    post_id = choice(posts)["id"]
                    comment_data = {"content": "Test comment from load testing"}
                    self.client.post(
                        f"/api/v1/posts/{post_id}/comments",
                        json=comment_data,
                        headers=self.get_headers(),
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
