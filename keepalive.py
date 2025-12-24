from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is alive')
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

class KeepAliveServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the keepalive server in a separate thread"""
        def run_server():
            self.server = HTTPServer((self.host, self.port), KeepAliveHandler)
            logger.info(f"Keepalive server started on {self.host}:{self.port}")
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the keepalive server"""
        if self.server:
            self.server.shutdown()
            logger.info("Keepalive server stopped")
