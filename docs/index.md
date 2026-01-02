# OpenUI: The Matter Protocol for the Web 🌐

**Standardizing Autonomous Agent Interactions via Deterministic UI Discovery.**

![OpenUI Banner](https://raw.githubusercontent.com/aigamer-dev/openui/master/assets/banner.png)

## The Vision: Closing the "Interface Gap"

Current AI agents rely on fragile, non-deterministic methods like screen scraping and computer vision to navigate web applications. This results in the **"Vision Tax"**—high latency, prohibitive inference costs, and low reliability (~85% success rate).

**OpenUI** is a standardized JSON-based protocol that allows web applications to explicitly declare their interactive states and logic to AI agents. By decoupling the **"Action Layer"** from the **"Visual Layer,"** we enable true agentic autonomy.

---

## Why OpenUI?

### 🚀 Zero Vision Tax
Processing a 1080p screenshot requires encoding thousands of vision tokens. OpenUI uses structured text, reducing token costs by **100x** and latency from seconds to milliseconds.

### 🎯 99.9% Determinism
No more "coordinate hallucination." OpenUI provides a deterministic "hit test" for every interactive element directly from the source code.

### 🛠️ Agent Interface Optimization (AIO)
Just as SEO optimized the web for search engines, **AIO** optimizes your application for the "Internet of Agents."

---

## Key Components

- **[The OpenUI Protocol](standards/protocol.md)**: A universal schema for UI discovery.
- **[OpenUI CLI](learn/cli.md)**: The reference auto-generator that translates your codebase into the standard.
- **[Benchmarks](learn/benchmarks.md)**: Real-world performance comparison (Vision vs. OpenUI).

## Installation

```bash
pip install openui-cli
```

## Quick Start

```bash
openui --target ./my-project --rag
```

This generates an `agent-ui.json` at your project root—the "OpenAPI" for your interface.
