from __future__ import annotations
"""
Orchestrator module for Compliance Copilot MCP Server.

Responsibilities (starter implementation):
- Normalize incoming queries
- Decide which connectors to call
- Coordinate calls (async) and merge responses
- Apply caching hooks (Redis placeholder)
- Compute risk via core.scoring.compute_risk
- Produce unified CompanyProfileV1 dict

This is intentionally a pragmatic, Copilot-friendly skeleton with TODOs for caching, persistent snapshots, rate-limiting, billing hooks, and connector circuit-breakers.
"""
from typing import Any, Dict, List, Optional
import os
import asyncio
import logging
from datetime import datetime

try:
    import aioredis
except Exception:
    aioredis = None  # Redis optional for now

from connectors.kvk_connector import search_company as kvk_search, get_basisprofiel as kvk_basisprofiel
from connectors.opensanctions_connector import search as opensanctions_search
from core.scoring import compute_risk

logger = logging.getLogger("mcp-orchestrator")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL_SEARCH = int(os.getenv("CACHE_TTL_SEARCH", "900"))  # 15 minutes default
CACHE_TTL_PROFILE = int(os.getenv("CACHE_TTL_PROFILE", "86400"))  # 24 hours

# Simple in-process cache fallback (for local dev) when Redis not configured
_inprocess_cache: Dict[str, Dict[str, Any]] = {}

async def _get_redis() -> Optional[aioredis.Redis]:
    if not aioredis:
        return None
    try:
        return await aioredis.from_url(REDIS_URL)
    except Exception as e:
        logger.warning("Redis not available: %s", e)
        return None

async def cache_get(key: str) -> Optional[Any]:
    redis = await _get_redis()
    if redis:
        try:
            val = await redis.get(key)
            if val is None:
                return None
            # assume JSON stored as bytes
            import json
            return json.loads(val)
        except Exception as e:
            logger.debug("Redis get failed for %s: %s", key, e)
    # fallback in-process
    item = _inprocess_cache.get(key)
    if item and item.get("expires_at") and item["expires_at"] > datetime.utcnow().timestamp():
        return item.get("value")
    return None

async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    redis = await _get_redis()
    if redis:
        try:
            import json
            await redis.set(key, json.dumps(value), ex=ttl)
            return
        except Exception as e:
            logger.debug("Redis set failed for %s: %s", key, e)
    # fallback
    _inprocess_cache[key] = {"value": value, "expires_at": datetime.utcnow().timestamp() + ttl}

# Utilities

def _normalize_query(query: str) -> Dict[str, Any]:
    q = query.strip()
    result = {
        "raw": q,
        "is_reg_number": False,
        "is_vat": False,
        "normalized_name": None,
    }
    # naive registration number detection: all digits (allow spaces)
    if q.replace(" ", "").isdigit():
        result["is_reg_number"] = True
    # naive VAT detection: starts with 2 letters + digits
    if len(q) > 2 and q[:2].isalpha() and q[2:].replace(" ", "").isdigit():
        result["is_vat"] = True
    # basic normalized name
    result["normalized_name"] = q.lower()
    return result

