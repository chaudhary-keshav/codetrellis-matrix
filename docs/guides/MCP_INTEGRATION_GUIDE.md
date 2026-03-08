# CodeTrellis MCP Integration Guide

## Overview

CodeTrellis exposes project intelligence via the **Model Context Protocol (MCP)**, allowing any MCP-compatible AI tool — Claude Desktop, Gemini CLI, Cursor, Cline, Continue, and others — to query your project's architecture, types, APIs, best practices, and more in real time.

**Version**: 1.0.0  
**Transport**: stdio (default)  
**Protocol**: MCP v1.0 (JSON-RPC 2.0)

---

## Quick Start

### 1. Scan your project first

```bash
codetrellis scan /path/to/project --cache-optimize
```

This generates `.codetrellis/cache/<version>/<project>/matrix.prompt` — the knowledge base that MCP serves.

### 2. Start the MCP server

```bash
codetrellis mcp /path/to/project
```

The server starts on **stdio** (stdin/stdout JSON-RPC), ready for any MCP client.

---

## Client Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "codetrellis": {
      "command": "codetrellis",
      "args": ["mcp", "/path/to/your/project"],
      "env": {}
    }
  }
}
```

> **Note**: If `codetrellis` is installed in a virtualenv, use the full path:
> ```json
> "command": "/path/to/venv/bin/codetrellis"
> ```

Restart Claude Desktop after saving. You should see "codetrellis" listed under the MCP tools icon (🔧).

### Cursor

Add to your workspace `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "codetrellis": {
      "command": "codetrellis",
      "args": ["mcp", "."],
      "env": {}
    }
  }
}
```

Or globally in Cursor Settings → MCP → Add Server.

### Cline / Continue

Both support MCP via stdio. Add to their respective config files:

**Cline** (`~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`):
```json
{
  "mcpServers": {
    "codetrellis": {
      "command": "codetrellis",
      "args": ["mcp", "/path/to/project"],
      "disabled": false
    }
  }
}
```

**Continue** (`.continue/config.json`):
```json
{
  "mcpServers": [
    {
      "name": "codetrellis",
      "command": "codetrellis",
      "args": ["mcp", "."]
    }
  ]
}
```

### Gemini CLI

```bash
# In your Gemini CLI config or via command line
gemini --mcp-server "codetrellis mcp /path/to/project"
```

### Custom / Programmatic

```python
from codetrellis.mcp_server import MatrixMCPServer

server = MatrixMCPServer("/path/to/project")
server.load_matrix()

# Use programmatically
section = server.get_section("PYTHON_TYPES")
results = server.search_matrix("authentication")
context = server.get_context_for_file("src/auth/login.py")

# Or run as stdio server
server.run_stdio()
```

---

## Available Resources

Resources are read-only data endpoints that MCP clients can browse.

| URI | Name | Description |
| --- | --- | --- |
| `matrix://sections` | Section List | List all available matrix sections |
| `matrix://full` | Full Matrix | Complete matrix.prompt content |
| `matrix://section/{name}` | Section Detail | Content of a specific section (e.g., `matrix://section/PYTHON_TYPES`) |
| `matrix://overview` | Project Overview | Combined: PROJECT + OVERVIEW + PROJECT_PROFILE + BUSINESS_DOMAIN |
| `matrix://types` | All Types | Combined: all language type sections (Python, Go, Java, Rust, etc.) |
| `matrix://api` | All APIs | Combined: all API/route/endpoint sections |
| `matrix://runbook` | Runbook | Build, run, test, and deploy commands |
| `matrix://practices` | Best Practices | Project-specific coding standards and guidelines |

### Reading a Resource

MCP clients typically provide UI to browse resources. Programmatically:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "matrix://section/PYTHON_TYPES"
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "contents": [{
      "uri": "matrix://section/PYTHON_TYPES",
      "mimeType": "text/plain",
      "text": "[PYTHON_TYPES]\n# UserService (class)\n  methods: create_user, get_user, ..."
    }]
  }
}
```

---

## Available Tools

Tools are callable functions that MCP clients can invoke.

### `search_matrix`

Full-text search across all matrix sections.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `query` | string | ✅ | Search query (case-insensitive) |
| `max_results` | integer | ❌ | Maximum results (default: 10) |

**Example prompt**: *"Search the matrix for authentication logic"*

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_matrix",
    "arguments": { "query": "authentication", "max_results": 5 }
  }
}
```

### `get_section`

Retrieve a specific matrix section by name.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | ✅ | Section name (e.g., `PYTHON_TYPES`, `RUNBOOK`, `BEST_PRACTICES`) |

**Example prompt**: *"Show me the project's best practices"*

### `get_context_for_file`

Get JIT (Just-In-Time) context relevant to a specific file. Automatically selects the most relevant matrix sections based on file extension and content patterns.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `file_path` | string | ✅ | Path to the file (relative or absolute) |
| `max_tokens` | integer | ❌ | Token budget (default: 30000) |

