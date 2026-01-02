import os
import torch
from sentence_transformers import SentenceTransformer, util

class SemanticClassifier:
    def __init__(self, model_path=None, threshold=0.25):
        self.threshold = threshold
        
        # Default intent definitions - "The Intent Store"
        # Maps Canonical Intent -> Natural Language Description
        self.intent_descriptions = {
            "login": "User authentication, log in, sign in, handle credentials, submit login form, auth, password, user access",
            "logout": "User log out, sign out, clear session, disconnect, unauthenticate",
            "add_to_cart": "Add item to shopping cart, put in basket, purchase list, buy item, add product",
            "checkout": "Process payment, finalize order, checkout flow, shipping address, pay now, credit card, transaction, purchase completed",
            "search": "Search for items, query database, find products, filter results, unique query",
            "send_email": "Send email, compose message, dispatch mail, submit contact form",
            "cancel": "Cancel action, close modal, dismiss dialog, abort, hide element",
            "navigate": "Go to page, redirect to url, load view, switch screen, open modal, show element, display block",
            "delete": "Remove item, delete record, trash, destroy"
        }
        
        # Load Model
        if model_path is None:
            # Fallback to default location relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base_dir, 'models', 'semantic', 'all-MiniLM-L6-v2')
            
        print(f"Loading Semantic Micro-Model from: {model_path}")
        # Try loading local, else download (safety fallback)
        try:
            self.model = SentenceTransformer(model_path)
        except:
            print("Local model not found, downloading default...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
        # Pre-compute intent embeddings
        self.intent_keys = list(self.intent_descriptions.keys())
        self.intent_texts = list(self.intent_descriptions.values())
        self.intent_embeddings = self.model.encode(self.intent_texts, convert_to_tensor=True)
        print("Intent Store initialized.")

    def classify(self, code_snippet):
        """
        Classifies a code snippet into one of the canonical intents.
        Returns: (intent, score) or (None, 0.0) if below threshold.
        """
        # Embed the code snippet
        # We assume function names and bodies contain semantic meaning.
        code_embedding = self.model.encode(code_snippet, convert_to_tensor=True)

        # Compute Cosine Similarity
        cosine_scores = util.cos_sim(code_embedding, self.intent_embeddings)[0]

        # Find best match
        best_score_idx = torch.argmax(cosine_scores).item()
        best_score = cosine_scores[best_score_idx].item()
        best_intent = self.intent_keys[best_score_idx]

        # Debug print
        # print(f"Snippet: {code_snippet[:30]}... -> {best_intent} ({best_score:.2f})")

        if best_score >= self.threshold:
            return best_intent, best_score
        else:
            return None, 0.0

if __name__ == "__main__":
    # Quick Test
    classifier = SemanticClassifier()
    test_cases = [
        "function handleLogin() { auth.user(user, pass); }",
        "const onCheckout = () => { payment.process(); }",
        "function doSearch(query) { db.find(query); }",
        "function randomStuff() { console.log('hello'); }"
    ]
    
    print("\n--- Diagnostic Test ---")
    for code in test_cases:
        intent, score = classifier.classify(code)
        print(f"Code: '{code}'\n  -> Intent: {intent} (Score: {score:.4f})\n")
