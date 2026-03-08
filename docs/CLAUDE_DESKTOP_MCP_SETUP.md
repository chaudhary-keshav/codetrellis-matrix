# Claude Desktop MCP Configuration for CodeTrellis

# =================================================

#

# Copy the JSON below into your Claude Desktop config file at:

# ~/Library/Application Support/Claude/claude_desktop_config.json

#

# This registers the CodeTrellis MCP server so Claude Desktop

# can query your project's matrix sections and search tools automatically.

#

# After adding, restart Claude Desktop.

#

# {

# "mcpServers": {

# "codetrellis": {

# "command": "/opt/homebrew/bin/python3",

# "args": [

# "-m", "codetrellis", "mcp",

# "/Users/keshavchaudhary/Documents/GitHub/codetrellis-reops/codetrellis"

# ]

# }

# }

# }

#

# For multiple projects, add one entry per project:

#

# {

# "mcpServers": {

# "codetrellis-main": {

# "command": "/opt/homebrew/bin/python3",

# "args": ["-m", "codetrellis", "mcp", "/path/to/project-a"]

# },

# "codetrellis-api": {

# "command": "/opt/homebrew/bin/python3",

# "args": ["-m", "codetrellis", "mcp", "/path/to/project-b"]

# }

# }

# }
