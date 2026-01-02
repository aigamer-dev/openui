import http.server
import socketserver
import threading
import time

class StaticServer:
    def __init__(self, root_dir, port=8000):
        self.root_dir = root_dir
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        handler = http.server.SimpleHTTPRequestHandler
        # Change directory to serve files from root_dir
        # We need to wrap this because SimpleHTTPRequestHandler serves cwd
        
        # Capture root_dir in a closure or partial
        from functools import partial
        Handler = partial(http.server.SimpleHTTPRequestHandler, directory=self.root_dir)
                
        self.httpd = socketserver.TCPServer(("", self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        print(f"Server started at http://localhost:{self.port} serving {self.root_dir}")
        time.sleep(1) # Give it a second

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("Server stopped.")
