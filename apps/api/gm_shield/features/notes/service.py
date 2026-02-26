"""
Business logic for the Notes feature slice.

Provides CRUD operations for note records and related tags while keeping route
handlers thin and focused on HTTP concerns.
"""

import json
import re
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from gm_shield.features.notes.entities import Note, NoteTag
from gm_shield.features.notes.models import (
    NoteCreateRequest,
    NoteLinkMetadata,
    NoteResponse,
    NoteUpdateRequest,
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def _dedupe_tags(tags: list[str]) -> list[str]:
    """Return tags normalized to lowercase and deduplicated while preserving order."""
    deduped: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        tag = raw_tag.strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag)
    return deduped


def _parse_markdown_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract simple YAML-like frontmatter from markdown content."""
    if not content.startswith("---\n"):
        return {}, content

    lines = content.splitlines()
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, content

    frontmatter: dict[str, Any] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    body = "\n".join(lines[closing_index + 1 :]).lstrip("\n")
    return frontmatter, body


def _extract_deterministic_tags(markdown_body: str) -> tuple[list[str], dict[str, Any]]:
    """Extract tags and metadata using deterministic token/entity heuristics."""
    hashtag_tags = re.findall(r"(?<!\w)#([A-Za-z][\w-]{1,30})", markdown_body)
    titlecase_entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", markdown_body)
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", markdown_body.lower())

    frequencies: dict[str, int] = {}
    for word in words:
        if word in STOPWORDS:
            continue
        frequencies[word] = frequencies.get(word, 0) + 1

    keyword_tags = [token for token, _ in sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))[:5]]
    entity_tags = [entity.lower().replace(" ", "-") for entity in titlecase_entities[:5]]
    extracted_tags = _dedupe_tags(hashtag_tags + entity_tags + keyword_tags)
    metadata = {
        "word_count": len(words),
        "hashtags": _dedupe_tags(hashtag_tags),
        "entities": sorted(set(titlecase_entities)),
        "top_keywords": keyword_tags,
    }
    return extracted_tags, metadata


def _extract_llm_tags_if_available(markdown_body: str) -> list[str]:
    """Call an optional LLM note-tagging agent when available."""
    try:
        agent_module = import_module("gm_shield.features.notes.tagging_agent")
        get_tagger = getattr(agent_module, "get_optional_tagger", None)
        if get_tagger is None:
            return []
        tagger = get_tagger()
        if tagger is None:
            return []
        llm_tags = tagger(markdown_body)
        if not isinstance(llm_tags, list):
            return []
        return [str(tag) for tag in llm_tags]
    except Exception:
        return []


def _run_note_enrichment(content: str, explicit_tags: list[str]) -> tuple[list[str], dict[str, Any], str]:
    """Parse markdown/frontmatter, then enrich tags using deterministic and optional LLM steps."""
    inline_frontmatter, markdown_body = _parse_markdown_frontmatter(content)
    deterministic_tags, extracted_metadata = _extract_deterministic_tags(markdown_body)
    llm_tags = _extract_llm_tags_if_available(markdown_body)
    all_tags = _dedupe_tags(explicit_tags + deterministic_tags + llm_tags)
    metadata = {
        **inline_frontmatter,
        "_extracted": {
            **extracted_metadata,
            "llm_tags": _dedupe_tags([tag.lower() for tag in llm_tags]),
            "resolved_tags": all_tags,
        },
    }
    return all_tags, metadata, markdown_body


def _to_response(note: Note) -> NoteResponse:
    """Convert a ``Note`` ORM entity to an API response schema."""
    parsed_frontmatter = json.loads(note.frontmatter_json) if note.frontmatter_json else None
    extracted_metadata = parsed_frontmatter.get("_extracted", {}) if parsed_frontmatter else {}
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content_markdown,
        frontmatter=parsed_frontmatter,
        metadata=extracted_metadata,
        folder_id=note.folder_id,
        created_at=note.created_at,
        updated_at=note.updated_at,
        tags=[tag.tag for tag in note.tags],
        links=[
            NoteLinkMetadata(tag=tag.tag, source_id=tag.source_id, page_number=tag.page_number)
            for tag in note.tags
        ],
    )


def create_note(db: Session, payload: NoteCreateRequest) -> NoteResponse:
    """
    Create and persist a new note.

    Args:
        db: Active SQLAlchemy session.
        payload: Incoming note creation payload.

    Returns:
        Created note as a response schema.
    """
    inferred_tags, extracted_metadata, normalized_content = _run_note_enrichment(payload.content, payload.tags)

    frontmatter = payload.frontmatter.copy() if payload.frontmatter else {}
    if extracted_metadata:
        frontmatter.update({k: v for k, v in extracted_metadata.items() if k not in frontmatter})
    if payload.campaign_id is not None:
        frontmatter.setdefault("campaign_id", payload.campaign_id)
    if payload.session_id is not None:
        frontmatter.setdefault("session_id", payload.session_id)

    note = Note(
        title=payload.title,
        content_markdown=normalized_content,
        frontmatter_json=json.dumps(frontmatter) if frontmatter else None,
        folder_id=payload.folder_id,
    )
    note.tags = [NoteTag(tag=tag) for tag in inferred_tags]

    db.add(note)
    db.commit()
    db.refresh(note)
    return _to_response(note)


def list_notes(db: Session) -> list[NoteResponse]:
    """
    List all notes sorted by newest update first.

    Args:
        db: Active SQLAlchemy session.

    Returns:
        Ordered list of note response objects.
    """
    notes = db.query(Note).order_by(Note.updated_at.desc(), Note.id.desc()).all()
    return [_to_response(note) for note in notes]


def get_note(db: Session, note_id: int) -> NoteResponse:
    """
    Retrieve a note by ID.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.

    Returns:
        Retrieved note schema.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _to_response(note)


def update_note(db: Session, note_id: int, payload: NoteUpdateRequest) -> NoteResponse:
    """
    Replace an existing note and bump the ``updated_at`` timestamp.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.
        payload: Replacement note payload.

    Returns:
        Updated note schema.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    inferred_tags, extracted_metadata, normalized_content = _run_note_enrichment(payload.content, payload.tags)

    frontmatter = payload.frontmatter.copy() if payload.frontmatter else {}
    if extracted_metadata:
        frontmatter.update({k: v for k, v in extracted_metadata.items() if k not in frontmatter})
    if payload.campaign_id is not None:
        frontmatter.setdefault("campaign_id", payload.campaign_id)
    if payload.session_id is not None:
        frontmatter.setdefault("session_id", payload.session_id)

    content_changed = note.content_markdown != normalized_content
    note.title = payload.title
    note.content_markdown = normalized_content
    note.folder_id = payload.folder_id
    note.frontmatter_json = json.dumps(frontmatter) if frontmatter else None
    if content_changed:
        note.updated_at = datetime.now(timezone.utc)

    note.tags.clear()
    note.tags.extend(NoteTag(tag=tag) for tag in inferred_tags)

    db.commit()
    db.refresh(note)
    return _to_response(note)


def delete_note(db: Session, note_id: int) -> None:
    """
    Delete an existing note.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.

    Raises:
        HTTPException: If no note exists for ``note_id``.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    db.delete(note)
    db.commit()
