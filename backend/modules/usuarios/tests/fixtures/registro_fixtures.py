"""
Registration-specific fixtures for usuarios module tests.
"""
import pytest
from django.test import AsyncClient


@pytest.fixture
def registro_api_client(db):
    """Django AsyncClient for testing async /auth/register endpoint."""
    return AsyncClient()


@pytest.fixture
def registro_base_setup(db, api_client):
    """Base setup for registration tests - provides api_client without auth."""
    return {
        "api_client": api_client,
    }
