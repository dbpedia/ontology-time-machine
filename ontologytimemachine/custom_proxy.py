from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser, httpParserTypes
from proxy.common.utils import build_http_response
from proxy.http.methods import HttpMethods
from ontologytimemachine.utils.utils import proxy_logic_http, proxy_logic_https
from ontologytimemachine.utils.utils import check_if_archivo_ontology_requested
from ontologytimemachine.utils.utils import get_headers_and_expected_type
from ontologytimemachine.utils.utils import get_ontology_from_request
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from http.client import responses
import proxy
import sys
import requests
import logging


IP = '0.0.0.0'
PORT = '8899'


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def before_upstream_connection(self, request: HttpParser):
        logger.debug('Before upstream')
        logger.debug(request.method)
        scheme = 'https' if request.method == b'CONNECT' else 'http'
        if scheme == 'https':
            logger.debug('The request is HTTPS, forward as it is')
            logger.debug(f'Request host: {request.host}')
            logger.debug(f'Request path: {request.path}')
            return request

        ontology_request = check_if_archivo_ontology_requested(request)
        if ontology_request:
            logger.debug('The request is for an ontology')
            try:
                ontology_url = str(request._url)
                headers, _ = get_headers_and_expected_type(request)
                response = requests.get(ontology_url, headers=headers, timeout=5)
                if response.status_code == 502:
                    logger.error('Received 502 Bad Gateway error')
                    response = proxy_logic_http(request)
                    logger.debug('Queue response')
                    self.queue_response(response)
                    return None
                else:
                    logger.debug('The request is correct')
                    return request
            except (SSLError, Timeout, ConnectionError, RequestException) as e:
                logger.error(f'Network-related exception occurred {e}')
                response = proxy_logic_http(request)
                logger.debug('Queue response')
                self.queue_response(response)
                return None
        return request


    def handle_client_request(self, request: HttpParser):
        logger.debug('HTTP call')

        logger.debug(request.method)
        scheme = 'https' if request.method == b'CONNECT' else 'http'
        if scheme == 'https':
            logger.debug('The request is HTTPS, forward as it is')
            return request

        ontology_request = check_if_archivo_ontology_requested(request)
        if not ontology_request:
            logger.info('No ontology is asked, forward original request')
            return request   

        logger.debug('Call proxy logic')
        response = proxy_logic_http(request)
        self.queue_response(response)

        return None
    

    def handle_upstream_chunk(self, chunk: memoryview):
        logger.info('HTTPS call')

        try:
            # Parse the HTTP response to handle different cases
            parser = HttpParser(httpParserTypes.RESPONSE_PARSER)
            parser.parse(memoryview(chunk))
            
            #chunk_bytes = chunk.tobytes()
            #chunk_str = chunk_bytes.decode('utf-8')
            #logger.debug(f'Decoded chunk: {chunk_str}')

            code = int(parser.code.decode('utf-8'))
            if code >= 100 and code < 200:
                return chunk
            elif code >= 201 and code <= 204:
                return chunk
            elif code == 451:
                return chunk
            else:
                response = proxy_logic_https(parser)
                logger.debug('Queue response')
                self.queue_response(response)
                return None
        except UnicodeDecodeError:
            logger.warning('Received non-text chunk, cannot decode')
        except Exception as e:
            logger.error(f'Exception occurred while handling upstream chunk: {e}')
        
        return chunk


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