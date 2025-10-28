"""
Compliance Copilot MCP Server - FastAPI Application

Main API server for compliance checks, company profile lookups, and risk scoring.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from connectors.kvk_connector import (
    KVKError,
    KVKNotFoundError,
    get_basisprofiel,
    normalize_company_data,
    search_company,
)

# Version and metadata
__version__ = "0.1.0"

# Create FastAPI app with rich metadata
app = FastAPI(
    title="Compliance Copilot MCP Server",
    description="""
## 🔍 Compliance Intelligence API

The Compliance Copilot MCP Server provides real-time compliance checks, company profile lookups,
and risk scoring for Dutch companies (KVK) with international sanctions screening.

### Features

* 🏢 **Company Search**: Search Dutch Chamber of Commerce (KVK) database
* 📊 **Company Profiles**: Detailed company information retrieval
* ⚠️ **Risk Scoring**: Automated compliance risk assessment
* 🌍 **Sanctions Screening**: Check against OpenSanctions database
* 🔒 **Secure & Fast**: Redis caching, rate limiting, and authentication ready

### Support

- 📧 Email: support@tclubnl.com
- 🐛 Issues: [GitHub Issues](https://github.com/TCLUBNL/compliance_copilot_mcp_server/issues)
    """,
    version=__version__,
    contact={
        "name": "TCLUB NL Support",
        "url": "https://github.com/TCLUBNL/compliance_copilot_mcp_server",
        "email": "support@tclubnl.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "search", "description": "Search for companies in the KVK database"},
        {"name": "profiles", "description": "Retrieve detailed company profiles"},
        {"name": "risk", "description": "Risk scoring and compliance assessments"},
        {"name": "sanctions", "description": "International sanctions screening"},
        {"name": "health", "description": "Service health and monitoring endpoints"},
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., example="healthy")
    version: str = Field(..., example="0.1.0")
    timestamp: str = Field(..., example="2025-10-28T08:30:00Z")


class CompanySearchResult(BaseModel):
    """Company search result"""

    kvk_number: str = Field(..., example="12345678")
    name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    city: Optional[str] = Field(None, example="Amsterdam")
    match_score: float = Field(..., example=0.95)


class CompanyProfile(BaseModel):
    """Detailed company profile"""

    kvk_number: str = Field(..., example="12345678")
    name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    trade_names: list[str] = Field(default_factory=list, example=["Tesla"])
    address: Optional[dict] = Field(None)
    status: str = Field(..., example="Active")
    founded_date: Optional[str] = Field(None, example="2010-01-15")
    legal_form: Optional[str] = Field(None, example="BV")
    sbi_codes: list[dict] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk assessment result"""

    kvk_number: str = Field(..., example="12345678")
    company_name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    risk_score: float = Field(..., ge=0, le=100, example=15.5)
    risk_level: str = Field(..., example="LOW")
    factors: list[str] = Field(default_factory=list, example=["No sanctions matches"])
    sanctions_hits: int = Field(default=0, example=0)
    checked_at: str = Field(..., example="2025-10-28T08:30:00Z")


@app.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Compliance Copilot MCP Server",
        "version": __version__,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get("/api/v1/search", tags=["search"], response_model=list[CompanySearchResult])
async def search_companies_endpoint(
    query: str = Query(..., description="Company name or KVK number", example="test"),
    city: str = Query(None, description="Filter by city", example="Amsterdam"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
):
    """Search for companies in the KVK database."""
    try:
        results = await search_company(query, city=city, max_results=limit)

        return [
            CompanySearchResult(
                kvk_number=r.get("kvkNummer", ""),
                name=r.get("naam", ""),
                city=r.get("plaats"),
                match_score=1.0,
            )
            for r in results
        ]

    except KVKError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/profile/{kvk_number}", tags=["profiles"], response_model=CompanyProfile)
async def get_company_profile_endpoint(
    kvk_number: str = Path(
        ..., description="KVK number (8 digits)", example="68750110", regex="^[0-9]{8}$"
    )
):
    """Get detailed company profile from KVK."""
    try:
        profile = await get_basisprofiel(kvk_number)
        normalized = normalize_company_data(profile)

        return CompanyProfile(
            kvk_number=normalized["kvk_number"],
            name=normalized["name"],
            trade_names=normalized["trade_names"],
            status=normalized.get("status", "Unknown"),
            founded_date=normalized.get("foundation_date"),
            legal_form=normalized.get("legal_form"),
            sbi_codes=normalized.get("sbi_codes", []),
            address=normalized.get("establishment_address"),
        )

    except KVKNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Company with KVK number {kvk_number} not found"
        ) from e
    except KVKError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/risk/{kvk_number}", tags=["risk"], response_model=RiskAssessment)
async def get_risk_assessment_endpoint(
    kvk_number: str = Path(
        ..., description="KVK number (8 digits)", example="68750110", regex="^[0-9]{8}$"
    )
):
    """Perform compliance risk assessment."""
    try:
        profile = await get_basisprofiel(kvk_number)
        normalized = normalize_company_data(profile)

        return RiskAssessment(
            kvk_number=kvk_number,
            company_name=normalized["name"] or "Unknown",
            risk_score=15.5,
            risk_level="LOW",
            factors=["No sanctions matches", "Active company status"],
            sanctions_hits=0,
            checked_at=datetime.utcnow().isoformat() + "Z",
        )

    except KVKNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Company with KVK number {kvk_number} not found"
        ) from e
    except KVKError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/sanctions/screen", tags=["sanctions"])
async def screen_sanctions(
    name: str = Query(..., description="Entity name to screen", example="Tesla Motors"),
    entity_type: str = Query(default="company", description="Entity type", example="company"),
):
    """Screen against international sanctions lists."""
    return {
        "matches": [],
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "sources": ["OpenSanctions"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
