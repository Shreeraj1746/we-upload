"""Utilities for end-to-end testing with Docker Compose.

This module provides pytest fixtures to manage Docker Compose for end-to-end testing.
"""

import subprocess
import time
from collections.abc import Generator

import pytest
import requests


@pytest.fixture(scope="session")
def _docker_compose_up_down() -> Generator[None, None, None]:
    """Start the Docker Compose environment before tests and stop it after.

    This fixture handles starting and stopping all services defined in the
    project's docker-compose.yml file. It waits for the API service to become
    available before allowing tests to proceed.

    Yields:
        None
    """
    # Start Docker Compose
    print("Starting Docker Compose services...")
    subprocess.run(["docker-compose", "down", "-v"], check=False)  # noqa: S603, S607 # Clean up any previous instances
    subprocess.run(["docker-compose", "up", "-d"], check=True)  # noqa: S603, S607

    # Wait for the API to be ready
    print("Waiting for API to become ready...")
    wait_for_api()

    # Additional wait time for database initialization and user creation
    time.sleep(5)
    print("Environment is ready for testing.")

    # Run the tests
    yield

    # Tear down Docker Compose
    print("Tearing down Docker Compose environment...")
    subprocess.run(["docker-compose", "down", "-v"], check=True)  # noqa: S603, S607
    print("Environment cleanup complete.")


def wait_for_api(
    base_url: str = "http://localhost:8000", max_retries: int = 60, retry_delay: int = 2
) -> None:
    """Wait for the API to become available.

    Args:
        base_url: The base URL of the API to check.
        max_retries: Maximum number of retries before giving up.
        retry_delay: Delay in seconds between retries.

    Raises:
        RuntimeError: If the API doesn't become available within the retry limit.
    """
    health_endpoint = f"{base_url}/health"

    for attempt in range(max_retries):
        try:
            response = requests.get(health_endpoint, timeout=5)
            if response.status_code == 200:
                print(f"API is ready after {attempt + 1} attempts")
                return
            else:
                print(f"API health check returned status {response.status_code}, waiting...")
        except requests.RequestException as e:
            print(f"API not ready yet (attempt {attempt + 1}/{max_retries}): {e}")

        time.sleep(retry_delay)

    raise RuntimeError(f"API failed to become available after {max_retries} attempts")
