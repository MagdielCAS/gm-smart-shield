"""
Encounter generation services.
"""

from typing import List, Optional
import structlog
from pydantic import BaseModel, Field

from gm_shield.shared.llm.client import OllamaClient, Message, Role

logger = structlog.get_logger(__name__)


class NPCStatBlock(BaseModel):
    """Structured NPC stat block."""

    name: str = Field(description="Name of the creature or NPC.")
    creature_type: str = Field(description="Type and size (e.g. Medium Humanoid).")
    cr: str = Field(description="Challenge Rating.")
    hp: str = Field(description="Hit Points (e.g. 50 (8d8 + 14)).")
    ac: str = Field(description="Armor Class.")
    speed: str = Field(description="Movement speed.")
    stats: str = Field(description="Ability scores formatted as STR 10 (+0), DEX...")
    actions: List[str] = Field(description="List of action descriptions.")
    special_abilities: Optional[List[str]] = Field(
        default=None, description="Passive traits or special abilities."
    )


class EncounterResponse(BaseModel):
    """
    The structured output of the encounter generation.
    """

    title: str = Field(description="A creative title for the encounter.")
    description: str = Field(
        description="A vivid narrative description of the scene and setup."
    )
    tactics: str = Field(
        description="Tactical advice for the GM on how the enemies behave."
    )
    loot: Optional[str] = Field(
        default=None, description="Potential rewards or treasure."
    )
    npcs: List[NPCStatBlock] = Field(description="List of stat blocks for the enemies.")


class EncounterAgent:
    """
    Agent responsible for generating tactical RPG encounters.
    """

    def __init__(self):
        self.client = OllamaClient()
        # Using a capable instruct model for creative writing and JSON formatting.
        # Fallback to llama3.2 if gemma3 is not available in a real environment check.
        self.model = "gemma2:9b"  # Or "llama3.1:8b" - using a standard robust model.

    async def generate_encounter(
        self, level: str, difficulty: str, theme: str
    ) -> Optional[EncounterResponse]:
        """
        Generates an encounter based on parameters using RAG context if available.
        """
        rag_context = await self._retrieve_context(
            f"{theme} {difficulty} monster enemy stat block"
        )

        system_prompt = """
        You are an expert Game Master assistant. Create a tactical RPG encounter based on the user's request.

        Your output must be a valid JSON object matching the provided schema.
        Includes:
        - A creative title.
        - A vivid description for the GM to read aloud.
        - Tactical advice.
        - Loot suggestions.
        - One or more complete NPC stat blocks (name, CR, HP, AC, stats, actions).

        Use the provided context to inspire the creatures, but ensure the encounter is balanced for the requested level and difficulty.
        """

        user_message = f"""
        Generate an encounter for:
        - Party Level: {level}
        - Difficulty: {difficulty}
        - Theme/Setting: {theme}

        Context (Rules/Bestiary):
        {rag_context}
        """

        messages = [
            Message(role=Role.SYSTEM, content=system_prompt),
            Message(role=Role.USER, content=user_message),
        ]

        try:
            logger.info("encounter_generation_started", level=level, theme=theme)

            # We use json mode to ensure structure
            response = await self.client.generate(
                model=self.model,
                messages=messages,
                format=EncounterResponse.model_json_schema(),
                stream=False,
                options={"temperature": 0.7},  # Creative but focused
            )

            if not response.message or not response.message.content:
                logger.error("encounter_generation_empty_response")
                return None

            import json

            try:
                data = json.loads(response.message.content)
                return EncounterResponse(**data)
            except json.JSONDecodeError as e:
                logger.error(
                    "encounter_generation_json_error",
                    error=str(e),
                    content=response.message.content,
                )
                return None

        except Exception as e:
            logger.error("encounter_generation_failed", error=str(e))
            return None

    async def _retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant chunks from the Knowledge Base (ChromaDB).
        """
        from gm_shield.shared.database.chroma import get_chroma_client
        from gm_shield.features.knowledge.service import get_embedding_model

        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection("knowledge_base")

            # Embed query
            model = get_embedding_model()
            query_embedding = model.encode([query])

            # Query
            results = collection.query(
                query_embeddings=query_embedding.tolist(), n_results=3
            )

            documents = results.get("documents", [])
            if documents and documents[0]:
                return "\n\n".join(documents[0])
            return ""

        except Exception as e:
            logger.warning("rag_retrieval_failed", error=str(e))
            return ""
