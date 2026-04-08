# 🤖 Xbot: The Limitless Native Agent

**Xbot** is an industrial-grade, system-native autonomous agent designed for developers and power users. Unlike traditional sandboxed assistants, Xbot operates directly on your host OS with full access to your filesystem, terminal, and network, allowing it to perform complex, real-world engineering tasks with surgical precision.

---

## 🚀 Vision & Philosophy

Xbot is built on the principle of **Universal Access regulated by Intelligence**. 

- **System-Native**: No sandboxes. Xbot interacts with your real environment — PowerShell, Git, Docker, and localized file systems.
- **Skill-Based Extensibility**: A modular "Skill System" that allows Xbot to adopt new domain expertise (GitHub, AWS, Notion) on the fly without bloating the core engine.
- **Minimalist Communication**: High-fidelity, value-dense narration. Xbot talks less and does more.

---

## ✨ Key Features

- 🏗️ **Limitless Filesystem**: Read, write, and refactor any file on the system using absolute paths.
- 🐚 **Persistent Shell**: A continuous PowerShell/CMD session for running compilers, servers, and scripts.
- 🧩 **Dynamic Skill System**: Load specialized instruction sets from the `skills/` directory.
- 🌐 **Web Grounding**: Real-time internet access via Gemini 2.0 grounding and Markdown extraction.
- 🛡️ **Intelligent Safety**: A non-restrictive safety model that requires confirmation for destructive actions (e.g., `rm -rf`).

---

## 🛠️ Installation

### 1. Prerequisites
- Python 3.10+
- [Optional] `gh` CLI for GitHub Skill
- [Optional] Docker for Docker Skill

### 2. Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/pathanaawej0-dot/Xbot.git
cd Xbot
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:

```env
MINIMAX_API_KEY=your_minimax_key
GOOGLE_API_KEY=your_google_key
MINIMAX_BASE_URL=https://api.minimax.io/anthropic
MINIMAX_MODEL=MiniMax-M2.7
```

---

## 🎮 Usage

Launch the Xbot agent:

```bash
python main.py
```

### Example Commands:
- *"Initialize a new Next.js project in the /projects folder."*
- *"Check my GitHub PR status and summarize the CI failures."* (Requires GitHub Skill)
- *"Refactor the core executor to use async/await."*

---

## 📂 Project Structure

```text
Xbot/
├── agent/            # Core ReAct loop & LLM integration
├── core/
│   ├── skills/       # Skill loading & registry logic
│   ├── tools/        # System-native tool implementations
│   └── executor.py   # Central tool dispatcher
├── skills/           # Specialized SKILL.md modules
├── prompt.md         # The Master System Prompt
└── main.py           # Entry point
```

---

## ⚖️ Safety & Ethics

Xbot operates with **Full Privileges**. It is your responsibility to monitor its actions.
- Xbot will **always** ask for confirmation before performing irreversible destructive operations.
- Never share sensitive environment keys with the agent that you wouldn't trust with a local shell script.

---

## 📜 License

[MIT](LICENSE) © 2026 Xbot Team
