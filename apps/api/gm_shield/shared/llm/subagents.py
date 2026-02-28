"""
DeepAgents subagent configurations for the main Chat Orchestrator.
"""


from gm_shield.shared.llm import config as llm_config
from gm_shield.features.encounters.service import EncounterAgent
from gm_shield.features.knowledge.agents.sheet import SheetAgent
from gm_shield.features.notes.agents.tagger import TaggingAgent

# ── ENCOUNTER SUBAGENT ─────────────────────────────────────
encounter_subagent = {
    "name": "encounter-generator",
    "description": "Delegated task for generating tactical D&D encounters with NPC stat blocks. Call this when the GM asks for an encounter, combat, or enemies.",
    "system_prompt": EncounterAgent().system_prompt,
    "tools": [],
    "model": f"ollama:{llm_config.MODEL_ENCOUNTER}",
}

# ── TAGGING SUBAGENT ───────────────────────────────────────
tagging_subagent = {
    "name": "note-tagger",
    "description": "Delegated task for extracting relevant tags and entities (e.g. NPCs, locations) from a raw note.",
    "system_prompt": TaggingAgent().system_prompt,
    "tools": [],
    "model": f"ollama:{llm_config.MODEL_TAGGING}",
}

# ── SHEET SUBAGENT ─────────────────────────────────────────
sheet_subagent = {
    "name": "sheet-extractor",
    "description": "Delegated task for analyzing rulebook text and extracting a structured character sheet template.",
    "system_prompt": SheetAgent().system_prompt,
    "tools": [],
    "model": f"ollama:{llm_config.MODEL_SHEET}",
}

# ── REFERENCE SUBAGENT ─────────────────────────────────────
# For ReferenceAgent we assemble the prompt dynamically, so here we provide a generic version.
reference_subagent = {
    "name": "reference-extractor",
    "description": "Delegated task for extracting quick reference items (spells, weapons, items, rules) from larger text blocks.",
    "system_prompt": "You are an RPG data extractor. Read the provided text and identify reference items. Extract their Name, Category, Description, and Tags.",
    "tools": [],
    "model": f"ollama:{llm_config.MODEL_REFERENCE_SMART}",
}

SUBAGENTS = [
    encounter_subagent,
    tagging_subagent,
    sheet_subagent,
    reference_subagent,
]
