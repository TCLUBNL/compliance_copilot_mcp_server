"""
KVK (Kamer van Koophandel) Connector

Integrates with the Dutch Chamber of Commerce API to retrieve company information.
Uses KVK Test API for development and testing.
"""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# KVK API Configuration
KVK_API_KEY = os.getenv("KVK_API_KEY", "l7xx1f2691f2520d487b902f4e0b57a0b197")
KVK_BASE_URL = os.getenv("KVK_BASE_URL", "https://api.kvk.nl/test/api")
KVK_TIMEOUT = int(os.getenv("KVK_TIMEOUT", "30"))

# API Endpoints
SEARCH_ENDPOINT = f"{KVK_BASE_URL}/v2/zoeken"
BASISPROFIEL_ENDPOINT = f"{KVK_BASE_URL}/v1/basisprofielen"
VESTIGINGSPROFIEL_ENDPOINT = f"{KVK_BASE_URL}/v1/vestigingsprofielen"


class KVKError(Exception):
    """Base exception for KVK API errors"""

    pass


class KVKAPIError(KVKError):
    """KVK API returned an error"""

    pass


class KVKNotFoundError(KVKError):
    """Company or establishment not found"""

    pass


class KVKRateLimitError(KVKError):
    """Rate limit exceeded"""

    pass


async def _make_request(
    url: str,
    params: Optional[dict[str, Any]] = None,
    timeout: int = KVK_TIMEOUT,
) -> dict[str, Any]:
    """Make an authenticated request to the KVK API."""
    headers = {"apikey": KVK_API_KEY, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info(f"KVK API Request: {url} with params {params}")
            response = await client.get(url, headers=headers, params=params)

            # Handle specific status codes
            if response.status_code == 404:
                raise KVKNotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                raise KVKRateLimitError("KVK API rate limit exceeded")
            elif response.status_code >= 400:
                raise KVKAPIError(f"KVK API error: {response.status_code} - {response.text}")

            response.raise_for_status()
            data = response.json()
            logger.info(f"KVK API Response: {response.status_code}")
            return data

    except KVKError:
        raise
    except httpx.TimeoutException as e:
        logger.error(f"KVK API timeout after {timeout}s")
        raise KVKAPIError(f"Request timeout after {timeout}s") from e
    except httpx.HTTPError as e:
        logger.error(f"KVK API HTTP error: {e}")
        raise KVKAPIError(f"HTTP error: {e}") from e
    except Exception as e:
        logger.error(f"KVK API unexpected error: {e}")
        raise KVKAPIError(f"Unexpected error: {e}") from e


async def search_company(
    query: str,
    company_type: Optional[str] = None,
    city: Optional[str] = None,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search for companies in the KVK database."""
    params = {
        "naam": query,
        "resultatenPerPagina": min(max_results, 1000),
    }

    if company_type:
        params["type"] = company_type
    if city:
        params["plaats"] = city

    try:
        data = await _make_request(SEARCH_ENDPOINT, params)
        results = data.get("resultaten", [])
        logger.info(f"Found {len(results)} results for query: {query}")
        return results

    except KVKError:
        raise
    except Exception as e:
        logger.error(f"Error searching company: {e}")
        return []


async def get_basisprofiel(kvk_number: str) -> dict[str, Any]:
    """Get base profile (basisprofiel) for a company by KVK number."""
    url = f"{BASISPROFIEL_ENDPOINT}/{kvk_number}"
    data = await _make_request(url)
    logger.info(f"Retrieved basisprofiel for KVK: {kvk_number}")
    return data


async def get_eigenaar(kvk_number: str) -> dict[str, Any]:
    """Get owner (eigenaar) information for a company."""
    url = f"{BASISPROFIEL_ENDPOINT}/{kvk_number}/eigenaar"
    return await _make_request(url)


async def get_hoofdvestiging(kvk_number: str) -> dict[str, Any]:
    """Get main establishment (hoofdvestiging) for a company."""
    url = f"{BASISPROFIEL_ENDPOINT}/{kvk_number}/hoofdvestiging"
    return await _make_request(url)


async def get_vestigingen(kvk_number: str) -> list[dict[str, Any]]:
    """Get all establishments (vestigingen) for a company."""
    url = f"{BASISPROFIEL_ENDPOINT}/{kvk_number}/vestigingen"
    data = await _make_request(url)
    return data.get("vestigingen", [])


async def get_vestigingsprofiel(vestiging_number: str) -> dict[str, Any]:
    """Get establishment profile by establishment number."""
    url = f"{VESTIGINGSPROFIEL_ENDPOINT}/{vestiging_number}"
    return await _make_request(url)


def normalize_company_data(kvk_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize KVK API response to internal company schema."""
    return {
        "kvk_number": kvk_data.get("kvkNummer"),
        "name": kvk_data.get("naam"),
        "legal_form": kvk_data.get("rechtsvorm"),
        "trade_names": kvk_data.get("handelsNamen", []),
        "sbi_codes": [
            {
                "code": sbi.get("sbiCode"),
                "description": sbi.get("sbiOmschrijving"),
                "primary": sbi.get("indHoofdactiviteit", False),
            }
            for sbi in kvk_data.get("sbiActiviteiten", [])
        ],
        "establishment_address": _normalize_address(
            kvk_data.get("_embedded", {}).get("hoofdvestiging", {}).get("adressen", [])
        ),
        "status": kvk_data.get("statutaireNaam"),
        "foundation_date": kvk_data.get("datumAanvang"),
        "raw_data": kvk_data,
    }


def _normalize_address(addresses: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Normalize address data from KVK format."""
    if not addresses:
        return None

    addr = addresses[0]
    return {
        "street": addr.get("straatnaam"),
        "house_number": addr.get("huisnummer"),
        "postal_code": addr.get("postcode"),
        "city": addr.get("plaats"),
        "country": addr.get("land", "Nederland"),
    }


# Test data KVK numbers for development
TEST_KVK_NUMBERS = {
    "eenmanszaak": "69599084",
    "bv": "68750110",
    "nv": "68727720",
    "stichting": "69599068",
    "vof": "69599076",
    "error": "90002903",
}
