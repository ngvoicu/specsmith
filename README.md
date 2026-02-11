# Spec Smith

**Plan mode, but actually good.**

Spec Smith replaces ephemeral AI coding plans with persistent, resumable specs built through deep research and iterative interviews. Create a spec, work through it task by task, pause, switch to another spec, come back a week later and pick up exactly where you left off.

Works with Claude Code (as a plugin), Codex, Cursor, Windsurf, Cline, Aider, Gemini CLI, and any AI coding tool that can read files.

## The Problem

Every AI coding tool has some version of "plan mode" — think before you code. But these plans are ephemeral. They live in the conversation context. Close the terminal, start a new session, and the plan is gone. There's no way to:

- **Resume** a plan you were halfway through implementing
- **Switch** between multiple plans when juggling features
- **Track** which tasks are done and which are next
- **Persist** the research and decisions that informed the plan

Spec Smith fixes all of this.

## How It Works

### The Forge Workflow

Run `/spec-smith:forge "add user authentication with OAuth"` and Spec Smith takes over:

**1. Deep Research** — Exhaustive codebase scan (reads 10-20+ actual files, not just file names), web search for best practices, Context7 library docs, UI inspection if applicable. Everything saved to `.specs/research/<id>/research-01.md`.

**2. Interview** — Presents findings, states assumptions, asks targeted questions informed by the research. Not generic questions — specific ones like "I see you're using Express middleware pattern X in `src/middleware/`. Should the auth middleware follow the same pattern?" Saves answers to `interview-01.md`.

**3. Deeper Research** — Investigates the specific directions from the interview. Checks feasibility, finds edge cases.

**4. More Interviews** — As many rounds as needed until every task in the spec can be described concretely. No ambiguous "figure out X" tasks.

**5. Write Spec** — Synthesizes all research and interviews into a structured SPEC.md with phases, tasks, a decision log, and resume context.

**6. Implement** — Works through the spec task by task, checking them off, updating progress, logging new decisions.

### Specs Are Files

Specs live in `.specs/` at your project root — plain markdown with YAML frontmatter. They diff cleanly in git, are readable in any editor, and work with any AI tool.

```
.specs/
├── active                          # Which spec is active (plain text)
├── registry.md                     # Index of all specs
├── research/
│   └── user-auth-system/
│       ├── research-01.md          # Initial codebase + web research
│       ├── interview-01.md         # First interview round
│       ├── research-02.md          # Follow-up research
│       └── interview-02.md         # Second interview round
└── specs/
    └── user-auth-system/
        └── SPEC.md                 # The spec document
```

### A SPEC.md Looks Like This

```markdown
---
id: user-auth-system
title: User Auth System
status: active
created: 2026-02-10
updated: 2026-02-11
priority: high
tags: [auth, security, backend]
---

# User Auth System

## Overview
Add JWT-based authentication with OAuth (Google, GitHub) to the Express
API. Uses the existing middleware pattern in src/middleware/.

## Phase 1: Foundation [completed]
- [x] Set up auth middleware in src/middleware/auth.ts
- [x] Create User model with Prisma schema
- [x] Implement JWT generation and verification in src/auth/tokens.ts
- [x] Add refresh token rotation

## Phase 2: OAuth Integration [in-progress]
- [x] Google OAuth provider
- [ ] GitHub OAuth provider ← current
- [ ] Token exchange flow for both providers

## Phase 3: Testing & Hardening [pending]
- [ ] Unit tests for auth middleware
- [ ] Integration tests for OAuth flow
- [ ] Rate limiting on auth endpoints

---

## Resume Context
> Finished Google OAuth. GitHub OAuth callback handler is in progress at
> `src/auth/oauth/github.ts`. The authorization URL redirect works but
> the callback endpoint at `/auth/github/callback` needs to exchange the
> code for tokens. Use the same pattern as Google in `src/auth/oauth/google.ts`
> lines 45-82. The GitHub OAuth app credentials are in `.env` as
> GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.

## Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-10 | JWT over sessions | Stateless, scales for microservices |
| 2026-02-10 | Refresh token rotation | Limits damage from stolen tokens |
| 2026-02-11 | Prisma over raw SQL | Already used in the project for other models |
```

