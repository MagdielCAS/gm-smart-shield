"""
Sheet Service — orchestrates character sheet template generation.

Retrieves relevant rules from the knowledge base and invokes the Sheet Agent.
"""

from typing import Dict, Any, List
from gm_shield.features.knowledge.service import query_knowledge
from gm_shield.features.sheets.agent import SheetAgent
from gm_shield.features.sheets.models import SheetTemplateResponse
from gm_shield.shared.ai.base import Citation
from gm_shield.core.logging import get_logger
import yaml
import re

logger = get_logger(__name__)


class SheetService:
    """
    Handles logic for character sheet template creation.
    """

    def __init__(self):
        self.agent = SheetAgent()

    async def generate_template(self, source_id: str, system_name: str = None) -> SheetTemplateResponse:
        """
        Retrieves rulebook content and generates a character sheet template.

        For now, we query for "character sheet creation rules stats" to get relevant context.
        In a full implementation, this might retrieve specific chapters known to contain rules.
        """
        logger.info("sheet_service_generate", source_id=source_id)

        # 1. Retrieve context (simulating scanning the rulebook for sheet-related terms)
        query = f"character sheet creation attributes skills stats {system_name or ''}"
        chunks = await query_knowledge(query, top_k=5) # Increased context might be needed for full sheets

        context_parts = []
        citations = []

        for chunk in chunks:
            # Filter by source_id if provided (assuming metadata has source_id)
            # This is a simplification; query_knowledge should ideally support filters
            content = chunk["content"]
            metadata = chunk["metadata"]
            source = metadata.get("source", "unknown")

            # If source_id is a filename, check if it matches
            if source_id in source:
                 context_parts.append(f"Source: {source}\nContent: {content}")
                 citations.append(
                    Citation(source=source, content=content, page=metadata.get("page"))
                 )

        # If no specific source match found, use all retrieved context (fallback)
        if not context_parts:
             for chunk in chunks:
                content = chunk["content"]
                metadata = chunk["metadata"]
                source = metadata.get("source", "unknown")
                context_parts.append(f"Source: {source}\nContent: {content}")
                citations.append(
                    Citation(source=source, content=content, page=metadata.get("page"))
                )

        context = "\n\n---\n\n".join(context_parts)

        # 2. Generate Template
        response = await self.agent.process(
            query="generate_sheet",
            context=context,
            citations=citations,
            system_name=system_name
        )

        # 3. Parse Frontmatter Schema (simple extraction)
        frontmatter_schema = self._extract_frontmatter_schema(response.text)

        return SheetTemplateResponse(
            template_markdown=response.text,
            frontmatter_schema=frontmatter_schema,
            metadata=response.metadata
        )

    def _extract_frontmatter_schema(self, text: str) -> Dict[str, Any]:
        """
        Parses the YAML frontmatter from the generated markdown to build a schema.
        """
        try:
            match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            if match:
                frontmatter_yaml = match.group(1)
                data = yaml.safe_load(frontmatter_yaml)
                # Convert values to types for schema (simplified)
                schema = {}
                if data:
                    for k, v in data.items():
                        schema[k] = {"type": type(v).__name__, "default": v}
                return schema
        except Exception as e:
            logger.warning("failed_to_parse_frontmatter", error=str(e))

        return {}


# Singleton
_sheet_service = SheetService()

def get_sheet_service() -> SheetService:
    return _sheet_service
