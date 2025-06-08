from locust import HttpUser, task, between
from random import choice
import uuid

class InstagramUser(HttpUser):
    wait_time = between(1, 5)  # Random wait between requests
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_uuid = str(uuid.uuid4())[:4]  # Generate a unique ID for each user
    
    def on_start(self):
        """Initialize user data and login on start."""
        self.token = None
        self.login_data = {
            "username": f"user_{self.user_uuid}",
            "password": "Test123!"
        }
        # Register user first
        self.register()
        # Then login
        self.login()
    
    def register(self):
        """Register a new user."""
        register_data = {
            "email": f"{self.login_data['username']}_{self.user_uuid}@gmail.com",
            "password": self.login_data["password"],
            "username": self.login_data["username"],
            "full_name": f"Test User {self.user_uuid}"
        }
        with self.client.post("/api/v1/auth/register", json=register_data, catch_response=True) as response:
            if response.status_code in [201, 400]:
                return True
            response.failure(f"Registration failed with status {response.status_code}")
    
    def login(self):
        """Login and store the token."""
        with self.client.post("/api/v1/auth/login", json=self.login_data, catch_response=True) as response:
            if response.status_code == 200:
                self.token = response.json()["data"]["access_token"]
                return True
            response.failure(f"Login failed with status {response.status_code}")

    def get_headers(self):
        """Get headers with authentication token."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def view_feed(self):
        """View user feed - most common operation."""
        self.client.get("/api/v1/posts/news-feed", headers=self.get_headers())

    @task(2)
    def create_post(self):
        """Create a new post."""
        post_data = {
            "caption": f"Test post from load testing.",
            "image_id": 1
        }
        self.client.post("/api/v1/posts", json=post_data, headers=self.get_headers())

    @task(2)
    def get_user_profile(self):
        """View user profile."""
        self.client.get(f"/api/v1/users/profile", headers=self.get_headers())

    @task(1)
    def search_users(self):
        """Search for users."""
        self.client.get("/api/v1/users/search?q=test", headers=self.get_headers())

    @task(2)
    def like_post(self):
        """Like a random post."""
        # First get some posts
        with self.client.get("/api/v1/posts/feed", headers=self.get_headers(), catch_response=True) as response:
            if response.status_code == 200:
                posts = response.json()
                if posts and len(posts) > 0:
                    post_id = choice(posts)["id"]
                    self.client.post(f"/api/v1/posts/{post_id}/like", headers=self.get_headers())

    @task(1)
    def comment_on_post(self):
        """Comment on a random post."""
        # First get some posts
        with self.client.get("/api/v1/posts/feed", headers=self.get_headers(), catch_response=True) as response:
            if response.status_code == 200:
                posts = response.json()
                if posts and len(posts) > 0:
                    post_id = choice(posts)["id"]
                    comment_data = {"content": "Test comment from load testing"}
                    self.client.post(
                        f"/api/v1/posts/{post_id}/comments",
                        json=comment_data,
                        headers=self.get_headers()
                    )

    @task(1)
    def update_profile(self):
        """Update user profile."""
        profile_data = {
            "bio": "Updated bio from load testing",
            "website": "https://example.com"
        }
        self.client.put("/api/v1/users/profile", json=profile_data, headers=self.get_headers())
