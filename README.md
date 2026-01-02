# OpenUI 🚀

**OpenUI** is a next-generation CLI tool for **Deterministic UI Discovery**. Unlike traditional scrapers, OpenUI uses a **Codebase RAG (Retrieval-Augmented Generation)** engine to analyze your source code and "dream" a deep, semantic `agent-ui.json` schema.

## Features

- 🧠 **Codebase RAG**: Scans and indexes your actual code to understand UI intent.
- 🏗️ **Multi-Framework**: Supports React, Vue, Angular, Java (Spring), Go, Rails, and more.
- 🛡️ **Developer Directives**: Control analysis with `// openui-ignore` and `@openui_include`.
- 🔌 **Manual Overrides**: Merge automated discovery with hand-crafted `openui.overrides.json`.
- 📦 **Standalone Binary**: Zero-dependency executables for Linux, Windows, and macOS.

## Installation

### Download Standalone Binary
Go to the [Releases](https://github.com/aigamer-dev/openui/releases) page and download the version for your OS.

### From Source
```bash
git clone https://github.com/aigamer-dev/openui.git
cd openui
pip install .
```

## Usage

Generate a UI schema for your project:
```bash
openui --target ./my-web-app --rag
```

### Options
- `--target`: Path to the project root.
- `--rag`: Enable full RAG pipeline (Recommended).
- `--lite`: Low-resource mode (Regex only).
- `--port`: Web server port (default: 8000).

## License
MIT © [aigamer-dev](https://github.com/aigamer-dev)
