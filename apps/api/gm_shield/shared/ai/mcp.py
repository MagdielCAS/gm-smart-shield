"""
MCP Server support — exposes API functionality as tools for AI agents.

Uses ``fastapi_mcp`` to bridge FastAPI endpoints with the Model Context Protocol.
"""

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from gm_shield.core.config import settings
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)

# Global MCP instance (will be initialized in setup_mcp)
mcp_bridge: FastApiMCP = None


def setup_mcp(app: FastAPI):
    """
    Register the MCP server with the FastAPI application.

    Mounts the MCP endpoints so agents can discover and use tools.
    """
    global mcp_bridge
    logger.info("mcp_server_initializing")

    # FastApiMCP constructor uses 'fastapi' as the first argument name.
    # It auto-discovers endpoints from the provided application.
    mcp_bridge = FastApiMCP(
        fastapi=app,
        name=settings.PROJECT_NAME,
        description="Provides tools for interacting with GM Smart Shield knowledge and features.",
    )

    # Mount the MCP server (SSE transport)
    mcp_bridge.mount_sse(app)

    logger.info("mcp_server_mounted", prefix="/sse")


def get_mcp() -> FastApiMCP:
    """Return the initialized MCP bridge."""
    return mcp_bridge
