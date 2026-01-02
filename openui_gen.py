import argparse
import os
import json
import sys
import shutil
# Add current directory to path so modules can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.server_utils import StaticServer
from modules.runtime_crawler import RuntimeCrawler
from modules.static_analyzer import StaticAnalyzer
from modules.codebase_rag import CodebaseRAG
# from modules.model_loader import load_model # Import inside to avoid load

def main():
    parser = argparse.ArgumentParser(description="OpenUI Auto-Generator")
    parser.add_argument("--target", required=True, help="Target directory (relative to current or absolute)")
    parser.add_argument("--model", default="gemma-3", help="Model key (gemma-3 or xLAM)")
    parser.add_argument("--port", type=int, default=8000, help="Port for local server")
    parser.add_argument("--lite", action="store_true", help="Run in Lite mode (no AI model) for low-spec machines")
    parser.add_argument("--external-url", help="URL of an already running server (skips local static server)")
    parser.add_argument("--rag", action="store_true", help="Use Codebase RAG pipeline (Static Code Analysis)")
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target)
    if not os.path.exists(target_dir):
        print(f"Error: Target directory {target_dir} does not exist.")
        sys.exit(1)
        
    if args.rag:
        print(f"--- Phase 1: Codebase RAG Pipeline ---")
        rag_engine = CodebaseRAG(target_dir)
        rag_engine.ingest()
        schema_data = rag_engine.query_ui_schema()
        
        # Save output
        output_path = os.path.join(target_dir, "agent-ui.json")
        with open(output_path, "w", encoding="utf-8") as f:
            # For now, we save the 'meta' info since we lack a live 7B model connection in this env
            # In a real run, schema_data would be the LLM JSON.
            json.dump(schema_data, f, indent=2)
        print(f"RAG Pipeline Complete. Output saved to {output_path}")
        return

    print(f"--- Phase 1: Setup (Nano-CLaRa) ---")
    # No extensive model loading here, StaticAnalyzer handles the semantic micro-model.
    # We keep the structure for compatibility.

    print(f"--- Phase 2: Runtime Analysis ---")
    
    start_url = ""
    server = None
    
    if args.external_url:
        print(f"Using External Server at: {args.external_url}")
        start_url = args.external_url
    else:
        # Start Server
        server = StaticServer(target_dir, port=args.port)
        server.start()
        start_url = f"http://localhost:{args.port}/index.html"
    
    # Crawl
    crawler = RuntimeCrawler(start_url)
    runtime_data = crawler.crawl()
    print(f"Runtime Deep Crawl: Found {len(runtime_data)} unique elements.")
    
    if server:
        server.stop()

    print(f"--- Phase 3: Static Analysis ---")
    # Initialize Semantic Analyzer (Uses all-MiniLM-L6-v2)
    # We pass None for model_client as we don't use the external Gemma anymore.
    analyzer = StaticAnalyzer(target_dir, model_client=None) 
    static_data = analyzer.analyze()
    print(f"Static analysis: Analyzed {len(static_data)} functions.")

    print(f"--- Phase 4: Merge & Output ---")
    schema = merge_data(runtime_data, static_data)
    
    output_path = os.path.join(target_dir, "agent-ui.json")
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"Success! Generated {output_path}")

def merge_data(runtime, static):
    """
    Merges runtime elements with static intent analysis.
    """
    # Group runtime elements by view_id
    states_map = {}
    
    intent_map = {item['function']: item['intent'] for item in static}
    
    for el in runtime:
        el_data = el.copy()
        onclick = el.get('onclick', '')
        intent = "unknown"
        
        if onclick:
            func_name = onclick.split('(')[0].strip()
            if func_name in intent_map:
                intent = intent_map[func_name]
            else:
                intent = f"call_{func_name}"
        
        el_data['semantic_intent'] = intent
        
        view_id = el_data.get('view_id', 'unknown_view')
        if view_id not in states_map:
            states_map[view_id] = []
        states_map[view_id].append(el_data)

    # Construct States List
    output_states = []
    for vid, elements in states_map.items():
        output_states.append({
            "id": vid,
            "description": f"Auto-detected state: {vid}",
            "elements": elements
        })

    return {
        "meta": {
            "generator": "OpenUI-Gen-CLI (Deep Crawler)",
            "version": "1.1"
        },
        "states": output_states,
        "raw_intents": static
    }

if __name__ == "__main__":
    main()
