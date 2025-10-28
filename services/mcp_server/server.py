"""
Compliance Copilot MCP Server

Model Context Protocol server exposing compliance tools for LLMs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP  # noqa: E402

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)

mcp = FastMCP(name="ComplianceHub")

# Import connectors  # noqa: E402
try:
    from connectors.kvk_connector import get_basisprofiel, normalize_company_data, search_company
    from connectors.opensanctions_connector import calculate_risk_score as calculate_sanctions_risk
    from connectors.opensanctions_connector import normalize_match_data, search_entity

    logger.info("Successfully imported connectors")
except ImportError as e:
    logger.error(f"Failed to import connectors: {e}")
    raise


@mcp.tool()
async def search_dutch_company(
    query: str, city: Optional[str] = None, max_results: int = 10
) -> dict:
    """Search for Dutch companies in the KVK register."""
    try:
        logger.info(f"Searching KVK for: {query}")
        results = await search_company(query, city=city, max_results=max_results)
        companies = [
            {
                "kvk_number": r.get("kvkNummer", ""),
                "name": r.get("naam", ""),
                "city": r.get("plaats", ""),
            }
            for r in results
        ]
        return {
            "success": True,
            "query": query,
            "count": len(companies),
            "companies": companies,
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_company_profile(kvk_number: str) -> dict:
    """Get detailed company profile from KVK."""
    try:
        if not kvk_number.isdigit() or len(kvk_number) != 8:
            return {"success": False, "error": "Invalid KVK number"}
        profile = await get_basisprofiel(kvk_number)
        normalized = normalize_company_data(profile)
        return {"success": True, **normalized}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def screen_sanctions(name: str, schema: str = "Organization", max_results: int = 10) -> dict:
    """Screen entity against sanctions lists."""
    try:
        results = await search_entity(name, schema=schema, limit=max_results)
        matches = [normalize_match_data(r) for r in results]
        risk = calculate_sanctions_risk(results)
        return {
            "success": True,
            "total_matches": len(matches),
            "risk_score": risk,
            "matches": matches,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def calculate_risk_score(sanctions_data: dict) -> dict:
    """Calculate risk score from sanctions data."""
    matches = sanctions_data.get("matches", [])
    risk = min(len(matches) * 20, 100)
    level = (
        "CRITICAL" if risk >= 75 else "HIGH" if risk >= 50 else "MEDIUM" if risk >= 25 else "LOW"
    )
    return {"success": True, "risk_score": risk, "risk_level": level}


@mcp.tool()
async def comprehensive_due_diligence(kvk_number: str) -> dict:
    """Complete compliance check combining KVK and sanctions."""
    try:
        profile = await get_company_profile(kvk_number)
        if not profile.get("success"):
            return profile
        sanctions = await screen_sanctions(profile.get("name", ""))
        from datetime import datetime

        return {
            "success": True,
            "company_profile": profile,
            "sanctions_screening": sanctions,
            "risk_assessment": {"risk_score": sanctions.get("risk_score", 0)},
            "checked_at": datetime.utcnow().isoformat() + "Z",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    logger.info("Starting Compliance MCP Server")
    mcp.run()
