from playwright.sync_api import sync_playwright
import hashlib
import time

class RuntimeCrawler:
    def __init__(self, start_url):
        self.start_url = start_url
        self.visited_states = set()
        self.all_elements = {} # Key: specific signature, Value: Element Dict
        self.max_depth = 3
        self.max_actions = 10 # Safety limit per page

    def _get_dom_hash(self, page):
        """Generates a hash of the structural DOM (ignoring specific text values) to identify unique states."""
        # Simple script to get tag structure
        structure = page.evaluate("""() => {
            function serialize(el) {
                if (!el) return "";
                let str = el.tagName.toLowerCase();
                if (el.id) str += "#" + el.id;
                let cls = el.className;
                if (cls && typeof cls !== 'string' && cls.baseVal) cls = cls.baseVal; // Handle SVG
                if (cls && typeof cls === 'string') str += "." + cls.split(" ").join(".");
                let children = "";
                for (let child of el.children) {
                    children += serialize(child);
                }
                return str + children;
            }
            return serialize(document.body);
        }""")
        return hashlib.md5(structure.encode()).hexdigest()

    def _extract_elements(self, page, view_id="main"):
        selector = "button, input, a[href], select, textarea, [onclick]"
        elements = page.query_selector_all(selector)
        
        extracted = []
        for el in elements:
            try:
                if not el.is_visible(): continue
                
                tag_name = el.evaluate("el => el.tagName.toLowerCase()")
                el_id = el.get_attribute("id") or ""
                el_class = el.get_attribute("class") or ""
                
                # Unique Signature for deduping
                sig = f"{tag_name}#{el_id}.{el_class}"
                
                # Store if new
                if sig not in self.all_elements:
                    el_text = el.inner_text().strip() if tag_name != "input" else ""
                    el_value = el.evaluate("el => el.value") if tag_name in ["input", "textarea", "select"] else ""
                    el_onclick = el.get_attribute("onclick") or ""
                    
                    data = {
                        "tag": tag_name,
                        "id": el_id,
                        "class": el_class,
                        "text": el_text[:50],
                        "value": el_value,
                        "onclick": el_onclick,
                        "view_id": f"state_{view_id}",
                        "type": "runtime_element"
                    }
                    self.all_elements[sig] = data
                    extracted.append(el)
            except Exception:
                continue
        return extracted

    def crawl(self):
        print(f"🕷️ Deep Crawl Starting at {self.start_url}...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Streamlit/SPAs keep sockets open, preventing networkidle.
                # 'domcontentloaded' is safer for general crawling.
                page.goto(self.start_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000) # Grace period for JS rendering
            except Exception as e:
                print(f"Failed to load: {e}")
                return []

            # BFS Queue: (ActionLambda, Depth)
            # Initial State is just "Do nothing"
            queue = [(None, 0)] 
            
            while queue:
                action, depth = queue.pop(0)
                
                # Perform Action
                if action:
                    try:
                        print(f"  Doing Action (Depth {depth})...")
                        action(page)
                        page.wait_for_timeout(500) # Wait for animation/js
                    except Exception as e:
                        print(f"  Action failed: {e}")
                        continue

                # Check State
                current_hash = self._get_dom_hash(page)
                if current_hash in self.visited_states:
                    continue
                
                self.visited_states.add(current_hash)
                print(f"  📍 New State Discovered! (Hash: {current_hash[:6]})")

                # Extract Elements from this new state
                interactive_els = self._extract_elements(page, view_id=current_hash[:6])
                
                if depth >= self.max_depth:
                    continue

                # Plan Future Actions from this state
                # Heuristic: Find first 3 inputs and first 3 buttons to click
                actions_taken = 0
                
                # Input Filling
                inputs = [el for el in interactive_els if el.evaluate("el => el.tagName === 'INPUT'")]
                for inp in inputs:
                    if actions_taken >= self.max_actions: break
                    try:
                        # Heuristic value
                        i_id = (inp.get_attribute("id") or "").lower()
                        val = "test"
                        if "email" in i_id: val = "test@example.com"
                        if "todo" in i_id: val = "Buy Milk"
                        
                        # Define Action
                        def perform_fill(p, selector=f"#{inp.get_attribute('id')}", v=val):
                            p.fill(selector, v)
                            p.press(selector, "Enter")
                        
                        if inp.get_attribute("id"): # Only interactive if it has ID for selector stability
                            queue.append((perform_fill, depth + 1))
                            actions_taken += 1
                    except: pass
                
                # Button Clicking
                buttons = [el for el in interactive_els if el.evaluate("el => el.tagName === 'BUTTON' || el.tagName === 'A'")]
                for btn in buttons:
                     if actions_taken >= self.max_actions: break
                     try:
                         # Use robust selector if possible, else skip
                         tag = btn.evaluate("el => el.tagName.toLowerCase()")
                         t_id = btn.get_attribute("id")
                         t_cls = btn.get_attribute("class")
                         
                         selector = ""
                         if t_id: selector = f"#{t_id}"
                         elif t_cls: selector = f".{t_cls.split(' ')[0]}"
                         
                         if selector:
                             def perform_click(p, s=selector):
                                 p.click(s)
                             queue.append((perform_click, depth + 1))
                             actions_taken += 1
                     except: pass
            
            browser.close()
        
        print(f"✅ Crawl Found {len(self.all_elements)} Unique Elements across {len(self.visited_states)} States.")
        return list(self.all_elements.values())
