---
name: github
description: "GitHub operations via gh CLI. Use when: (1) checking PR status or CI, (2) creating/commenting on issues, (3) listing/filtering PRs or issues, (4) viewing run logs."
---

# GitHub Skill

Use the `gh` CLI for GitHub operations.

## When to Use

- Checking PR status, reviews, or merge readiness
- Viewing CI/workflow run status and logs
- Creating, closing, or commenting on issues
- Creating or merging pull requests

## Setup

```bash
gh auth login
```

## Common Commands

### Pull Requests

```bash
# List PRs
gh pr list --repo owner/repo

# Check CI status
gh pr checks 55 --repo owner/repo

# Create PR
gh pr create --title "feat: add feature" --body "Description"
```

### Issues

```bash
# List issues
gh issue list --repo owner/repo --state open

# Create issue
gh issue create --title "Bug: something" --body "Details..."
```

### CI Runs

```bash
# List recent runs
gh run list --repo owner/repo --limit 10

# View failed logs
gh run view <run-id> --log-failed
```
