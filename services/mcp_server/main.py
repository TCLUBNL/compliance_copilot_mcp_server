"""
Compliance Copilot MCP Server - FastAPI Application

Main API server for compliance checks, company profile lookups, and risk scoring.
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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

### Use Cases

- **KYC/AML Compliance**: Verify customer identities and screen for sanctions
- **Due Diligence**: Research companies before business relationships
- **Risk Management**: Automated risk scoring for compliance workflows
- **Regulatory Reporting**: Access structured data for compliance reports

### Getting Started

1. Obtain API credentials (if authentication is enabled)
2. Use `/api/v1/search` to find companies by name or KVK number
3. Retrieve detailed profiles with `/api/v1/profile/{kvk_number}`
4. Get risk assessments with `/api/v1/risk/{kvk_number}`

### Support

- 📧 Email: support@tclubnl.com
- 🐛 Issues: [GitHub Issues](https://github.com/TCLUBNL/compliance_copilot_mcp_server/issues)
- 📖 Docs: [Full Documentation](https://github.com/TCLUBNL/compliance_copilot_mcp_server)
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
        {
            "name": "search",
            "description": "Search for companies in the KVK database",
        },
        {
            "name": "profiles",
            "description": "Retrieve detailed company profiles and information",
        },
        {
            "name": "risk",
            "description": "Risk scoring and compliance assessments",
        },
        {
            "name": "sanctions",
            "description": "International sanctions screening via OpenSanctions",
        },
        {
            "name": "health",
            "description": "Service health and monitoring endpoints",
        },
    ],
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status", example="healthy")
    version: str = Field(..., description="API version", example="0.1.0")
    timestamp: str = Field(..., description="Current server time", example="2025-10-27T18:30:00Z")


class CompanySearchResult(BaseModel):
    """Company search result"""

    kvk_number: str = Field(..., description="KVK number", example="12345678")
    name: str = Field(..., description="Company name", example="Tesla Motors Netherlands B.V.")
    city: Optional[str] = Field(None, description="City", example="Amsterdam")
    match_score: float = Field(..., description="Match confidence (0-1)", example=0.95)


class CompanyProfile(BaseModel):
    """Detailed company profile"""

    kvk_number: str = Field(..., description="KVK number", example="12345678")
    name: str = Field(
        ..., description="Legal company name", example="Tesla Motors Netherlands B.V."
    )
    trade_names: list[str] = Field(
        default_factory=list, description="Trade names", example=["Tesla"]
    )
    address: Optional[dict] = Field(None, description="Company address")
    status: str = Field(..., description="Company status", example="Active")
    founded_date: Optional[str] = Field(None, description="Foundation date", example="2010-01-15")
    employees: Optional[int] = Field(None, description="Number of employees", example=150)
    sbi_codes: list[str] = Field(default_factory=list, description="SBI activity codes")


class RiskAssessment(BaseModel):
    """Risk assessment result"""

    kvk_number: str = Field(..., description="KVK number", example="12345678")
    company_name: str = Field(
        ..., description="Company name", example="Tesla Motors Netherlands B.V."
    )
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)", example=15.5)
    risk_level: str = Field(..., description="Risk level", example="LOW")
    factors: list[str] = Field(
        default_factory=list,
        description="Risk factors identified",
        example=["No sanctions matches", "Active company status"],
    )
    sanctions_hits: int = Field(default=0, description="Number of sanctions matches", example=0)
    checked_at: str = Field(..., description="Assessment timestamp", example="2025-10-27T18:30:00Z")


class ErrorResponse(BaseModel):
    """Error response"""

    error: str = Field(..., description="Error message", example="Company not found")
    detail: Optional[str] = Field(None, description="Additional error details")
    code: str = Field(..., description="Error code", example="NOT_FOUND")


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is running and get version information",
)
async def health_check():
    """
    Simple health check endpoint.

    Returns service status, version, and current timestamp.
    Useful for monitoring and load balancer health checks.
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


