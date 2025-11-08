#!/usr/bin/env python3
"""
Migration script: Integer x-coordinates → Beads issue ID strings

This script migrates existing .vector-memory/ directories from the old format
(integer-based x-coordinates) to the new format (Beads issue ID strings).

Old format: .vector-memory/x-005/y-2-z-1.json
New format: .vector-memory/x-{issue-id}/y-2-z-1.json

Usage:
    python scripts/migrate_x_coordinates.py <repo_path> <issue_id_mapping_json>

Where issue_id_mapping_json is a JSON file mapping integer x values to Beads issue IDs:
    {
        "1": "codeframe-aco-abc",
        "2": "codeframe-aco-def",
        ...
    }
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def load_issue_mapping(mapping_file: Path) -> dict[int, str]:
    """Load integer → issue ID mapping from JSON file."""
    with open(mapping_file, 'r') as f:
        str_mapping = json.load(f)

    # Convert string keys to integers
    return {int(k): v for k, v in str_mapping.items()}


def migrate_directory(vector_memory_dir: Path, issue_mapping: dict[int, str], dry_run: bool = False) -> dict:
    """
    Migrate .vector-memory/ directory from integer to issue ID x-coordinates.

    Returns:
        Statistics dict with migration results
    """
    if not vector_memory_dir.exists():
        print(f"❌ Directory not found: {vector_memory_dir}")
        return {"error": "directory_not_found"}

    stats = {
        "total_files": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": [],
    }

    # Find all x-* directories
    x_dirs = sorted(vector_memory_dir.glob("x-*"))

    for x_dir in x_dirs:
        # Extract integer x value from directory name
        # Old format: x-005 (zero-padded 3 digits)
        dir_name = x_dir.name
        if not dir_name.startswith("x-"):
            continue

        x_str = dir_name[2:]  # Remove "x-" prefix

        # Try to parse as integer (old format)
        try:
            x_int = int(x_str)
        except ValueError:
            # Already in new format (issue ID string), skip
            print(f"⏭️  Skipping {x_dir} (already migrated)")
            stats["skipped"] += 1
            continue

        # Look up issue ID
        if x_int not in issue_mapping:
            error_msg = f"No mapping found for x={x_int}"
            print(f"⚠️  {error_msg}")
            stats["errors"].append(error_msg)
            continue

        issue_id = issue_mapping[x_int]
        new_dir = vector_memory_dir / f"x-{issue_id}"

        # Find all JSON files in this directory
        json_files = list(x_dir.glob("*.json"))
        stats["total_files"] += len(json_files)

        if dry_run:
            print(f"🔍 [DRY RUN] Would migrate {x_dir} → {new_dir} ({len(json_files)} files)")
        else:
            # Create new directory
            new_dir.mkdir(exist_ok=True)

            # Move all files
            for json_file in json_files:
                new_file = new_dir / json_file.name
                shutil.move(str(json_file), str(new_file))

            # Remove old directory
            x_dir.rmdir()

            print(f"✅ Migrated {x_dir} → {new_dir} ({len(json_files)} files)")
            stats["migrated"] += len(json_files)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate .vector-memory/ from integer to issue ID x-coordinates")
    parser.add_argument("repo_path", type=Path, help="Path to repository containing .vector-memory/")
    parser.add_argument("mapping_file", type=Path, help="JSON file mapping integer x → issue IDs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")

    args = parser.parse_args()

    # Load mapping
    try:
        issue_mapping = load_issue_mapping(args.mapping_file)
        print(f"📋 Loaded mapping for {len(issue_mapping)} issues")
    except Exception as e:
        print(f"❌ Failed to load mapping file: {e}")
        sys.exit(1)

    # Find .vector-memory directory
    vector_memory_dir = args.repo_path / ".vector-memory"

    # Run migration
    print(f"\n{'🔍 DRY RUN MODE' if args.dry_run else '🚀 MIGRATION STARTING'}")
    print(f"Directory: {vector_memory_dir}\n")

    stats = migrate_directory(vector_memory_dir, issue_mapping, dry_run=args.dry_run)

    # Print summary
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total files:     {stats.get('total_files', 0)}")
    print(f"Migrated:        {stats.get('migrated', 0)}")
    print(f"Skipped:         {stats.get('skipped', 0)}")
    print(f"Errors:          {len(stats.get('errors', []))}")

    if stats.get('errors'):
        print("\nErrors encountered:")
        for error in stats['errors']:
            print(f"  - {error}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
