#!/usr/bin/env python3
"""
Obsidian Integration
Provides programmatic access to Obsidian vaults for knowledge management
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    # Optional: used to enforce repo-hygiene for vault location.
    from integrations.paths import validate_external_workspace
except Exception:
    validate_external_workspace = None


class ObsidianIntegration:
    """Integration with Obsidian knowledge base"""

    def __init__(self, vault_path: str = None):
        raw = (vault_path or os.getenv("OBSIDIAN_VAULT_PATH", "")).strip()

        # If no explicit vault path was provided, prefer the external semester
        # workspace layout: <OSMEN_SEMESTER_WORKSPACE>/vault
        if not raw:
            semester_ws = os.getenv("OSMEN_SEMESTER_WORKSPACE", "").strip()
            if semester_ws:
                try:
                    ws_path = Path(semester_ws).expanduser().resolve()
                    if validate_external_workspace is not None:
                        ws_path = validate_external_workspace(ws_path)
                    raw = str(ws_path / "vault")
                except Exception:
                    # Fall back to empty (no vault configured)
                    raw = ""

        self.vault_path = Path(raw) if raw else None

    def list_notes(self, folder: str = "") -> List[Dict]:
        """List all notes in the vault or a specific folder"""
        if not self.vault_path or not self.vault_path.exists():
            return []

        search_path = self.vault_path / folder if folder else self.vault_path
        notes = []

        for md_file in search_path.rglob("*.md"):
            relative_path = md_file.relative_to(self.vault_path)
            notes.append(
                {
                    "title": md_file.stem,
                    "path": str(relative_path),
                    "modified": datetime.fromtimestamp(
                        md_file.stat().st_mtime
                    ).isoformat(),
                }
            )

        return notes

    def read_note(self, note_path: str) -> Dict:
        """Read a note from the vault"""
        if not self.vault_path:
            return {"error": "Vault path not configured"}

        full_path = self.vault_path / note_path
        if not full_path.exists():
            return {"error": f"Note not found: {note_path}"}

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter if present
        frontmatter = {}
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = self._parse_frontmatter(parts[1])
                content = parts[2].strip()

        # Extract links
        links = self._extract_links(content)

        # Extract tags
        tags = self._extract_tags(content)

        return {
            "title": Path(note_path).stem,
            "path": note_path,
            "content": content,
            "frontmatter": frontmatter,
            "links": links,
            "tags": tags,
            "modified": datetime.fromtimestamp(full_path.stat().st_mtime).isoformat(),
        }

    def create_note(
        self,
        title: str,
        content: str,
        folder: str = "",
        frontmatter: Dict = None,
        tags: List[str] = None,
    ) -> Dict:
        """Create a new note in the vault"""
        if not self.vault_path:
            return {"error": "Vault path not configured"}

        # Sanitize title for filename
        filename = self._sanitize_filename(title) + ".md"

        # Determine full path
        if folder:
            note_folder = self.vault_path / folder
            note_folder.mkdir(parents=True, exist_ok=True)
            full_path = note_folder / filename
        else:
            full_path = self.vault_path / filename

        # Build note content
        note_content = []

        # Add frontmatter
        if frontmatter or tags:
            note_content.append("---")
            if frontmatter:
                for key, value in frontmatter.items():
                    note_content.append(f"{key}: {value}")
            if tags:
                note_content.append(f'tags: [{", ".join(tags)}]')
            note_content.append("---")
            note_content.append("")

        # Add title as H1
        note_content.append(f"# {title}")
        note_content.append("")

        # Add content
        note_content.append(content)

        # Write file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(note_content))

        return {
            "success": True,
            "path": str(full_path.relative_to(self.vault_path)),
            "created": datetime.now().isoformat(),
        }

    def update_note(
        self,
        note_path: str,
        content: str = None,
        append: bool = False,
        frontmatter: Dict = None,
    ) -> Dict:
        """Update an existing note"""
        if not self.vault_path:
            return {"error": "Vault path not configured"}

        full_path = self.vault_path / note_path
        if not full_path.exists():
            return {"error": f"Note not found: {note_path}"}

        if append:
            # Append to existing content
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + content)
        elif content:
            # Replace content (preserve frontmatter if exists)
            existing = self.read_note(note_path)
            note_content = []

            if existing.get("frontmatter") or frontmatter:
                note_content.append("---")
                fm = frontmatter or existing.get("frontmatter", {})
                for key, value in fm.items():
                    note_content.append(f"{key}: {value}")
                note_content.append("---")
                note_content.append("")

            note_content.append(content)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(note_content))

        return {
            "success": True,
            "path": note_path,
            "updated": datetime.now().isoformat(),
        }

    def delete_note(self, note_path: str, trash: bool = True) -> Dict:
        """Delete a note from the vault.

        Args:
            note_path: Path relative to vault root.
            trash: If True, move into a vault-local .trash folder. If False,
                permanently deletes the file.

        Returns:
            Dict with success/error and resulting path information.
        """
        if not self.vault_path:
            return {"error": "Vault path not configured"}

        vault_root = self.vault_path.expanduser().resolve()

        requested = Path(note_path)
        full_path = (vault_root / requested).resolve()

        # Prevent path traversal outside the vault.
        if vault_root != full_path and vault_root not in full_path.parents:
            return {"error": "Invalid note path (outside vault)"}

        if not full_path.exists():
            return {"error": f"Note not found: {note_path}"}
        if full_path.is_dir():
            return {"error": f"Path is a directory, not a note: {note_path}"}

        if trash:
            trash_root = vault_root / ".trash"
            dest_path = (trash_root / requested).resolve()

            # Ensure destination stays inside .trash.
            trash_root_resolved = trash_root.resolve()
            if (
                trash_root_resolved != dest_path
                and trash_root_resolved not in dest_path.parents
            ):
                return {"error": "Invalid trash destination"}

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # If a file already exists at the destination, add a timestamp suffix.
            if dest_path.exists():
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = dest_path.with_name(
                    f"{dest_path.stem}_{stamp}{dest_path.suffix}"
                )

            full_path.rename(dest_path)
            return {
                "success": True,
                "deleted": True,
                "trashed": True,
                "path": note_path,
                "trash_path": str(dest_path.relative_to(vault_root)),
                "updated": datetime.now().isoformat(),
            }

        full_path.unlink()
        return {
            "success": True,
            "deleted": True,
            "trashed": False,
            "path": note_path,
            "updated": datetime.now().isoformat(),
        }

    def search_notes(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search for notes containing the query text"""
        if not self.vault_path or not self.vault_path.exists():
            return []

        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        for md_file in self.vault_path.rglob("*.md"):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(query, content, flags):
                relative_path = md_file.relative_to(self.vault_path)
                results.append(
                    {
                        "title": md_file.stem,
                        "path": str(relative_path),
                        "modified": datetime.fromtimestamp(
                            md_file.stat().st_mtime
                        ).isoformat(),
                    }
                )

        return results

    def get_backlinks(self, note_path: str) -> List[Dict]:
        """Get all notes that link to the specified note"""
        if not self.vault_path or not self.vault_path.exists():
            return []

        note_title = Path(note_path).stem
        backlinks = []

        # Search for [[note_title]] or [[note_title|alias]]
        pattern = rf"\[\[{re.escape(note_title)}(?:\|[^\]]+)?\]\]"

        for md_file in self.vault_path.rglob("*.md"):
            if md_file.stem == note_title:
                continue  # Skip the note itself

            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            if re.search(pattern, content, re.IGNORECASE):
                relative_path = md_file.relative_to(self.vault_path)
                backlinks.append({"title": md_file.stem, "path": str(relative_path)})

        return backlinks

    def export_graph(self) -> Dict:
        """Export the graph structure of the vault (notes and their connections)"""
        if not self.vault_path or not self.vault_path.exists():
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        for md_file in self.vault_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(self.vault_path))
            node_id = md_file.stem

            nodes.append({"id": node_id, "label": node_id, "path": relative_path})

            # Extract links from this note
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            links = self._extract_links(content)
            for link in links:
                edges.append({"source": node_id, "target": link, "type": "wikilink"})

        return {"nodes": nodes, "edges": edges, "vault": str(self.vault_path)}

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename to be filesystem-safe"""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        # Replace spaces with underscores (optional)
        # filename = filename.replace(' ', '_')
        return filename.strip()

    @staticmethod
    def _parse_frontmatter(fm_text: str) -> Dict:
        """Parse YAML-style frontmatter"""
        frontmatter = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                frontmatter[key.strip()] = value.strip()
        return frontmatter

    @staticmethod
    def _extract_links(content: str) -> List[str]:
        """Extract wikilinks from content"""
        # Match [[note]] or [[note|alias]]
        pattern = r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]"
        return re.findall(pattern, content)

    @staticmethod
    def _extract_tags(content: str) -> List[str]:
        """Extract tags from content"""
        # Match #tag but not ##heading
        pattern = r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/-]*)"
        return re.findall(pattern, content)


def main():
    """Test the integration"""
    integration = ObsidianIntegration()

    # Example: List notes
    notes = integration.list_notes()
    print(f"Found {len(notes)} notes")

    # Example: Create a note
    result = integration.create_note(
        title="Test Note",
        content="This is a test note created by OsMEN.",
        tags=["test", "osmen"],
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
