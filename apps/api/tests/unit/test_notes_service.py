"""Unit tests for Notes service helper behaviour and timestamp handling."""

import pytest
from fastapi import HTTPException

from gm_shield.features.notes.models import NoteCreateRequest, NoteUpdateRequest
from gm_shield.features.notes.service import (
    _extract_deterministic_tags,
    _parse_markdown_frontmatter,
    create_note,
    delete_note,
    get_note,
    update_note,
)


def test_markdown_frontmatter_parsing_and_body_normalization() -> None:
    """Extract frontmatter key/value pairs while keeping markdown body content."""
    frontmatter, body = _parse_markdown_frontmatter(
        "---\nlocation: Waterdeep\nmood: tense\n---\n# Session\nThe #Harper contact arrived."
    )

    assert frontmatter == {"location": "Waterdeep", "mood": "tense"}
    assert body == "# Session\nThe #Harper contact arrived."


def test_metadata_and_tag_extraction_behavior() -> None:
    """Infer hashtags, entities, keywords, and deduplicated tags deterministically."""
    tags, metadata = _extract_deterministic_tags(
        "#Harper agents met Mirt in Waterdeep harbor where smuggling clues surfaced."
    )

    assert "harper" in tags
    assert "waterdeep" in tags
    assert metadata["word_count"] >= 10
    assert "harper" in metadata["hashtags"]
    assert "Mirt" in metadata["entities"]
    assert len(metadata["top_keywords"]) <= 5


def test_note_timestamp_correctness_when_content_changes(db_session) -> None:
    """Keep created_at stable and update updated_at only when markdown content changes."""
    created = create_note(
        db_session,
        NoteCreateRequest(
            title="Session Log",
            content="Initial content with #Tag",
            tags=["session"],
            sources=[],
        ),
    )

    first_update = update_note(
        db_session,
        created.id,
        NoteUpdateRequest(
            title="Session Log",
            content="Initial content with #Tag",
            tags=["session"],
            sources=[],
        ),
    )

    assert first_update.created_at == created.created_at
    assert first_update.updated_at == created.updated_at

    second_update = update_note(
        db_session,
        created.id,
        NoteUpdateRequest(
            title="Session Log",
            content="Changed content with #Tag and #Clue",
            tags=["session"],
            sources=[],
        ),
    )

    assert second_update.created_at == created.created_at
    assert second_update.updated_at >= first_update.updated_at


def test_note_crud_error_cases_raise_404(db_session) -> None:
    """Raise HTTP 404 for missing note IDs on fetch, update, and delete operations."""
    with pytest.raises(HTTPException) as get_error:
        get_note(db_session, 999)
    assert get_error.value.status_code == 404

    with pytest.raises(HTTPException) as update_error:
        update_note(
            db_session,
            999,
            NoteUpdateRequest(title="Missing", content="None", tags=[], sources=[]),
        )
    assert update_error.value.status_code == 404

    with pytest.raises(HTTPException) as delete_error:
        delete_note(db_session, 999)
    assert delete_error.value.status_code == 404
