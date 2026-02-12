---
name: spec-smith
description: >
  Structured spec management for AI coding workflows. Converts ephemeral
  plans into persistent, resumable specs with phases, tasks, and progress
  tracking that survive across sessions. Use this skill whenever the user:
  exits plan mode (automatically offer to save the plan as a spec), says
  "resume" or "what was I working on", wants to switch between projects,
  mentions specs/phases/tasks, says "spec new/list/resume/status/pause/activate",
  says "generate openapi", "update api spec", "create api docs", "openapi",
  or any workflow involving structured planning that should persist. Also
  trigger when the user starts a new session in a project that has a `.specs/`
  directory — check for an active spec and offer to resume.
---

# Spec Smith

Turn ephemeral plans into structured, persistent specs built through deep
research and iterative interviews. Specs have phases, tasks, resume context,
and a decision log. They live in `.specs/` at the project root and work
with any AI coding tool that can read markdown.

## Claude Code Plugin

If you're running as a Claude Code plugin, use these commands for the full
experience:

| Command | What it does |
|---------|-------------|
| `/spec-smith:forge <description>` | **The main workflow.** Deep research -> interview -> more research -> more interview -> write spec -> implement. This replaces plan mode. |
| `/spec-smith:resume` | Resume the active spec from where you left off |
| `/spec-smith:pause` | Pause the active spec with detailed resume context |
| `/spec-smith:switch <id>` | Switch to a different spec (pauses current) |
| `/spec-smith:list` | List all specs with status and progress |
| `/spec-smith:status` | Detailed progress of the active spec |
| `/spec-smith:openapi` | Scan the project and generate/update `.openapi/openapi.yaml` + per-endpoint docs in `.openapi/endpoints/` |

The `/forge` command is the key innovation — it's what plan mode should be.
Instead of a quick scan and a plan, it does exhaustive research, interviews
the user in multiple rounds, stores everything, then writes a spec where
every task is concrete and unambiguous. See `commands/forge.md` for the
full workflow.

**Plan mode handling:** The forge workflow bypasses built-in plan mode — it
IS the planning phase. If you're in plan mode (read-only), research and
interviews still work. When it's time to write the spec, ask the user to
exit plan mode so files can be created.

## Session Start

When a session begins in a project that has `.specs/`:

1. Read `.specs/active` to check for an active spec
2. If one exists, briefly mention it:
   "You have an active spec: **User Auth System** (5/12 tasks, Phase 2).
   Say 'resume' to pick up where you left off."
3. Don't force it — the user might want to do something else first

## Working on a Spec

### Resuming

When the user says "resume", "what was I working on", or similar:

1. Read `.specs/active` — if empty, list specs and ask which to resume
2. Load `.specs/specs/<id>/SPEC.md`
3. Parse progress:
   - Count completed `[x]` vs total tasks per phase
   - Find current phase (first `[in-progress]` phase)
   - Find current task (`← current` marker, or first unchecked in current phase)
4. Read the **Resume Context** section
5. Present a compact summary:

   ```
   Resuming: User Auth System
   Progress: 5/12 tasks (Phase 2: OAuth Integration)
   Current: Implement Google OAuth callback handler
   Context: Token exchange is working. Need to handle the callback
   URL parsing and store refresh tokens in the user model.
   Next file: src/auth/oauth/google.ts
   ```

6. Begin working on the current task — don't wait for permission

### Implementing

While working through a spec's tasks:

- Check off tasks proactively as you complete them: `- [ ]` -> `- [x]`
- Move the `← current` marker to the next task
- When all tasks in a phase are done:
  - Phase status: `[in-progress]` -> `[completed]`
  - Next phase: `[pending]` -> `[in-progress]`
- If a task is more complex than expected, split it into subtasks
- Update resume context at natural pauses
- Log non-obvious technical decisions to the Decision Log

### Pausing

When the user says "pause", switches specs, or a session is ending:

1. Capture what was happening:
   - Which task was in progress
   - What files were being modified (paths, function names)
   - Key decisions made this session
   - Any blockers or open questions
2. Write this to the **Resume Context** section in SPEC.md
3. Update checkboxes to reflect actual progress
4. Move `← current` marker to the right task
5. Add any session decisions to the **Decision Log**
6. Update `status: paused` in frontmatter
7. Update the `updated` date

**Resume Context is the most important part of pausing.** Write it as if
briefing a colleague who will pick up tomorrow. Include specific file paths,
function names, and the exact next step. Vague context like "was working on
auth" is useless — write "implementing `verifyRefreshToken()` in
`src/auth/tokens.ts`, the JWT verification works but refresh rotation isn't
hooked up to the `/auth/refresh` endpoint yet."

### Switching Between Specs

1. Pause the current spec (full pause workflow)
2. Load the target spec
3. Write target ID to `.specs/active`
4. Set target status to `active` in its frontmatter
5. Resume the target spec (full resume workflow)