# Root endpoint
@app.get(
    "/",
    tags=["health"],
    summary="API information",
    description="Get basic API information and links to documentation",
)
async def root():
    """
    Root endpoint with API information.

    Provides links to interactive documentation and basic API metadata.
    """
    return {
        "name": "Compliance Copilot MCP Server",
        "version": __version__,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


# Company search endpoint
@app.get(
    "/api/v1/search",
    tags=["search"],
    response_model=list[CompanySearchResult],
    summary="Search companies",
    description="Search for companies by name or KVK number in the Dutch Chamber of Commerce database",
    responses={
        200: {
            "description": "Successful search results",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "kvk_number": "12345678",
                            "name": "Tesla Motors Netherlands B.V.",
                            "city": "Amsterdam",
                            "match_score": 0.95,
                        }
                    ]
                }
            },
        },
        400: {"model": ErrorResponse, "description": "Invalid search parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def search_companies(
    query: str = Query(
        ..., description="Company name or KVK number to search for", example="Tesla"
    ),
    country: str = Query(default="NL", description="Country code", example="NL"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
):
    """
    Search for companies in the KVK database.

    **Parameters:**
    - **query**: Company name or KVK number (required)
    - **country**: ISO country code (default: NL)
    - **limit**: Maximum number of results (1-100, default: 10)

    **Returns:**
    - List of matching companies with match scores
    - Empty list if no matches found

    **Example:**
    ```
    GET /api/v1/search?query=Tesla&limit=5
    ```
    """
    # TODO: Implement actual search logic
    # For now, return mock data
    return [
        CompanySearchResult(
            kvk_number="12345678",
            name="Tesla Motors Netherlands B.V.",
            city="Amsterdam",
            match_score=0.95,
        )
    ]


# Company profile endpoint
@app.get(
    "/api/v1/profile/{kvk_number}",
    tags=["profiles"],
    response_model=CompanyProfile,
    summary="Get company profile",
    description="Retrieve detailed company profile by KVK number",
    responses={
        200: {"description": "Company profile found"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_company_profile(
    kvk_number: str = Path(
        ..., description="KVK number (8 digits)", example="12345678", regex="^[0-9]{8}$"
    )
):
    """
    Get detailed company profile from KVK.

    **Parameters:**
    - **kvk_number**: 8-digit KVK number (required, in URL path)

    **Returns:**
    - Complete company profile with all available data
    - Includes address, trade names, SBI codes, etc.

    **Example:**
    ```
    GET /api/v1/profile/12345678
    ```
    """
    # TODO: Implement actual profile retrieval
    return CompanyProfile(
        kvk_number=kvk_number,
        name="Tesla Motors Netherlands B.V.",
        trade_names=["Tesla", "Tesla Motors"],
        status="Active",
        founded_date="2010-01-15",
        employees=150,
        sbi_codes=["45112"],
    )


# Risk assessment endpoint
@app.get(
    "/api/v1/risk/{kvk_number}",
    tags=["risk"],
    response_model=RiskAssessment,
    summary="Get risk assessment",
    description="Get compliance risk assessment for a company including sanctions screening",
    responses={
        200: {"description": "Risk assessment completed"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_risk_assessment(
    kvk_number: str = Path(
        ..., description="KVK number (8 digits)", example="12345678", regex="^[0-9]{8}$"
    )
):
    """
    Perform compliance risk assessment.

    Combines data from multiple sources:
    - KVK company data
    - OpenSanctions screening
    - Risk scoring algorithm

    **Parameters:**
    - **kvk_number**: 8-digit KVK number (required, in URL path)

    **Returns:**
    - Risk score (0-100)
    - Risk level (LOW/MEDIUM/HIGH/CRITICAL)
    - Identified risk factors
    - Sanctions screening results

    **Example:**
    ```
    GET /api/v1/risk/12345678
    ```
    """
    # TODO: Implement actual risk assessment
    return RiskAssessment(
        kvk_number=kvk_number,
        company_name="Tesla Motors Netherlands B.V.",
        risk_score=15.5,
        risk_level="LOW",
        factors=["No sanctions matches", "Active company status"],
        sanctions_hits=0,
        checked_at=datetime.utcnow().isoformat() + "Z",
    )


# Sanctions screening endpoint
@app.get(
    "/api/v1/sanctions/screen",
    tags=["sanctions"],
    summary="Screen for sanctions",
    description="Check if a company or person appears in international sanctions lists",
)
async def screen_sanctions(
    name: str = Query(..., description="Company or person name to screen", example="Tesla Motors"),
    entity_type: str = Query(
        default="company", description="Entity type: company or person", example="company"
    ),
):
    """
    Screen against international sanctions lists.

    Uses OpenSanctions database to check for:
    - OFAC sanctions
    - EU sanctions
    - UN sanctions
    - Other international watchlists

    **Parameters:**
    - **name**: Entity name to screen (required)
    - **entity_type**: Type of entity (company/person, default: company)

    **Returns:**
    - List of potential matches with confidence scores
    - Empty list if no matches found

    **Example:**
    ```
    GET /api/v1/sanctions/screen?name=Tesla Motors&entity_type=company
    ```
    """
    # TODO: Implement actual sanctions screening
    return {
        "matches": [],
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "sources": ["OpenSanctions"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
