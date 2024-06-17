from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.common.utils import build_http_response
import requests
import sys
import proxy
import logging
from typing import Any, Optional


IP = '0.0.0.0'
PORT = '8899'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    dbpedia_api = 'https://archivo.dbpedia.org/download'

    def __init__(
            self,
            *args: Any,
            **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

    def before_upstream_connection(self, request: HttpParser):
        return None


    def handle_client_request(self, request: HttpParser):
        # Check if the request is for google.com and provide a static response
        if b'google.com' in request.host:
            self.client.queue(
                build_http_response(
                    200, reason=b'OK', headers={
                        b'Content-Type': b'text/plain'
                    }, body=b'This is a static response for google.com'
                )
            )
            return None

        # Process other requests using proxy logic
        self.proxy_logic(request)
        return None


    def proxy_logic(self, request: HttpParser):
        self.failover_mode(request)
        self.time_based_mode(request)
        self.dependency_based_mode(request)


    def failover_mode(self, request):
        logging.info('Failover mode')
        ontology = str(request._url)
        logging.info(f'Ontology: {ontology}')
        
        try:
            response = requests.get(ontology)
            logging.info('Response received')
            logging.info(f'Response status code: {response.status_code}')
            content_type = response.headers.get('Content-Type', '')
            logging.info(f'Content type: {content_type}')

            if response.status_code == 200 and content_type in ['text/turtle']:
                self.client.queue(
                    build_http_response(
                        200, reason=b'OK', headers={
                            b'Content-Type': bytes(content_type, 'utf-8')
                        }, body=response.content
                    )
                )
            else:
                logging.info('Content type is not text/turtle or status code is not 200, fetching from DBpedia Archivo API')
                self.fetch_from_dbpedia_archivo_api(ontology)

        except requests.exceptions.RequestException as e:
            logging.info(f'Exception occurred: {e}')
            self.fetch_from_dbpedia_archivo_api(ontology)


    def time_based_mode(self, request):
        pass


    def dependency_based_mode(self, request):
        pass


    def fetch_from_dbpedia_archivo_api(self, ontology: str, format: str = 'ttl'):
        dbpedia_url = f'{self.dbpedia_api}?o={ontology}&f={format}'
        try:
            logging.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
            response = requests.get(dbpedia_url)
            logging.info('Response received')
            logging.info(f'Response status code: {response.status_code}')
            if response.status_code == 200:
                self.client.queue(
                    build_http_response(
                        200, reason=b'OK', headers={
                            b'Content-Type': b'text/turtle'
                        }, body=response.content
                    )
                )
            else:
                self.client.queue(
                    build_http_response(
                        404, reason=b'Not Found', body=b'Resource not found'
                    )
                )
        except requests.exceptions.RequestException as e:
            logging.info(f'Exception occurred while fetching from DBpedia Archivo API: {e}')
            self.client.queue(
                build_http_response(
                    404, reason=b'Not Found', body=b'Failed to fetch from DBpedia Archivo API'
                )
            )


    def handle_upstream_chunk(self, chunk: memoryview):
        return chunk


    def on_upstream_connection_close(self):
        pass


    def on_client_connection_close(self):
        pass


if __name__ == '__main__':
    sys.argv += [
        '--hostname', IP,
        '--port', PORT,
        '--plugins', __name__ + '.OntologyTimeMachinePlugin',
    ]
    proxy.main()
