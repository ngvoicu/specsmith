"""specsmith openapi — Generate OpenAPI 3.1.1 spec + endpoint docs from project codebase."""

import os
from pathlib import Path

import typer

from specsmith.display import console


OPENAPI_DIR = ".openapi"
OPENAPI_FILE = "openapi.yaml"
ENDPOINTS_DIR = "endpoints"


def openapi(
    project_root: Path,
    model: str = "claude-sonnet-4-20250514",
    include: list[str] | None = None,
    dry_run: bool = False,
    api_key: str | None = None,
) -> None:
    # 1. Check AI dependency
    try:
        from specsmith.ai.openapi import (  # noqa: WPS433
            gather_api_context,
            generate_endpoint_docs,
            generate_openapi,
            validate_openapi_yaml,
        )
    except ImportError:
        console.print(
            "[red]AI dependencies not installed.[/red]\n\n"
            "Install with: [bold]pip install specsmith\\[ai][/bold]"
        )
        raise typer.Exit(1)

    # 2. Resolve API key
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        console.print(
            "[red]ANTHROPIC_API_KEY not set.[/red]\n\n"
            "Set it via environment variable or --api-key flag."
        )
        raise typer.Exit(1)

    # 3. Check existing state
    openapi_dir = project_root / OPENAPI_DIR
    openapi_path = openapi_dir / OPENAPI_FILE
    endpoints_dir = openapi_dir / ENDPOINTS_DIR
    is_update = openapi_path.exists()

    action = "Updating" if is_update else "Generating"
    console.print(f"[bold]{action} OpenAPI spec[/bold] for {project_root.name}\n")

    # 4. Gather context
    with console.status("Scanning project for API endpoints, schemas, and routes..."):
        context = gather_api_context(project_root, include or [])

    if not context.has_api_code:
        console.print("[yellow]Warning:[/yellow] No API-related code detected in this project.")
        console.print("The generated spec may be minimal. Use --include to point at specific files.\n")

    # 5. Read existing spec if updating
    existing_spec = None
    if is_update:
        existing_spec = openapi_path.read_text()

    # 6. Generate OpenAPI spec
    with console.status(f"Calling {model} to generate OpenAPI 3.1.1 spec..."):
        yaml_content = generate_openapi(key, model, context, existing_spec)

    # 7. Validate
    if not validate_openapi_yaml(yaml_content):
        console.print("[yellow]Warning:[/yellow] Generated YAML may not be valid OpenAPI. Writing anyway.\n")

    # 8. Read existing endpoint docs if updating
    existing_docs: dict[str, str] = {}
    if endpoints_dir.is_dir():
        for md_file in endpoints_dir.glob("*.md"):
            existing_docs[md_file.name] = md_file.read_text()

    # 9. Generate endpoint docs
    with console.status(f"Calling {model} to generate endpoint documentation..."):
        endpoint_docs = generate_endpoint_docs(key, model, context, yaml_content, existing_docs or None)

    # 10. Dry run — print and return
    if dry_run:
        console.print("\n[bold]Generated openapi.yaml:[/bold]\n")
        console.print(yaml_content)
        if endpoint_docs:
            console.print(f"\n[bold]Generated {len(endpoint_docs)} endpoint doc(s):[/bold]\n")
            for fname, content in endpoint_docs:
                console.print(f"\n[dim]--- {fname} ---[/dim]")
                console.print(content)
        return

    # 11. Write files
    openapi_dir.mkdir(parents=True, exist_ok=True)
    openapi_path.write_text(yaml_content)

    if endpoint_docs:
        endpoints_dir.mkdir(parents=True, exist_ok=True)
        for fname, content in endpoint_docs:
            (endpoints_dir / fname).write_text(content)

    # 12. Summary
    verb = "Updated" if is_update else "Created"
    console.print(f"\n[green]{verb}:[/green] {openapi_path}")
    console.print(f"  Endpoints detected: {context.endpoint_count}")
    console.print(f"  Schemas detected: {context.schema_count}")
    if endpoint_docs:
        console.print(f"  Endpoint docs: {len(endpoint_docs)} files in {endpoints_dir}/")
