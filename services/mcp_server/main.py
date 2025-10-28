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
from connectors.opensanctions_connector import OpenSanctionsError
from connectors.opensanctions_connector import calculate_risk_score as calculate_sanctions_risk
from connectors.opensanctions_connector import normalize_match_data, search_entity

# Version and metadata
__version__ = "0.1.0"

# Create FastAPI app
app = FastAPI(
    title="Compliance Copilot MCP Server",
    description="""
## 🔍 Compliance Intelligence API

Real-time compliance checks, company profile lookups, and risk scoring.

### Features

* 🏢 **KVK Integration**: Dutch Chamber of Commerce data
* 🌍 **Sanctions Screening**: OpenSanctions international database
* ⚠️ **Risk Assessment**: Automated compliance scoring
* 🔒 **Secure & Fast**: Production-ready architecture

### Support

- 📧 Email: support@tclubnl.com
- 🐛 Issues: [GitHub](https://github.com/TCLUBNL/compliance_copilot_mcp_server/issues)
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
        {"name": "search", "description": "Company search operations"},
        {"name": "profiles", "description": "Company profile retrieval"},
        {"name": "risk", "description": "Risk assessment and scoring"},
        {"name": "sanctions", "description": "International sanctions screening"},
        {"name": "health", "description": "Health and monitoring"},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="0.1.0")
    timestamp: str = Field(..., example="2025-10-28T08:52:00Z")


class CompanySearchResult(BaseModel):
    kvk_number: str = Field(..., example="12345678")
    name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    city: Optional[str] = Field(None, example="Amsterdam")
    match_score: float = Field(..., example=0.95)


class CompanyProfile(BaseModel):
    kvk_number: str = Field(..., example="12345678")
    name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    trade_names: list[str] = Field(default_factory=list)
    address: Optional[dict] = None
    status: str = Field(..., example="Active")
    founded_date: Optional[str] = None
    legal_form: Optional[str] = None
    sbi_codes: list[dict] = Field(default_factory=list)


class SanctionsMatch(BaseModel):
    entity_id: str = Field(..., example="sanc-123")
    name: str = Field(..., example="Sanctioned Entity")
    match_score: float = Field(..., ge=0, le=1, example=0.92)
    schema: str = Field(..., example="Person")
    topics: list[str] = Field(default_factory=list, example=["sanction"])
    countries: list[str] = Field(default_factory=list, example=["RU"])
    datasets: list[str] = Field(default_factory=list)


class SanctionsScreeningResult(BaseModel):
    query: str = Field(..., example="Vladimir Putin")
    matches: list[SanctionsMatch] = Field(default_factory=list)
    total_matches: int = Field(..., example=5)
    risk_score: float = Field(..., ge=0, le=100, example=95.0)
    checked_at: str = Field(..., example="2025-10-28T08:52:00Z")


class RiskAssessment(BaseModel):
    kvk_number: str = Field(..., example="12345678")
    company_name: str = Field(..., example="Tesla Motors Netherlands B.V.")
    risk_score: float = Field(..., ge=0, le=100, example=15.5)
    risk_level: str = Field(..., example="LOW")
    factors: list[str] = Field(default_factory=list)
    sanctions_hits: int = Field(default=0, example=0)
    checked_at: str = Field(..., example="2025-10-28T08:52:00Z")


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
    """Root endpoint."""
    return {
        "name": "Compliance Copilot MCP Server",
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/api/v1/search", tags=["search"], response_model=list[CompanySearchResult])
async def search_companies_endpoint(
    query: str = Query(..., description="Company name or KVK number", example="test"),
    city: str = Query(None, description="Filter by city"),
    limit: int = Query(default=10, ge=1, le=100),
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
    kvk_number: str = Path(..., regex="^[0-9]{8}$", example="68750110")
):
    """Get detailed company profile."""
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
        raise HTTPException(status_code=404, detail=str(e)) from e
    except KVKError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/v1/sanctions/screen",
    tags=["sanctions"],
    response_model=SanctionsScreeningResult,
)
async def screen_sanctions(
    name: str = Query(..., description="Entity name to screen", example="Test Company"),
    schema: str = Query(default="Organization", description="Entity type", example="Organization"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """
    Screen entity against international sanctions lists.

    Checks OpenSanctions database including:
    - OFAC sanctions
    - EU sanctions
    - UN sanctions
    - PEP databases
    - Criminal watchlists
    """
    try:
        # Search OpenSanctions
        results = await search_entity(name, schema=schema, limit=limit)

        # Normalize results
        matches = [normalize_match_data(r) for r in results]

        # Calculate risk score
        risk_score = calculate_sanctions_risk(results)

        # Build response
        return SanctionsScreeningResult(
            query=name,
            matches=[
                SanctionsMatch(
                    entity_id=m["entity_id"] or "unknown",
                    name=m["name"] or "Unknown",
                    match_score=m["match_score"],
                    schema=m["schema"] or schema,
                    topics=m["topics"],
                    countries=m["countries"],
                    datasets=m["datasets"],
                )
                for m in matches
            ],
            total_matches=len(matches),
            risk_score=risk_score,
            checked_at=datetime.utcnow().isoformat() + "Z",
        )
    except OpenSanctionsError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/risk/{kvk_number}", tags=["risk"], response_model=RiskAssessment)
async def get_risk_assessment_endpoint(
    kvk_number: str = Path(..., regex="^[0-9]{8}$", example="68750110")
):
    """
    Comprehensive risk assessment combining KVK and sanctions data.
    """
    try:
        # Get company profile
        profile = await get_basisprofiel(kvk_number)
        normalized = normalize_company_data(profile)
        company_name = normalized["name"] or "Unknown"

        # Screen for sanctions
        sanctions_results = await search_entity(company_name, schema="Organization", limit=10)
        sanctions_hits = len(sanctions_results)
        sanctions_risk = calculate_sanctions_risk(sanctions_results)

        # Calculate overall risk
        base_risk = 10.0  # Base risk for any company
        overall_risk = base_risk + (sanctions_risk * 0.9)  # Weight sanctions heavily

        # Determine risk level
        if overall_risk >= 75:
            risk_level = "CRITICAL"
        elif overall_risk >= 50:
            risk_level = "HIGH"
        elif overall_risk >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Build factors
        factors = []
        if sanctions_hits == 0:
            factors.append("No sanctions matches found")
        else:
            factors.append(f"{sanctions_hits} potential sanctions matches")

        if normalized.get("status"):
            factors.append(f"Company status: {normalized['status']}")

        return RiskAssessment(
            kvk_number=kvk_number,
            company_name=company_name,
            risk_score=round(overall_risk, 2),
            risk_level=risk_level,
            factors=factors,
            sanctions_hits=sanctions_hits,
            checked_at=datetime.utcnow().isoformat() + "Z",
        )
    except KVKNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (KVKError, OpenSanctionsError) as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
