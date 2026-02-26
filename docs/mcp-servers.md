# MCP Servers — Deep Dive

> Connect Claude Code to the real world: your GitHub repos, Slack channels, databases, and more.

## What MCP is

The Model Context Protocol (MCP) is an open standard for connecting AI tools to external data sources and services. For Claude Code, it means you can give Claude the ability to read from and write to the systems your team actually uses.

Without MCP, Claude Code works within your local filesystem and terminal. With MCP, it can:

- Open pull requests on GitHub
- Post updates to a Slack channel
- Query your production database
- Read tickets from Jira or Linear
- Search your Google Drive docs

## How it works

Each MCP integration runs as a small local server process that Claude Code communicates with. You configure which servers to run in `.mcp.json`. When Claude needs to interact with, say, GitHub, it calls the GitHub MCP server — which handles the actual API call using your credentials.

```
Claude Code ←→ GitHub MCP Server ←→ GitHub API
Claude Code ←→ Slack MCP Server  ←→ Slack API
Claude Code ←→ Postgres MCP Server ←→ Your DB
```

## Configuration

### Project-level (`.mcp.json` in project root)

Committed to git — shared with the whole team. Use environment variable placeholders for secrets.

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

The `${GITHUB_TOKEN}` placeholder is filled from your actual environment variables at runtime — so the file is safe to commit.

### Via CLI

```bash
# Add a server interactively
claude mcp add github \
  --command "npx -y @modelcontextprotocol/server-github" \
  --env "GITHUB_PERSONAL_ACCESS_TOKEN=your_token"

# List configured servers
claude mcp list

# Check server status
claude mcp status github
```

### Verify inside a session

```
/mcp
→ Lists all connected MCP servers and their available tools
```

## Common servers

### GitHub

```json
{
  "github": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

**What it enables:**
- "Create a PR for my current branch with a summary of the changes"
- "Find all open issues labeled 'bug' and give me a list"
- "Comment on PR #142 with the review I just wrote"
- "What's the CI status of the latest commit on main?"

**Setup:** Generate a Personal Access Token at github.com/settings/tokens with `repo` scope.

### Slack

```json
{
  "slack": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-slack"],
    "env": {
      "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
      "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
    }
  }
}
```

**What it enables:**
- "Post a deploy notification to #releases with the version and key changes"
- "Check #incidents for anything from the last hour"
- "DM @Sarah that the feature she requested is ready for review"

**Setup:** Create a Slack app at api.slack.com/apps with `chat:write` and `channels:read` scopes.

### PostgreSQL

```json
{
  "postgres": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "env": {
      "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
    }
  }
}
```

**What it enables:**
- "How many users signed up last week vs the week before?"
- "What are the top 10 most-used features by active users?"
- "Check if there are any orphaned rows in the sessions table"
- "Write and explain the migration for adding a `last_login` column to users"

**⚠️ Safety tip:** Connect to a read-only replica or a staging database, not production. The MCP server has real query access.

### Filesystem

```json
{
  "filesystem": {
    "type": "stdio",
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "/path/to/documents"
    ]
  }
}
```

**What it enables:** Read files outside the current project directory — useful for referencing shared design docs, specs, or a second repo.

## Scoping credentials

Never put actual tokens in `.mcp.json`. Use env var placeholders:

```bash
# In your shell profile (~/.zshrc or ~/.bashrc)
export GITHUB_TOKEN="ghp_your_token_here"
export SLACK_BOT_TOKEN="xoxb-your-token-here"
export DATABASE_URL="postgresql://user:pass@localhost/mydb"
```

The `${VAR_NAME}` syntax in `.mcp.json` reads from these at startup.

## Discovering available tools

Once an MCP server is running, ask Claude what it can do:

```
"What GitHub tools do you have available?"
→ Claude lists: create_pull_request, get_issue, list_issues, create_issue, get_file_contents, push_files, fork_repository...
```

## Full config example

See `examples/.mcp.json.example` for a complete config covering GitHub, Slack, filesystem, and PostgreSQL.

## Finding more servers

The MCP ecosystem is growing rapidly. Find community-built servers at:
- https://github.com/modelcontextprotocol/servers (official)
- https://github.com/punkpeye/awesome-mcp-servers (community list)
