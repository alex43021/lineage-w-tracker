@AGENTS.md

# Claude Code specifics
- Commands: `ruff check .`, `pytest -q` (single test file preferred).
- Use plan mode for multi-file changes; skip planning for one-line fixes.
- Use subagents for codebase investigation to keep the main context clean.
- When compacting, always preserve the list of modified files and the test commands.
