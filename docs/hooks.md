# Hooks — Deep Dive

> Automate the tedious stuff: format every file Claude edits, run safety checks before bash commands, log everything Claude does.

## What hooks are

Hooks are shell commands that Claude Code runs automatically at specific points in its workflow — before or after it uses a tool. They run in your terminal environment with full access to your project.

Think of them as git hooks, but for Claude's actions instead of git operations.

## The hook lifecycle

Every time Claude uses a tool (like editing a file or running bash), the lifecycle is:

```
1. PreToolUse hook  →  runs BEFORE Claude uses the tool
       ↓
2. Claude uses the tool (edit file, run bash, etc.)
       ↓
3. PostToolUse hook  →  runs AFTER Claude uses the tool
```

You can hook into either point, with any shell command.

## Hook triggers (matchers)

| Matcher | Fires when Claude... |
|---|---|
| `Write` | Creates a new file |
| `Edit` | Edits an existing file |
| `MultiEdit` | Makes multiple edits to a file |
| `Bash` | Runs a bash command |
| `Read` | Reads a file |

You can combine with pipes: `"Write\|Edit\|MultiEdit"` matches any file write operation.

## Configuration

Hooks live in `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write $CLAUDE_FILE_PATH"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/safety-check.sh"
          }
        ]
      }
    ]
  }
}
```

## Environment variables

Hooks receive context from Claude Code via environment variables:

| Variable | Value |
|---|---|
| `$CLAUDE_FILE_PATH` | Path of the file being edited/written |
| `$CLAUDE_TOOL_NAME` | Name of the tool being used (`Write`, `Bash`, etc.) |
| `$CLAUDE_BASH_COMMAND` | The bash command Claude is about to run (PreToolUse only) |

## Real hook examples

### Auto-format every file Claude edits

```bash
#!/bin/bash
# PostToolUse on Write|Edit|MultiEdit
FILE="$CLAUDE_FILE_PATH"

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx) prettier --write "$FILE" ;;
  *.py) black "$FILE" --quiet ;;
  *.go) gofmt -w "$FILE" ;;
  *.json) jq . "$FILE" > /tmp/fmt && mv /tmp/fmt "$FILE" ;;
esac
```

Result: every file Claude touches comes out formatted. No more "Claude wrote valid code but with wrong spacing" issues.

### Log all bash commands Claude runs

```bash
#!/bin/bash
# PreToolUse on Bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] CLAUDE BASH: $CLAUDE_BASH_COMMAND" \
  >> ~/.claude/audit.log
```

Result: a full audit trail of every command Claude ran. Useful for debugging and team accountability.

### Block destructive commands

```bash
#!/bin/bash
# PreToolUse on Bash
CMD="$CLAUDE_BASH_COMMAND"

# Block patterns
if echo "$CMD" | grep -qE "rm -rf|DROP TABLE|DELETE FROM .* WHERE 1=1"; then
  echo "⛔ Hook blocked: destructive command pattern detected"
  echo "Command: $CMD"
  exit 1  # Non-zero exit cancels the tool use
fi

exit 0
```

Result: Claude cannot accidentally run catastrophic commands even if confused about context.

### Auto-run tests after editing test files

```bash
#!/bin/bash
# PostToolUse on Write|Edit
FILE="$CLAUDE_FILE_PATH"

# Only for test files
if echo "$FILE" | grep -qE "\.(test|spec)\.(ts|tsx|js)$"; then
  echo "🧪 Running tests for: $FILE"
  npx vitest run "$FILE" --reporter=verbose
fi
```

Result: Claude gets immediate feedback when it edits a test — it sees failures inline and can fix them.

## Hook exit codes

- **Exit 0**: Success — Claude continues normally
- **Exit 1+ (PreToolUse)**: Claude is told the hook failed and cancels the tool use
- **Exit 1+ (PostToolUse)**: Claude sees the error output but the tool use already happened

This makes `PreToolUse` hooks great for safety gates and `PostToolUse` hooks great for side effects.

## Tips

- **Keep hooks fast.** They run on every Claude action. A 5-second formatter that runs on every file edit adds up fast.
- **Fail loudly.** Use `echo` to output what the hook is doing — Claude sees this output and can react to it.
- **Test hooks manually first.** Run your hook script from the terminal before wiring it into Claude Code. Debug in isolation.
- **Scope matchers tightly.** Don't run an expensive operation on `Read` when you only need it on `Write`.

## Full example

See `examples/hooks/post-edit-format.sh` and `examples/.claude/settings.json.example` for a working setup.
