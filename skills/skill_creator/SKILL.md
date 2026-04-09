# Skill Creator: Autonomous Evolution Protocol

This skill grants Xbot the capability to create new specialized skills for its own library. 

## 🧠 Logic & Strategy
When Xbot identifies a recurring complex task or a new domain (e.g., "Advanced SQLite Optimization" or "Personal Finance Automation"), it can use this protocol to "instantiate" a new skill.

### How to Create a Skill:
1. **Identify the Need**: Recognize a pattern of logic or a specific toolset requirement.
2. **Design the Skill**: Define the purpose, core rules, and "God-Mode" instructions.
3. **Execute Creation**:
   - Use `list_files` to ensure the name is unique in the `skills/` directory.
   - Use `write` to create a new folder: `skills/<skill_name>/`.
   - Use `write` to create `skills/<skill_name>/SKILL.md`.

## 📝 SKILL.md Template
Every new skill created must follow this high-fidelity structure:
```markdown
# <Skill Name>: <One-line Purpose>

## 🎯 Objective
[Detailed mission statement]

## 🛠️ Logic & Rules
[Numbered list of internal logic, shell command patterns, or file handling rules]

## 🚀 God-Mode Commands
[Examples of how the agent should call tools when this skill is active]
```

## 🔋 Capability Injection
After creation, the new skill will automatically be loaded in the next Xbot session (or current session if the agent re-reads the directory).
