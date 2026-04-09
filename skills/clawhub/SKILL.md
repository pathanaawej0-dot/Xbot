---
name: clawhub
description: "Manage and discover skills via the ClawHub CLI Marketplace."
metadata:
  openclaw:
    requires:
      bins: ["clawhub"]
---

# ClawHub Skill

This skill allows Xbot to interact with the global [ClawHub](https://clawhub.ai) marketplace to discover, install, and manage skills.

## 1. Discovery & Search
Use these commands to find new capabilities on ClawHub.

```bash
# Search for skills by keyword or topic
clawhub search "postgres"
clawhub search "automation"

# Get details about a specific skill
clawhub info <skill-slug>
```

## 2. Installation & Updates
Manage the lifecycle of your local skills.

```bash
# Install a new skill to the local skills directory
clawhub install <skill-slug>

# Update a specific skill or all skills
clawhub update <skill-slug>
clawhub update --all

# List all installed skills currently managed by ClawHub
clawhub list
```

## 3. Bootstrap (If CLI Missing)
If the `clawhub` command is not found, you can attempt to install it using one of the following methods (verify which one the user prefers or has available):

### Via NPM (Recommended)
```bash
npm install -g @openclaw/clawhub
```

### Via Go
```bash
go install github.com/openclaw/clawhub@latest
```

## 4. Xbot Strategy
- If the user asks for a task that is NOT covered by local skills, **always** search ClawHub first.
- If a skill is found, ask the user: *"I found the '<name>' skill on ClawHub. Should I install it to handle this task?"*
- Upon approval, use `clawhub install` and then reload your system prompt to include the new skill.