## Spec Format

### Frontmatter

YAML frontmatter with: `id`, `title`, `status`, `created`, `updated`,
optional `priority` and `tags`.

Status values: `active`, `paused`, `completed`, `archived`

### Phase Markers

`[pending]`, `[in-progress]`, `[completed]`, `[blocked]`

### Task Markers

- `- [ ]` unchecked, `- [x]` done
- `← current` after the task text marks the active task
- `[NEEDS CLARIFICATION]` prefix on unclear tasks

### Resume Context

Blockquote section with specific file paths, function names, and exact
next step. This is what makes cross-session continuity work.

### Decision Log

Markdown table with date, decision, and rationale columns. Log non-obvious
technical choices (library selection, architecture pattern, API design).

See `references/spec-format.md` for the full SPEC.md template.

## Creating Specs

When asked to plan or spec out work:

1. Generate a spec ID from the title (lowercase, hyphenated):
   `"User Auth System"` -> `user-auth-system`
2. Initialize `.specs/` if it doesn't exist:
   ```bash
   mkdir -p .specs/specs
   ```
3. Create `.specs/specs/<id>/SPEC.md` with:
   - YAML frontmatter (id, title, status, created, updated, priority, tags)
   - Overview section (2-4 sentences on what and why)
   - Phases with status markers (3-6 phases is typical)
   - Tasks as markdown checkboxes within each phase
   - Resume Context section (blockquote)
   - Decision Log table
4. Update `.specs/registry.md` (create if missing)
5. Write the ID to `.specs/active`

**Phase/task guidelines:**
- Each task should be completable in roughly one focused session
- Mark Phase 1 as `[in-progress]`, the rest as `[pending]`
- Mark the first unchecked task with `← current`

## Before Session Ends

If the session is ending:

1. Pause the active spec (run full pause workflow)
2. Write detailed resume context
3. Confirm to the user that context was saved

## Directory Layout

All state lives in `.specs/` at the project root:

```
.specs/
├── active                    # Plain text file containing active spec ID
├── registry.md               # Table of all specs with status
├── research/
│   └── <spec-id>/
│       ├── research-01.md    # Deep research findings
│       ├── interview-01.md   # Interview rounds
│       └── ...
└── specs/
    └── <spec-id>/
        └── SPEC.md           # The spec document
```

## Registry Format

`.specs/registry.md` is a simple markdown table:

```markdown
# Spec Registry

| ID | Title | Status | Priority | Updated |
|----|-------|--------|----------|---------|
| user-auth-system | User Auth System | active | high | 2026-02-10 |
| api-refactor | API Refactoring | paused | medium | 2026-02-09 |
```

Always keep this in sync when creating, pausing, completing, or archiving.

## Listing Specs

Read `.specs/registry.md` and present specs grouped by status:

```
Active:
  -> user-auth-system: User Auth System (5/12 tasks, Phase 2)

Paused:
  || api-refactor: API Refactoring (2/8 tasks, Phase 1)

Completed:
  ok ci-pipeline: CI Pipeline Setup (8/8 tasks)
```

## Completing a Spec

1. Verify all tasks are checked (warn if not, but allow override)
2. Set status to `completed` in frontmatter
3. Update registry
4. Clear `.specs/active` if this was active
5. Suggest next spec to activate if any are paused

## Cross-Tool Compatibility

The spec format is pure markdown with YAML frontmatter. Any tool that can
read and write files can use these specs:

- **Claude Code**: Full plugin support or skill via `npx skills add`
- **Codex**: Snippet in AGENTS.md or skill via `npx skills add`
- **Cursor / Windsurf / Cline**: Snippet in rules file
- **Gemini CLI**: Snippet in GEMINI.md
- **Humans**: Readable and editable in any text editor
- **Git**: Diffs cleanly, easy to track in version control

To configure another tool, run `npx skills add ngvoicu/specsmith-forge -a <tool>`.

## Behavioral Notes

**Be proactive about spec management.** If you notice the user has been
working for a while and made progress, update the spec without being asked.
If a session is ending, offer to pause and save context.

**Specs should evolve.** It's fine to add tasks, reorder phases, or split a
phase into two as understanding deepens. Specs aren't contracts — they're
living documents that adapt as you learn more about the problem.

**The Decision Log matters.** When the user makes a non-obvious technical
choice (library selection, architecture pattern, API design), log it with
the rationale. Future-you resuming this spec will thank present-you.

**Don't over-structure.** A spec with 3 phases and 15 tasks is useful. A
spec with 12 phases and 80 tasks is a project plan, not a coding spec.
Keep it lean enough to parse and act on in one read.

**Respect the user's flow.** Don't interrupt deep coding work to update
the spec. Batch updates for natural pauses — task completion, phase
transitions, or session boundaries.
