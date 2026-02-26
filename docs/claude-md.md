# CLAUDE.md — Deep Dive

> The single most impactful thing you can do to improve Claude Code's output quality.

## What it is

`CLAUDE.md` is a markdown file in your project root (or any parent directory) that Claude Code reads automatically at the start of every session. Think of it as a README written *for the AI*, not for humans.

Where a README explains what your project does to a new developer, `CLAUDE.md` explains *how to work on your project* — the rules, conventions, tools, and context that Claude needs to be a good teammate.

## Why it matters

Without `CLAUDE.md`, Claude Code starts every session cold. It has to infer your conventions from code patterns, ask clarifying questions, or make wrong assumptions.

With a good `CLAUDE.md`, Claude Code behaves like a senior engineer who already knows your stack — it uses the right tools, follows your naming conventions, runs your lint commands, and avoids your known footguns.

## File hierarchy

Claude Code reads `CLAUDE.md` files from multiple locations and merges them:

```
~/.claude/CLAUDE.md          ← Global: your personal preferences across all projects
/your/project/CLAUDE.md      ← Project: shared team conventions (commit this)
/your/project/src/CLAUDE.md  ← Subdirectory: context for a specific module
```

This lets you layer context — global preferences + project standards + module-specific rules.

## Anatomy of a great CLAUDE.md

### 1. Tech stack declaration

```markdown
## Tech Stack
- Frontend: React 18 + TypeScript 5
- Backend: Node.js 20 / Express 4
- Database: PostgreSQL 15 via Prisma ORM
- Testing: Vitest + Testing Library
- Deployment: Vercel (frontend), Fly.io (backend)
```

Why: Claude picks up on these and uses the right idioms. Say "TypeScript" and it won't write `var`. Say "Prisma" and it won't write raw SQL queries.

### 2. Coding standards

```markdown
## Coding Standards
- Functional React components only — no class components
- Prefer `const` arrow functions over `function` declarations
- All async functions must explicitly handle errors (try/catch or .catch())
- No `console.log` in production code — use the `logger` utility from `src/lib/logger.ts`
- File naming: kebab-case for files, PascalCase for component exports
- Import order: external packages → internal modules → relative paths
```

Why: These prevent the most common AI-generated anti-patterns for your codebase.

### 3. Common commands

```markdown
## Common Commands
- `npm run dev`         → Start dev server (port 3000)
- `npm run build`       → Production build
- `npm run test`        → Run full test suite
- `npm run test:watch`  → Watch mode
- `npm run lint`        → Check for errors (run after every TS edit)
- `npm run db:migrate`  → Run pending Prisma migrations
- `npm run db:studio`   → Open Prisma Studio (database GUI)
```

Why: Claude Code uses these automatically when appropriate, rather than guessing or running the wrong command.

### 4. Architecture decisions

```markdown
## Architecture Decisions
- State management: React Query for server state, Zustand for UI state
- Authentication: JWT stored in httpOnly cookies (NOT localStorage)
- API routes follow REST: GET/POST/PUT/DELETE — no custom verbs
- All API responses shape: `{ data: T | null, error: string | null }`
- Environment config: always use `src/lib/env.ts` — never access `process.env` directly
```

Why: These are decisions that aren't visible from the code itself but that Claude needs to respect when adding new features.

### 5. Notes for Claude Code specifically

```markdown
## Notes for Claude Code
- Always run `npm run lint` after editing TypeScript files
- Database migrations go in `src/db/migrations/` with timestamp prefix: `YYYYMMDD_description.sql`
- When adding new API routes, update `docs/openapi.yaml`
- Never commit `.env` — update `.env.example` instead
- The `src/lib/` directory is for pure utilities only — no React, no side effects
```

Why: This section is the "things I wish I didn't have to keep reminding Claude about." Put your footguns here.

## Advanced patterns

### Reference other files

```markdown
## Architecture
See `docs/architecture.md` for the full system design.
See `docs/api.md` for the API specification.
```

Claude Code will read those files when relevant.

### Scope rules to directories

```markdown
## Backend (src/api/)
- Never use ORM in route handlers — use the service layer
- All routes must validate input with Zod before processing

## Frontend (src/components/)
- All components must be accessible (ARIA labels, keyboard nav)
- Use CSS modules for styling — no inline styles
```

### Keep it honest

If `CLAUDE.md` says "always write tests" but your codebase has 30% test coverage, Claude will be confused when it looks at the actual code. Document what *should* be true, not what is ideally true — or be explicit: "We're working toward 80% coverage; write tests for all new code."

## What to avoid

- **Too long**: If `CLAUDE.md` is 500 lines, Claude spends more context on reading it. Keep the total under ~200 lines.
- **Redundant**: Don't copy your entire `eslint.config.js` in. Just say "follow ESLint rules — run `npm run lint`."
- **Stale**: An outdated `CLAUDE.md` is worse than none. Review it when your stack changes.

## Template

See `examples/CLAUDE.md.template` for a ready-to-use starting point.
