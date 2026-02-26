# 🤖 Claude Code — Learning Workflow

> A hands-on, visual guide to setting up and mastering Claude Code for your projects.

![8 steps](https://img.shields.io/badge/workflow-8%20steps-ff6b35?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-v1.x-7c6aff?style=flat-square)
![Open in Browser](https://img.shields.io/badge/open-index.html-00d4aa?style=flat-square)

---

## 🚀 Quick Start

```bash
git clone https://github.com/Stephenjhayes/claude-code-learning.git
cd claude-code-learning
open index.html   # or double-click it in Finder / Explorer
```

**That's it.** Open `index.html` in your browser and follow the interactive step-by-step workflow.

---

## 📁 What's in this repo

```
claude-code-learning/
│
├── index.html                         ← 🌟 Start here — visual interactive guide
├── CLAUDE.md                          ← Meta example: this repo uses what it teaches
│
├── examples/
│   ├── CLAUDE.md.template             ← Copy into your own project
│   ├── .mcp.json.example              ← MCP config (GitHub, Slack, Postgres, FS)
│   │
│   ├── .claude/
│   │   ├── settings.json.example      ← Permissions + hooks config
│   │   ├── commands/
│   │   │   ├── review-pr.md           ← /review-pr slash command
│   │   │   └── deploy-staging.md      ← /deploy-staging slash command
│   │   └── agents/
│   │       └── frontend-agent.md      ← Sub-agent definition example
│   │
│   └── hooks/
│       └── post-edit-format.sh        ← Auto-format hook (TS/Python/Go/JSON)
│
└── docs/                              ← Deep-dive markdown per feature (coming soon)
```

---

## 🗺️ The 8-Step Workflow

The guide walks you through 4 phases:

**Phase 1 — Installation & First Run**
1. Install Claude Code (Homebrew / WinGet / npm)
2. Start your first session — explore the TUI

**Phase 2 — Project Configuration**
3. Create your `CLAUDE.md` — project memory & standards
4. Configure permissions — allow/deny bash commands

**Phase 3 — Power Features**
5. Custom slash commands — package team workflows
6. Hooks — auto-format, safety checks on every action
7. MCP server connections — GitHub, Slack, Jira, databases

**Phase 4 — Multi-Agent & Automation**
8. Sub-agents + checkpoints — parallel work, safe rewinding

---

## 💡 How to use this as a team

1. **Clone the repo** and open `index.html` — everyone starts from the same visual guide
2. **Copy `examples/CLAUDE.md.template`** into your project root and fill it in
3. **Copy `.claude/commands/`** into your project and customize the workflows
4. **Adapt `settings.json.example`** permissions to your team's tools
5. Track progress — the interactive guide saves your state in localStorage

---

## 🔗 Official Resources

| Resource | URL |
|---|---|
| Claude Code Docs | https://code.claude.com |
| Claude Code GitHub | https://github.com/anthropics/claude-code |
| MCP Servers Registry | https://github.com/modelcontextprotocol/servers |
| Anthropic Console | https://console.anthropic.com |

---

*Built to learn Claude Code by doing. Fork it, adapt it, share it.*
