import os
import yaml
import dataclasses
from pathlib import Path
from typing import Optional, List, Dict

@dataclasses.dataclass
class Skill:
    name: str
    description: str
    file_path: str
    metadata: Dict = dataclasses.field(default_factory=dict)

class SkillRegistry:
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self.skills: List[Skill] = []
        self.by_name: Dict[str, Skill] = {}
        self.load_all()

    def load_all(self):
        """Scans the skills directory and loads all valid SKILL.md files."""
        if not self.skills_dir.exists():
            return

        for skill_folder in self.skills_dir.iterdir():
            if skill_folder.is_dir():
                skill_file = skill_folder / "SKILL.md"
                if skill_file.exists():
                    self._load_skill(skill_folder.name, skill_file)

    def _load_skill(self, name: str, path: Path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    description = frontmatter.get("description", "No description provided.")
                    metadata = frontmatter.get("metadata", {})
                    
                    skill = Skill(
                        name=frontmatter.get("name", name),
                        description=description,
                        file_path=str(path.absolute()),
                        metadata=metadata
                    )
                    self.skills.append(skill)
                    self.by_name[skill.name] = skill
        except Exception as e:
            print(f"Error loading skill at {path}: {e}")

    def format_for_prompt(self) -> str:
        """Formats the registered skills into an XML block for the system prompt."""
        if not self.skills:
            return ""

        lines = ["<available_skills>"]
        for skill in self.skills:
            lines.append("  <skill>")
            lines.append(f"    <name>{self._escape_xml(skill.name)}</name>")
            lines.append(f"    <description>{self._escape_xml(skill.description)}</description>")
            lines.append(f"    <location>{self._escape_xml(skill.file_path)}</location>")
            lines.append("  </skill>")
        lines.append("</available_skills>")
        return "\n".join(lines)

    def _escape_xml(self, s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")
