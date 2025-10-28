"""
OpenSanctions API Connector

Provides sanctions screening against OpenSanctions database.
"""

import os
from typing import Any, Optional

import httpx

# OpenSanctions API configuration
OPENSANCTIONS_API_URL = "https://api.opensanctions.org"
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY")

# Test entities for development
TEST_ENTITIES = {
    "sanctioned_person": "Vladimir Putin",
    "sanctioned_company": "Rosneft",
    "pep": "Xi Jinping",
    "clean": "John Smith",
}


async def search_entity(
    name: str,
    schema: str = "LegalEntity",
    limit: int = 10,
    datasets: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """
    Search for entities in OpenSanctions database.

    Args:
        name: Entity name to search for
        schema: Entity schema type (e.g., 'Person', 'Company', 'Organization', 'LegalEntity')
        limit: Maximum number of results to return
        datasets: Optional list of specific datasets to search

    Returns:
        List of matching entities

    Raises:
        httpx.HTTPError: If the API request fails
    """
    if not OPENSANCTIONS_API_KEY:
        raise ValueError("OPENSANCTIONS_API_KEY environment variable not set")

    # Prepare request headers with API key
    headers = {
        "Authorization": f"Bearer {OPENSANCTIONS_API_KEY}",
        "Accept": "application/json",
    }

    # Prepare query parameters
    params = {
        "q": name,
        "schema": schema,
        "limit": limit,
    }

    if datasets:
        params["datasets"] = ",".join(datasets)

    # Make API request
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{OPENSANCTIONS_API_URL}/search/default",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    return data.get("results", [])


async def get_entity(entity_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific entity.

    Args:
        entity_id: OpenSanctions entity ID

    Returns:
        Entity details

    Raises:
        httpx.HTTPError: If the API request fails
    """
    if not OPENSANCTIONS_API_KEY:
        raise ValueError("OPENSANCTIONS_API_KEY environment variable not set")

    headers = {
        "Authorization": f"Bearer {OPENSANCTIONS_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{OPENSANCTIONS_API_URL}/entities/{entity_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


def normalize_match_data(entity: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize OpenSanctions entity data to a consistent format.

    Args:
        entity: Raw entity data from OpenSanctions

    Returns:
        Normalized entity data
    """
    properties = entity.get("properties", {})

    # Extract names (can be multiple)
    names = properties.get("name", [])
    primary_name = names[0] if names else entity.get("caption", "Unknown")

    # Extract countries
    countries = properties.get("country", [])

    # Extract topics (sanction programs, etc.)
    topics = properties.get("topics", [])

    # Extract dates
    created_at = properties.get("createdAt", [])
    modified_at = properties.get("modifiedAt", [])

    return {
        "id": entity.get("id"),
        "name": primary_name,
        "all_names": names,
        "schema": entity.get("schema"),
        "countries": countries,
        "topics": topics,
        "datasets": entity.get("datasets", []),
        "created_at": created_at[0] if created_at else None,
        "modified_at": modified_at[0] if modified_at else None,
        "caption": entity.get("caption"),
        "properties": properties,
    }


def calculate_risk_score(results: list[dict[str, Any]]) -> int:
    """
    Calculate a risk score based on sanctions screening results.

    Args:
        results: List of matching entities from OpenSanctions

    Returns:
        Risk score from 0-100 (0 = no risk, 100 = maximum risk)
    """
    if not results:
        return 0

    # Base score on number of matches
    base_score = min(len(results) * 15, 60)

    # Increase score based on topics (sanctions, PEP, etc.)
    max_topic_score = 0
    high_risk_topics = {
        "sanction": 40,
        "crime": 30,
        "role.pep": 25,
        "poi": 20,
        "fin": 15,
    }

    for entity in results:
        topics = entity.get("properties", {}).get("topics", [])
        for topic in topics:
            for risk_topic, score in high_risk_topics.items():
                if risk_topic in topic.lower():
                    max_topic_score = max(max_topic_score, score)

    total_score = min(base_score + max_topic_score, 100)
    return total_score
