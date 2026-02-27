import asyncio
import sys
import argparse
from pathlib import Path

# Add api root to path
sys.path.append(str(Path(__file__).parent.parent))

from gm_shield.features.sheets.service import SheetService
from gm_shield.features.references.service import ReferenceService
from gm_shield.features.encounters.service import EncounterService
from gm_shield.features.notes.service import TaggingService

async def run_sheet_demo(source_id: str, system: str):
    service = SheetService()
    print(f"Generating sheet template for source: {source_id} (System: {system})...")
    try:
        response = await service.generate_template(source_id, system)
        print("\n✅ Template Generated Successfully!")
        print("-" * 40)
        print(f"Frontmatter Schema Keys: {list(response.frontmatter_schema.keys())}")
        print("-" * 40)
        print("Markdown Preview (first 500 chars):")
        print(response.template_markdown[:500] + "...")
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_reference_demo(category: str, source_id: str):
    service = ReferenceService()
    print(f"Generating reference for category: {category} from source: {source_id}...")
    try:
        response = await service.generate_reference(category, source_id)
        print("\n✅ Reference Generated Successfully!")
        print("-" * 40)
        print("Content Preview (first 500 chars):")
        print(response.content[:500] + "...")
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_encounter_demo(level: int, env: str, difficulty: str, theme: str):
    service = EncounterService()
    print(f"Generating encounter (Level: {level}, Env: {env}, Diff: {difficulty}, Theme: {theme})...")
    try:
        response = await service.generate_encounter(level, env, difficulty, theme)
        print("\n✅ Encounter Generated Successfully!")
        print("-" * 40)
        print(f"Title: {response.title}")
        print(f"Description: {response.description}")
        print(f"Tactics: {response.tactics}")
        print(f"Loot: {response.loot}")
        print("-" * 40)
        print("NPC Stats:")
        if response.npc_stats:
            for npc in response.npc_stats:
                print(f" - {npc}")
        else:
            print(" - None")
    except Exception as e:
        print(f"❌ Error: {e}")

async def run_tagging_demo(note: str):
    service = TaggingService()
    print(f"Tagging note: '{note}'...")
    try:
        response = await service.tag_note(note)
        print("\n✅ Note Tagged Successfully!")
        print("-" * 40)
        print(f"Tags: {response.tags}")
        print(f"Keywords: {response.keywords}")
        print(f"Suggested Links: {response.suggested_links}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Demo GM Smart Shield Agents via CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sheet Command
    sheet_parser = subparsers.add_parser("sheet", help="Generate a character sheet template")
    sheet_parser.add_argument("--source", type=str, required=True, help="Source ID or filename (e.g. 'phb.pdf')")
    sheet_parser.add_argument("--system", type=str, default="D&D 5e", help="RPG System Name")

    # Reference Command
    ref_parser = subparsers.add_parser("reference", help="Generate quick reference content")
    ref_parser.add_argument("--category", type=str, required=True, help="Category (e.g. Spells, Conditions)")
    ref_parser.add_argument("--source", type=str, required=True, help="Source ID or filename")

    # Encounter Command
    enc_parser = subparsers.add_parser("encounter", help="Generate an encounter")
    enc_parser.add_argument("--level", type=int, default=1, help="Party Level")
    enc_parser.add_argument("--env", type=str, required=True, help="Environment (e.g. Forest, Dungeon)")
    enc_parser.add_argument("--diff", type=str, default="Medium", help="Difficulty (Easy, Medium, Hard)")
    enc_parser.add_argument("--theme", type=str, default=None, help="Theme or specific monsters")

    # Tagging Command
    tag_parser = subparsers.add_parser("tag", help="Auto-tag a note")
    tag_parser.add_argument("--note", type=str, required=True, help="Note content to tag")

    args = parser.parse_args()

    # Dispatch to async function
    if args.command == "sheet":
        asyncio.run(run_sheet_demo(args.source, args.system))
    elif args.command == "reference":
        asyncio.run(run_reference_demo(args.category, args.source))
    elif args.command == "encounter":
        asyncio.run(run_encounter_demo(args.level, args.env, args.diff, args.theme))
    elif args.command == "tag":
        asyncio.run(run_tagging_demo(args.note))

if __name__ == "__main__":
    main()
