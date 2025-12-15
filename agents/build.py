#!/usr/bin/env python3
"""Build agent role files by combining source fragments."""

import re
import sys
from pathlib import Path


def increase_header_levels(content: str) -> str:
    """Increase markdown header levels by one.

    Args:
        content: Markdown content

    Returns:
        Content with headers increased by one level
    """
    return re.sub(r'^(#+) ', r'#\1 ', content, flags=re.MULTILINE)


def build_role(output_path: Path, role_title: str, *source_files: Path) -> None:
    """Combine source files into a single role file with decorators.

    Args:
        output_path: Where to write the combined output
        role_title: Title for the agent role
        source_files: Source fragment files to combine
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as out:
        # Write role title
        out.write(f"# {role_title}\n\n")
        out.write("---\n\n")

        # Combine source files
        for i, src_file in enumerate(source_files):
            if not src_file.exists():
                print(f"Warning: {src_file} does not exist", file=sys.stderr)
                continue

            content = src_file.read_text()

            # Add separator between sections (but not before first)
            if i > 0:
                out.write("\n---\n\n")

            # Increase header levels and write source content
            content = increase_header_levels(content)
            out.write(content)

            # Ensure newline at end
            if not content.endswith("\n"):
                out.write("\n")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: build.py OUTPUT TITLE SOURCE...", file=sys.stderr)
        sys.exit(1)

    output_path = Path(sys.argv[1])
    role_title = sys.argv[2]
    source_files = [Path(f) for f in sys.argv[3:]]

    build_role(output_path, role_title, *source_files)
    print(f"Built {output_path}")


if __name__ == "__main__":
    main()