**Example prompt**: *"What context do I need to work on src/api/routes.py?"*

### `get_skills`

List all auto-generated AI skills with their instructions and required context.

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `skill_name` | string | ❌ | Get details for a specific skill |

**Example prompt**: *"What skills are available for this project?"*

### `get_cache_stats`

Get cache optimization statistics for the current matrix.

No parameters required.

---

## Usage Examples

### With Claude Desktop

Once configured, you can ask Claude naturally:

- *"What types are defined in this project?"* → Claude reads `matrix://types`
- *"Search for how authentication is implemented"* → Claude calls `search_matrix`
- *"What context do I need to edit src/auth/login.py?"* → Claude calls `get_context_for_file`
- *"Show me the runbook for this project"* → Claude reads `matrix://runbook`
- *"What skills can you help me with?"* → Claude calls `get_skills`

### With Cursor

In Cursor's chat, the MCP tools appear as available actions. Cursor can:

1. **Auto-discover** project structure via `matrix://overview`
2. **Pull relevant context** when you open a file via `get_context_for_file`
3. **Search for patterns** across the codebase via `search_matrix`
4. **Apply best practices** by reading `matrix://practices`

### Workflow: Fix a Bug

1. Developer opens a file with a bug
2. AI tool calls `get_context_for_file("src/api/routes.py")` → gets relevant types, routes, error handling
3. AI tool calls `get_skills()` → finds `fix-issue` skill with instructions
4. AI applies the fix following project best practices from `matrix://practices`

### Workflow: Add a New Feature

1. AI tool reads `matrix://overview` for project understanding
2. AI tool calls `search_matrix("similar_feature")` to find patterns
3. AI tool calls `get_context_for_file` on related files
4. AI generates code following `matrix://practices` guidelines

---

## CLI Quick Reference

```bash
# Scan and optimize for caching
codetrellis scan /path/to/project --cache-optimize

# Start MCP server (stdio)
codetrellis mcp /path/to/project

# Start with explicit matrix path
codetrellis mcp /path/to/project --matrix-path /custom/matrix.prompt

# Standalone cache optimization
codetrellis cache-optimize /path/to/project --stats

# Get Anthropic API cache messages
codetrellis cache-optimize --anthropic-messages

# Get JIT context for a file
codetrellis context src/api/routes.py --json

# List available skills
codetrellis skills --json

# Get specific skill details
codetrellis skills --skill fix-issue

# Export skills in Claude Skills format
codetrellis skills --claude-format
```

---

## Troubleshooting

### "No matrix.prompt found"

Run `codetrellis scan /path/to/project` first to generate the matrix.

### MCP server not appearing in Claude Desktop

1. Check the config file path is correct for your OS
2. Ensure `codetrellis` is accessible from PATH (or use full path to executable)
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs for MCP connection errors

### Empty or missing sections

Some sections only appear if the project uses those technologies. For example:
- `PYTHON_TYPES` requires `.py` files with classes/types
- `REACT_COMPONENTS` requires React/JSX files
- `SQL_TABLES` requires `.sql` files or ORM definitions

### Token budget exceeded

Use `--max-tokens` with the `context` command or `max_tokens` parameter with `get_context_for_file` to control context size:

```bash
codetrellis context src/large_file.py --max-tokens 15000
```

### Performance

- The MCP server loads `matrix.prompt` once at startup
- Subsequent queries are in-memory (sub-millisecond)
- Re-scan with `codetrellis scan` when the codebase changes significantly
- Use `--cache-optimize` for optimal prompt caching with Anthropic/Google APIs

---

## Architecture

```
┌─────────────────────┐     stdio (JSON-RPC 2.0)     ┌──────────────────┐
│   Claude Desktop    │◄─────────────────────────────►│                  │
│   Cursor            │                               │  MatrixMCPServer │
│   Cline             │     Resources:                │                  │
│   Continue          │     matrix://sections         │  ┌────────────┐  │
│   Gemini CLI        │     matrix://section/{name}   │  │   Matrix   │  │
│   Custom Client     │     matrix://overview         │  │  .prompt   │  │
│                     │     matrix://types             │  │  (parsed)  │  │
│                     │     matrix://api               │  └────────────┘  │
│                     │     matrix://runbook           │                  │
│                     │     matrix://practices         │  Tools:          │
│                     │                               │  search_matrix   │
│                     │     Tools:                     │  get_section     │
│                     │     search_matrix(query)       │  get_context_..  │
│                     │     get_section(name)          │  get_skills      │
│                     │     get_context_for_file(path) │  get_cache_stats │
│                     │     get_skills()               │                  │
│                     │     get_cache_stats()          │                  │
└─────────────────────┘                               └──────────────────┘
```

---

## Version History

| Version | Date | Changes |
| --- | --- | --- |
| 1.0.0 | 2025 | Initial release — 5 tools, 8 resource URIs, stdio transport |
