"""
Tests for OpenSanctions Connector

Tests the OpenSanctions API integration with mocked responses.
"""

from unittest.mock import AsyncMock, patch

import pytest

from connectors.opensanctions_connector import (
    OpenSanctionsAPIError,
    calculate_risk_score,
    normalize_match_data,
    search_entity,
)


@pytest.mark.asyncio
@patch("connectors.opensanctions_connector._make_request", new_callable=AsyncMock)
async def test_search_entity_person(mock_request):
    """Test searching for a person."""
    # Mock API response
    mock_request.return_value = {
        "results": [
            {
                "id": "test-123",
                "schema": "Person",
                "caption": "Vladimir Putin",
                "score": 0.95,
                "properties": {"name": ["Vladimir Putin"], "topics": ["sanction"]},
            }
        ]
    }

    results = await search_entity("Vladimir Putin", schema="Person", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    assert results[0]["caption"] == "Vladimir Putin"
    mock_request.assert_called_once()


@pytest.mark.asyncio
@patch("connectors.opensanctions_connector._make_request", new_callable=AsyncMock)
async def test_search_entity_organization(mock_request):
    """Test searching for an organization."""
    mock_request.return_value = {
        "results": [
            {
                "id": "test-456",
                "schema": "Organization",
                "caption": "Rosneft",
                "score": 0.88,
                "properties": {"name": ["Rosneft"], "topics": ["sanction"]},
            }
        ]
    }

    results = await search_entity("Rosneft", schema="Organization", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    mock_request.assert_called_once()


@pytest.mark.asyncio
@patch("connectors.opensanctions_connector._make_request", new_callable=AsyncMock)
async def test_search_entity_empty_query(mock_request):
    """Test searching with empty query."""
    mock_request.return_value = {"results": []}

    results = await search_entity("", limit=5)
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
@patch("connectors.opensanctions_connector._make_request", new_callable=AsyncMock)
async def test_search_entity_api_error(mock_request):
    """Test handling API errors."""
    mock_request.side_effect = OpenSanctionsAPIError("API Error")

    with pytest.raises(OpenSanctionsAPIError):
        await search_entity("Test Query")


def test_calculate_risk_score_no_matches():
    """Test risk score with no matches."""
    score = calculate_risk_score([])
    assert score == 0.0


def test_calculate_risk_score_with_matches():
    """Test risk score calculation with matches."""
    matches = [
        {"score": 0.95, "properties": {"topics": ["sanction"]}},
        {"score": 0.75, "properties": {"topics": []}},
    ]
    score = calculate_risk_score(matches)
    assert score > 0
    assert score <= 100


def test_calculate_risk_score_high_risk():
    """Test risk score for high-risk matches."""
    matches = [{"score": 0.90, "properties": {"topics": ["sanction", "crime"]}}]
    score = calculate_risk_score(matches)
    assert score >= 90


def test_normalize_match_data():
    """Test data normalization."""
    match = {
        "id": "test-123",
        "schema": "Person",
        "caption": "Test Person",
        "score": 0.95,
        "properties": {
            "name": ["Test Person"],
            "topics": ["sanction"],
            "country": ["RU"],
        },
    }

    normalized = normalize_match_data(match)

    assert normalized["entity_id"] == "test-123"
    assert normalized["name"] == "Test Person"
    assert normalized["match_score"] == 0.95
    assert "sanction" in normalized["topics"]


def test_normalize_empty_match():
    """Test normalizing empty match data."""
    normalized = normalize_match_data({})
    assert normalized["entity_id"] is None
    assert normalized["name"] is None
    assert normalized["match_score"] == 0
