"""
Stdio entry point for the MCP server.
Allows the server to be run as a subprocess and communicated with over stdio.
"""

import asyncio
from gm_shield.features.mcp.server import mcp_server

if __name__ == "__main__":
    import asyncio

    async def run_server():
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    asyncio.run(run_server())
