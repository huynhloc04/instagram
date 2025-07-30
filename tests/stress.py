import requests

# Configuration
BASE_URL = "http://localhost:8000/api/v1/health"


def test_health():
    """Simple health check test"""
    try:
        response = requests.get(BASE_URL)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def stress_test(num_requests=100):
    """Simple stress test"""
    print(f"Running {num_requests} requests...")
    success = 0

    for i in range(num_requests):
        try:
            response = requests.get(BASE_URL)
            if response.status_code == 200:
                success += 1
        except:
            pass

    print(f"Success: {success}/{num_requests}")


if __name__ == "__main__":
    # Test single request
    print("Testing health endpoint...")
    test_health()

    # Run stress test
    print("\nRunning stress test...")
    stress_test(1000)
