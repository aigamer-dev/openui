import os
import re
import json
from typing import List, Dict

from modules.dependency_graph import DependencyGraph

class CodebaseRAG:
    """
    Ingests codebase using a Dependency Graph for context-aware analysis.
    """
    def __init__(self, target_dir: str, model_loader=None):
        self.target_dir = target_dir
        self.model_loader = model_loader
        self.chunks: List[Dict] = []
        self.graph = None
        self.manual_config = self.load_manual_overrides()

    def load_manual_overrides(self) -> Dict:
        """Loads openui.overrides.json if present."""
        config_path = os.path.join(self.target_dir, "openui.overrides.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    print(f"Loaded Manual Overrides from {config_path}")
                    return json.load(f)
            except Exception as e:
                print(f"Error loading overrides: {e}")
                return {}
        return {}
        
    def ingest(self):
        """Scans codebase, builds dependency graph, and processes in order."""
        print(f"Indexing Codebase in: {self.target_dir}")
        all_files = []
        
        # 1. Collect all valid files
        for root, _, files in os.walk(self.target_dir):
             if any(x in root for x in ["node_modules", "venv", ".git", "__pycache__", "build", "dist"]):
                 continue
             for file in files:
                valid_exts = (".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".dart", ".html", ".css", ".vue", ".go", ".rb", ".php", ".erb", ".jsp", ".ghtml", ".scala.html")
                if file.endswith(valid_exts):
                    all_files.append(os.path.join(root, file))
        
        # 2. Build Dependency Graph
        print(f"Building Dependency Graph for {len(all_files)} files...")
        self.graph = DependencyGraph(self.target_dir, all_files)
        self.graph.build()
        
        # 3. Get Topological Order (Detailed Low-Level -> High-Level)
        ordered_files = self.graph.get_execution_order()
        
        print("Processing files in dependency order...")
        for file_path in ordered_files:
            self._process_file(file_path)
            
        print(f"Ingested {len(self.chunks)} code chunks.")

    def _process_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for file-level ignore
            if "openui-ignore-file" in content:
                print(f"Ignoring file (Directive): {file_path}")
                return

            included_manual_entries = []
            
            # Line-level ignore processing
            lines = content.splitlines()
            filtered_lines = []
            
            # Heuristic for Manual Includes (Decorator/Comment approach)
            # Looks for @openui_include OR // openui-include
            # Captures: 1. The tag 2. The function signature 3. The docstring (reason)
            
            manual_pattern = r"(?:@openui_include|//\s*@openui_include|#\s*@openui_include)\s*(?:\(([^)]+)\))?\s*\n\s*(?:def|function|class|func)\s+([a-zA-Z0-9_]+)"
            matches = re.finditer(manual_pattern, content)
            
            for m in matches:
                extra_args = m.group(1) # e.g. "reason='Important'"
                func_name = m.group(2)
                
                # Usage Tracer: Find where this function is called in the file (simple)
                # In a real scanner, we'd search the whole codebase.
                usage_count = content.count(func_name) - 1 # Subtract definition
                
                # Extract Docstring (Naive approach: look for next quotes)
                reason = "Manual Override"
                start_idx = m.end()
                docstring_match = re.search(r'[\'"]{3}(.*?)[\'"]{3}', content[start_idx:], re.DOTALL)
                if docstring_match:
                    reason = docstring_match.group(1).strip()
                elif extra_args:
                    reason = extra_args

                included_manual_entries.append({
                    "type": "manual_entry",
                    "name": func_name,
                    "reason": reason,
                    "usage_count": max(0, usage_count),
                    "invocation_hint": f"Called {usage_count} times in file.",
                    "forced": True
                })

            for line in lines:
                if "openui-ignore" in line and "openui-ignore-file" not in line:
                    continue
                filtered_lines.append(line)
            
            content = "\n".join(filtered_lines)

            # Simple chunking by file for now (Context Window is large enough for small demos)
            # In production: accurate function splitter.
            self.chunks.append({
                "path": file_path,
                "content": content,
                "type": "source",
                "manual_entries": included_manual_entries
            })
        except Exception as e:
            print(f"Skipping {file_path}: {e}")

    def get_file_role(self, file_path: str, content: str) -> str:
        """
        Determines the role of a file for dynamic prompting.
        """
        path_lower = file_path.lower()
        
        # View/UI
        if any(x in path_lower for x in ['view', 'component', 'template', 'layout', 'ui', 'page', 'screen']):
            return "VIEW"
        if file_path.endswith(('.html', '.jsx', '.tsx', '.vue', '.erb', '.jsp', '.ghtml', '.css')):
            return "VIEW"
            
        # Controller/Logic
        if any(x in path_lower for x in ['controller', 'service', 'handler', 'manager', 'store', 'bloc', 'provider']):
            return "CONTROLLER"
            
        # Data/Model
        if any(x in path_lower for x in ['model', 'entity', 'dto', 'schema', 'type']):
            return "MODEL"
            
        # Config/Setup
        if any(x in path_lower for x in ['config', 'setup', 'init', 'main', 'app']):
            return "CONFIG"
            
        return "GENERIC"

    def generate_contextual_prompt(self, file_path: str, role: str, neighbors: List[str]) -> str:
        """
        Generates a specialized system prompt based on file role and graph context.
        """
        base_prompt = "You are an expert software architect."
        
        if role == "VIEW":
            return f"{base_prompt} FOCUS: UI Extraction. Identify all interactive elements, visible text, and user inputs. Context: Used by {neighbors[:3]}."
        elif role == "CONTROLLER":
            return f"{base_prompt} FOCUS: Logic Flow. Map user actions to state changes. Context: Manages {neighbors[:3]}."
        elif role == "MODEL":
            return f"{base_prompt} FOCUS: Data Structure. Define the schema and properties. Context: Used by {neighbors[:3]}."
        else:
            return f"{base_prompt} FOCUS: General Analysis. Identify purpose and relations."

    def query_ui_schema(self) -> Dict:
        """
        Constructs a prompt with the codebase context and asks the LLM to generate agent-ui.json.
        """
        # Extensions to ingest
        self.extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.dart', '.html', '.css',
                          '.vue', '.go', '.rb', '.php', '.erb', '.jsp']
        
        # Regex heuristics for "Mocking" the LLM's understanding of UI components for the Verification Phase
        self.heuristics = {} # Not used in main logic anymore, kept for compat if needed
        context = ""
        discovered_elements = []
        discovered_states = set()
        manual_overrides = []

        # 1. Project Type Filter (Skip API-Only)
        # Check if project has ANY view files
        has_views = False
        view_exts = ['.html', '.jsx', '.tsx', '.vue', '.erb', '.jsp', '.ghtml']
        for chunk in self.chunks:
            if any(chunk['path'].endswith(ext) for ext in view_exts):
                has_views = True
                break
        
        # 1. Project Type Filter (Skip API-Only)
        # Check if project has ANY view files
        has_views = False
        view_exts = ['.html', '.jsx', '.tsx', '.vue', '.erb', '.jsp', '.ghtml']
        
        # Streamlit check: .py files with 'st.'
        has_streamlit = False
        
        for chunk in self.chunks:
            if any(chunk['path'].endswith(ext) for ext in view_exts):
                has_views = True
                break
            if chunk['path'].endswith('.py') and ('import streamlit' in chunk['content'] or 'st.' in chunk['content']):
                 has_streamlit = True
                 has_views = True
                 break
        
        if not has_views:
            print(f"Skipping {self.target_dir}: No UI files found (API-Only detected).")
            return {"name": "API-Only Project", "states": [], "elements": []}

        # Regex heuristics to find "State" or "Component" candidates
        # EXPANDED FOR PHASE 10 (Maximum Coverage)
        state_patterns = [
            r"class\s+(\w+)\s+extends\s+Component", # React Class
            r"function\s+(\w+)\s*\(", # React Function / JS
            r"class\s+(\w+Controller)", # Java Spring/Rails
            r"@Controller\s+class\s+(\w+)", # Java Annotation
            r"class\s+(\w+)\s+extends\s+StatelessWidget", # Flutter
            r"class\s+(\w+)\s+extends\s+StatefulWidget", # Flutter
            r"def\s+(\w+)\(", # Python
            r"func\s+(?:.*?\s+)?([A-Z]\w*)", # Go
            r"export\s+class\s+(\w+Component)", # Angular
            r'name:\s*[\'"](\w+)[\'"]', # Vue
            r"define\s*\(\s*['\"](\w+)['\"]", # AMD/RequireJS",
            # PHASE 12: Implicit API States
            r"\.catch\s*\(\s*(?:function\s*)?\(?\s*(\w+)", # JS Promise Catch -> Error State
            r"on(?:Error|Failure)\s*:\s*(\w+)", # Generic Callback
        ]
        
        # Regex for elements - UNIVERSAL INTERACTION PATTERNS (PERMISSIVE)
        element_patterns = [
            # HTML/JSX Tags (Permissive: Matches opening tag of button/input/a/form or Capitalized Components)
            r"<button[^>]*>", 
            r"<a\s+[^>]*>",
            r"<input[^>]*>",
            r"<form[^>]*>",
            r"<([A-Z][a-zA-Z0-9]*)\s+[^>]*>", # React/Vue Component usage <MyButton />
            
            # Framework Specifics
            r"st\.(button|text_input|checkbox|selectbox|radio|slider|number_input|date_input|time_input|file_uploader|multiselect|color_picker)\(", # Streamlit
            r"(FloatingActionButton|TextFormField|FlatButton|RaisedButton)\(", # Flutter
            r"link_to\s+['\"]", # Rails
            r"button_to\s+['\"]",
            r"form_for\s+",
            r"th:(field|action|href|replace)\s*=", # Thymeleaf (Java)
            
            # Attributes (Events) - Matches the attribute itself, we extract value later if needed
            r"(@click|v-on:click|ng-click|hx-post|hx-get|th:action)\s*=\s*['\"]([^'\"]+)['\"]", 
            r"(onClick|onChange|onSubmit)\s*=\s*",
        ]

        total_content_len = 0
        min_inference_log = []
        
        for chunk in self.chunks:
            # 1. Identify Role
            role = self.get_file_role(chunk['path'], chunk['content'])
            
            # 2. Get Neighbors (Context) from Graph
            neighbors = []
            if self.graph:
                # Find edges where this node is Source (Dependencies) or Target (Dependents)?
                # We want "What does this file use?" -> Successors in our dependency graph A->B (A imports B)
                # If A->B means A imports B, then Successors are imports.
                try:
                    neighbors = list(self.graph.graph.successors(chunk['path']))
                except:
                    pass
            
            # 3. Generate Contextual Prompt (Simulated "Mini-Inference")
            system_prompt = self.generate_contextual_prompt(chunk['path'], role, [os.path.basename(n) for n in neighbors])
            min_inference_log.append(f"Analyzing {os.path.basename(chunk['path'])} as {role} with context {len(neighbors)} neighbors.")

            # Add relative path
            rel_path = os.path.relpath(chunk['path'], self.target_dir)
            content_snippet = chunk['content'][:5000]
            context += f"\n--- FILE: {rel_path} (ROLE: {role}) ---\n"
            context += f"System Hint: {system_prompt}\n" 
            context += f"{content_snippet}\n"
            total_content_len += len(chunk['content'])

            # Collect Manual Overrides
            if "manual_entries" in chunk:
                for entry in chunk["manual_entries"]:
                    manual_overrides.append(entry)
                    discovered_states.add(f"{entry['name']} (MANUAL)")

            # --- RECURSIVE EXTRACTION BASED ON ROLE ---
            
            # 1. State/Component Discovery (Scan EVERYWHERE)
            # In Component-based frameworks (React/Vue), the View IS the State definition.
            for pattern in state_patterns:
                states = re.findall(pattern, chunk['content'])
                for s in states:
                    discovered_states.add(s)
            
            # 2. Element Discovery (Heuristic)
            # Associating elements with the file they are in.
            # We focus mainly on VIEW/GENERIC, but some Controllers might have implicit UI (e.g. render())
            if role in ["VIEW", "GENERIC", "CONTROLLER"]:
                for pattern in element_patterns:
                    # re.finditer for better context if needed
                    matches = re.finditer(pattern, chunk['content'])
                    for m in matches:
                        full_match = m.group(0)
                        # Extract Label Group (usually group 1 or 2 depending on regex)
                        # Heuristic: try group 1, if None try 2, else full match
                        # We simplified regexes to mostly have no capture or 1 capture
                        
                        label = "Element"
                        if m.lastindex:
                            label = m.group(m.lastindex)
                        
                        discovered_elements.append({
                            "type": "interaction", 
                            "label": label[:30], 
                            "source": rel_path,
                            "role_context": role
                        })


        # PHASE 13: Apply Manual Overrides (Additive)
        if self.manual_config and "files" in self.manual_config:
            print(f"[Manual Overrides] Processing {len(self.manual_config['files'])} override rules...")
            for override in self.manual_config["files"]:
                target_path = override.get("path", "")
                
                # 1. Add Manual States
                for state in override.get("add_states", []):
                    discovered_states.add(f"{state}")
                    # Also suggest it in context for the LLM
                    context += f"\n--- MANUAL OVERRIDE: {target_path} ---\nState Force-Added: {state}\n"

                # 2. Add Manual Elements
                for elem in override.get("add_elements", []):
                    discovered_elements.append({
                        "type": "interaction",
                        "label": elem.get("label", "Manual Element"),
                        "source": target_path, 
                        "role_context": "MANUAL",
                        "intent": elem.get("intent", "manual_action")
                    })
                    context += f"Element Force-Added: {elem.get('label')} ({elem.get('type')})\n"

        print("\n".join(min_inference_log[:5]) + "\n... (Recursive Log Truncated)")
        
        prompt = f"""
You are an expert AI UI Analyst. Your goal is to analyze the following Source Code and generate a precise JSON schema representing the User Interface State Map.

### INSTRUCTIONS:
1. Identify all distinct UI States (screens/views) based on the code (e.g., "Login", "Dashboard", "Cart").
2. For each state, list all Interactive Elements (Inputs, Buttons) with their semantic intent (e.g., "login_email", "submit_login").
3. Determine the "Action" function that is called when an element is interacted with (e.g., `handleLogin()`).
4. Output STRICT JSON format matching the `agent-ui.json` spec.

### DEVELOPER DIRECTIVES (MUST INCLUDE):
The following components have been manually tagged by the developer. You MUST include them in the schema:
{[f"- {m['name']}: {m['reason']} (Invoked: {m['invocation_hint']})" for m in manual_overrides]}

### CODEBASE CONTEXT (Topologically Sorted):
{context}

### OUTPUT SCHEMA CONSTRAINTS:
- JSON Only.
- Keys: `states` (array of objects with `id`, `name`, `elements`, `details`).
- `elements` keys: `id`, `tag`, `intent`, `action_code`.

GENERATE JSON NOW:
"""
        print(f"[GraphRAG] Constructed Prompt with Context Length: {len(context)} chars (from {total_content_len} total codepoints).")
        
        # Mock Output for Verification Phase
        states_json = []
        
        # Pre-assign explicitly matched elements to avoid duplication logic complexity
        # Strategy:
        # 1. Clean State Name (remove Controller, Component, etc)
        # 2. Check if clean name matches file path (case-insensitive)
        
        used_element_ids = set()

        for i, state in enumerate(discovered_states):
            clean_name = re.sub(r'(Controller|Component|View|Page|Handler)$', '', state, flags=re.IGNORECASE).lower()
            
            matched_elements = []
            for j, e in enumerate(discovered_elements):
                # Unique ID for tracking
                el_uid = f"{e['source']}_{j}"
                
                # Check association based on role context and file path match
                source_lower = e['source'].lower()
                
                match = False
                # If Element is in a View, and State is the Controller for that View? (Heuristic: Similarity)
                if clean_name in source_lower:
                    match = True
                
                # If Single Page App/Small Demo
                elif len(discovered_states) <= 3:
                     match = True
                
                if match:
                    intent_label = e.get('label', 'action')
                    matched_elements.append({
                        "id": f"el_{i}_{len(matched_elements)}", 
                        "tag": "element", 
                        "intent": f"interact_{intent_label}", 
                        "source": e['source']
                    })
                    used_element_ids.add(el_uid)
            
            states_json.append({
                "id": f"state_{i}",
                "name": state,
                "elements": matched_elements
            })
        
        # Fallback: Collect "Orphaned" elements (Found by RAG but not associated to a specific state)
        # This ensures 100% Coverage of discovered elements.
        orphaned_elements = []
        for j, e in enumerate(discovered_elements):
            el_uid = f"{e['source']}_{j}"
            if el_uid not in used_element_ids:
                orphaned_elements.append({
                    "id": f"el_orphan_{j}", 
                    "tag": "element", 
                    "intent": f"interact_{e['label']}", 
                    "source": e['source']
                })
        
        # If we have orphans, attach them to the first state (if exists) or create a "Global" state
        if orphaned_elements:
            if states_json:
                states_json[0]['elements'].extend(orphaned_elements)
            else:
                states_json.append({
                    "id": "state_global",
                    "name": "Global Shared Scope",
                    "elements": orphaned_elements
                })

        # Inject Manual Details into the Mock Output
        for s in states_json:
            for m in manual_overrides:
                if m['name'] in s['name']:
                    s['description'] = m['reason']
                    s['invocation_hint'] = m['invocation_hint']
                    s['forced_inclusion'] = True
        
        # Inject Manual Details into the Mock Output
        for s in states_json:
            for m in manual_overrides:
                if m['name'] in s['name']:
                    s['description'] = m['reason']
                    s['invocation_hint'] = m['invocation_hint']
                    s['forced_inclusion'] = True

        return {
            "rag_metadata": {
                "prompt_length": len(context),
                "files_ingested": len(self.chunks),
                "detected_framework_hints": list(discovered_states)[:10],
                "manual_overrides": len(manual_overrides)
            },
            "states": states_json,
            "note": "Output generated via Codebase RAG Heuristics (LLM Simulation)"
        }
