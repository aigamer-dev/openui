import os
import re
from typing import List, Dict, Set, Optional
import networkx as nx

class ImportParser:
    """
    Parses source code to extract dependencies (imports/includes).
    Supports: Python, JavaScript/TypeScript, Go, Java, Ruby, PHP.
    """
    
    # Regex patterns for imports
    PATTERNS = {
        "python": [
            r"^\s*import\s+([\w\.]+)",           # import os
            r"^\s*from\s+([\w\.]+)\s+import",    # from modules.utils import x
        ],
        "javascript": [
            r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",  # import x from './y'
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",   # require('./y')
        ],
        "typescript": [
            r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ],
        "go": [
            r"import\s+\"([^\"]+)\"",             # import "fmt"
            r"import\s*\(\s*([\s\S]*?)\s*\)",     # import ( ... ) - multiline handling needed separately or via simpler single-line checks if formatted
        ],
        "java": [
            r"^\s*import\s+([\w\.]+);",           # import java.util.List;
        ],
        "ruby": [
            r"^\s*require\s+['\"]([^'\"]+)['\"]", # require 'json'
            r"^\s*require_relative\s+['\"]([^'\"]+)['\"]",
        ],
        "php": [
            r"^\s*(?:include|require|include_once|require_once)\s*['\"]([^'\"]+)['\"]",
        ]
    }

    EXT_TO_LANG = {
        ".py": "python",
        ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "typescript",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php"
    }

    @staticmethod
    def extract_imports(content: str, file_path: str) -> Set[str]:
        """
        Extracts raw import strings from file content based on extension.
        """
        ext = os.path.splitext(file_path)[1]
        lang = ImportParser.EXT_TO_LANG.get(ext)
        if not lang:
            return set()
            
        imports = set()
        
        # Special case for Go multiline block
        if lang == "go":
            # Find blocks first
            block_matches = re.findall(r"import\s*\(\s*([\s\S]*?)\s*\)", content)
            for block in block_matches:
                # Extract individual imports from block
                # Each line in block is like: _ "github.com/lib/pq" or "fmt"
                lines = block.split('\n')
                for line in lines:
                    match = re.search(r"\"([^\"]+)\"", line)
                    if match:
                        imports.add(match.group(1))
        
        patterns = ImportParser.PATTERNS.get(lang, [])
        for pattern in patterns:
            # For Python/JS/etc single line imports
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # match could be a tuple if regex has groups, usually specific capture
                val = match if isinstance(match, str) else match[0]
                imports.add(val.strip())
                
        return imports

class DependencyGraph:
    """
    Builds a directed graph of file dependencies.
    """
    def __init__(self, root_dir: str, file_paths: List[str]):
        self.root_dir = root_dir
        self.file_paths = set(file_paths) # Absolute paths
        self.graph = nx.DiGraph()
        self.rel_map = {os.path.relpath(p, root_dir): p for p in file_paths} # rel -> abs
        
        # Build initial nodes
        for fp in file_paths:
            self.graph.add_node(fp)

    def build(self):
        """
        Parses all files and creates edges.
        """
        for file_path in self.file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                raw_imports = ImportParser.extract_imports(content, file_path)
                resolved_paths = self._resolve_imports(file_path, raw_imports)
                
                for output_path in resolved_paths:
                    if output_path in self.file_paths:
                        # Edge from dependency TO dependent? 
                        # Usually we want "Process A then B if B depends on A" -> Topological Sort
                        # So Edge A -> B means A is needed by B vs A imports B.
                        # If A imports B, B should be processed first (mostly).
                        # Let's say Edge: A -> B means A imports B.
                        # Topo sort would give leaf nodes (no imports) first? No.
                        # If A imports B, we want to understand B first to understand A better.
                        # So we process dependencies first.
                        # Graph: A -> B (A depends on B).
                        self.graph.add_edge(file_path, output_path)
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")

    def _resolve_imports(self, source_file: str, raw_imports: Set[str]) -> Set[str]:
        """
        Resolves raw import strings to absolute file paths in the project.
        """
        resolved = set()
        source_dir = os.path.dirname(source_file)
        
        for imp in raw_imports:
            # 1. Relative paths (./ or ../) - Common in JS/TS/Ruby
            if imp.startswith('.') or imp.startswith('/'): # / is rare in imports but possible
                # Construct absolute path candidate
                if imp.startswith('.'):
                    candidate = os.path.abspath(os.path.join(source_dir, imp))
                else:
                    candidate = os.path.abspath(os.path.join(self.root_dir, imp.lstrip('/')))
                
                # Check extensions
                candidates = [candidate, candidate + '.js', candidate + '.ts', candidate + '.jsx', candidate + '.tsx']
                # For directories (index.js)
                candidates.extend([os.path.join(candidate, 'index.js'), os.path.join(candidate, 'index.ts')])
                
                for c in candidates:
                    if c in self.file_paths:
                        resolved.add(c)
                        break
            
            # 2. Python module style (modules.utils)
            else:
                # Try converting dots to slashes
                rel_path = imp.replace('.', '/')
                # Try relative to root (most common for top-level python execution)
                candidate_base = os.path.join(self.root_dir, rel_path)
                
                # Extensions to try
                exts = ['.py', '.java', '.go', '.rb'] # Java packages often map to folders, but imports imply classes
                candidates = [candidate_base + e for e in exts]
                # Also check if it's a folder (package) with __init__.py
                candidates.append(os.path.join(candidate_base, '__init__.py'))
                
                for c in candidates:
                    if c in self.file_paths:
                        resolved.add(c)
                        break
        
        return resolved

    def get_execution_order(self) -> List[str]:
        """
        Returns a list of files in topological order (dependencies first).
        If cycles exist, handle gracefully (break cycles or return valid partial).
        """
        try:
            # Reversed topological sort: if A -> B (A imports B), B comes first.
            # nx.topological_sort returns: node without incoming edges first? 
            # In A->B, B is dependency. A needs B.
            # We want to process B before A.
            # nx.topological_sort(G) returns nodes u,v... such that for every edge u->v, u comes before v.
            # If A->B, then A comes before B. This is opposite of what we want if we want dependencies first.
            # So we should reverse the result of topological_sort.
            ordered = list(nx.topological_sort(self.graph))
            return list(reversed(ordered))
        except nx.NetworkXUnfeasible:
            # Cycle detected. Fallback to standard list or attempt breaking cycles.
            # For now, return standard list but maybe prioritize non-cyclic nodes?
            # Simple fallback: Return standard list, RAG will still inspect all, just without optimal context order.
            print("Cycle detected in dependency graph. Falling back to default order.")
            return list(self.file_paths)
