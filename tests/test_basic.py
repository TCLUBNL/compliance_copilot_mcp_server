"""Basic tests to verify the test suite works."""

import asyncio

import pytest


def test_imports():
    """Test that basic imports work."""
    assert True


def test_environment():
    """Test environment setup."""
    assert True


@pytest.mark.asyncio
async def test_async_works():
    """Test that async tests work."""
    await asyncio.sleep(0)
    assert True


if __name__ == "__main__":
    pytest.main([__file__])
