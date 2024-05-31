from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

PORT = 8080

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if 'google.com' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'This is a static response for google.com')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Resource not found')

def run_proxy(server_class=HTTPServer, handler_class=ProxyHandler, port=PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting proxy on port {port}...')
    httpd.serve_forever()

def start_proxy():
    proxy_thread = threading.Thread(target=run_proxy)
    proxy_thread.daemon = True
    proxy_thread.start()
    return proxy_thread

if __name__ == '__main__':
    start_proxy().join()
