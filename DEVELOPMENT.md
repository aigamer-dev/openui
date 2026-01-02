# Development Guide

Welcome to the development community of OpenUI! This document provides information on how to contribute, extend, and improve the OpenUI standard and generator.

## Project Architecture

OpenUI is built with a modular "RAG-First" architecture:

- `openui_gen.py`: Entry point and orchestration.
- `modules/codebase_rag.py`: The core ingestion and retrieval engine. Handles multi-framework parsing and chunking.
- `modules/llm_client.py`: Interface for local LLM inference (Gemma-3/xLAM).
- `modules/dependency_graph.py`: Maps file relationships to provide context for UI discovery.
- `modules/schema_auditor.py`: Quantitative analysis tools to verify discovery coverage.
- `modules/semantic_classifier.py`: Lightweight NLP for element intent matching.

## Development Setup

We use **Poetry** for dependency management.

```bash
# Clone the repo
git clone https://github.com/aigamer-dev/openui.git
cd openui

# Install dependencies
poetry install

# Run in development
poetry run python openui_gen.py --target /path/to/test/project --rag
```

## Building the CLI

We use a unified `build.py` script to package the application for all platforms.

```bash
python build.py
```

This uses PyInstaller to create a standalone directory in `dist/openui`.

## Contributing Principles

1.  **Agnosticism**: Ensure parsers work across different frameworks (React, Vue, etc.) wherever possible.
2.  **Determinism**: The standard should be as deterministic as possible. Avoid excessive LLM "hallucination" by grounding results in RAG context.
3.  **Privacy**: Respect `// openui-ignore` tags and do not leak sensitive business logic into the UI schema.

## Roadmap

- [ ] Support for Mobile framework analysis (Flutter, React Native).
- [ ] Direct integration with Claude "Computer Use" API.
- [ ] VS Code Extension for real-time `agent-ui.json` preview.
