"""
Local stub for core.scoring.compute_risk

Replace with your real scoring logic. This stub returns a deterministic,
safe risk result suitable for development and unit tests without external
dependencies. It intentionally returns minimal structured data that your
orchestrator/logging/audit code can consume.
"""

from typing import Any, Dict

def compute_risk(profile: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Compute a minimal risk summary for a company profile.

    Args:
      profile: normalized company profile dict (may be partial in dev).
      context: optional context such as sources, country, premium flag.

    Returns:
      A dict with at least:
        - score: float (0.0..1.0)
        - reasons: list[str]
        - provenance: dict (pseudonymized references)
    """
    # Deterministic, safe placeholder logic:
    name = (profile or {}).get("name") or (profile or {}).get("company") or ""
    score = 0.0
    reasons = []
    if name and len(name) % 2 == 0:
        score = 0.2
        reasons.append("name-length-even-stub")
    elif name:
        score = 0.05
        reasons.append("name-length-odd-stub")
    else:
        reasons.append("no-name-stub")

    return {
        "score": float(score),
        "reasons": reasons,
        "provenance": {"stub": True}
    }
