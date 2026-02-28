import os
from pathlib import Path
import json
import git
from sqlalchemy.orm import Session
from gm_shield.features.notes.entities import AppSettings, Note, NoteFolder, NoteTag, NoteLink
from gm_shield.features.notes.service import _run_note_enrichment
from gm_shield.core.logging import get_logger

logger = get_logger(__name__)

def sync_obsidian_vault(db: Session) -> dict:
    """Sync the configured Obsidian vault to the database."""
    settings = db.get(AppSettings, "obsidian_vault_path")
    if not settings or not settings.value:
        return {"status": "error", "message": "No vault path configured"}

    vault_path = settings.value
    if not os.path.isdir(vault_path):
        return {"status": "error", "message": f"Vault path {vault_path} is not a valid directory"}

    try:
        repo = git.Repo(vault_path)
    except git.exc.InvalidGitRepositoryError:
        logger.info(f"Initializing new git repository at {vault_path}")
        repo = git.Repo.init(vault_path)

    if repo.is_dirty(untracked_files=True):
        repo.git.add(A=True)
        repo.index.commit("Auto-commit before sync")

    db.query(NoteTag).delete()
    db.query(NoteLink).delete()
    db.query(Note).delete()
    db.query(NoteFolder).delete()
    db.commit()

    folder_map = {}

    def get_or_create_folder(rel_dir: str) -> int | None:
        if not rel_dir or rel_dir == ".":
            return None
        if rel_dir in folder_map:
            return folder_map[rel_dir]

        parts = Path(rel_dir).parts
        parent_id = None
        current_path = ""

        for part in parts:
            current_path = os.path.join(current_path, part) if current_path else part
            if current_path not in folder_map:
                folder = NoteFolder(name=part, parent_id=parent_id)
                db.add(folder)
                db.commit()
                db.refresh(folder)
                folder_map[current_path] = folder.id
                parent_id = folder.id
            else:
                parent_id = folder_map[current_path]
        return parent_id

    md_files = []
    for root, dirs, files in os.walk(vault_path):
        if ".git" in dirs:
            dirs.remove(".git")
        if ".obsidian" in dirs:
            dirs.remove(".obsidian")
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))

    stats = {
        "notes_synced": 0,
        "folders_created": 0,
    }

    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            continue

        rel_path = os.path.relpath(file_path, vault_path)
        rel_dir = os.path.dirname(rel_path)
        title = os.path.splitext(os.path.basename(file_path))[0]

        folder_id = get_or_create_folder(rel_dir)

        # Parse tags, wiki links, etc.
        import re
        wiki_links = re.findall(r"\[\[(.*?)\]\]", content)
        tags_match = re.findall(r"#([a-zA-Z0-9_]+)", content)

        explicit_tags = tags_match + ["obsidian"]

        inferred_tags, extracted_metadata, normalized_content = _run_note_enrichment(content, explicit_tags)

        frontmatter = {}
        if extracted_metadata:
            frontmatter.update(extracted_metadata)

        frontmatter["obsidian_path"] = rel_path
        frontmatter["wiki_links"] = wiki_links

        note = Note(
            title=title,
            content_markdown=content,
            frontmatter_json=json.dumps(frontmatter),
            folder_id=folder_id,
        )
        note.tags = [NoteTag(tag=tag) for tag in inferred_tags]

        db.add(note)
        stats["notes_synced"] += 1

    db.commit()
    stats["folders_created"] = len(folder_map)
    return {"status": "success", "stats": stats}
