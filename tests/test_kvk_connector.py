"""
Tests for KVK Connector

Tests the KVK API integration using the test API.
"""

import pytest

from connectors.kvk_connector import (
    KVKNotFoundError,
    get_basisprofiel,
    normalize_company_data,
    search_company,
)


@pytest.mark.asyncio
async def test_search_company_by_name():
    """Test searching for a company by name."""
    results = await search_company("test")
    assert isinstance(results, list)
    # Test API should return results for "test"
    if results:
        assert "kvkNummer" in results[0]


@pytest.mark.asyncio
async def test_search_company_with_city():
    """Test searching with city filter."""
    results = await search_company("test", city="Amsterdam")
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_get_basisprofiel_valid():
    """Test getting base profile for valid KVK number."""
    # Use test KVK number for BV
    profile = await get_basisprofiel("68750110")
    assert profile is not None
    assert "kvkNummer" in profile
    assert profile["kvkNummer"] == "68750110"


@pytest.mark.asyncio
async def test_get_basisprofiel_invalid():
    """Test getting profile for invalid KVK number."""
    with pytest.raises(KVKNotFoundError):
        await get_basisprofiel("00000000")


@pytest.mark.asyncio
async def test_normalize_company_data():
    """Test data normalization."""
    kvk_data = {
        "kvkNummer": "12345678",
        "naam": "Test BV",
        "rechtsvorm": "BV",
        "handelsNamen": ["Test Company"],
        "sbiActiviteiten": [
            {
                "sbiCode": "6201",
                "sbiOmschrijving": "Software development",
                "indHoofdactiviteit": True,
            }
        ],
    }

    normalized = normalize_company_data(kvk_data)

    assert normalized["kvk_number"] == "12345678"
    assert normalized["name"] == "Test BV"
    assert normalized["legal_form"] == "BV"
    assert len(normalized["sbi_codes"]) == 1
    assert normalized["sbi_codes"][0]["code"] == "6201"


def test_normalize_empty_data():
    """Test normalizing empty data."""
    normalized = normalize_company_data({})
    assert normalized["kvk_number"] is None
    assert normalized["name"] is None