## Installation

Three ways to use Spec Smith, depending on your setup.

### Path 1: Claude Code Plugin (Full — Recommended)

Everything: all 6 slash commands, researcher agent (Opus-powered deep codebase analysis), session start hooks, SKILL.md auto-triggers.

```bash
# In Claude Code, run:
/plugin marketplace add ngvoicu/specsmith-forge
/plugin install spec-smith
```

Or manually:
```bash
git clone https://github.com/ngvoicu/specsmith-forge.git ~/.claude/plugins/spec-smith
```

After install, just run:
```
/spec-smith:forge "add user authentication"
```

### Path 2: Claude Code Skill (Lightweight via npx)

Installs just the SKILL.md. You get auto-triggers ("resume", "what was I working on", "create a spec for X") and session start detection.

You **don't** get: `/forge`, `/resume`, `/pause`, `/switch`, `/list`, `/status` slash commands, the researcher agent, or hooks.

```bash
npx skills add ngvoicu/specsmith-forge -a claude-code
```

After install, use natural language:
```
"create a spec for user authentication"
"resume"
"what was I working on"
"pause this"
"show my specs"
```

### Path 3: CLI (Any Terminal, Any AI Tool)

Standalone `specsmith` command. Works with or without AI, from any terminal.

```bash
# Core CLI
pipx install specsmith

# With AI-assisted spec generation (requires ANTHROPIC_API_KEY)
pipx install "specsmith[ai]"
```

All CLI commands:

| Command | What it does |
|---------|-------------|
| `specsmith init` | Initialize `.specs/` in your project |
| `specsmith new "Title"` | Create a new spec |
| `specsmith forge "description"` | AI-assisted research → interview → spec |
| `specsmith status` | Show progress of active spec |
| `specsmith list` | List all specs |
| `specsmith switch <id>` | Switch to a different spec |
| `specsmith pause` | Pause current spec with context |
| `specsmith resume` | Resume a paused spec |
| `specsmith complete` | Mark spec as done |
| `specsmith archive <id>` | Archive a spec |
| `specsmith edit` | Open active spec in your editor |
| `specsmith setup <tool>` | Configure another AI tool |
| `specsmith version` | Show version |

### Comparison: Plugin vs Skill vs CLI

| Feature | Plugin (full) | Skill (npx) | CLI |
|---------|:---:|:---:|:---:|
| `/forge` research-interview workflow | Yes | No | Yes (`specsmith forge`) |
| `/resume`, `/pause`, `/switch` commands | Yes | No | Yes |
| Researcher subagent (Opus, deep analysis) | Yes | No | No |
| Session start hook (detects active spec) | Yes | No | No |
| Auto-triggers ("resume", "create a spec") | Yes | Yes | N/A |
| Works outside Claude Code | No | No | Yes |
| Multi-tool `.specs/` compatibility | Yes | Yes | Yes |

## Usage

### Claude Code Plugin Flow

```
# Start a new spec with deep research
/spec-smith:forge "add OAuth authentication"
→ Deep research (reads 10-20+ files, web search, library docs)
→ Interview rounds (targeted questions, not generic)
→ Writes SPEC.md with phases, tasks, decision log
→ Implements task by task

# Session ends — save context
/spec-smith:pause
→ Writes detailed resume context (file paths, function names, next step)

# New session — pick up where you left off
/spec-smith:resume
→ Reads resume context, continues from exact spot

# Juggling features
/spec-smith:list                    # See all specs
/spec-smith:switch auth-system      # Pauses current, activates auth-system
/spec-smith:status                  # Detailed progress
```

### npx Skill Flow

Same workflow via natural language:

