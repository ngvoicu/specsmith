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
  trigger when the user starts a new Claude Code session in a project that
  has a `.specs/` directory — check for an active spec and offer to resume.
---

# Spec Smith

Turn ephemeral plans into structured, persistent specs built through deep
research and iterative interviews. Specs have phases, tasks, resume context,
and a decision log. They live in `.specs/` at the project root and work
with any AI coding tool that can read markdown.

## Plugin Commands

Spec Smith is a Claude Code plugin. These commands are the primary interface:

| Command | What it does |
|---------|-------------|
| `/spec-smith:forge <description>` | **The main workflow.** Deep research → interview → more research → more interview → write spec → implement. This replaces plan mode. |
| `/spec-smith:resume` | Resume the active spec from where you left off |
| `/spec-smith:pause` | Pause the active spec with detailed resume context |
| `/spec-smith:switch <id>` | Switch to a different spec (pauses current) |
| `/spec-smith:list` | List all specs with status and progress |
| `/spec-smith:status` | Detailed progress of the active spec |
| `/spec-smith:openapi` | Scan the project and generate/update `.openapi/openapi.yaml` + per-endpoint docs in `.openapi/endpoints/` |

The `/forge` command is the key innovation — it's what plan mode should be.
Instead of a quick scan and a plan, it does exhaustive research, interviews
the user in multiple rounds, stores everything, then writes a spec where
every task is concrete and unambiguous.

## Plan Mode Handling

The `/forge` workflow bypasses Claude Code's built-in plan mode — it IS the
planning phase. However, users might invoke forge while already in plan mode.

**If you detect you're in plan mode (read-only, can't write files):**

1. Tell the user: "You're in plan mode. Research and interviews work fine
   here since they're read-only. When we're ready to write the spec and
   implement, I'll need you to exit plan mode (Shift+Tab)."
2. Proceed with research and interviews normally (Phases 1-4)
3. When reaching Phase 5 (write spec), remind the user: "We're ready to
   write the spec. Please exit plan mode (Shift+Tab) so I can create the
   spec files."
4. Wait for the user to confirm they've exited plan mode before writing

This means forge works in ANY permission mode — it adapts. The research
and interview phases are naturally read-only. Only spec writing and
implementation need write access.

## How Forge Works (The Enhanced Plan Mode)

The forge workflow replaces Claude Code's plan mode with something far more
thorough. See `commands/forge.md` for the full workflow, but the key phases:

1. **Deep Research** — Exhaustive codebase scan, web search, Context7 docs,
   UI inspection. Reads 10-20+ files, maps architecture, finds patterns.
   All findings saved to `.specs/research/<id>/research-01.md`

2. **Interview Round 1** — Present findings, state assumptions, ask targeted
   questions informed by the research. Save to `interview-01.md`

3. **Deeper Research** — Investigate the specific directions from the
   interview. Save to `research-02.md`

4. **Interview Round 2+** — Repeat research → interview until everything
   is clear. No ambiguous tasks. As many rounds as needed.

5. **Write Spec** — Synthesize all research and interviews into a SPEC.md
   with phases, tasks, decision log

6. **Implement** — Work through the spec task by task, tracking progress

All research and interviews are stored in `.specs/research/<id>/` so
nothing is ever lost across sessions.

## Session Lifecycle

### Session Start

When a session begins in a project that has `.specs/`:

1. Read `.specs/active` to check for an active spec
2. If one exists, briefly mention it:
   "You have an active spec: **User Auth System** (5/12 tasks, Phase 2).
   Say 'resume' or run `/spec-smith:resume` to pick up where you left off."
3. Don't force it — the user might want to do something else first

### After Plan Mode Ends

If the user used Claude Code's built-in plan mode (not forge), offer to
capture the plan as a spec:

1. **Offer to save**: "Want me to save this plan as a spec? That way you
   can resume it across sessions and track progress."
2. If yes, convert the plan into a SPEC.md:
   - Plan's high-level steps → phases
   - Substeps → tasks (checkboxes)
   - Decisions → Decision Log
   - Context/rationale → Overview
3. Set as active spec and begin implementing

### During Implementation

While working through a spec's tasks:

- Check off tasks proactively as you complete them
- When finishing a task, note what's next
- If a task is more complex than expected, split it into subtasks
- Update resume context at natural pauses

### Before Session Ends

If the session is ending:

1. Pause the active spec (run full pause workflow)
2. Write detailed resume context
3. Confirm to the user that context was saved

### Re-Forging

Sometimes a spec needs rework. The user might say "this approach isn't
working" or "let's rethink Phase 3."

1. Run `/spec-smith:forge` again with the new direction
2. Or update the SPEC.md directly with revised phases/tasks
3. Add a Decision Log entry explaining why the plan changed
4. Don't delete completed work — mark changed tasks clearly

## When to Use This

- User exits plan mode → offer to save as spec
- User returns after a break → `spec resume`
- User juggles multiple features → `spec list`, `spec activate`
- User wants progress tracking → `spec status`
- User says "what was I working on" → `spec resume`
- Session starts in a project with `.specs/` → mention active spec
- Plan isn't working → re-plan and update the spec

## Directory Layout

All state lives in `.specs/` at the project root:

```
.specs/
├── active                    # Plain text file containing active spec ID
├── registry.md               # Table of all specs with status
└── specs/
    └── <spec-id>/
        └── SPEC.md           # The spec document
```

## Commands

