from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.common.utils import build_http_response
from ontologytimemachine.utils.utils import parse_arguments
from ontologytimemachine.utils.mock_responses import mock_response_403
from ontologytimemachine.proxy_wrapper import HttpRequestWrapper
from ontologytimemachine.utils.proxy_logic import proxy_logic, is_archivo_ontology_request
from ontologytimemachine.utils.proxy_logic import do_deny_request_due_non_archivo_ontology_uri
from ontologytimemachine.utils.proxy_logic import if_intercept_host
from http.client import responses
import proxy
import sys
import logging


IP = '0.0.0.0'
PORT = '8899'

config = ({'format': 'turtle', 'precedence': 'enforcedPriority', 'patchAcceptUpstream': False}, 'originalFailoverLiveLatest', False, 'all', False, True, None, None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        logger.info('Init')
        super().__init__(*args, **kwargs)
        (self.ontoFormat, self.ontoVersion, self.restrictedAccess,
         self.httpsInterception, self.disableRemovingRedirects, 
         self.forward_headers, self.timestamp, self.manifest) = config

    def before_upstream_connection(self, request: HttpParser):
        logger.info('Before upstream connection hook')
        logger.info(f'Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}')
        wrapped_request = HttpRequestWrapper(request)

        if wrapped_request.is_connect_request():
            logger.info(f'HTTPS interception mode: {self.httpsInterception}')
            # Only intercept if interception is enabled
            # Move this to the utils
            if if_intercept_host(self.httpsInterception):
                logger.info('HTTPS interception is on, forwardig the request')
                return request
            else:
                logger.info('HTTPS interception is turned off')
                return None

        # If only ontology mode, return None in all other cases
        if do_deny_request_due_non_archivo_ontology_uri(wrapped_request, self.restrictedAccess):
            logger.warning('Request denied: not an ontology request and only ontologies mode is enabled')
            self.queue_response(mock_response_403)
            return None
        
        if is_archivo_ontology_request(wrapped_request):
            logger.debug('The request is for an ontology')
            response = proxy_logic(wrapped_request, self.ontoFormat, self.ontoVersion, self.disableRemovingRedirects, self.timestamp, self.manifest)
            self.queue_response(response)
            return None

        return request

    def handle_client_request(self, request: HttpParser):
        logger.info('Handle client request hook')
        logger.info(f'Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}')

        wrapped_request = HttpRequestWrapper(request)
        if wrapped_request.is_connect_request():
            return request

        if not do_deny_request_due_non_archivo_ontology_uri(wrapped_request):
            logger.info('The requested IRI is not part of DBpedia Archivo')
            return request   

        response = proxy_logic(wrapped_request, self.ontoFormat, self.ontoVersion, self.disableRemovingRedirects, self.timestamp, self.manifest)
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

    config = parse_arguments()

    sys.argv = [sys.argv[0]]

    # check it https interception is enabled
    if config[3] != 'none':
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