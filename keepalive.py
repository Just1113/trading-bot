from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import socket

logger = logging.getLogger(__name__)

class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bybit Trading Bot is running')
        
    def log_message(self, format, *args):
        # Suppress default logging
        logger.debug(f"HTTP request: {args[0]} {args[1]}")

class KeepAliveServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the keepalive server in a separate thread"""
        def run_server():
            try:
                self.server = HTTPServer((self.host, self.port), KeepAliveHandler)
                logger.info(f"🌐 Keepalive server started on {self.host}:{self.port}")
                self.server.serve_forever()
            except OSError as e:
                logger.error(f"❌ Failed to start keepalive server: {e}")
                # Try alternative port if 8080 is taken
                try:
                    self.port = 10000
                    self.server = HTTPServer((self.host, self.port), KeepAliveHandler)
                    logger.info(f"🌐 Keepalive server started on {self.host}:{self.port} (alternative)")
                    self.server.serve_forever()
                except Exception as e2:
                    logger.error(f"❌ Alternative port also failed: {e2}")
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the keepalive server"""
        if self.server:
            self.server.shutdown()
            logger.info("🛑 Keepalive server stopped")