async def orchestrator_get_company_profile(params: Dict[str, Any]) -> Dict[str, Any]:
    """Main orchestrator entrypoint called by the FastAPI handler.

    Steps implemented here:
     - normalize input
     - check cache
     - call registry connector(s)
     - call sanctions provider(s)
     - merge and compute risk
     - return unified CompanyProfileV1

    This is intentionally conservative: it returns partial results on connector failures and logs errors.
    """
    country = params.get("country", "").upper()
    query = params.get("query", "").strip()
    premium = bool(params.get("premium", False))
    include_history = bool(params.get("include_history", False))

    norm = _normalize_query(query)
    cache_key = f"profile:{country}:{norm['raw']}:{'premium' if premium else 'basic'}"
    # 1) try cache
    cached = await cache_get(cache_key)
    if cached:
        logger.info("Cache hit for %s", cache_key)
        return cached

    # Prepare response skeleton
    company = {
        "name": None,
        "country": country,
        "registration_number": None,
        "vat_number": None,
        "kvk_number": None,
        "status": "unknown",
        "registered_address": None,
        "legal_form": None,
        "sbi_codes": [],
    }
    basic_checks = {"vat_valid": None, "reg_verified": False, "last_data_pull": datetime.utcnow().isoformat() + "Z"}
    sanctions_section = {"hits_count": 0, "matches": []}
    audit = {"sources": [], "raw_calls": {}}

    # 2) Registry lookup
    try:
        if country == "NL":
            # If it's detected as a reg number and premium, try basisprofiel first
            if norm["is_reg_number"] and premium:
                bp = await kvk_basisprofiel(norm["raw"])  # connector maps minimal fields
                audit["raw_calls"]["kvk_basisprofiel"] = {"fetched": bool(bp)}
                if bp:
                    company["name"] = bp.get("name")
                    company["kvk_number"] = bp.get("kvkNumber")
                    company["registration_number"] = bp.get("kvkNumber")
                    company["legal_form"] = bp.get("legalForm")
                    company["registered_address"] = bp.get("address")
                    company["status"] = bp.get("status") or "unknown"
                    basic_checks["reg_verified"] = True
                    audit["sources"].append(f"kvk:basisprofiel:{company.get('kvk_number')}")
            else:
                # Search
                sr = await kvk_search(norm["raw"]) or {}
                audit["raw_calls"]["kvk_search"] = {"result_count": len(sr.get("data", [])) if isinstance(sr, dict) else None}
                hits = sr.get("data") if isinstance(sr, dict) else []
                if hits and len(hits) == 1:
                    it = hits[0]
                    company["name"] = it.get("name") or it.get("handelsnaam")
                    company["kvk_number"] = it.get("kvkNumber") or it.get("kvk_nummer")
                    company["registration_number"] = company["kvk_number"]
                    company["status"] = it.get("status") or company["status"]
                    company["registered_address"] = it.get("address")
                    basic_checks["reg_verified"] = True
                    audit["sources"].append(f"kvk:search:{company.get('kvk_number')}")
                else:
                    audit["sources"].append(f"kvk:search:multiple_or_none:{len(hits) if hits is not None else 'unknown'}")
        elif country == "BE":
            # TODO: call CBE connector; for now mark skipped
            audit["sources"].append("cbe:skipped")
        elif country == "LU":
            # TODO: call LBR connector
            audit["sources"].append("lbr:skipped")
        else:
            audit["sources"].append("registry:unknown_country")
    except Exception as e:
        logger.exception("Registry lookup failed: %s", e)
        audit["raw_calls"]["registry_error"] = {"error": str(e)}

    # 3) Sanctions/PEP screening
    try:
        osr = await opensanctions_search(query)
        matches = osr.get("matches") if isinstance(osr, dict) else []
        sanctions_section["hits_count"] = len(matches)
        for m in matches:
            sanctions_section["matches"].append({
                "source": m.get("source") or "opensanctions",
                "entity_id": m.get("id"),
                "confidence": float(m.get("confidence", 0.8)),
                "matched_name": m.get("name"),
                "raw": m.get("raw") if isinstance(m.get("raw", None), dict) else m.get("raw")
            })
        audit["raw_calls"]["opensanctions"] = {"result_count": sanctions_section["hits_count"]}
        if sanctions_section["hits_count"]:
            audit["sources"].append("opensanctions")
    except Exception as e:
        logger.exception("Sanctions provider failed: %s", e)
        audit["raw_calls"]["opensanctions_error"] = {"error": str(e)}

    # 4) Compute risk
    scoring_input = {
        "company": company,
        "sanctions": sanctions_section,
        "pep": {"hits_count": 0, "matches": []},
        "ubo": {"missing_and_required": False},
        "status": company.get("status", "unknown"),
        "recent_name_changes": 0
    }
    risk = compute_risk(scoring_input)

    result = {
        "company": company,
        "basic_checks": basic_checks,
        "sanctions": sanctions_section,
        "risk_score": risk,
        "audit": audit
    }

    # 5) cache profile for a longer TTL (profiles change less frequently)
    try:
        await cache_set(cache_key, result, ttl=CACHE_TTL_PROFILE)
    except Exception as e:
        logger.debug("Cache set failed: %s", e)

    return result


# Lightweight helper for multiple parallel calls (example usage)
async def _parallel_map(coros: List[Any]) -> List[Any]:
    results = await asyncio.gather(*coros, return_exceptions=True)
    return results


# Exported for import by FastAPI main
__all__ = ["orchestrator_get_company_profile"]