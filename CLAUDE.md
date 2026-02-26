# Claude Code Learning Project

## About This Repository
This is a hands-on educational guide for learning Claude Code features. The repo itself demonstrates best practices for CLAUDE.md configuration.

## Project Architecture
- `index.html` - Interactive visual step-by-step guide (open in browser)
- `docs/` - Deep-dive documentation for each feature
- `examples/` - Copy-paste ready example files for every feature
- `CLAUDE.md` - This file! Your project context for Claude Code

## Coding Standards
- All example code should be runnable and tested
- Markdown files use ATX-style headers (`#` not underline style)
- Shell scripts must include comments explaining each step
- Keep examples minimal but complete — no half-finished code

## Architecture Decisions
- No build system required — this is a learning repo, not a framework
- Examples use vanilla JS and bash to stay accessible
- MCP examples target the most common integrations (GitHub, Slack)

## Review Checklist Before Committing
- [ ] Examples are tested and working
- [ ] New features have a matching entry in `docs/`
- [ ] `index.html` updated if adding a new step/module
- [ ] README badges and links are accurate

## Preferred Libraries & Tools
- Shell: bash (not zsh-specific syntax)
- JSON formatting: `jq`
- HTTP testing: `curl`

## Notes for Claude Code
When helping contributors, always suggest running examples from the repo root. Prefer editing existing examples over creating new files unless a genuinely new concept is being introduced.
