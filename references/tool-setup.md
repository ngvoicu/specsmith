# Tool Setup Guide

Spec Smith works with any AI coding tool that can read and write files. But
each tool needs to be told about the `.specs/` directory through its own
instruction mechanism.

Below are copy-paste snippets for each tool. Add the relevant one to your
project and the tool will know how to work with specs.

## Claude Code

Claude Code has native skill support. Just install the skill:

```bash
# From GitHub (via npx skills add)
npx skills add <owner>/spec-smith --skill spec-smith -a claude-code

# Or manually: copy the spec-smith/ directory to
# .claude/skills/spec-smith/    (project-level)
# ~/.claude/skills/spec-smith/  (global)
```

No additional config needed — Claude Code reads SKILL.md automatically.

## OpenAI Codex

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a codex
```

Or manually — Codex uses `AGENTS.md` (or `codex.md`) for instructions. Add this block:

```markdown
## Spec Management (Spec Smith)

This project uses structured specs for task tracking in `.specs/`.

### On session start
1. Check if `.specs/active` exists and contains a spec ID
2. If yes, read `.specs/specs/<id>/SPEC.md`
3. Find the current phase (`[in-progress]`) and current task (`← current`)
4. Read the "Resume Context" section for where you left off
5. Begin working on the current task

### While working
- Check off tasks as you complete them: `- [ ]` → `- [x]`
- Move the `← current` marker to the next task
- When a phase is done: change `[in-progress]` → `[completed]`, next phase
  `[pending]` → `[in-progress]`

### Before finishing
- Update the "Resume Context" section with:
  - What you just completed
  - What files you modified (specific paths, function names)
  - The exact next step someone should take
  - Any blockers or open questions
- Update the `updated` date in the YAML frontmatter
- Update `.specs/registry.md` if status changed

### Creating a new spec
When asked to plan or spec out work, create a SPEC.md in
`.specs/specs/<id>/SPEC.md` with this structure:

- YAML frontmatter: id, title, status, created, updated, priority, tags
- Overview section (2-4 sentences on what and why)
- Phases with `[pending]`/`[in-progress]`/`[completed]` markers
- Tasks as markdown checkboxes within each phase
- Resume Context section (blockquote)
- Decision Log table

See `.specs/specs/` for examples of existing specs.
```

### Why this works for Codex

Codex doesn't have plan mode. It receives a task and executes. The spec
replaces plan mode by giving Codex structured context about:

- What the overall goal is (Overview)
- What's already been done (checked tasks)
- What to do right now (← current marker)
- What happened last time (Resume Context)

This means you can give Codex a simple prompt like "resume the auth spec"
and it has everything it needs to pick up where the last session left off,
even though it has no memory of previous sessions.

## Cursor

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a cursor
```

Or manually — Cursor uses `.cursor/rules` (or `.cursorrules`) for project instructions.
Add this block:

```markdown
## Spec Management (Spec Smith)

This project tracks work in `.specs/`. When starting a task:

1. Check `.specs/active` for the current spec ID
2. Read `.specs/specs/<id>/SPEC.md` to understand context and progress
3. Find the task marked `← current` — that's what to work on
4. Read the "Resume Context" section for detailed state from last session

While working:
- Check off completed tasks: `- [ ]` → `- [x]`
- Move `← current` to the next unchecked task
- When a phase completes, mark it `[completed]` and start the next

Before finishing:
- Update "Resume Context" with specific files, functions, and next steps
- Update the `updated` date in frontmatter
- Be specific: "implementing verifyToken() in src/auth/tokens.ts" not
  "working on auth"
```

## Windsurf

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a windsurf
```

Or manually — Windsurf uses `.windsurfrules` for project instructions. Add the same
content as the Cursor section above.

## Cline

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a cline
```

Or manually — Cline uses `.clinerules` for project instructions. Add the same content
as the Cursor section above.

## Aider

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a aider
```

Or manually — Aider uses `.aider.conf.yml` or reads from conventions files. Create a
`.aider/conventions.md` with the Cursor snippet above.

## Gemini CLI

Quick setup:
```bash
npx skills add ngvoicu/specsmith-forge -a gemini
```

Or manually — Gemini CLI uses `GEMINI.md` for project instructions. Add the same
content as the Cursor section above.

## Any Other Tool

If your tool has a project-level instruction file (most do), add the
snippet from the Cursor section. The core pattern is the same everywhere:

1. Read `.specs/active` to find current spec
2. Read the SPEC.md for context
3. Work on the `← current` task
4. Update checkboxes and resume context when done

The format is pure markdown — any tool that can read and write files can
participate in the spec workflow.

## Multi-Tool Projects

If you use multiple tools on the same project (e.g., Claude Code for
complex features, Codex for batch tasks, Cursor for quick edits), they
all share the same `.specs/` directory. The resume context and task
checkboxes keep them in sync.

This works because:
- The spec format is tool-agnostic markdown
- State is in files, not in any tool's memory
- The `← current` marker and resume context tell any tool where to start
- Checked/unchecked tasks show what's done regardless of which tool did it

The only thing to be careful about: don't run two tools on the same spec
simultaneously. One at a time per spec. (Different specs in parallel is
fine.)
