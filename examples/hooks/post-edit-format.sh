#!/bin/bash
# =============================================================================
# Claude Code Hook: Post-Edit Auto-Formatter
# 
# This hook runs AFTER Claude edits a file, automatically formatting it.
# Place this in your Claude Code hooks config (settings.json).
#
# Trigger: PostToolUse (when Claude uses the Write/Edit file tool)
# =============================================================================

# The file that was just edited is passed via the CLAUDE_TOOL_INPUT env variable
# (Claude Code provides context about what just happened)

FILE_PATH="$1"

if [ -z "$FILE_PATH" ]; then
  echo "No file path provided to formatter hook"
  exit 0
fi

echo "🎨 Auto-formatting: $FILE_PATH"

# Determine formatter based on file extension
case "$FILE_PATH" in
  *.ts|*.tsx|*.js|*.jsx)
    # Format TypeScript/JavaScript with Prettier
    if command -v prettier &> /dev/null; then
      prettier --write "$FILE_PATH"
      echo "✅ Formatted with Prettier"
    fi
    ;;
  *.py)
    # Format Python with Black
    if command -v black &> /dev/null; then
      black "$FILE_PATH" --quiet
      echo "✅ Formatted with Black"
    fi
    ;;
  *.go)
    # Format Go with gofmt
    gofmt -w "$FILE_PATH"
    echo "✅ Formatted with gofmt"
    ;;
  *.json)
    # Pretty-print JSON with jq
    if command -v jq &> /dev/null; then
      tmp=$(mktemp)
      jq . "$FILE_PATH" > "$tmp" && mv "$tmp" "$FILE_PATH"
      echo "✅ Formatted JSON"
    fi
    ;;
  *)
    echo "ℹ️  No formatter configured for this file type"
    ;;
esac
