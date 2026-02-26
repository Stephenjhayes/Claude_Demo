# VS Code Extension — Deep Dive

> Bring Claude Code into your IDE with inline diffs, @-mentions, plan review, and conversation history — no terminal switching required.

## What it adds over the terminal

The VS Code extension isn't just a terminal wrapper. It adds a richer IDE-native experience:

| Feature | Terminal | VS Code Extension |
|---|---|---|
| Chat interface | ✓ | ✓ (sidebar panel) |
| Inline file diffs | ✗ | ✓ |
| @-mention files/symbols | limited | ✓ |
| Plan preview & commenting | ✗ | ✓ |
| Conversation history | session only | ✓ persistent |
| See changes before apply | ✗ | ✓ |

## Installation

### From the marketplace

1. Open VS Code
2. Open Extensions (`Cmd+Shift+X` / `Ctrl+Shift+X`)
3. Search for **"Claude Code"**
4. Click **Install**

### From the command line

```bash
code --install-extension anthropic.claude-code
```

### For Cursor

The same extension works in Cursor. Search "Claude Code" in Cursor's extension view, or:

```bash
cursor --install-extension anthropic.claude-code
```

## First launch

1. After installing, open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Type **"Claude Code"**
3. Select **"Claude Code: Open in New Tab"**
4. The Claude Code panel opens — log in if prompted

## The VS Code panel layout

```
┌─────────────────────────────────┐
│  Claude Code                [×] │  ← Tab header
├─────────────────────────────────┤
│                                 │
│  [Chat history]                 │  ← Scrollable conversation
│                                 │
│  ✎ Claude is editing            │  ← Live status indicator
│    src/components/Button.tsx    │
│                                 │
├─────────────────────────────────┤
│  [Plan preview]                 │  ← Expandable plan (when active)
│  1. Edit Button.tsx             │
│  2. Update Button.test.tsx      │
│  [Comment] [Approve]            │
├─────────────────────────────────┤
│  > Ask Claude anything...  [↵]  │  ← Input
└─────────────────────────────────┘
```

## Key features

### Inline diffs

When Claude edits a file, you see the diff directly in your editor — exactly like a code review:

- Green lines = additions
- Red lines = deletions
- Accept or reject individual hunks

This is the biggest UX improvement over the terminal. You can review every change before it lands.

### Plan preview and commenting

When Claude is about to make multiple changes, it shows a **plan** before executing:

```
Claude's Plan:
1. Add `isLoading` prop to Button component
2. Update Button.tsx to show spinner when isLoading=true
3. Add test for loading state in Button.test.tsx
4. Update Storybook story

[Comment on plan] [Approve & Run]
```

You can:
- **Comment** to adjust the plan before Claude runs it
- **Approve** to let Claude execute
- The plan auto-updates as Claude iterates — you can comment again mid-run

### @-mentions

Reference specific context in your prompts:

```
@Button.tsx  — attach a specific file
@src/         — attach a whole directory
#isLoading    — reference a TypeScript symbol
```

This is more precise than Claude Code searching on its own, especially for large codebases.

### Conversation history

Unlike the terminal (where closing the session clears history), the VS Code extension persists conversation history. You can:

- Scroll back through past sessions
- Resume a conversation from where you left off
- See what changes Claude made and why

## Keyboard shortcuts

| Action | Mac | Windows/Linux |
|---|---|---|
| Open Claude Code panel | `Cmd+Shift+C` | `Ctrl+Shift+C` |
| Accept all changes | `Cmd+Enter` | `Ctrl+Enter` |
| Reject all changes | `Cmd+Backspace` | `Ctrl+Backspace` |
| Accept single hunk | `Cmd+Y` | `Ctrl+Y` |

## Combining with the terminal

The VS Code extension and the terminal CLI share the same session context when used in the same project. You can:

- Start a task in the terminal
- Switch to VS Code to review diffs visually
- Continue the conversation in VS Code

They're two interfaces into the same Claude Code session.

## JetBrains (IntelliJ, PyCharm, WebStorm)

A separate plugin is available for JetBrains IDEs:

1. Open JetBrains Marketplace in your IDE
2. Search for **"Claude Code"**
3. Install and restart

Features are similar — interactive diff viewing and selection context sharing. The UI integrates into JetBrains' tool window system.

## Tips

- **Use plan preview for risky changes.** Before asking Claude to refactor a large module, ask it to "make a plan" first. Review the plan, comment adjustments, then approve. Much safer than a single "go do it."
- **@-mention your CLAUDE.md.** If Claude seems to be forgetting your conventions mid-session, `@CLAUDE.md` re-anchors it.
- **Keep the panel open alongside your editor.** Dock it to the right sidebar and treat it like a second monitor — your AI pair programming view.
