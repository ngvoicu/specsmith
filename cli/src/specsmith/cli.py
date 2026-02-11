"""SpecSmith CLI — Typer app with all commands."""

from pathlib import Path
from typing import Annotated, Optional

import typer

from specsmith import __version__
from specsmith.core.paths import find_specs_root

app = typer.Typer(
    name="specsmith",
    help="Spec-driven development from the terminal.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# ── Global options via callback ──────────────────────────────────────

PathOption = Annotated[
    Optional[Path],
    typer.Option("--path", "-p", help="Project root directory."),
]
JsonFlag = Annotated[bool, typer.Option("--json", help="Output as JSON.")]
VerboseFlag = Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output.")]
NoColorFlag = Annotated[bool, typer.Option("--no-color", help="Disable colour output.")]


def _resolve_root(path: Path | None) -> Path:
    """Resolve project root: explicit --path, or walk up to find .specs/."""
    if path is not None:
        root = Path(path).resolve()
        if not (root / ".specs").is_dir():
            # For init, the root doesn't need .specs/ yet
            return root
        return root
    found = find_specs_root()
    if found:
        return found
    return Path.cwd()


_PROJECT_MARKERS = {".git", "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "Gemfile"}


def _resolve_project_root(path: Path | None) -> Path:
    """Resolve project root by walking up to find .git or a package manifest."""
    if path is not None:
        return Path(path).resolve()
    current = Path.cwd().resolve()
    while True:
        if any((current / m).exists() for m in _PROJECT_MARKERS):
            return current
        parent = current.parent
        if parent == current:
            return Path.cwd()
        current = parent


# ── Commands ─────────────────────────────────────────────────────────


@app.command()
def init(
    path: PathOption = None,
) -> None:
    """Initialize .specs/ in the current project."""
    from specsmith.commands.init import init as do_init

    root = path.resolve() if path else Path.cwd()
    do_init(root)


@app.command()
def new(
    title: Annotated[str, typer.Argument(help="Spec title.")],
    priority: Annotated[str, typer.Option(help="Priority: high, medium, low.")] = "medium",
    path: PathOption = None,
) -> None:
    """Create a new spec from a title."""
    from specsmith.commands.new import new as do_new

    do_new(_resolve_root(path), title, priority)


@app.command()
def status(
    spec_id: Annotated[Optional[str], typer.Argument(help="Spec ID (default: active spec).")] = None,
    path: PathOption = None,
) -> None:
    """Show progress of a spec."""
    from specsmith.commands.status import status as do_status

    do_status(_resolve_root(path), spec_id)


@app.command(name="list")
def list_cmd(
    path: PathOption = None,
) -> None:
    """List all specs grouped by status."""
    from specsmith.commands.list_cmd import list_specs

    list_specs(_resolve_root(path))


@app.command()
def switch(
    spec_id: Annotated[str, typer.Argument(help="Spec ID to switch to.")],
    path: PathOption = None,
) -> None:
    """Switch active spec (pauses current, resumes target)."""
    from specsmith.commands.switch import switch as do_switch

    do_switch(_resolve_root(path), spec_id)


@app.command()
def pause(
    spec_id: Annotated[Optional[str], typer.Argument(help="Spec ID (default: active spec).")] = None,
    context: Annotated[Optional[str], typer.Option("--context", help="Add context message to Resume Context.")] = None,
    path: PathOption = None,
) -> None:
    """Mark a spec as paused."""
    from specsmith.commands.pause import pause as do_pause

    do_pause(_resolve_root(path), spec_id, context)


@app.command()
def resume(
    spec_id: Annotated[Optional[str], typer.Argument(help="Spec ID (default: active spec).")] = None,
    path: PathOption = None,
) -> None:
    """Reactivate a paused spec."""
    from specsmith.commands.resume import resume as do_resume

    do_resume(_resolve_root(path), spec_id)


@app.command()
def complete(
    spec_id: Annotated[Optional[str], typer.Argument(help="Spec ID (default: active spec).")] = None,
    force: Annotated[bool, typer.Option("--force", help="Complete even with unchecked tasks.")] = False,
    path: PathOption = None,
) -> None:
    """Mark a spec as completed."""
    from specsmith.commands.complete import complete as do_complete

    do_complete(_resolve_root(path), spec_id, force)


@app.command()
def archive(
    spec_id: Annotated[str, typer.Argument(help="Spec ID to archive.")],
    path: PathOption = None,
) -> None:
    """Archive a spec."""
    from specsmith.commands.archive import archive as do_archive

    do_archive(_resolve_root(path), spec_id)


@app.command()
def edit(
    spec_id: Annotated[Optional[str], typer.Argument(help="Spec ID (default: active spec).")] = None,
    path: PathOption = None,
) -> None:
    """Open SPEC.md in $EDITOR."""
    from specsmith.commands.edit import edit as do_edit

    do_edit(_resolve_root(path), spec_id)


@app.command()
def setup(
    tool: Annotated[str, typer.Argument(help="Tool to configure (cursor/codex/windsurf/cline/aider/gemini/claude-code).")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be appended.")] = False,
    path: PathOption = None,
) -> None:
    """Auto-configure a coding tool for SpecSmith."""
    from specsmith.commands.setup import setup as do_setup

    root = path.resolve() if path else Path.cwd()
    do_setup(root, tool, dry_run)


@app.command()
def forge(
    description: Annotated[str, typer.Argument(help="Description of what to build.")],
    model: Annotated[str, typer.Option(help="Claude model to use.")] = "claude-sonnet-4-20250514",
    include: Annotated[Optional[list[str]], typer.Option("--include", help="Additional files to include in context.")] = None,
    edit_after: Annotated[bool, typer.Option("--edit", help="Open in $EDITOR after creation.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print to stdout instead of saving.")] = False,
    api_key: Annotated[Optional[str], typer.Option("--api-key", help="Anthropic API key.")] = None,
    path: PathOption = None,
) -> None:
    """AI-assisted spec creation (requires ANTHROPIC_API_KEY)."""
    from specsmith.commands.forge import forge as do_forge

    do_forge(_resolve_root(path), description, model, include, edit_after, dry_run, api_key)


@app.command()
def openapi(
    model: Annotated[str, typer.Option(help="Claude model to use.")] = "claude-sonnet-4-20250514",
    include: Annotated[Optional[list[str]], typer.Option("--include", help="Additional files to include in context.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print to stdout instead of saving.")] = False,
    api_key: Annotated[Optional[str], typer.Option("--api-key", help="Anthropic API key.")] = None,
    path: PathOption = None,
) -> None:
    """Generate OpenAPI 3.1.1 spec + endpoint docs from project codebase (requires ANTHROPIC_API_KEY)."""
    from specsmith.commands.openapi import openapi as do_openapi

    do_openapi(_resolve_project_root(path), model, include, dry_run, api_key)


@app.command()
def version() -> None:
    """Show version."""
    typer.echo(f"specsmith {__version__}")


if __name__ == "__main__":
    app()