```
"create a spec for OAuth authentication"   → creates SPEC.md
"resume"                                   → reads active spec, continues
"what was I working on"                    → shows progress
"pause this"                               → saves context
"show my specs"                            → lists all
"switch to the auth spec"                  → changes active spec
```

### CLI Flow

```bash
# Manual spec creation
specsmith init                              # Set up .specs/
specsmith new "OAuth Authentication"        # Create spec, edit SPEC.md

# AI-assisted spec creation (needs ANTHROPIC_API_KEY)
specsmith forge "add OAuth authentication"  # Research → interview → spec

# Working with specs
specsmith status                            # Progress of active spec
specsmith list                              # All specs, grouped by status
specsmith pause --context "halfway through token rotation"
specsmith resume
specsmith switch other-spec-id
specsmith complete

# Configure other tools to use your specs
specsmith setup cursor                      # Adds to .cursorrules
specsmith setup codex                       # Adds to AGENTS.md
specsmith setup windsurf                    # Adds to .windsurfrules
specsmith setup cline                       # Adds to .clinerules
specsmith setup aider                       # Adds to .aider/conventions.md
specsmith setup gemini                      # Adds to GEMINI.md
```

## Multi-Tool Support

The spec format is pure markdown. Claude Code, Codex, Cursor, Windsurf, Cline, Aider, and Gemini CLI can all work on the same `.specs/` directory.

### Setting Up Other Tools

Run `specsmith setup <tool>` to auto-configure any supported tool. This appends a snippet to the tool's instruction file that teaches it how to read, update, and resume specs.

Supported tools: `cursor`, `codex`, `windsurf`, `cline`, `aider`, `gemini`

Or manually add the snippets from `references/tool-setup.md` to your tool's config file.

### Cross-Tool Sync

All tools share the same files:
- **`← current` marker** — Every tool knows which task is next
- **Resume Context** — Detailed state with file paths and function names
- **Phase status markers** — `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`

**One rule:** Don't run two tools on the same spec simultaneously. Different specs in parallel is fine.

## The Forge Workflow (Detailed)

### Phase 1: Deep Research

Not a quick scan. The researcher reads 10-20+ files, following dependency chains, checking tests, examining config. Also runs web searches for best practices, pulls library docs via Context7.

Output saved to `.specs/research/<id>/research-01.md`. Covers:
- Project architecture and directory structure
- Every file touching the area of change
- Tech stack versions (from lock files, not guesses)
- How similar features are currently implemented
- Test patterns and coverage
- Risk assessment

### Phase 2-4: Interviews

Targeted questions based on what research found. Not generic "what do you want?" — specific questions like:

- "I see rate limiting middleware at `src/middleware/rateLimit.ts`. Should auth endpoints use the same limiter or a stricter one?"
- "The User model uses Prisma. Should OAuth tokens go in the same schema or a separate `AuthToken` model?"

Multiple rounds (typically 2-5) until every task can be described concretely. Each round saved to `interview-01.md`, `interview-02.md`, etc.

### Phase 5: Write Spec

Synthesizes everything into a SPEC.md:
- 3-6 phases, each with concrete tasks
- Each task is ~30 min to 2 hours of work
- Decision log captures non-obvious technical choices
- Resume context section ready for first pause

### Phase 6: Implement

Works through the spec task by task:
- Marks tasks `← current` as they start
- Checks off `- [x]` when done
- Updates phase status markers
- Logs new decisions to the Decision Log
- Updates Resume Context at natural pauses

## Plan Mode

Spec Smith **bypasses** Claude Code's built-in plan mode. The `/forge` command IS your planning phase — deep research, interviews, spec writing. You don't need plan mode at all.

If you happen to be in plan mode when you run `/forge`, it still works:
- Research and interviews are read-only and run fine
- When it's time to write the spec, you'll be asked to exit plan mode (Shift+Tab) so files can be created

## Plugin Structure

