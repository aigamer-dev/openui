# Usage Guide

## Generating a Schema

To generate an `agent-ui.json` for your project:

```bash
openui --target /path/to/your/code --rag
```

## Advanced Options

### Directives

Control the generator by adding tags to your source code:

- `// openui-ignore`: Excludes a specific line.
- `// openui-ignore-file`: Excludes the entire file.
- `@openui_include`: Forces the inclusion of a method or class.

### Manual Overrides

Create an `openui.overrides.json` in your project root to manually add or modify elements.

```json
{
  "files": [
    {
      "path": "src/Login.js",
      "add_elements": [
        {"label": "Custom Button", "type": "button", "intent": "custom_action"}
      ]
    }
  ]
}
```
