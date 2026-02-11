"""specsmith setup — Auto-configure a coding tool."""

import importlib.resources
from pathlib import Path

import typer

from specsmith.display import console

TOOL_CONFIG_MAP = {
    "cursor": [".cursor/rules", ".cursorrules"],
    "windsurf": [".windsurfrules"],
    "cline": [".clinerules"],
    "codex": ["AGENTS.md", "codex.md"],
    "aider": [".aider/conventions.md"],
    "gemini": ["GEMINI.md"],
}

MARKER = "Spec Management (Spec Smith)"


def _load_snippet(tool: str) -> str:
    """Load the setup snippet for a tool from package data."""
    ref = importlib.resources.files("specsmith.setup_snippets").joinpath(f"{tool}.md")
    return ref.read_text(encoding="utf-8")


def _find_config_file(project_root: Path, candidates: list[str]) -> Path | None:
    """Find the first existing config file, or return the first candidate."""
    for c in candidates:
        p = project_root / c
        if p.exists():
            return p
    return None


def setup(project_root: Path, tool: str, dry_run: bool = False) -> None:
    tool = tool.lower()

    if tool == "claude-code":
        console.print(
            "Claude Code uses the plugin system. Install SpecSmith as a plugin:\n\n"
            "  [bold]/plugin marketplace add ngvoicu/specsmith-forge[/bold]\n"
            "  [bold]/plugin install spec-smith[/bold]\n\n"
            "Or install the skill only:\n"
            "  [bold]npx skills add ngvoicu/specsmith-forge -a claude-code[/bold]"
        )
        return

    if tool not in TOOL_CONFIG_MAP:
        supported = ", ".join(sorted(TOOL_CONFIG_MAP.keys()) + ["claude-code"])
        console.print(f"[red]Unknown tool:[/red] {tool}")
        console.print(f"Supported tools: {supported}")
        raise typer.Exit(1)

    snippet = _load_snippet(tool)
    candidates = TOOL_CONFIG_MAP[tool]

    if dry_run:
        console.print(f"[bold]Would append to config file for {tool}:[/bold]\n")
        console.print(snippet)
        return

    config_file = _find_config_file(project_root, candidates)
    if config_file is None:
        # Create the first candidate
        config_file = project_root / candidates[0]
        config_file.parent.mkdir(parents=True, exist_ok=True)

    # Check if already present
    if config_file.exists():
        existing = config_file.read_text()
        if MARKER in existing:
            console.print(f"[yellow]SpecSmith is already configured in {config_file}[/yellow]")
            return
        # Append
        with open(config_file, "a") as f:
            f.write("\n\n" + snippet)
    else:
        config_file.write_text(snippet)

    console.print(f"[green]Added SpecSmith config to {config_file}[/green]")
    console.print(
        f"\n[dim]Tip: You can also use: npx skills add ngvoicu/specsmith-forge -a {tool}[/dim]"
    )
