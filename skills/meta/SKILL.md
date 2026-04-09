---
name: meta
description: "Self-evolution skill. Use when: (1) you identify a repetitive complex workflow, (2) you need to store persistent domain knowledge, (3) the user asks to 'teach you' something new."
metadata:
  openclaw:
    invocation: "manual"
---

# Meta Skill: Skill Creator

This skill allows Xbot to generate new skills for its own library.

## When to Use

- When the user says "From now on, always do X like Y."
- When you discover a complex set of steps for a new tool (e.g., AWS CDK, Kubernetes) that isn't currently in your `skills/` directory.
- When you want to "remember" a specific project architecture.

## How to Create a New Skill

1. Identify the **name** and **description** (trigger context).
2. Define the **requirements** (binaries needed).
3. Draft the **SKILL.md** using the following structure:
   ```markdown
   ---
   name: [name]
   description: "[trigger description]"
   metadata:
     openclaw:
       requires:
         bins: [list of binaries]
   ---
   # [Name] Skill
   [Detailed instructions, common commands, and best practices]
   ```
4. Use `write_file` to save it to `skills/[name]/SKILL.md`.
5. The next turn, you will automatically detect it.
