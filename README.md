# Spec Smith

**Plan mode, but actually good.**

Spec Smith replaces ephemeral AI coding plans with persistent, resumable specs built through deep research and iterative interviews. Create a spec, work through it task by task, pause, switch to another spec, come back a week later and pick up exactly where you left off.

Works with Claude Code (as a plugin), Codex, Cursor, Windsurf, Cline, Gemini CLI, and any AI coding tool that can read files.

## The Problem

Every AI coding tool has some version of "plan mode" — think before you code. But these plans are ephemeral. They live in the conversation context. Close the terminal, start a new session, and the plan is gone. There's no way to:

- **Resume** a plan you were halfway through implementing
- **Switch** between multiple plans when juggling features
- **Track** which tasks are done and which are next
- **Persist** the research and decisions that informed the plan

Spec Smith fixes all of this.

## How It Works

### The Forge Workflow

Run `/specsmith:forge "add user authentication with OAuth"` and Spec Smith takes over:

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
├── registry.md                     # Index of all specs (source of truth for status)
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
- [x] [AUTH-01] Set up auth middleware in src/middleware/auth.ts
- [x] [AUTH-02] Create User model with Prisma schema
- [x] [AUTH-03] Implement JWT generation and verification in src/auth/tokens.ts
- [x] [AUTH-04] Add refresh token rotation

## Phase 2: OAuth Integration [in-progress]
- [x] [AUTH-05] Google OAuth provider
- [ ] [AUTH-06] GitHub OAuth provider ← current
- [ ] [AUTH-07] Token exchange flow for both providers

## Phase 3: Testing & Hardening [pending]
- [ ] [AUTH-08] Unit tests for auth middleware
- [ ] [AUTH-09] Integration tests for OAuth flow
- [ ] [AUTH-10] Rate limiting on auth endpoints

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

## Deviations
| Task | Spec Said | Actually Did | Why |
|------|-----------|-------------|-----|
| AUTH-05 | Use passport.js | Direct googleapis calls | Simpler for a single provider, avoids passport session overhead |
```

## Installation

Two ways to use Spec Smith, depending on your setup.

### Path 1: Claude Code Plugin (Full — Recommended)

Everything: all 7 slash commands (`/forge`, `/resume`, `/pause`, `/switch`, `/list`, `/status`, `/openapi`), researcher agent (Opus-powered deep codebase analysis), session start hooks, SKILL.md auto-triggers.

```bash
# In Claude Code, run:
/plugin marketplace add ngvoicu/specsmith
/plugin install specsmith
```

Or manually:
```bash
git clone https://github.com/ngvoicu/specsmith.git ~/.claude/plugins/specsmith
```

After install, just run:
```
/specsmith:forge "add user authentication"
```

### Path 2: Quick Setup via npx (Any Tool)

Installs the SKILL.md into your tool's skill/instruction directory so it knows how to read, update, and resume specs from `.specs/`.

```bash
# Claude Code (skill only — auto-triggers, no slash commands)
npx skills add ngvoicu/specsmith -a claude-code

# OpenAI Codex
npx skills add ngvoicu/specsmith -a codex

# Cursor
npx skills add ngvoicu/specsmith -a cursor

# Windsurf (see Windsurf Note below — extra step required)
npx skills add ngvoicu/specsmith -a windsurf

# Cline
npx skills add ngvoicu/specsmith -a cline

# Gemini CLI
npx skills add ngvoicu/specsmith -a gemini
```

For Claude Code, this installs SKILL.md with auto-triggers ("resume", "what was I working on", "create a spec for X"). You **don't** get slash commands, the researcher agent, or hooks — use Path 1 for the full plugin.

For other tools, this installs the SKILL.md which teaches the tool the full spec workflow — session start detection, resuming, pausing, creating specs, updating progress, and cross-session continuity.

#### Windsurf Note

`npx skills add -a windsurf` creates a symlink at `.windsurf/skills/specsmith` that Windsurf Cascade doesn't follow. After installing, replace it with real files and also copy to the Codeium path:

**macOS / Linux:**
```bash
rm .windsurf/skills/specsmith                                        # remove symlink
rm .codeium/windsurf/skills/specsmith                                # remove symlink

