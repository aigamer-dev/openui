# OpenUI 🚀: The OpenAPI for Large Action Models (LAM)

**OpenUI** is the industry-first open standard for **Deterministic UI Discovery**. Just as **OpenAPI (Swagger)** revolutionized how we describe REST APIs, OpenUI defines how **Large Action Models (LAMs)** and Agents interact with graphical user interfaces.

## Why OpenUI?

Large Action Models (like Claude Computer Use, Rabbit R1, or Browser Agents) often struggle with dynamic, non-deterministic UIs. OpenUI solves this by providing a machine-readable, semantic map of an application's interface directly from the codebase.

The OpenUI CLI is the reference implementation for generating the **Agent-UI JSON Standard**.

---

## Features

- 🧠 **Codebase RAG**: Scans and indexes project source code to extract high-fidelity UI intent.
- 🏗️ **Deterministic Schema**: Produces a structured `agent-ui.json` that acts as the source of truth for Agents.
- 🛡️ **Developer-First**: Annotate your code with `// openui-ignore` or `@openui_include` to control the standard.
- 🔌 **Universal Support**: Works across React, Vue, Angular, Java, Go, Rails, and more.
- 📦 **Standalone Portability**: Pre-compiled binaries for Linux, Windows, and macOS.

## Installation

### Download Standalone Binary
Download the latest pre-compiled binary for your OS from the [Releases](https://github.com/aigamer-dev/openui/releases) page.

### From Source
```bash
git clone https://github.com/aigamer-dev/openui.git
cd openui
pip install .
```

## Quick Start
```bash
openui --target ./your-app-path --rag
```

This will analyze the codebase and generate an `agent-ui.json` file, effectively creating an "API for your UI" that any Agent can use.

## The Standard
For detailed documentation on the `agent-ui.json` specification and how to implement it in your projects, visit our [Official Documentation](https://aigamer-dev.github.io/openui/).

## License
MIT © [aigamer-dev](https://github.com/aigamer-dev)
