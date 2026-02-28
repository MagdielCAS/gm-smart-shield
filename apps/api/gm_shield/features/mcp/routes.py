"""
MCP feature routes. Exposes the internal MCP server via SSE.
"""

from fastapi import APIRouter, Request
from mcp.server.sse import SseServerTransport

from gm_shield.features.mcp.server import mcp_server
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# The endpoint param is the path where messages should be posted.
# When mounted in main.py, e.g. prefix="/api/v1/mcp",
# the root_path becomes "/api/v1/mcp" or "".
# The client will use root_path + "/messages".
sse_transport = SseServerTransport("/api/v1/mcp/messages")


@router.get("/sse")
async def handle_sse(request: Request):
    """Establish SSE connection for MCP."""
    logger.info("mcp_sse_connection_started")
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


@router.post("/messages")
async def handle_messages(request: Request):
    """Receive messages from MCP client."""
    await sse_transport.handle_post_message(
        request.scope, request.receive, request._send
    )
