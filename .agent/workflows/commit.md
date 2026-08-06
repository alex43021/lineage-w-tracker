---
description: Lint + test changed code, then propose a conventional commit
---

1. Run the linter and tests only for the files changed in this session.
// turbo
2. Run `git status` and `git diff --stat` to review the change set.
3. Stage the relevant files and draft a conventional commit message (feat:/fix:/refactor:/docs:), English, title <=72 chars.
4. Show me the message and WAIT for my approval before committing. Never push.