cp -r .agents/skills/specsmith .windsurf/skills/specsmith            # real copy
cp -r .agents/skills/specsmith .codeium/windsurf/skills/specsmith    # real copy
```

**Windows (PowerShell):**
```powershell
Remove-Item .windsurf\skills\specsmith                                           # remove symlink
Remove-Item .codeium\windsurf\skills\specsmith                                   # remove symlink
Copy-Item -Recurse .agents\skills\specsmith .windsurf\skills\specsmith           # real copy
Copy-Item -Recurse .agents\skills\specsmith .codeium\windsurf\skills\specsmith.  # real copy
```

Cascade will auto-activate the skill when your request matches the description, or you can invoke it manually with `@specsmith`.

### Comparison: Plugin vs npx

| Feature | Plugin (full) | npx (any tool) |
|---------|:---:|:---:|
| `/forge` research-interview workflow | Yes | No |
| `/resume`, `/pause`, `/switch` commands | Yes | No |
| Researcher subagent (Opus, deep analysis) | Yes | No |
| Session start hook (detects active spec) | Yes | No |
| Auto-triggers (Claude Code only) | Yes | Yes |
| Works with Codex, Cursor, Windsurf, etc. | No | Yes |
| Multi-tool `.specs/` compatibility | Yes | Yes |

## Usage

### Claude Code Plugin Flow

```
# Start a new spec with deep research
/specsmith:forge "add OAuth authentication"
→ Deep research (reads 10-20+ files, web search, library docs)
→ Interview rounds (targeted questions, not generic)
→ Writes SPEC.md with phases, tasks, decision log
→ Implements task by task

# Generate OpenAPI spec from your codebase
/specsmith:openapi
→ Scans routes, schemas, security config
→ Writes .openapi/openapi.yaml + per-endpoint docs

# Session ends — save context
/specsmith:pause
→ Writes detailed resume context (file paths, function names, next step)

# New session — pick up where you left off
/specsmith:resume
→ Reads resume context, continues from exact spot

# Juggling features
/specsmith:list                    # See all specs
/specsmith:switch auth-system      # Pauses current, activates auth-system
/specsmith:status                  # Detailed progress
```

### Any Tool Flow (Codex, Cursor, Windsurf, Cline, Gemini CLI)

Once configured via `npx skills add`, every tool understands the same spec lifecycle. Here's the complete workflow:

**Create a spec** — Ask the tool to plan or spec out work. It creates `.specs/specs/<id>/SPEC.md` with phases, tasks, a decision log, and resume context.

**Resume** — The tool reads `.specs/registry.md` to find the active spec, loads the SPEC.md, finds the `← current` task, reads the Resume Context section, and continues from exactly where you left off.

**Pause** — The tool captures current state into the Resume Context section: which files were modified (specific paths, function names), what was completed, the exact next step. Updates checkboxes, sets status to `paused`.

**Switch** — The tool pauses the current spec (full pause), loads the target spec, sets it to `active` in the registry, and resumes it.

**List** — The tool reads `.specs/registry.md` and shows specs grouped by status (active, paused, completed).

**Complete** — The tool verifies all tasks are checked, sets status to `completed` in both the SPEC.md frontmatter and the registry.

#### Tool-specific invocation examples

**Codex** (task-based prompts):
```
"create a spec for user authentication"
"resume the auth spec"
"pause and save context"
"switch to the api-refactor spec"
"show my specs"
"mark the spec as done"
```

**Cursor / Windsurf / Cline** (chat-based):
```
"plan out a caching layer"
"what was I working on?"
"save my progress and pause"
"switch to the auth spec"
"list all specs"
"complete the current spec"
```

**Gemini CLI**:
```bash
gemini "create a spec for rate limiting"
gemini "resume"
gemini "pause and save context"
gemini "switch to auth-system"
```

## Multi-Tool Support

The spec format is pure markdown. Claude Code, Codex, Cursor, Windsurf, Cline, and Gemini CLI can all work on the same `.specs/` directory.

### Setting Up Other Tools

Most tools can be set up via npx (see [Path 2](#path-2-quick-setup-via-npx-any-tool) above):

```bash
npx skills add ngvoicu/specsmith -a <tool>
```

For manual setup, see the snippet format in [SKILL.md](SKILL.md).

### Cross-Tool Sync

All tools share the same files:
- **Task codes** — `[AUTH-03]` is the same task everywhere
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

## Project Structure

```
specsmith/
├── .claude-plugin/
│   ├── plugin.json                 # Plugin metadata (v0.2.0)
│   └── marketplace.json            # Marketplace registration
├── commands/
│   ├── forge.md                    # Research → interview → spec → implement
│   ├── resume.md                   # Resume active spec
│   ├── pause.md                    # Pause with context
│   ├── switch.md                   # Switch between specs
│   ├── list.md                     # List all specs
│   ├── status.md                   # Detailed progress
│   └── openapi.md                  # Generate OpenAPI spec from codebase
├── agents/
│   └── researcher.md               # Deep research subagent (Opus)
├── hooks/
│   └── hooks.json                  # SessionStart detection
├── references/
│   └── spec-format.md              # SPEC.md format specification
├── SKILL.md                        # Universal skill (works with all tools)
└── README.md
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
- **Task codes**: `[PREFIX-NN]` — unique per task, auto-incrementing across phases
- **Task checkboxes**: `- [ ] [AUTH-01]` unchecked, `- [x] [AUTH-01]` done
- **Current task**: `← current` after the task text
- **Uncertainty**: `[NEEDS CLARIFICATION]` after the task code on unclear tasks
- **Resume Context**: Blockquote with specific file paths, function names, exact next step
- **Decision Log**: Table with date, decision, rationale
- **Deviations**: Table tracking where implementation diverged from spec

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
