"""Shared pytest configuration for zAIkon."""

from fastapi.testclient import TestClient
import pytest

from zaikon.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())

