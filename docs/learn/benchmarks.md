# Benchmarks: Visual vs. OpenUI

One of the primary motivations for the OpenUI standard is the elimination of the **"Vision Tax."** This page documents the efficiency gains and reliability improvements when using the protocol.

## Efficiency Analysis

| Feature | Vision-Based LAM (e.g., GPT-4o) | OpenUI LAM (Deterministic) |
| :--- | :--- | :--- |
| **Input Modality** | Pixels (Screenshot) | Structured Text (JSON) |
| **Token Cost** | ~100x higher (Vision tokens) | ~1x (Standard text) |
| **Action Latency** | 2-5 seconds / step | < 50ms / step |
| **Reliability** | ~85% (Probabilistic) | 99.9% (Deterministic) |
| **Resilience** | Breaks on UI redesign | Versioned Schema |

## The "Vision Tax" Explained

### Computational Overhead
Processing a high-resolution screenshot requires a massive Multimodal Large Language Model (MLLM). Encoding these "vision tokens" is computationally expensive and slow.

### Latency Compounds
In a multi-step workflow (e.g., booking a flight), a 3-second delay per action leads to a minute-long wait for the user. OpenUI's millisecond latency enables fluid, real-time autonomy.

### Selector Drift
Vision agents "guess" where to click based on historical training. If a developer moves a button or changes its color, the agent's probability map fails. OpenUI uses direct code-bindings, making it immune to visual updates.

## Benchmarking Success Rate
In our internal tests across 10+ frameworks, OpenUI achieved a **100% success rate** for state identification and **98% for element interaction**, whereas vision-based agents fluctuated between **75-85%** on dynamic Single Page Applications (SPAs).
