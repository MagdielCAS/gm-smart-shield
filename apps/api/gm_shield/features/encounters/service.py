"""
Encounter Service — Orchestrates encounter generation.

Queries knowledge base for relevant monsters and environments,
then uses the Encounter Agent to build the encounter.
"""

from typing import Dict, Any, List
from gm_shield.features.knowledge.service import query_knowledge
from gm_shield.features.encounters.agent import EncounterAgent
from gm_shield.features.encounters.models import EncounterResponse
from gm_shield.shared.ai.base import Citation
from gm_shield.core.logging import get_logger
import json

logger = get_logger(__name__)


class EncounterService:
    """
    Service for generating encounters.
    """

    def __init__(self):
        self.agent = EncounterAgent()

    async def generate_encounter(self, party_level: int, environment: str, difficulty: str, theme: str = None) -> EncounterResponse:
        """
        Retrieves context and generates an encounter.
        """
        logger.info("encounter_service_generate", level=party_level, environment=environment)

        # 1. Retrieve context (simulating search for monsters in that environment)
        query = f"monsters {environment} CR {party_level} {theme or ''}"
        chunks = await query_knowledge(query, top_k=5)

        context_parts = []
        citations = []

        for chunk in chunks:
            content = chunk["content"]
            metadata = chunk["metadata"]
            source = metadata.get("source", "unknown")

            context_parts.append(f"Source: {source}\nContent: {content}")
            citations.append(
                Citation(source=source, content=content, page=metadata.get("page"))
            )

        context = "\n\n---\n\n".join(context_parts)

        # 2. Generate Encounter
        response = await self.agent.process(
            query="generate_encounter",
            context=context,
            citations=citations,
            level=party_level,
            environment=environment,
            difficulty=difficulty,
            theme=theme
        )

        # 3. Parse and structure response
        try:
            # If the agent correctly returned JSON in metadata, use it
            data = response.metadata.get("json_data")
            if not data:
                # Fallback: try parsing the text if metadata is missing
                data = json.loads(response.text)

            return EncounterResponse(
                title=data.get("title", "Untitled Encounter"),
                description=data.get("description", "No description provided."),
                tactics=data.get("tactics", "No tactics provided."),
                npc_stats=data.get("npc_stats", []),
                loot=data.get("loot", "No loot."),
                metadata=response.metadata
            )
        except Exception as e:
            logger.error("encounter_parsing_failed", error=str(e))
            # Return a minimal valid response if parsing fails
            return EncounterResponse(
                title="Error Generating Encounter",
                description=f"The encounter could not be generated correctly. Raw output: {response.text}",
                tactics="N/A",
                npc_stats=[],
                loot="N/A",
                metadata={"error": str(e), "raw_output": response.text}
            )


# Singleton
_encounter_service = EncounterService()

def get_encounter_service() -> EncounterService:
    return _encounter_service
