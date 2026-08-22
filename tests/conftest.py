"""Conftest for pytest configuration."""
import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Set test values for any required env vars
    os.environ.setdefault("X_BEARER_TOKEN", "test_token")
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_bot_token")
    os.environ.setdefault("TELEGRAM_CHAT_ID", "test_chat_id")
    os.environ.setdefault("APP_MODE", "test")
