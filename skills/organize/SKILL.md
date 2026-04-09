---
name: organize
description: "Industrial file organization. Use when: (1) cleanup of large directories, (2) establishing project structure, (3) bulk moving/renaming."
metadata:
  openclaw:
    requires:
      bins: []
---

# Organize Skill

Use this skill to transform chaotic directories into industrial-grade structures.

## Standard Project Structure

```text
project_root/
├── assets/          # Static files, images, icons
├── src/             # Source code
├── tests/           # Unit and integration tests
├── docs/            # Documentation
├── scripts/         # Automation scripts
└── .gitignore       # Git exclusion
```

## Common Operations

### 1. Group by Extension
Move all files of a specific type into a folder.
`mv *.py ./src/`

### 2. Standardize Naming
Ensure all files use lowercase with underscores.

### 3. Cleanup
Identify and move old or temporary files to a `tmp/` or `backups/` directory.

## Best Practices
- **Dry Run First**: Always list the files you intend to move before executing `mv`.
- **Absolute Paths**: Use absolute paths for the destination to avoid "deep nesting" accidents.
