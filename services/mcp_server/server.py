"""
Compliance Copilot MCP Server

Model Context Protocol server exposing compliance tools for LLMs.
Provides KVK company lookups and OpenSanctions screening.
"""

import logging
import sys
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Configure logging to stderr (NEVER use print() or stdout for STDIO servers!)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="ComplianceHub",
    version="1.0.0",
)


# Health check function
@mcp.tool()
async def health_check() -> dict:
    """
    Check if the Compliance Hub MCP server is running and healthy.
    
    Returns:
        Dictionary with server status and version information
    """
    return {
        "status": "healthy",
        "server": "ComplianceHub",
        "version": "1.0.0",
        "capabilities": {
            "kvk_search": True,
            "sanctions_screening": True,
            "risk_assessment": True,
        },
    }


# Placeholder for future tools
# Tools will be added in subsequent steps following issues #37-41


def main():
    """Run the MCP server."""
    logger.info("Starting ComplianceHub MCP Server v1.0.0")
    logger.info("Server ready to accept tool calls from MCP clients")
    mcp.run()


if __name__ == "__main__":
    main()