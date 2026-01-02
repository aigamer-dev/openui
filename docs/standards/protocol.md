# The OpenUI Protocol (Agent-UI Standard)

The **OpenUI Protocol** is a declarative metadata standard designed to bridge the "Interface Gap" between Large Action Models (LAMs) and software applications.

## The Problem: The "Black Box" Interface
Modern web applications are designed exclusively for human biological perception. An AI agent perceiving a DOM tree sees a chaotic grid of `<div>` tags, not a structured logic tree. This leads to:

- **Selector Drift**: Brittle automation that breaks when a CSS class changes.
- **Context Exhaustion**: Visual agents forgetting the state of a checkbox three screens ago.

## The Solution: A Declarative State Machine

We propose the `agent-ui.json` file, hosted at the root of an application. It defines the application as a **Deterministic State Machine**.

### Core Schema Components

#### 1. State Definitions
Defines the current context (e.g., `login_screen`, `checkout_flow`) and how to detect it.

#### 2. Semantic Actions
Defines high-level intents (e.g., `add_to_cart`) decoupled from low-level inputs (e.g., `click_div_45`).

#### 3. Execution Logic
Precise DOM selectors, JavaScript hooks, or API endpoints to trigger actions without visual estimation.

#### 4. Parameter Constraints
Data typing and validation (e.g., "Search query must be > 3 characters").

## Matter for the Web
Just as the **Matter** protocol standardized how smart home devices communicate, OpenUI standardizes how software applications communicate with autonomous agents. This marks the transition from **probabilistic interaction** (guessing) to **deterministic interaction** (knowing).
