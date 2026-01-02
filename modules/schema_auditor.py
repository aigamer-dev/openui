
import os
import json
import re
from pathlib import Path

class SchemaAuditor:
    def __init__(self):
        self.heuristics = {
            'states': r'("id":\s*"state_|id:\s*state_)',
            'inputs': r'(<input|st\.text_input|st\.slider|type="text"|v-model|\[\(ngModel\)]|form\.text_field|TextFormField)',
            'buttons': r'(<button|<a\s|st\.button|type="submit"|onclick=|@click|\(click\)|link_to|button_to|ng-click|hx-post|th:action|FloatingActionButton)',
        }

    def audit_project(self, project_path):
        """
        Audits a single project:
        1. Counts potential states/elements in SOURCE CODE.
        2. Counts actual states/elements in AGENT-UI.JSON.
        3. Returns a "Coverage Score".
        """
        json_path = os.path.join(project_path, "agent-ui.json")
        if not os.path.exists(json_path):
            return {"error": "No agent-ui.json found"}

        with open(json_path, 'r') as f:
            data = json.load(f)

        # 1. Analyze JSON (Actual)
        json_states = len(data.get("states", []))
        json_elements = 0
        for state in data.get("states", []):
            json_elements += len(state.get("elements", []))

        # 2. Analyze Source (Potential)
        # This is a Rough Estimation Audit
        source_files = []
        for root, _, files in os.walk(project_path):
                if any(x in root for x in ["node_modules", "venv", ".git", "__pycache__", "build", "dist", "target", ".mvn", "gradle"]):
                    continue
                for file in files:
                    if not file.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.dart', '.html', '.css', '.vue', '.go', '.rb', '.php', '.erb', '.jsp', '.ghtml', '.scala.html')):
                        continue
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)

        potential_elements = 0
        potential_states = 0
        
        # Check for View/UI files to filter API-only projects
        has_views = False
        for file_path in source_files:
            if file_path.endswith(('.html', '.jsx', '.tsx', '.vue', '.erb', '.jsp', '.ghtml')):
                has_views = True
                break
        
        # Check for View/UI files to filter API-only projects
        has_views = False
        for file_path in source_files:
            if file_path.endswith(('.html', '.jsx', '.tsx', '.vue', '.erb', '.jsp', '.ghtml')):
                has_views = True
                break
            # Streamlit check
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        c = f.read()
                        if 'import streamlit' in c or 'st.' in c:
                            has_views = True
                            break
                except:
                    pass
        
        if not has_views:
             return {"project": os.path.basename(project_path), "error": "Skipped (API-Only)"}

        # Simple heuristic: specific keywords imply interactive intent
        # In a real expanded version, this would reuse the regexes from CodebaseRAG but more aggressively
        for file_path in source_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Count "controllers" or "components" as State Candidates
                    if re.search(r'(class\s+[A-Z][a-zA-Z0-9]*|func\s+[A-Z]|@Controller|name:\s*[\'"]\w+[\'"])', content): 
                        potential_states += 1
                    # Count "buttons" or "inputs" as Element Candidates (Expanded)
                    potential_elements += len(re.findall(r'(<button|<input|<a\s|st\.(button|slider|text_input|checkbox|selectbox|radio)|on[A-Z][a-z]+|@click|ng-|hx-|th:(field|action|href|replace)|link_to|button_to)', content))
            except:
                pass
        
        # Avoid div zero
        state_coverage = (json_states / potential_states * 100) if potential_states > 0 else 100
        element_coverage = (json_elements / potential_elements * 100) if potential_elements > 0 else 100
        
        # Cap at 100% just in case regexes under-count
        state_coverage = min(state_coverage, 100)
        element_coverage = min(element_coverage, 100)

        return {
            "project": os.path.basename(project_path),
            "json_states": json_states,
            "potential_states": potential_states,
            "state_coverage": round(state_coverage, 1),
            "json_elements": json_elements,
            "potential_elements": potential_elements,
            "element_coverage": round(element_coverage, 1)
        }

if __name__ == "__main__":
    auditor = SchemaAuditor()
    base_dir = "../" # Assuming running from open-ui-gen
    
    # List of expected projects
    projects = [
        "external-react-cart",
        "external-streamlit-uber",
        "external-flutter-samples/provider_counter",
        "external-java-petclinic",
        "external-expanded-projects/vue-app",
        "external-expanded-projects/angular-app",
        "external-expanded-projects/go-app",
        "external-expanded-projects/rails-app",
        "external-vanilla-projects/expense-tracker"
    ]

    print(f"{'PROJECT':<30} | {'STATES':<10} | {'COV %':<8} | {'ELEMS':<10} | {'COV %':<8}")
    print("-" * 80)
    
    for relative_path in projects:
        full_path = os.path.join(base_dir, relative_path)
        if os.path.exists(full_path):
            res = auditor.audit_project(full_path)
            if "error" in res:
                print(f"{relative_path[:28]:<30} | ERROR: {res['error']}")
            else:
                print(f"{res['project'][:28]:<30} | {res['json_states']}/{res['potential_states']:<5} | {res['state_coverage']:<8} | {res['json_elements']}/{res['potential_elements']:<5} | {res['element_coverage']:<8}")
