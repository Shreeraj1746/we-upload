#!/usr/bin/env python
"""
Script to update type annotations from Python 3.9 style to Python 3.13 style.

This script:
1. Removes 'from __future__ import annotations' since it's no longer needed
2. Replaces typing.Union[X, Y] with X | Y
3. Replaces typing.Optional[X] with X | None
4. Updates isinstance checks to use the | operator

Usage:
    python scripts/update_type_annotations.py [directory]

Example:
    python scripts/update_type_annotations.py app
"""

import os
import re
import sys
from pathlib import Path


def process_file(file_path: Path) -> bool:
    """Process a single Python file and update its type annotations.

    Args:
        file_path: Path to the Python file to process

    Returns:
        bool: True if changes were made, False otherwise
    """
    with file_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Track if we made any changes
    changes_made = False

    # Remove 'from __future__ import annotations'
    if re.search(r"from\s+__future__\s+import\s+annotations", content):
        content = re.sub(r"from\s+__future__\s+import\s+annotations\s*\n", "", content)
        changes_made = True

    # Replace import statements to avoid conflicts
    if re.search(r"from\s+typing\s+import.*Union", content):
        content = re.sub(r"from\s+typing\s+import\s+Union\s*", "", content)
        content = re.sub(
            r"from\s+typing\s+import\s+(.*),\s*Union", r"from typing import \1", content
        )
        changes_made = True

    if re.search(r"from\s+typing\s+import.*Optional", content):
        content = re.sub(r"from\s+typing\s+import\s+Optional\s*", "", content)
        content = re.sub(
            r"from\s+typing\s+import\s+(.*),\s*Optional", r"from typing import \1", content
        )
        changes_made = True

    # Replace typing.Union[X, Y] with X | Y
    if re.search(r"typing\.Union\[", content) or re.search(r"Union\[", content):
        content = re.sub(r"typing\.Union\[(.*?), (.*?)\]", r"\1 | \2", content)
        content = re.sub(r"Union\[(.*?), (.*?)\]", r"\1 | \2", content)
        changes_made = True

    # Replace typing.Optional[X] with X | None
    if re.search(r"typing\.Optional\[", content) or re.search(r"Optional\[", content):
        content = re.sub(r"typing\.Optional\[(.*?)\]", r"\1 | None", content)
        content = re.sub(r"Optional\[(.*?)\]", r"\1 | None", content)
        changes_made = True

    # Update isinstance checks
    if re.search(r"isinstance\(.*?, \(.*?, .*?\)\)", content):
        content = re.sub(
            r"isinstance\((.*?), \((.*?), (.*?)\)\)", r"isinstance(\1, \2 | \3)", content
        )
        changes_made = True

    if changes_made:
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {file_path}")
    return changes_made


def process_directory(directory_path: str) -> None:
    """Process all Python files in the directory recursively.

    Args:
        directory_path: Path to the directory to process
    """
    changed_files = 0
    total_files = 0

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                total_files += 1
                if process_file(file_path):
                    changed_files += 1

    print(f"Processed {total_files} files, updated {changed_files} files.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_type_annotations.py [directory]")
        print("Example: python scripts/update_type_annotations.py app")
        sys.exit(1)

    directory = sys.argv[1]
    if not Path(directory).is_dir():
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    process_directory(directory)
