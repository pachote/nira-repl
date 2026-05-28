# NIRA REPL MCP

> Secure code execution sandbox for Claude — run Python, JavaScript, and shell commands

[![PyPI version](https://badge.fury.io/py/nira-repl.svg)](https://pypi.org/project/nira-repl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
pip install nira-repl
```

Add to your Claude Code MCP config (`~/.claude.json`):
```json
{
  "mcpServers": {
    "nira-repl": {
      "command": "python",
      "args": ["-m", "nira_repl"]
    }
  }
}
```

## License

MIT — built by [pachote](https://github.com/pachote)
