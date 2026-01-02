import os
import re
from .semantic_classifier import SemanticClassifier

class StaticAnalyzer:
    def __init__(self, target_dir, model_client=None):
        self.target_dir = target_dir
        # We ignore external model_client (LLM) and use internal Embedding Model
        print("Initializing Semantic Static Analyzer (Nano-CLaRa)...")
        self.classifier = SemanticClassifier() # Loads MiniLM

    def scan_files(self):
        files_to_scan = []
        for root, _, files in os.walk(self.target_dir):
            if "node_modules" in root or "venv" in root or ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith((".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".dart")):
                    files_to_scan.append(os.path.join(root, file))
        return files_to_scan

    def extract_functions(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        matches = []
        
        # JS/TS Logic
        if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
             # 1. [async] function name() { ... }
            pattern1 = r"(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{"
            for m in re.finditer(pattern1, content):
                matches.append({"name": m.group(1), "body": content[m.start():m.start()+400]})
            
            # 2. const name = ... => { ... }
            pattern2 = r"(const|let|var)\s+(\w+)\s*=\s*(\([^)]*\)|[^=]+)\s*=>\s*\{"
            for m in re.finditer(pattern2, content):
                matches.append({"name": m.group(2), "body": content[m.start():m.start()+400]})
                
        # Python Logic
        elif file_path.endswith(".py"):
            # def name(...):
            pattern_py = r"def\s+(\w+)\s*\("
            for m in re.finditer(pattern_py, content):
                 matches.append({"name": m.group(1), "body": content[m.start():m.start()+400]})

        # Java Logic
        elif file_path.endswith(".java"):
            # public void name() { }
            pattern_java = r"(?:public|private|protected)\s+(?:static\s+)?[\w<>]+\s+(\w+)\s*\("
            for m in re.finditer(pattern_java, content):
                 matches.append({"name": m.group(1), "body": content[m.start():m.start()+400]})

        # Dart Logic
        elif file_path.endswith(".dart"):
            # void name() { }
            pattern_dart = r"(?:void|Future<void>)\s+(\w+)\s*\("
            for m in re.finditer(pattern_dart, content):
                 matches.append({"name": m.group(1), "body": content[m.start():m.start()+400]})

        return matches

    def analyze(self):
        results = []
        js_files = self.scan_files()
        
        for js_file in js_files:
            print(f"  Scanning {js_file}...")
            funcs = self.extract_functions(js_file)
            for func in funcs:
                # Classify using Embedding Model
                # Optimization: Prepend function name to body to give it higher weight
                query = f"Function Name: {func['name']}. Code: {func['body']}"
                intent, score = self.classifier.classify(query)
                
                if intent:
                    print(f"    [MATCH] {func['name']} -> {intent} ({score:.2f})")
                    results.append({
                        "file": js_file,
                        "function": func['name'],
                        "intent": intent,
                        "type": "semantic_embedding"
                    })
                # No regex fallback! Strict semantic check.
        return results
