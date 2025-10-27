""" (main.py content - copy as above) """
import os
import logging
import json
import time
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.mcp_server.auth import require_api_key
from services.mcp_server.redis_client import get_redis
from services.mcp_server.utils.security import redact_pii, hash_identifier
from services.mcp_server.orchestrator import orchestrator_get_company_profile

logger = logging.getLogger("mcp-server")
logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="Compliance Copilot MCP Server", version="0.1.0")

class CompanyQuery(BaseModel):
    country: str
    query: str
    premium: bool = False
    include_history: bool = False

@app.middleware("http")
async def redact_logs_middleware(request: Request, call_next):
    req_info = {
        "method": request.method,
        "path": redact_pii(str(request.url.path)),
    }
    logger.info(json.dumps({"event":"request.start", "request": req_info}))
    start = time.time()
    response = await call_next(request)
    latency = time.time() - start
    logger.info(json.dumps({"event":"request.end","path": req_info["path"], "status": response.status_code, "latency": latency}))
    return response

async def _acquire_token(api_key: str) -> bool:
    redis = await get_redis()
    if not redis:
        return True
    key = f"rl:{hash_identifier(api_key)}"
    tokens = int(os.getenv("RATE_LIMIT_TOKENS", "100"))
    window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    try:
        cur = await redis.incr(key)
        if cur == 1:
            await redis.expire(key, window)
        if cur > tokens:
            return False
        return True
    except Exception as e:
        logger.warning("Rate limiter failed, allowing: %s", e)
        return True

@app.post("/mcp/get_company_profile")
async def get_company_profile(query: CompanyQuery, api_key: str = Depends(require_api_key)):
    allowed = await _acquire_token(api_key)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    params = query.dict()
    logger.info("get_company_profile called country=%s query=%s premium=%s", params["country"], redact_pii(params["query"]), params.get("premium", False))
    result = await orchestrator_get_company_profile(params)
    if "audit" in result and "raw_calls" in result["audit"]:
        result["audit"]["raw_calls"] = {k: {"fetched": bool(v.get("fetched", True))} for k,v in result["audit"]["raw_calls"].items()}
    return JSONResponse(result)

@app.get("/.well-known/mcp-tools")
def list_tools():
    import os, json
    path = os.path.join(os.path.dirname(__file__), "mcp_tools.json")
    if not os.path.exists(path):
        return {
            "tools": [
                {
                    "name": "get_company_profile",
                    "description": "Fetch a normalized company profile and optional compliance intelligence.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "country": {"type": "string", "enum": ["NL", "BE", "LU"]},
                            "query": {"type": "string"},
                            "premium": {"type": "boolean", "default": False}
                        },
                        "required": ["country", "query"]
                    }
                }
            ]
        }
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/admin/forget_company")
async def forget_company(company_id: str, api_key: str = Depends(require_api_key)):
    job = {"status": "queued", "company_id_hash": hash_identifier(company_id)}
    logger.info("forget_company requested (hashed=%s)", job["company_id_hash"])
    return job
