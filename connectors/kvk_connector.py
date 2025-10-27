"""
Stub KVK connector for local development.

Replace with the real connector implementation later.
This stub provides:
- search_company(...)
- get_basisprofiel(...)
"""

def search_company(query: str, country: str = None, **kwargs):
    """
    Return a minimal stubbed search result structure expected by orchestrator.
    """
    return {
        "query": query,
        "country": country,
        "results": []
    }

def get_basisprofiel(company_id: str, **kwargs):
    """
    Return a minimal basisprofiel stub for a given company id.
    """
    return {
        "company_id": company_id,
        "name": None,
        "address": None,
        "source": "stub"
    }
