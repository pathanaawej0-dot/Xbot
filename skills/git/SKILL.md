---
name: git
description: "Local git operations. Use when: (1) committing changes, (2) creating branches, (3) viewing history, (4) stashing changes."
---

# Git Skill

Use git for local version control operations.

## When to Use

- Committing changes
- Creating or switching branches
- Viewing commit history
- Stashing changes
- Merging branches

## Common Commands

```bash
# Check status
git status

# Stage and commit
git add .
git commit -m "feat: description"

# Create branch
git checkout -b feature/new-feature

# View history
git log --oneline -20

# Stash changes
git stash
git stash pop
```
