"""Basic test to verify the project is importable."""


def test_version() -> None:
    """Verify we can import the app package."""
    import app

    assert app is not None
