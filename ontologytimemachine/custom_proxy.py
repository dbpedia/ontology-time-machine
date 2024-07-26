from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser, httpParserTypes
from proxy.common.utils import build_http_response
from proxy.http.methods import HttpMethods
from ontologytimemachine.utils.utils import proxy_logic, parse_arguments
from ontologytimemachine.utils.utils import check_if_archivo_ontology_requested
from ontologytimemachine.utils.mock_responses import mock_response_403
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from http.client import responses
import proxy
import sys
import logging


IP = '0.0.0.0'
PORT = '8899'


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        (self.ontoFormat, self.ontoVersion, self.only_ontologies,
         self.https_intercept, self.inspect_redirects, self.forward_headers,
         self.subject_binary_search_threshold) = parse_arguments()


    def before_upstream_connection(self, request: HttpParser):
        logger.info('Before upstream connection hook')
        logger.info(f'Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}')

        if request.method == b'CONNECT':
            logger.info(f'HTTPS interception mode: {self.https_intercept}')
            # Only intercept if interception is enabled
            if self.https_intercept in ['all', 'archivo']:
                return request
            else:
                return None
            

        ontology_request = check_if_archivo_ontology_requested(request)
        # If only ontology mode, return None in all other cases
        if self.only_ontologies and not ontology_request:
            logger.warning('Request denied: not an ontology request and only ontologies mode is enabled')
            self.queue_response(mock_response_403)
            return None
        
        if ontology_request:
            logger.debug('The request is for an ontology')
            response = proxy_logic(request, self.ontoFormat, self.ontoVersion)
            self.queue_response(response)
            return None
        return request


    def handle_client_request(self, request: HttpParser):
        logger.info('Handle client request hook')
        logger.info(f'Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}')

        logger.debug(request.method)
        if request.method == b'CONNECT':
            return request

        ontology_request = check_if_archivo_ontology_requested(request)
        if not ontology_request:
            logger.info('The requested IRI is not part of DBpedia Archivo')
            return request   

        response = proxy_logic(request, self.ontoFormat, self.ontoVersion)
        self.queue_response(response)

        return None
    

    def handle_upstream_chunk(self, chunk: memoryview):
        return chunk


    def queue_response(self, response):
        self.client.queue(
            build_http_response(
                response.status_code, 
                reason=bytes(responses[response.status_code], 'utf-8'), 
                headers={
                    b'Content-Type': bytes(response.headers.get('Content-Type'), 'utf-8')
                }, 
                body=response.content
            )
        )


if __name__ == '__main__':

    sys.argv += [
        '--ca-key-file', 'ca-key.pem',
        '--ca-cert-file', 'ca-cert.pem',
        '--ca-signing-key-file', 'ca-signing-key.pem',
    ]
    sys.argv += [
        '--hostname', IP,
        '--port', PORT,
        '--plugins', __name__ + '.OntologyTimeMachinePlugin'
    ]

    logger.info("Starting OntologyTimeMachineProxy server...")
    proxy.main()