| Trigger | What it does |
|---------|-------------|
| `spec new <title>` / "create a spec for X" / "save this plan as a spec" | Create a new spec |
| `spec list` / "show my specs" / "what specs do I have" | List all specs |
| `spec resume` / "resume" / "what was I working on" | Resume active spec |
| `spec status` / "how far along am I" | Show progress of active spec |
| `spec activate <id>` / "switch to spec X" | Switch to a different spec |
| `spec pause` / "pause this" / "park this for now" | Pause and save context |
| `spec complete` / "mark spec as done" | Complete active spec |
| `spec archive <id>` | Archive a finished or abandoned spec |
| `spec update` / "check off task X" | Update progress in active spec |

## Workflows

### Creating a Spec

**From plan mode output (most common path):**

1. Take the approved plan from the conversation
2. Generate a spec ID from the title (lowercase, hyphenated):
   `"User Auth System"` → `user-auth-system`
3. Initialize `.specs/` if it doesn't exist:
   ```bash
   mkdir -p .specs/specs
   ```
4. Create `.specs/specs/<id>/SPEC.md` using the template from
   `references/spec-format.md`
5. Map the plan structure to spec format:
   - Plan's major steps → Phases
   - Plan's substeps → Tasks (checkboxes)
   - Plan's file/architecture notes → Overview
   - Plan's trade-off decisions → Decision Log
6. Update `.specs/registry.md` (create if missing)
7. Write the ID to `.specs/active`
8. Present the spec to the user for review before implementing

**From conversation (no plan mode):**

1. Extract the goal, phases, and tasks from discussion
2. Same steps as above

**From scratch (vague idea):**

Ask clarifying questions to establish scope, then structure into phases. Be
opinionated about phasing — suggest a reasonable breakdown and let the user
adjust rather than asking them to define every phase.

**Phase/task guidelines:**

- Phases are major milestones (3-6 phases is typical)
- Tasks are concrete, actionable items (checkbox format)
- Each task should be completable in roughly one focused session
- Mark Phase 1 as `[in-progress]`, the rest as `[pending]`
- Mark the first unchecked task with `← current`
- Preserve the plan's original structure but add granularity where needed

### Resuming a Spec

When the user says "resume", "what was I working on", or `spec resume`:

1. Read `.specs/active` — if empty, show `spec list` and ask which to resume
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

### Pausing a Spec

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

This should feel seamless — one command to context-switch.

### Updating Progress

As the user works through tasks:

1. Check off completed tasks: `- [ ]` → `- [x]`
2. Move `← current` to the next task
3. When all tasks in a phase are done:
   - Phase status: `[in-progress]` → `[completed]`
   - Next phase: `[pending]` → `[in-progress]`
4. Update Resume Context with latest state
5. Update `updated` date in frontmatter

Don't wait for the user to explicitly say "check off task X" — when you
finish implementing something that matches a task, check it off proactively.

### Listing Specs

Read `.specs/registry.md` and present specs grouped by status:

```
Active:
  → user-auth-system: User Auth System (5/12 tasks, Phase 2)

Paused:
  ⏸ api-refactor: API Refactoring (2/8 tasks, Phase 1)
  ⏸ dark-mode: Dark Mode Support (0/6 tasks, not started)

Completed:
  ✓ ci-pipeline: CI Pipeline Setup (8/8 tasks)
```

### Completing a Spec

1. Verify all tasks are checked (warn if not, but allow override)
2. Set status to `completed` in frontmatter
3. Update registry
4. Clear `.specs/active` if this was active
5. Suggest next spec to activate if any are paused

### Archiving

Set status to `archived`. Files stay in place — can be reactivated anytime
with `spec activate`.

## Registry Format

`.specs/registry.md` is a simple markdown table:

```markdown
# Spec Registry

| ID | Title | Status | Priority | Updated |
|----|-------|--------|----------|---------|
| user-auth-system | User Auth System | active | high | 2026-02-10 |
| api-refactor | API Refactoring | paused | medium | 2026-02-09 |
| ci-pipeline | CI Pipeline Setup | completed | high | 2026-02-05 |
```

Always keep this in sync when creating, pausing, completing, or archiving.

## Tools Without Plan Mode (Codex, Cursor, Windsurf, etc.)

Most AI coding tools don't have a plan mode. In those tools, the spec
replaces plan mode entirely — it's both the plan and the tracker.

**The workflow becomes:**

1. User describes what they want to build (in chat or a prompt)
2. Tool creates a SPEC.md with phases and tasks (the "planning" step)
3. User reviews the spec
4. Tool implements task by task, checking them off
5. When the session ends, resume context is saved to the spec
6. Next session: tool reads the spec and picks up where it left off

**To make other tools aware of `.specs/`**, add a snippet to their
instruction file (AGENTS.md for Codex, .cursorrules for Cursor, etc.).
Read `references/tool-setup.md` for copy-paste snippets for each tool.

**Multi-tool projects work naturally.** If you use Claude Code for complex
features and Codex for batch work, they share the same `.specs/` directory.
The markdown format and `← current` marker keep everything in sync.

## Cross-Tool Compatibility

The spec format is pure markdown with YAML frontmatter. This means:

- **Claude Code**: Native skill support, reads SKILL.md automatically
- **Codex**: Add snippet to AGENTS.md (see `references/tool-setup.md`)
- **Cursor / Windsurf / Cline**: Add snippet to rules file
- **Humans**: Readable, editable in any text editor
- **Git**: Diffs cleanly, easy to track in version control

Any tool that can read and write files can use these specs. The format is
deliberately tool-agnostic — no proprietary metadata, no binary formats,
no database. Just markdown files in a directory.

## Spec Format

Read `references/spec-format.md` for the full SPEC.md template with all
fields and sections. Use it as a starting point for every new spec.

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
