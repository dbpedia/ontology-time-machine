from proxy.http.parser import HttpParser, httpParserTypes
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from http.client import responses
from urllib.parse import urlparse
import logging
import requests


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


dbpedia_api = 'https://archivo.dbpedia.org/download'


ontology_types = [
    'application/turtle',               # Turtle (Terse RDF Triple Language)
    'text/turtle',                      # Turtle (alternative media type)
    'application/rdf+xml',              # RDF/XML
    'text/rdf+xml',                     # RDF/XML (alternative media type)
    'application/n-triples',            # N-Triples
    'text/n-triples',                   # N-Triples (alternative media type)
    'application/n-quads',              # N-Quads
    'text/n-quads',                     # N-Quads (alternative media type)
    'application/ld+json',              # JSON-LD (JSON for Linking Data)
    'application/trig',                 # TriG
    'application/sparql-results+json',  # SPARQL Query Results JSON
    'application/json',                 # JSON (alternative for SPARQL Query Results JSON)
    'application/sparql-results+xml',   # SPARQL Query Results XML
    'text/xml'                          # XML (alternative for SPARQL Query Results XML)
]


format_mapping = {
    'application/turtle': 'ttl',               # Turtle (Terse RDF Triple Language)
    'text/turtle': 'ttl',                      # Turtle (alternative media type)
}


passthrough_status_codes_http = [
    100, 101, 102, 103,
    200,
    300, 301, 302, 303, 304, 307, 308,
    451,
]


def check_if_archivo_ontology_requested(request):
    urls = []
    with open('ontologytimemachine/utils/archivo_ontologies.txt', 'r') as file:
        urls = [line.strip() for line in file]
    parsed_urls = [urlparse(url).netloc for url in urls]
    host_to_check = request.host.decode('utf-8')
    return host_to_check in parsed_urls


def mock_response_404():
    mock_response = requests.Response()
    mock_response.status_code = 404
    mock_response.url = 'https://example.com/resource-not-found'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>404 Not Found</h1></body></html>'
    return mock_response


def get_headers_and_expected_type(request):
    headers = {}
    expected_type = 'text/turtle'
    for k, v in request.headers.items():
        headers[v[0].decode('utf-8')] = v[1].decode('utf-8')
        if v[0].decode('utf-8') == 'Accept':
            expected_type = v[1].decode('utf-8')
    return headers, expected_type


def proxy_logic_http(request: HttpParser):
    logger.info('Start proxy logic in case of HTTP')
    response = failover_mode_http(request)
    return response


def failover_mode_http(request):
    headers, expected_type = get_headers_and_expected_type(request)
    logger.debug(headers)
    ontology = str(request._url)
    try:
        response = requests.get(url=ontology, headers=headers, timeout=5)
        logger.info(f' Status code: {response.status_code}')
        if response.history:
            logger.debug("Request was redirected")
            for resp in response.history:
                logger.debug(f"{resp.status_code}, {resp.url}")
            logger.debug(f"Final destination: {response.status_code}, {response.url}")
        else:
            logger.debug("Request was not redirected")
        content_type = response.headers.get('Content-Type')
        logger.debug(content_type)
        if response.status_code in passthrough_status_codes_http and content_type in ontology_types:
                logging.info(f'We found the right answer')
                return response
        else:
            logging.info('Content type is not as expected')
            return fetch_from_dbpedia_archivo_api(ontology)
    except (SSLError, Timeout, ConnectionError, RequestException) as e:
        #logger.error("Request failed:", e)
        return fetch_from_dbpedia_archivo_api(ontology)


def proxy_logic_https(parser):
    logger.info('Start proxy logic in case of HTTPS')
    response = failover_mode_https(parser)
    return response


def failover_mode_https(parser):
    code = int(parser.code.decode('utf-8'))
    if code >= 300 and code < 400:
        logger.info('Status code: 3XX')
        # Handle redirection
        redirect_url = parser.header(b'Location').decode('utf-8')
        logger.info(f'Redirected to {redirect_url}')
        response = get_data_from_redirect(redirect_url)
        return response


def get_data_from_redirect(ontology):
    try:
        response = requests.get(url=ontology, timeout=5)
        logger.info(response.status_code)
        if response.history:
            logger.debug("Request was redirected")
            for resp in response.history:
                logger.debug(f"{resp.status_code}, {resp.url}")
            logger.debug(f"Final destination: {response.status_code}, {response.url}")
        else:
            logger.debug("Request was not redirected")
        content_type = response.headers.get('Content-Type')
        if response.status_code in passthrough_status_codes_http:
                logging.info(f'We found the rights answer')
                return response
        else:
            logging.info('Content type is not as expected')
            return fetch_from_dbpedia_archivo_api(ontology)
    except (SSLError, Timeout, ConnectionError, RequestException) as e:
        #logger.error("Request failed:", e)
        return fetch_from_dbpedia_archivo_api(ontology)


def fetch_from_dbpedia_archivo_api(ontology: str, format: str = 'ttl'):
    dbpedia_url = f'{dbpedia_api}?o={ontology}&f={format}'
    try:
        logger.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
        response = requests.get(dbpedia_url, timeout=5)
        logger.debug('Response received')
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f'Exception occurred while fetching from DBpedia Archivo API: {e}')
        return mock_response_404()