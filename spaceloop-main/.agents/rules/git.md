---
trigger: always_on
---

# Git Rules
- Commit Format: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- Branches: `main` is production-ready; develop features in dedicated topic branches.

# SpaceLoop Git Rules

## Never Automatically Commit

Do NOT run:

- git add
- git commit
- git push
- git reset --hard
- git checkout -- <files>

unless the user explicitly requests the operation.

## Before Finishing a Task

Report:

1. Files created
2. Files modified
3. Files deleted
4. Tests executed
5. Test results
6. Brief summary of changes

Leave changes uncommitted for user review.

## Preserve Work

Never discard existing user changes.

Do not overwrite unrelated modifications.

Do not reset or revert files to solve an implementation problem.

## Commits

When requested to commit, create a focused commit containing only the relevant changes.

Do not combine unrelated changes into one commit.
