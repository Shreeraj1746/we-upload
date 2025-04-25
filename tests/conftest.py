"""Pytest configuration for integration tests.

This file contains fixtures used by the integration tests.
"""
# ruff: noqa: PT004, PTH100, PTH120, RUF005, S603, S607, S608, S609, UP022
import os
import subprocess
import time
from collections.abc import Generator

import pytest
import requests


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


@pytest.fixture(scope="module")
def docker_compose_up_down() -> Generator[None, None, None]:
    """Start Docker Compose before tests and stop it after.

    This fixture ensures that the Docker Compose environment is up and running
    before the tests start, and that it is properly shut down after the tests
    finish, regardless of whether they pass or fail.

    Yields:
        None
    """
    # Get the directory containing the test file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    # Determine which docker compose command to use
    # First try the modern "docker compose" format
    compose_command = ["docker", "compose"]
    try:
        subprocess.run(
            compose_command + ["version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        # Fall back to legacy "docker-compose" format
        compose_command = ["docker-compose"]

    # Try to stop any existing containers first to ensure a clean state
    subprocess.run(
        compose_command + ["down", "-v"],
        cwd=project_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Start Docker Compose
    print("Starting Docker Compose services...")
    subprocess.run(
        compose_command + ["up", "-d"],
        cwd=project_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the API to be ready
    print("Waiting for API to become ready...")
    wait_for_api()

    # Additional wait time for database initialization and user creation
    time.sleep(5)
    print("Environment is ready for testing.")

    try:
        # Yield control back to the tests
        yield
    finally:
        # Tear down Docker Compose after tests
        print("Stopping Docker Compose services...")
        subprocess.run(
            compose_command + ["down", "-v"],
            cwd=project_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
