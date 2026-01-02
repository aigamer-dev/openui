# The OpenUI Standard

The OpenUI Standard (or `agent-ui.json`) is designed to be the single source of truth for an application's interface.

## Schema Overview

The schema is composed of:

### 1. States
A "State" represents a logical view or screen in your application (e.g., `LoginState`, `DashboardState`).

### 2. Elements
Interactive components within a state (Buttons, Inputs, Links).

### 3. Intents
The semantic meaning of an action (e.g., `login`, `submit_form`, `navigate_back`).

## Comparison to OpenAPI

| Feature | OpenAPI (REST) | OpenUI (LAM) |
| :--- | :--- | :--- |
| **Description** | API Endpoints | UI States & Elements |
| **Input** | JSON/Query Params | User Inputs & Events |
| **Logic** | HTTP Methods | Interaction Intents |
| **Outcome** | Data Response | UI Navigation/Action |
