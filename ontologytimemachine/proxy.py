from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import requests

PORT = 8080

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # static usecase to check the Proxy is working
        if 'google.com' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'This is a static response for google.com')
        else:
            self.proxy_logic()

    def proxy_logic(self):
        self.failover_mode()
        self.time_based_mode()
        self.dependency_based_mode()

    def failover_mode(self):
        ontology = self.path[1:]
        try:
            response = requests.get(ontology)
            content_type = response.headers.get('Content-Type', '')

            if response.status_code == 200 and content_type in ['text/turtle']:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(response.content)
            else:
                self.fetch_from_dbpedia_archivo_api(ontology)

        except requests.exceptions.RequestException:
            self.fetch_from_dbpedia_archivo_api(ontology)

    def fetch_from_dbpedia_archivo_api(self, ontology):
        dbpedia_url = f'https://archivo.dbpedia.org/download?o={ontology}&f=ttl'
        print(dbpedia_url)
        try:
            response = requests.get(dbpedia_url)
            if response.status_code == 200:
                self.send_response(200)
                self.send_header('Content-type', 'text/turtle')
                self.end_headers()
                self.wfile.write(response.content)
            else:
                self.send_error(404, 'Resource not found')
        except requests.exceptions.RequestException:
            self.send_error(404, 'Resource not found')
    
    def time_based_mode(self):
        pass

    def dependency_based_mode(self):
        pass

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
