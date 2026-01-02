import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

def load_model(model_name_key):
    """
    Loads a model and tokenizer from the local models directory.
    model_name_key: 'gemma-3' or 'xLAM'
    """
    # Map keys to directory names if they differ, or just use naming convention
    # In download_models.py we used "gemma-3" and "xLAM" as keys/dir names
    model_path = os.path.join(MODELS_DIR, model_name_key)
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Please run download_models.py first.")

    print(f"Loading {model_name_key} from {model_path}...")
    # Using CPU for stability on dev machine (4GB GPU is unstable with 4-bit)
    # Using bfloat16 to reduce RAM from ~16GB (FP32) to ~8GB.
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="cpu",
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True
    )
    return tokenizer, model

def generate_intent(tokenizer, model, code_snippet):
    """
    Generates semantic intent for a given code snippet using the loaded model.
    """
    prompt = f"""
    Analyze the following JavaScript function and determine its semantic intent (e.g., login, add_to_cart, checkout, search).
    Output ONLY the intent in snake_case.

    Code:
    ```javascript
    {code_snippet}
    ```

    Intent:
    """
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=20)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the intent portion (naive cleanup)
    intent = response.split("Intent:")[-1].strip().split("\n")[0].strip()
    return intent
