# CLAUDE.md — SpecSmith Forge

## Project Overview

SpecSmith Forge is a Claude Code plugin that replaces ephemeral AI coding plans with persistent, resumable specs. It has two layers:

1. **Plugin layer** — Markdown-based Claude Code plugin (commands, agents, hooks, skill)
2. **Skill layer** — Universal SKILL.md that works with any AI coding tool via `npx skills add`

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
│   ├── status.md            # /status — detailed progress
│   └── openapi.md           # /openapi — generate OpenAPI spec from codebase
├── agents/
│   └── researcher.md        # Deep research subagent (opus model)
├── hooks/
│   └── hooks.json           # SessionStart hook — detects active specs
├── references/
│   ├── spec-format.md       # Complete SPEC.md format specification
│   └── tool-setup.md        # Setup snippets for Codex, Cursor, etc.
├── SKILL.md                 # Universal skill definition (works with all tools)
└── README.md
```

## Architecture

### Plugin Layer

The plugin is consumed directly by Claude Code — no build step. Markdown files define behavior:

- **`plugin.json`** — Plugin identity (name: `spec-smith`, version: `0.2.0`)
- **`commands/*.md`** — Each file is a slash command. Claude reads these as instructions.
- **`agents/researcher.md`** — Subagent definition. Uses Opus model with Read, Glob, Grep, Bash, WebSearch, WebFetch, Task tools for exhaustive codebase analysis.
- **`hooks/hooks.json`** — SessionStart hook checks `.specs/active` and reports the active spec ID.
- **`SKILL.md`** — Universal skill with sections for all tools + Claude Code plugin section. Defines natural language triggers ("resume", "what was I working on", "create a spec for X") and session lifecycle behavior.

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

## Versions

- **Plugin**: v0.2.0 (`.claude-plugin/plugin.json`)

## Working on This Codebase

- Plugin commands are pure markdown — edit `commands/*.md` to change behavior
- SKILL.md is universal — it must work for all AI tools, not just Claude Code
- The Claude Code Plugin section in SKILL.md is tool-specific (~20 lines at the top)
- Setup snippets in `references/tool-setup.md` are for manual tool configuration
- No build step — markdown files are consumed directly
