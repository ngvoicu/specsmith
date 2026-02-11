# CLAUDE.md — SpecSmith Forge

## Project Overview

SpecSmith Forge is a Claude Code plugin + Python CLI that replaces ephemeral AI coding plans with persistent, resumable specs. It has two layers:

1. **Plugin layer** — Markdown-based Claude Code plugin (commands, agents, hooks, skill)
2. **CLI layer** — Standalone Python CLI (`specsmith`) that works from any terminal

## Repository Structure

```
specsmith-forge/
├── .claude-plugin/          # Plugin metadata
│   ├── plugin.json          # Name: spec-smith, version 0.2.0
│   └── marketplace.json     # Marketplace registration
├── commands/                # Plugin slash commands (markdown instructions)
│   ├── forge.md             # /forge — research → interview → spec → implement
│   ├── resume.md            # /resume — pick up where you left off
│   ├── pause.md             # /pause — save context and stop
│   ├── switch.md            # /switch — change active spec
│   ├── list.md              # /list — show all specs
│   └── status.md            # /status — detailed progress
├── agents/
│   └── researcher.md        # Deep research subagent (opus model)
├── hooks/
│   └── hooks.json           # SessionStart hook — detects active specs
├── references/
│   ├── spec-format.md       # Complete SPEC.md format specification
│   └── tool-setup.md        # Setup snippets for Codex, Cursor, etc.
├── scripts/                 # Standalone Python utility scripts
│   ├── init_specs.py
│   ├── new_spec.py
│   └── spec_status.py
├── SKILL.md                 # Claude Code skill definition (auto-triggers)
├── cli/                     # Python CLI package
│   ├── pyproject.toml       # specsmith v0.1.0, Python 3.10+
│   ├── src/specsmith/
│   │   ├── cli.py           # Main Typer app, all commands registered here
│   │   ├── display.py       # Terminal UI (colors, progress bars, tables)
│   │   ├── core/            # Spec data model and file management
│   │   │   ├── spec.py      # Spec, Phase, Task dataclasses
│   │   │   ├── parser.py    # Parse SPEC.md files
│   │   │   ├── template.py  # SPEC.md template
│   │   │   ├── paths.py     # Find .specs/ directory
│   │   │   ├── active.py    # Manage .specs/active file
│   │   │   ├── registry.py  # Manage .specs/registry.md
│   │   │   └── slugify.py   # Title → spec-id conversion
│   │   ├── commands/        # CLI command implementations (12 files)
│   │   ├── ai/              # AI-assisted spec generation
│   │   │   ├── client.py    # Anthropic API wrapper
│   │   │   ├── forge.py     # Forge workflow orchestration
│   │   │   └── prompts.py   # LLM prompts
│   │   └── setup_snippets/  # Tool config snippets (.md for each tool)
│   └── tests/
│       ├── test_commands.py
│       ├── test_parser.py
│       ├── test_registry.py
│       └── test_slugify.py
└── README.md
```

## Architecture

### Plugin Layer

The plugin is consumed directly by Claude Code — no build step. Markdown files define behavior:

- **`plugin.json`** — Plugin identity (name: `spec-smith`, version: `0.2.0`)
- **`commands/*.md`** — Each file is a slash command. Claude reads these as instructions.
- **`agents/researcher.md`** — Subagent definition. Uses Opus model with Read, Glob, Grep, Bash, WebSearch, WebFetch, Task tools for exhaustive codebase analysis.
- **`hooks/hooks.json`** — SessionStart hook checks `.specs/active` and reports the active spec ID.
- **`SKILL.md`** — Defines natural language triggers ("resume", "what was I working on", "create a spec for X") and session lifecycle behavior.

### CLI Layer

Python package in `cli/`. Entry point: `specsmith.cli:app` (Typer).

- **Dependencies**: `typer[all]>=0.12`, `pyyaml>=6.0`
- **Optional**: `anthropic>=0.40` (install with `pip install "specsmith[ai]"`)
- **Build system**: Hatchling

### Data Layer — `.specs/` Directory

Created in the project root. All tools (Claude Code, Codex, Cursor, etc.) share this directory.

```
.specs/
├── active                  # Plain text file containing active spec ID
├── registry.md             # Markdown table indexing all specs
├── research/<spec-id>/     # Research and interview artifacts
│   ├── research-01.md
│   ├── interview-01.md
│   └── ...
└── specs/<spec-id>/
    └── SPEC.md             # The spec document
```

## Key Conventions

### Spec Format

Full spec in `references/spec-format.md`. Summary:

- **Frontmatter**: YAML with `id`, `title`, `status`, `created`, `updated`, optional `priority` and `tags`
- **Spec IDs**: Lowercase hyphenated slugs derived from titles (e.g., "User Auth System" → `user-auth-system`)
- **Phase status markers**: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`
- **Task markers**: `- [ ]` unchecked, `- [x]` done, `← current` marks the active task
- **Resume Context**: Blockquote with specific file paths, function names, exact next step
- **Decision Log**: Markdown table with date, decision, rationale

### Status Values

Specs: `active`, `paused`, `completed`, `archived`
Phases: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`

### Forge Workflow Phases

1. Deep Research → save to `.specs/research/<id>/research-01.md`
2. Interview Round 1 → save to `.specs/research/<id>/interview-01.md`
3. Deeper Research → `research-02.md`
4. Interview Round 2+ → repeat until no ambiguity
5. Write SPEC.md → `.specs/specs/<id>/SPEC.md`
6. Implement → work through tasks, update checkboxes

## Build & Test

### CLI

```bash
cd cli
pip install -e ".[ai]"   # Dev install with AI support
pytest                    # Run tests
```

### Plugin

No build step. Markdown files are consumed directly by Claude Code.

## Versions

- **Plugin**: v0.2.0 (`.claude-plugin/plugin.json`)
- **CLI**: v0.1.0 (`cli/pyproject.toml`)

## Dependencies

- Python 3.10+ (CLI)
- `typer[all]>=0.12` — CLI framework
- `pyyaml>=6.0` — YAML frontmatter parsing
- `anthropic>=0.40` — Optional, for AI forge command

## Working on This Codebase

- Plugin commands are pure markdown — edit `commands/*.md` to change behavior
- CLI commands live in `cli/src/specsmith/commands/` — one file per command
- The core data model is in `cli/src/specsmith/core/spec.py` (Spec, Phase, Task dataclasses)
- Parser (`core/parser.py`) reads SPEC.md files and must handle all format variations in `references/spec-format.md`
- Template (`core/template.py`) generates new SPEC.md files
- Setup snippets in `cli/src/specsmith/setup_snippets/` are markdown fragments injected into tool config files
- Tests are in `cli/tests/` — run with `pytest` from the `cli/` directory
