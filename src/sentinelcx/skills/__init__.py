"""Agent skills loader — reads markdown skill files at runtime."""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def load_skill(name: str) -> str:
    """Load a skill markdown file by name (without .md extension).

    Args:
        name: Skill name, e.g. "sentiment_analysis", "product_knowledge", "compliance_check"

    Returns:
        The full markdown content of the skill file.
    """
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {name} (looked for {path})")
    return path.read_text(encoding="utf-8")


def list_skills() -> list[str]:
    """List all available skill names."""
    return [p.stem for p in sorted(SKILLS_DIR.glob("*.md"))]
