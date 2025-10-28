"""
OpenSanctions Connector

Integrates with OpenSanctions API for international sanctions screening.
Screens entities against OFAC, EU, UN sanctions lists and PEP databases.

API Documentation: https://www.opensanctions.org/docs/api/
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# OpenSanctions API Configuration
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
OPENSANCTIONS_BASE_URL = os.getenv("OPENSANCTIONS_BASE_URL", "https://api.opensanctions.org")
OPENSANCTIONS_TIMEOUT = int(os.getenv("OPENSANCTIONS_TIMEOUT", "30"))

# Default datasets to search
DEFAULT_DATASETS = [
    "sanctions",  # All sanctions lists
    "peps",  # Politically Exposed Persons
    "crime",  # Criminal watchlists
]


class OpenSanctionsError(Exception):
    """Base exception for OpenSanctions API errors"""

    pass


class OpenSanctionsAPIError(OpenSanctionsError):
    """OpenSanctions API returned an error"""

    pass


class OpenSanctionsNotFoundError(OpenSanctionsError):
    """Entity not found"""

    pass


class OpenSanctionsRateLimitError(OpenSanctionsError):
    """Rate limit exceeded"""

    pass


async def _make_request(
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    timeout: int = OPENSANCTIONS_TIMEOUT,
) -> dict[str, Any]:
    """Make an authenticated request to the OpenSanctions API."""
    url = f"{OPENSANCTIONS_BASE_URL}{endpoint}"
    headers = {"Accept": "application/json"}

    if OPENSANCTIONS_API_KEY:
        headers["Authorization"] = f"Bearer {OPENSANCTIONS_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"OpenSanctions API Request: {url} with params {params}")
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 404:
                raise OpenSanctionsNotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                raise OpenSanctionsRateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                raise OpenSanctionsAPIError(f"API error: {response.status_code} - {response.text}")

            response.raise_for_status()
            data = response.json()
            logger.info(f"OpenSanctions API Response: {response.status_code}")
            return data

    except OpenSanctionsError:
        raise
    except httpx.TimeoutException as e:
        logger.error(f"Timeout after {timeout}s")
        raise OpenSanctionsAPIError(f"Timeout after {timeout}s") from e
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise OpenSanctionsAPIError(f"HTTP error: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise OpenSanctionsAPIError(f"Unexpected error: {e}") from e


async def search_entity(
    query: str,
    schema: str = "Person",
    datasets: Optional[list[str]] = None,
    limit: int = 10,
    fuzzy: bool = True,
) -> list[dict[str, Any]]:
    """Search for entities in OpenSanctions database."""
    if datasets is None:
        datasets = DEFAULT_DATASETS

    params = {
        "q": query,
        "schema": schema,
        "datasets": ",".join(datasets),
        "limit": limit,
        "fuzzy": str(fuzzy).lower(),
    }

    try:
        data = await _make_request("/search/", params)
        results = data.get("results", [])
        logger.info(f"Found {len(results)} results for query: {query}")
        return results
    except OpenSanctionsError:
        raise
    except Exception as e:
        logger.error(f"Error searching entity: {e}")
        return []


async def get_entity(entity_id: str) -> dict[str, Any]:
    """Get detailed entity information by ID."""
    endpoint = f"/entities/{entity_id}/"
    return await _make_request(endpoint)


async def match_entity(
    name: str,
    schema: str = "Person",
    birth_date: Optional[str] = None,
    country: Optional[str] = None,
    datasets: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Match entity with structured data."""
    if datasets is None:
        datasets = DEFAULT_DATASETS

    # Build properties
    properties: dict[str, Any] = {"name": [name]}

    if birth_date:
        properties["birthDate"] = [birth_date]
    if country:
        properties["country"] = [country]

    try:
        url = f"{OPENSANCTIONS_BASE_URL}/match/"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if OPENSANCTIONS_API_KEY:
            headers["Authorization"] = f"Bearer {OPENSANCTIONS_API_KEY}"

        payload = {"schema": schema, "properties": properties}

        async with httpx.AsyncClient(timeout=OPENSANCTIONS_TIMEOUT) as client:
            logger.info(f"OpenSanctions Match Request: {url}")
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 429:
                raise OpenSanctionsRateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                raise OpenSanctionsAPIError(f"API error: {response.status_code}")

            response.raise_for_status()
            data = response.json()
            return data.get("results", [])

    except OpenSanctionsError:
        raise
    except Exception as e:
        logger.error(f"Error matching entity: {e}")
        return []


def calculate_risk_score(matches: list[dict[str, Any]]) -> float:
    """Calculate risk score based on sanctions matches."""
    if not matches:
        return 0.0

    max_score = max(m.get("score", 0) for m in matches)
    risk_score = max_score * 100

    for match in matches:
        topics = match.get("properties", {}).get("topics", [])
        if any(topic in ["sanction", "crime", "poi"] for topic in topics):
            risk_score = min(100, risk_score * 1.5)

    return round(risk_score, 2)


def normalize_match_data(match: dict[str, Any]) -> dict[str, Any]:
    """Normalize OpenSanctions match data to internal schema."""
    properties = match.get("properties", {})

    return {
        "entity_id": match.get("id"),
        "name": properties.get("name", [""])[0] if properties.get("name") else None,
        "schema": match.get("schema"),
        "caption": match.get("caption"),
        "match_score": match.get("score", 0),
        "datasets": match.get("datasets", []),
        "topics": properties.get("topics", []),
        "countries": properties.get("country", []),
        "birth_date": properties.get("birthDate", [None])[0],
        "program": properties.get("program", []),
        "sanctions": properties.get("sanctions", []),
        "raw_data": match,
    }


# Test entities for development
TEST_ENTITIES = {
    "sanctioned_person": "Vladimir Putin",
    "sanctioned_company": "Rosneft",
    "pep": "Xi Jinping",
    "clean": "John Smith",
}
