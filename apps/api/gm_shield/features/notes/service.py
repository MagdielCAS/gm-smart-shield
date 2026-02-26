"""
Business logic for the Notes feature slice.

Provides CRUD operations for note records, source links, and link-suggestion
flows while keeping route handlers thin and focused on HTTP concerns.
"""

import json
import re
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from gm_shield.features.notes.entities import Note, NoteLink, NoteTag
from gm_shield.features.notes.models import (
    NoteCreateRequest,
    NoteLinkMetadata,
    NoteLinkSuggestion,
    NoteLinkSuggestionRequest,
    NoteLinkSuggestionResponse,
    NoteResponse,
    NoteUpdateRequest,
)
from gm_shield.shared.database.chroma import get_chroma_client

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


def _keywords(text: str) -> set[str]:
    """Extract normalized non-stopword keywords from free text."""
    return {
        token
        for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
        if token not in STOPWORDS
    }


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
            NoteLinkMetadata(
                source_id=link.source_id,
                source_file=link.source_file,
                page_number=link.page_number,
                chunk_id=link.chunk_id,
            )
            for link in note.links
        ],
    )


def _assign_links(note: Note, links: list[NoteLinkMetadata]) -> None:
    """Replace note links with a normalized list of structured source links."""
    note.links.clear()
    for link in links:
        note.links.append(
            NoteLink(
                source_id=link.source_id,
                source_file=link.source_file,
                page_number=link.page_number,
                chunk_id=link.chunk_id,
            )
        )


def create_note(db: Session, payload: NoteCreateRequest) -> NoteResponse:
    """Create and persist a new note."""
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
    _assign_links(note, payload.sources)

    db.add(note)
    db.commit()
    db.refresh(note)
    return _to_response(note)


def list_notes(db: Session) -> list[NoteResponse]:
    """List all notes sorted by newest update first."""
    notes = db.query(Note).order_by(Note.updated_at.desc(), Note.id.desc()).all()
    return [_to_response(note) for note in notes]


def get_note(db: Session, note_id: int) -> NoteResponse:
    """Retrieve a note by ID."""
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return _to_response(note)


def update_note(db: Session, note_id: int, payload: NoteUpdateRequest) -> NoteResponse:
    """Replace an existing note and bump the ``updated_at`` timestamp."""
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
    _assign_links(note, payload.sources)

    db.commit()
    db.refresh(note)
    return _to_response(note)


def suggest_note_links(
    db: Session,
    note_id: int,
    payload: NoteLinkSuggestionRequest,
) -> NoteLinkSuggestionResponse:
    """
    Suggest source links for a note using semantic similarity and keyword overlap.

    Args:
        db: Active SQLAlchemy session.
        note_id: Note identifier.
        payload: Suggestion parameters, including maximum result size.

    Returns:
        A response containing structured link suggestions.

    Raises:
        HTTPException: If the note does not exist.
    """
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    note_keywords = _keywords(note.content_markdown)
    if not note_keywords:
        return NoteLinkSuggestionResponse(note_id=note.id, suggestions=[])

    client = get_chroma_client()
    try:
        collection = client.get_collection(name="knowledge_base")
    except ValueError:
        return NoteLinkSuggestionResponse(note_id=note.id, suggestions=[])

    semantic_results = collection.query(
        query_texts=[note.content_markdown],
        n_results=max(payload.limit * 2, 10),
        include=["documents", "metadatas", "distances"],
    )
    keyword_results = collection.get(include=["documents", "metadatas"])

    candidates: dict[str, dict[str, Any]] = {}

    ids = semantic_results.get("ids", [[]])[0]
    documents = semantic_results.get("documents", [[]])[0]
    metadatas = semantic_results.get("metadatas", [[]])[0]
    distances = semantic_results.get("distances", [[]])[0]

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
        doc_keywords = _keywords(document or "")
        keyword_overlap = len(note_keywords.intersection(doc_keywords))
        similarity_score = max(0.0, min(1.0, 1.0 - float(distance if distance is not None else 1.0)))
        candidates[chunk_id] = {
            "source_id": (metadata or {}).get("source_id") or (metadata or {}).get("source"),
            "source_file": (metadata or {}).get("source"),
            "page_number": (metadata or {}).get("page") or (metadata or {}).get("page_number"),
            "chunk_id": chunk_id,
            "snippet": (document or "")[:280],
            "similarity_score": similarity_score,
            "keyword_overlap": keyword_overlap,
        }

    for chunk_id, document, metadata in zip(
        keyword_results.get("ids", []),
        keyword_results.get("documents", []),
        keyword_results.get("metadatas", []),
    ):
        doc_keywords = _keywords(document or "")
        keyword_overlap = len(note_keywords.intersection(doc_keywords))
        if keyword_overlap == 0:
            continue
        if chunk_id not in candidates:
            candidates[chunk_id] = {
                "source_id": (metadata or {}).get("source_id") or (metadata or {}).get("source"),
                "source_file": (metadata or {}).get("source"),
                "page_number": (metadata or {}).get("page") or (metadata or {}).get("page_number"),
                "chunk_id": chunk_id,
                "snippet": (document or "")[:280],
                "similarity_score": 0.0,
                "keyword_overlap": keyword_overlap,
            }
        else:
            candidates[chunk_id]["keyword_overlap"] = max(candidates[chunk_id]["keyword_overlap"], keyword_overlap)

    ranked = sorted(
        candidates.values(),
        key=lambda item: (item["similarity_score"], item["keyword_overlap"]),
        reverse=True,
    )[: payload.limit]

    return NoteLinkSuggestionResponse(
        note_id=note.id,
        suggestions=[NoteLinkSuggestion(**item) for item in ranked],
    )


def delete_note(db: Session, note_id: int) -> None:
    """Delete an existing note."""
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    db.delete(note)
    db.commit()
