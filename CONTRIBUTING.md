# Contributing to Xbot

We welcome contributions from the community to help make Xbot the most powerful system-native agent in the world.

## How to Contribute Skills

Skills are the easiest way to extend Xbot.
1. Create a new directory in `skills/`.
2. Add a `SKILL.md` following the template:
   ```yaml
   ---
   name: your-skill
   description: "Trigger phrases and use cases."
   ---
   # Instructions...
   ```
3. Test your skill by asking Xbot to perform a task associated with it.

## Architecture Guidelines

- **Limitless Access**: All new tools should support absolute paths.
- **Safety**: Implement safety checks for any destructive operations.
- **Async First**: Use `asyncio` for all I/O bound tool executions.

## Reporting Bugs

Please open an issue on GitHub with:
- A clear description of the problem.
- Your OS and Python version.
- The `prompt.md` version you are using.
