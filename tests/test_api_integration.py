"""API integration tests.

This module contains tests that verify the API endpoints functionality
in a Docker Compose environment with the full application stack.
"""

import time
from typing import Any

import pytest
import requests

# Test constants
BASE_URL = "http://localhost:8000"
API_V1_STR = "/api/v1"
TEST_EMAIL = "admin@example.com"  # This matches the FIRST_SUPERUSER in docker-compose
TEST_PASSWORD = (
    "admin"  # noqa: S105 # This matches the FIRST_SUPERUSER_PASSWORD in docker-compose
)


def wait_for_api(max_retries: int = 30, retry_delay: int = 2) -> bool:
    """Wait for the API to become available.

    Args:
        max_retries: Maximum number of retries before giving up.
        retry_delay: Delay in seconds between retries.

    Returns:
        bool: True if API is available, False otherwise.
    """
    health_endpoint = f"{BASE_URL}/health"

    for attempt in range(max_retries):
        try:
            response = requests.get(health_endpoint, timeout=5)
            if response.status_code == 200:
                print(f"API is ready after {attempt + 1} attempts")
                return True
            else:
                print(f"API health check returned status {response.status_code}, waiting...")
        except requests.RequestException as e:
            print(f"API not ready yet (attempt {attempt + 1}/{max_retries}): {e}")

        time.sleep(retry_delay)

    print(f"API failed to become available after {max_retries} attempts")
    return False


@pytest.fixture(scope="module")
def auth_headers(docker_compose_up_down: Any) -> dict[str, str]:
    """Get authentication headers with access token.

    Args:
        docker_compose_up_down: Fixture that ensures Docker Compose is running.

    Returns:
        A dictionary with the Authorization header.
    """
    # Wait for API to be ready
    api_ready = wait_for_api()
    assert api_ready, "API not available, cannot proceed with tests"

    # For OAuth2 form login, we need to use form data, not JSON
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
    }

    # Try to login with retries to account for app startup time
    max_retries = 20
    retry_delay = 3  # seconds

    for attempt in range(max_retries):
        try:
            # Using form data instead of JSON
            login_response = requests.post(
                f"{BASE_URL}/login/access-token", data=login_data, timeout=10
            )

            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                return {"Authorization": f"Bearer {token}"}

            print(f"Login attempt {attempt+1} failed with status {login_response.status_code}")
            if attempt == 0:
                # Print response text on first failure for debugging
                print(f"Response: {login_response.text}")
            time.sleep(retry_delay)
        except requests.RequestException as e:
            print(f"Login attempt {attempt+1} failed with error: {e}")
            time.sleep(retry_delay)

    pytest.fail("Failed to obtain authentication token after multiple attempts")


def test_health_endpoints(docker_compose_up_down: Any) -> None:
    """Test the health check endpoints.

    Args:
        docker_compose_up_down: Fixture that ensures Docker Compose is running.
    """
    # Wait for API to be ready
    api_ready = wait_for_api()
    assert api_ready, "API not available, cannot proceed with tests"

    # Test the main health endpoint
    health_response = requests.get(f"{BASE_URL}/health", timeout=10)
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] == "ok"
    assert health_data["service"] == "we-upload-api"

    # Test the database health endpoint
    db_health_response = requests.get(f"{BASE_URL}/health/db", timeout=10)
    assert db_health_response.status_code == 200
    db_health_data = db_health_response.json()
    assert db_health_data["status"] == "ok"
    assert db_health_data["database"] == "connected"


def test_user_me_endpoint(auth_headers: dict[str, str]) -> None:
    """Test the current user endpoint.

    Args:
        auth_headers: Authentication headers with access token.
    """
    me_response = requests.get(f"{BASE_URL}{API_V1_STR}/users/me", headers=auth_headers, timeout=10)

    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == TEST_EMAIL
    assert user_data["is_active"] is True
    assert user_data["is_superuser"] is True


def test_users_endpoint(auth_headers: dict[str, str]) -> None:
    """Test the users endpoint.

    Args:
        auth_headers: Authentication headers with access token.
    """
    users_response = requests.get(f"{BASE_URL}{API_V1_STR}/users", headers=auth_headers, timeout=10)

    assert users_response.status_code == 200
    users = users_response.json()
    assert len(users) > 0
    # Check that at least one user has the admin email
    admin_found = False
    for user in users:
        if user["email"] == TEST_EMAIL:
            admin_found = True
            break
    assert admin_found, f"Admin user with email {TEST_EMAIL} not found in users list"


def test_file_lifecycle(auth_headers: dict[str, str]) -> None:
    """Test the full file lifecycle: create, get, and delete.

    Args:
        auth_headers: Authentication headers with access token.
    """
    # 1. Create a file record
    file_info = {
        "filename": "integration_test_file.txt",
        "content_type": "text/plain",
        "size_bytes": 1024,
        "description": "File created during integration test",
        "is_public": True,
    }

    create_response = requests.post(
        f"{BASE_URL}{API_V1_STR}/files/upload",
        headers=auth_headers,
        json=file_info,
        timeout=10,
    )

    assert create_response.status_code == 200
    file_data = create_response.json()
    file_id = file_data["file_id"]
    assert "upload_url" in file_data

    # 2. Get the file metadata
    get_response = requests.get(
        f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
    )

    assert get_response.status_code == 200
    file_metadata = get_response.json()
    assert file_metadata["filename"] == file_info["filename"]
    assert file_metadata["content_type"] == file_info["content_type"]
    assert file_metadata["size_bytes"] == file_info["size_bytes"]
    assert file_metadata["description"] == file_info["description"]
    assert file_metadata["is_public"] == file_info["is_public"]

    # 3. Get download URL
    download_response = requests.get(
        f"{BASE_URL}{API_V1_STR}/files/download/{file_id}",
        headers=auth_headers,
        timeout=10,
    )

    assert download_response.status_code == 200
    download_data = download_response.json()
    assert "download_url" in download_data

    # 4. Delete the file
    delete_response = requests.delete(
        f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
    )

    assert delete_response.status_code == 200
    # The API returns the file data on delete, not a success flag
    delete_data = delete_response.json()
    # Check if the response contains the file details that we're trying to delete
    assert delete_data["filename"] == file_info["filename"]
    assert delete_data["content_type"] == file_info["content_type"]
    assert "id" in delete_data

    # 5. Verify deletion by trying to get the file metadata again
    get_deleted_response = requests.get(
        f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
    )
    assert get_deleted_response.status_code == 404