```
specsmith-forge/
├── .claude-plugin/
│   ├── plugin.json                 # Plugin metadata (v0.2.0)
│   └── marketplace.json            # Marketplace registration
├── commands/
│   ├── forge.md                    # Research → interview → spec → implement
│   ├── resume.md                   # Resume active spec
│   ├── pause.md                    # Pause with context
│   ├── switch.md                   # Switch between specs
│   ├── list.md                     # List all specs
│   └── status.md                   # Detailed progress
├── agents/
│   └── researcher.md               # Deep research subagent (Opus)
├── hooks/
│   └── hooks.json                  # SessionStart detection
├── references/
│   ├── spec-format.md              # SPEC.md format specification
│   └── tool-setup.md               # Setup snippets for all tools
├── scripts/
│   ├── init_specs.py               # Initialize .specs/
│   ├── new_spec.py                 # Create a spec
│   └── spec_status.py              # Show progress
├── SKILL.md                        # Core skill (auto-triggers)
└── cli/                            # Python CLI package (v0.1.0)
    ├── pyproject.toml
    ├── src/specsmith/
    │   ├── cli.py                  # Typer app
    │   ├── display.py              # Terminal UI
    │   ├── core/                   # Data model + file management
    │   ├── commands/               # Command implementations
    │   ├── ai/                     # AI forge (Anthropic API)
    │   └── setup_snippets/         # Tool config snippets
    └── tests/
```

## Spec Format

Full specification in [`references/spec-format.md`](references/spec-format.md).

### Frontmatter

| Field | Required | Description |
|-------|:---:|-------------|
| `id` | Yes | URL-safe slug (e.g., `user-auth-system`) |
| `title` | Yes | Human-readable name |
| `status` | Yes | `active`, `paused`, `completed`, `archived` |
| `created` | Yes | ISO date (YYYY-MM-DD) |
| `updated` | Yes | ISO date of last modification |
| `priority` | No | `high`, `medium`, `low` (default: medium) |
| `tags` | No | YAML array |

### Conventions

- **Phase markers**: `[pending]`, `[in-progress]`, `[completed]`, `[blocked]`
- **Task checkboxes**: `- [ ]` unchecked, `- [x]` done
- **Current task**: `← current` after the task text
- **Uncertainty**: `[NEEDS CLARIFICATION]` prefix on unclear tasks
- **Resume Context**: Blockquote with specific file paths, function names, exact next step
- **Decision Log**: Table with date, decision, rationale

## CLI Reference

### Global Flags

| Flag | Description |
|------|-------------|
| `--path, -p <dir>` | Project root directory |
| `--no-color` | Disable colored output |
| `--json` | Output as JSON |
| `--verbose, -v` | Verbose output |

### Forge Options

```bash
specsmith forge "description" \
  --model claude-sonnet-4-20250514 \    # Model to use
  --include <path> \                    # Additional files to include
  --edit \                              # Open spec in editor after creation
  --dry-run \                           # Preview without writing files
  --api-key <key>                       # Anthropic API key (or ANTHROPIC_API_KEY env)
```

### Other Command Options

```bash
specsmith new "Title" --priority high   # Set priority on creation
specsmith pause --context "message"     # Add context message
specsmith complete --force              # Skip confirmation
specsmith setup <tool> --dry-run       # Preview config changes
```

See the full [CLI documentation](cli/README.md) for details.

## Why Not Just Use Plan Mode?

Plan mode is a good idea with a bad implementation. It restricts Claude to read-only tools and asks for a plan. That's it. No persistence, no research depth, no interviews, no progress tracking.

Spec Smith's `/forge` command does what plan mode should do:

- **Research depth**: Reads 10-20+ files, searches the web, pulls library docs. Not a quick scan.
- **Interviews**: Asks you targeted questions based on what it found. Multiple rounds until there's no ambiguity.
- **Persistence**: Everything is saved to files. Research notes, interviews, the spec itself. Nothing lives only in context.
- **Resumability**: Close the terminal, come back next week. The spec remembers exactly where you were.
- **Multi-spec**: Juggle multiple features. Switch between them with one command.

## License

MIT
