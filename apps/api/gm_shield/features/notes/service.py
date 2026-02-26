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

from gm_shield.features.notes.entities import Note, NoteFolder, NoteLink, NoteTag
from gm_shield.features.notes.models import (
    NoteCreateRequest,
    NoteFolderCreateRequest,
    NoteFolderResponse,
    NoteInlineSuggestionRequest,
    NoteInlineSuggestionResponse,
    NoteLinkMetadata,
    NoteLinkSuggestion,
    NoteLinkSuggestionRequest,
    NoteLinkSuggestionResponse,
    NoteResponse,
    NoteTransformAction,
    NoteTransformRequest,
    NoteTransformResponse,
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

TRANSFORM_ACTIONS = {
    NoteTransformAction.REWRITE,
    NoteTransformAction.FORMAT,
    NoteTransformAction.MAKE_DRAMATIC,
    NoteTransformAction.GENERATE_CONTENT,
    NoteTransformAction.ADD_REFERENCE_LINK,
    NoteTransformAction.SEARCH_REFERENCE_LINK,
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
    titlecase_entities = re.findall(
        r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", markdown_body
    )
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", markdown_body.lower())

    frequencies: dict[str, int] = {}
    for word in words:
        if word in STOPWORDS:
            continue
        frequencies[word] = frequencies.get(word, 0) + 1

    keyword_tags = [
        token
        for token, _ in sorted(
            frequencies.items(), key=lambda item: (-item[1], item[0])
        )[:5]
    ]
    entity_tags = [
        entity.lower().replace(" ", "-") for entity in titlecase_entities[:5]
    ]
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


def _run_note_enrichment(
    content: str, explicit_tags: list[str]
) -> tuple[list[str], dict[str, Any], str]:
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


def _safe_slice(content: str, start: int, end: int) -> tuple[int, int, str]:
    """Clamp selection bounds and return the selected segment.

    Args:
        content: Full content string.
        start: Raw selection start.
        end: Raw selection end.

    Returns:
        A tuple of clamped ``(start, end, selected_text)``.
    """
    clamped_start = max(0, min(start, len(content)))
    clamped_end = max(clamped_start, min(end, len(content)))
    return clamped_start, clamped_end, content[clamped_start:clamped_end]


def suggest_inline_text(
    payload: NoteInlineSuggestionRequest,
) -> NoteInlineSuggestionResponse:
    """Generate ghost-text continuation for phrase-boundary editor events.

    Args:
        payload: Current editor content and cursor location.

    Returns:
        A deterministic local suggestion payload for ghost-text rendering.
    """
    cursor_index = min(payload.cursor_index, len(payload.content))
    prefix = payload.content[:cursor_index]
    tail = prefix.rstrip()
    if not tail:
        return NoteInlineSuggestionResponse(suggestion="", reason="none")

    reason = "idle"
    if tail.endswith("\n"):
        reason = "newline"
    elif tail[-1] in ".!?;:":
        reason = "punctuation"

    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", tail)
    subject = words[-1] if words else "scene"
    templates = {
        "newline": f"- {subject.capitalize()} detail: ",
        "punctuation": " Next, ",
        "idle": " and ",
    }
    return NoteInlineSuggestionResponse(suggestion=templates[reason], reason=reason)


def preview_transform(payload: NoteTransformRequest) -> NoteTransformResponse:
    """Create non-destructive previews for note context-menu actions.

    Args:
        payload: Requested action and editor selection details.

    Returns:
        A preview response that can be applied by the client.

    Raises:
        HTTPException: If action is unsupported or selection bounds are invalid.
    """
    if payload.action not in TRANSFORM_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Unsupported action",
        )

    start, end, selected_text = _safe_slice(
        payload.content, payload.selection_start, payload.selection_end
    )
    base_text = selected_text.strip() or payload.content.strip()
    if payload.action == NoteTransformAction.REWRITE:
        preview = f"{base_text} (rewritten for clarity)"
        mode = "replace"
    elif payload.action == NoteTransformAction.FORMAT:
        preview = "\n".join(
            line.strip() for line in base_text.splitlines() if line.strip()
        )
        mode = "replace"
    elif payload.action == NoteTransformAction.MAKE_DRAMATIC:
        preview = f"⚔️ {base_text} The air crackles with ominous intent."
        mode = "replace"
    elif payload.action == NoteTransformAction.GENERATE_CONTENT:
        seed = base_text or "Scene prompt"
        preview = f"{seed}\n- Stakes escalate when an unseen rival intervenes."
        mode = "insert" if not selected_text.strip() else "replace"
    elif payload.action == NoteTransformAction.ADD_REFERENCE_LINK:
        anchor = base_text or "reference"
        preview = f"[{anchor}](ref://knowledge/{re.sub(r'[^a-z0-9]+', '-', anchor.lower()).strip('-') or 'entry'})"
        mode = "replace"
    else:
        keyword = base_text or "lore"
        preview = f"Related references: {keyword} compendium, faction dossier, regional timeline"
        mode = "insert"

    return NoteTransformResponse(
        action=payload.action,
        original_text=selected_text,
        preview_text=preview,
        selection_start=start,
        selection_end=end,
        mode=mode,
    )


def _to_response(note: Note) -> NoteResponse:
    """Convert a ``Note`` ORM entity to an API response schema."""
    parsed_frontmatter = (
        json.loads(note.frontmatter_json) if note.frontmatter_json else None
    )
    extracted_metadata = (
        parsed_frontmatter.get("_extracted", {}) if parsed_frontmatter else {}
    )
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
                tag=link.tag,
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
                tag=link.tag,
                source_id=link.source_id,
                source_file=link.source_file,
                page_number=link.page_number,
                chunk_id=link.chunk_id,
            )
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
    inferred_tags, extracted_metadata, normalized_content = _run_note_enrichment(
        payload.content, payload.tags
    )

    frontmatter = payload.frontmatter.copy() if payload.frontmatter else {}
    if extracted_metadata:
        frontmatter.update(
            {k: v for k, v in extracted_metadata.items() if k not in frontmatter}
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    inferred_tags, extracted_metadata, normalized_content = _run_note_enrichment(
        payload.content, payload.tags
    )

    frontmatter = payload.frontmatter.copy() if payload.frontmatter else {}
    if extracted_metadata:
        frontmatter.update(
            {k: v for k, v in extracted_metadata.items() if k not in frontmatter}
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

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

    for chunk_id, document, metadata, distance in zip(
        ids, documents, metadatas, distances
    ):
        doc_keywords = _keywords(document or "")
        keyword_overlap = len(note_keywords.intersection(doc_keywords))
        similarity_score = max(
            0.0, min(1.0, 1.0 - float(distance if distance is not None else 1.0))
        )
        candidates[chunk_id] = {
            "source_id": (metadata or {}).get("source_id")
            or (metadata or {}).get("source"),
            "source_file": (metadata or {}).get("source"),
            "page_number": (metadata or {}).get("page")
            or (metadata or {}).get("page_number"),
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
                "source_id": (metadata or {}).get("source_id")
                or (metadata or {}).get("source"),
                "source_file": (metadata or {}).get("source"),
                "page_number": (metadata or {}).get("page")
                or (metadata or {}).get("page_number"),
                "chunk_id": chunk_id,
                "snippet": (document or "")[:280],
                "similarity_score": 0.0,
                "keyword_overlap": keyword_overlap,
            }
        else:
            candidates[chunk_id]["keyword_overlap"] = max(
                candidates[chunk_id]["keyword_overlap"], keyword_overlap
            )

    ranked = sorted(
        candidates.values(),
        key=lambda item: (item["similarity_score"], item["keyword_overlap"]),
        reverse=True,
    )[: payload.limit]

    return NoteLinkSuggestionResponse(
        note_id=note.id,
        suggestions=[NoteLinkSuggestion(**item) for item in ranked],
    )




def _to_folder_response(folder: NoteFolder) -> NoteFolderResponse:
    """Convert a ``NoteFolder`` ORM entity to API schema."""
    return NoteFolderResponse(id=folder.id, name=folder.name, parent_id=folder.parent_id)


def list_folders(db: Session) -> list[NoteFolderResponse]:
    """Return all note folders ordered by name then ID."""
    folders = db.query(NoteFolder).order_by(NoteFolder.name.asc(), NoteFolder.id.asc()).all()
    return [_to_folder_response(folder) for folder in folders]


def create_folder(db: Session, payload: NoteFolderCreateRequest) -> NoteFolderResponse:
    """Create a note folder/notebook."""
    if payload.parent_id is not None and db.get(NoteFolder, payload.parent_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent folder not found",
        )

    folder = NoteFolder(name=payload.name.strip(), parent_id=payload.parent_id)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return _to_folder_response(folder)


def delete_note(db: Session, note_id: int) -> None:
    """Delete an existing note."""
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    db.delete(note)
    db.commit()
