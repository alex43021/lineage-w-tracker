# AGENTS.md — Shared rules for all AI coding agents

## Language
- Chat responses: Traditional Chinese (繁體中文). Code, comments, and commit messages: English.

## Workflow — accuracy first
- Plan before coding: for any multi-file change, first list the files to modify, the steps, and the "done" criteria. Wait for confirmation.
- Never guess. If a file, API, or requirement is unclear, read the source or ask ONE precise question.
- Follow existing patterns in this repo. Before writing new code, check how similar code is already written here.
- Verify your work: run the relevant linter/tests after changes and show the output.
- Fix root causes, not symptoms. Never suppress or silence errors to make a check pass.

## Token efficiency
- Be concise. No recap of what you just did, no preamble, no restating my request.
- Only read files relevant to the task. Do not re-read unchanged files.
- Prefer small incremental changes over large rewrites.
- Do not add features, refactors, dependencies, or files that were not requested.

## Code style
- Keep functions under ~30 lines and files under ~300 lines; split when larger.
- No dead code, no commented-out code, no unused imports.

### Python (this repo)
- Type hints on all function signatures. Use pathlib and f-strings.
- Lint/format: Ruff. Tests: pytest.

## Safety
- Never hardcode secrets. Use .env files; never read, print, or commit them.
- Ask before: deleting files, dropping/altering DB tables, force-pushing, or editing CI/CD config.
- Never commit or push unless asked. Use conventional commits (feat:, fix:, refactor:, docs:), title <=72 chars.
