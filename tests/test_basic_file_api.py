"""Basic test for file API endpoints.

This test checks the file endpoints to verify that the API is working correctly.
It only tests the API without actually uploading or downloading files to S3.
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
    "admin"  # noqa: S105  # This matches the FIRST_SUPERUSER_PASSWORD in docker-compose
)


@pytest.fixture(scope="module")
def auth_headers(docker_compose_up_down: Any) -> dict:  # Use Docker Compose fixture
    """Get authentication headers with access token.

    Args:
        docker_compose_up_down: Fixture that ensures Docker Compose is running.

    Returns:
        A dictionary with the Authorization header.
    """
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


def test_get_upload_url(auth_headers: dict) -> None:
    """Test creating a presigned upload URL.

    Args:
        auth_headers: Authentication headers with access token.
    """
    # Test file info
    upload_info = {
        "filename": "test-file.txt",
        "content_type": "text/plain",
        "size_bytes": 100,
        "description": "Test file for API testing",
        "is_public": False,
    }

    # Request a presigned upload URL
    upload_response = requests.post(
        f"{BASE_URL}{API_V1_STR}/files/upload",
        headers=auth_headers,
        json=upload_info,
        timeout=10,
    )

    # Verify the response
    assert upload_response.status_code == 200, f"Upload URL creation failed: {upload_response.text}"
    upload_data = upload_response.json()
    assert "upload_url" in upload_data, "Upload URL not found in response"
    assert "file_id" in upload_data, "File ID not found in response"

    file_id = upload_data["file_id"]

    # Test that we can get the file metadata
    file_response = requests.get(
        f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
    )

    assert file_response.status_code == 200, f"Failed to get file metadata: {file_response.text}"
    file_data = file_response.json()
    assert file_data["filename"] == upload_info["filename"], "Filename does not match"
    assert file_data["content_type"] == upload_info["content_type"], "Content type does not match"

    # Test that we can get a download URL
    download_response = requests.get(
        f"{BASE_URL}{API_V1_STR}/files/download/{file_id}",
        headers=auth_headers,
        timeout=10,
    )

    assert (
        download_response.status_code == 200
    ), f"Download URL creation failed: {download_response.text}"
    download_data = download_response.json()
    assert "download_url" in download_data, "Download URL not found in response"

    # Clean up by deleting the file
    delete_response = requests.delete(
        f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
    )

    assert delete_response.status_code == 200, f"File deletion failed: {delete_response.text}"


def test_list_files(auth_headers: dict) -> None:
    """Test listing files.

    Args:
        auth_headers: Authentication headers with access token.
    """
    # Create a couple of test files
    file_ids = []
    for i in range(2):
        upload_info = {
            "filename": f"test-file-{i}.txt",
            "content_type": "text/plain",
            "size_bytes": 100,
            "description": f"Test file {i} for API testing",
            "is_public": False,
        }

        upload_response = requests.post(
            f"{BASE_URL}{API_V1_STR}/files/upload",
            headers=auth_headers,
            json=upload_info,
            timeout=10,
        )

        assert (
            upload_response.status_code == 200
        ), f"Upload URL creation failed: {upload_response.text}"
        file_ids.append(upload_response.json()["file_id"])

    # List files
    list_response = requests.get(f"{BASE_URL}{API_V1_STR}/files", headers=auth_headers, timeout=10)

    assert list_response.status_code == 200, f"Failed to list files: {list_response.text}"
    files = list_response.json()
    assert len(files) >= 2, "Not enough files returned"

    # Clean up
    for file_id in file_ids:
        delete_response = requests.delete(
            f"{BASE_URL}{API_V1_STR}/files/{file_id}", headers=auth_headers, timeout=10
        )
        assert delete_response.status_code == 200, f"File deletion failed: {delete_response.text}"
