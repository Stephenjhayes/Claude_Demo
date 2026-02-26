# Custom Slash Commands — Deep Dive

> Package your team's repeatable workflows so anyone can run them with a single command.

## What they are

Slash commands are markdown files stored in `.claude/commands/`. Each file becomes a command you can invoke with `/filename` inside a Claude Code session. The markdown content becomes the prompt — with full access to your codebase and tools.

Think of them as saved prompts that run with Claude Code's full power: file reads, bash execution, git access, and your MCP integrations.

## File location

```
.claude/
└── commands/
    ├── review-pr.md        → /review-pr
    ├── deploy-staging.md   → /deploy-staging
    ├── write-tests.md      → /write-tests
    └── changelog.md        → /changelog
```

Files in your project's `.claude/commands/` are project-scoped (great for team sharing via git). Files in `~/.claude/commands/` are personal and available in every project.

## Anatomy of a good command

```markdown
# [Command Title]

[One sentence: what this command does and when to use it.]

## Context to gather first
[Tell Claude what to read/check before acting]

## Steps
[Ordered list of what Claude should do]

## Output Format
[Be explicit about how results should be presented]

## On failure
[What to do if something goes wrong]
```

## Real examples

### Code review

```markdown
# Review Pull Request

Review all changes in the current branch against main.

## Steps
1. Run `git diff main...HEAD --stat` to get a file overview
2. Run `git diff main...HEAD` to read all changes
3. Check each changed file for:
   - Logic errors or off-by-one bugs
   - Missing or inadequate error handling
   - Security issues (injection, exposed secrets, unsafe deserialization)
   - Missing tests for new behavior
   - Style violations (check with `npm run lint`)

## Output Format
**Summary**: 2-3 sentences on what this PR does
**Issues**:
- [CRITICAL] `src/auth.ts:42` — JWT secret read from process.env, not env utility
- [WARNING]  `src/api/users.ts:89` — missing error handling on DB call
- [SUGGEST]  `src/components/Form.tsx:15` — prop type could be more specific

**Verdict**: Approve ✓ / Request Changes ✗ / Discuss ?
```

### Automated changelog

```markdown
# Generate Changelog Entry

Create a CHANGELOG.md entry for all commits since the last tag.

## Steps
1. Run `git describe --tags --abbrev=0` to find the last release tag
2. Run `git log {tag}..HEAD --oneline` to get all commits since then
3. Group commits by type:
   - feat: → New Features
   - fix:  → Bug Fixes
   - docs: → Documentation
   - perf: → Performance
4. Write a changelog entry in Keep a Changelog format
5. Prepend the entry to CHANGELOG.md

## Output
Show me the generated entry before writing it to the file. Ask me to confirm the version number.
```

### Scaffold a new feature

```markdown
# New Feature Scaffold

Scaffold all the boilerplate files for a new feature, given a feature name.

## What to create
Given the feature name $ARGUMENTS, create:
- `src/api/routes/{feature}.ts` — Express route handler (empty, with TODO)
- `src/services/{feature}.service.ts` — Business logic layer (empty class)
- `src/types/{feature}.types.ts` — TypeScript types for request/response
- `tests/{feature}.test.ts` — Test file with describe block and empty `it` stubs

## After creating files
Run `npm run lint` to verify they pass, then list the files created with a brief note on what to fill in.
```

## Using arguments

Commands can reference `$ARGUMENTS` — whatever text comes after the command name:

```bash
/new-feature user-authentication
# → $ARGUMENTS = "user-authentication"
```

This turns one command into a flexible template.

## Combining with MCP

If you have MCP servers configured, commands can use them:

```markdown
# Create Jira Ticket

Create a Jira ticket for the bug described in $ARGUMENTS.

## Steps
1. Use the Jira MCP tool to create a ticket in the BUGS project
2. Title: the $ARGUMENTS summary
3. Description: ask Claude to expand the summary into a proper bug report with Steps to Reproduce, Expected vs Actual, and Environment fields
4. Set priority to Medium unless the word "critical" or "urgent" appears in $ARGUMENTS
```

## Tips

- **Be specific about output format.** Vague commands produce vague output. Tell Claude exactly what structure you want back.
- **Include verification steps.** Good commands run `lint`, `test`, or `build` and report results — not just make changes and hope.
- **Version control them.** Commit `.claude/commands/` to your repo. When you improve a command, everyone benefits.
- **Document in your README.** Add a "Available Commands" section so new team members discover them.

## Ready-made examples

- `examples/.claude/commands/review-pr.md`
- `examples/.claude/commands/deploy-staging.md`
