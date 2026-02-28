"""
MCP Server implementation providing internal tools.
"""

import structlog
from mcp.server import Server
from mcp.types import TextContent, Tool

from gm_shield.features.encounters.service import EncounterAgent
from gm_shield.features.notes.service import create_note
from gm_shield.features.notes.schemas import NoteCreate
from gm_shield.shared.database.sqlite import SessionLocal

logger = structlog.get_logger(__name__)

mcp_server = Server("gm-smart-shield-mcp")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Expose GM Smart Shield tools to the MCP client."""
    return [
        Tool(
            name="generate_encounter",
            description="Generates a tactical RPG encounter with NPC stat blocks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Party level (e.g. 'Level 5')",
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Difficulty (e.g. 'Hard')",
                    },
                    "theme": {
                        "type": "string",
                        "description": "Thematic setting (e.g. 'Goblin Ambush')",
                    },
                },
                "required": ["level", "difficulty", "theme"],
            },
        ),
        Tool(
            name="create_note",
            description="Saves a new GM note with content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the note"},
                    "content": {
                        "type": "string",
                        "description": "Markdown content for the note",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="search_knowledge_base",
            description="Searches the GM's knowledge base (campaign notes, rules, sourcebooks) for specific information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question.",
                    }
                },
                "required": ["query"],
            },
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool request from the MCP client."""
    logger.info("mcp_call_tool", tool_name=name)

    if name == "generate_encounter":
        agent = EncounterAgent()  # We will transition this to deepagents later
        level = arguments.get("level", "Level 1")
        difficulty = arguments.get("difficulty", "Medium")
        theme = arguments.get("theme", "Random")

        encounter = await agent.generate_encounter(level, difficulty, theme)
        if encounter:
            return [TextContent(type="text", text=encounter.model_dump_json())]
        else:
            return [TextContent(type="text", text="Failed to generate encounter.")]

    elif name == "create_note":
        title = arguments.get("title", "Untitled Note")
        content = arguments.get("content", "")

        session = SessionLocal()
        try:
            note_create = NoteCreate(title=title, content=content)
            note = await create_note(session, note_create)
            return [
                TextContent(
                    type="text", text=f"Note created successfully. ID: {note.id}"
                )
            ]
        finally:
            session.close()

    elif name == "search_knowledge_base":
        query = arguments.get("query", "")
        context = await _retrieve_knowledge_context(query)
        if context:
            return [TextContent(type="text", text=context)]
        else:
            return [
                TextContent(
                    type="text", text="No relevant context found in the knowledge base."
                )
            ]

    raise ValueError(f"Unknown tool: {name}")


async def _retrieve_knowledge_context(query: str) -> str:
    """Helper to query ChromaDB for chunks."""
    from gm_shield.shared.database.chroma import get_chroma_client
    from gm_shield.features.knowledge.service import get_embedding_model

    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection("knowledge_base")

        model = get_embedding_model()
        query_embedding = model.encode([query])

        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=3,
            include=["documents", "metadatas"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return ""

        context_str = "\n\n".join(
            [
                f"[Source: {m.get('source', 'Unknown')}]\n{c}"
                for c, m in zip(documents, metadatas)
            ]
        )
        return context_str
    except Exception as e:
        logger.warning("mcp_search_failed", error=str(e))
        return ""
