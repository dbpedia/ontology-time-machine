from proxy.http.parser import HttpParser, httpParserTypes
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from http.client import responses
from urllib.parse import urlparse
import logging
import requests


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


dbpedia_api = 'https://archivo.dbpedia.org/download'


passthrough_status_codes_http = [
    100, 101, 102, 103,
    200,
    300, 301, 302, 303, 304, 307, 308,
    451,
]


def check_if_archivo_ontology_requested(request):
    with open('ontologytimemachine/utils/archivo_ontologies.txt', 'r') as file:
        urls = [line.strip() for line in file]
    parsed_urls = [(urlparse(url).netloc, urlparse(url).path) for url in urls]

    _, request_host, request_path = get_ontology_from_request(request)
    for host, path in parsed_urls:
        if request_host == host and request_path.startswith(path):
            return True
    return False


def mock_response_404():
    mock_response = requests.Response()
    mock_response.status_code = 404
    mock_response.url = 'https://example.com/resource-not-found'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>404 Not Found</h1></body></html>'
    return mock_response


def get_headers_and_expected_type(request):
    headers = {}
    for k, v in request.headers.items():
        headers[v[0].decode('utf-8')] = v[1].decode('utf-8')
    return headers


def get_ontology_from_request(request):
    logger.debug('Get ontology from request')
    if (request.method == b'GET' or request.method == b'HEAD') and not request.host:
        for k, v in request.headers.items():
            if v[0].decode('utf-8') == 'Host':
                print('host found')
                host = v[1].decode('utf-8')
                path = request.path.decode('utf-8')
        ontology = 'https://' + host + request.path.decode('utf-8')
    else:
        host = request.host.decode('utf-8')
        path = request.path.decode('utf-8')
        ontology = str(request._url)
    logger.debug(f'Ontology: {ontology}')
    return ontology, host, path

def proxy_logic(request: HttpParser):
    logger.info('Proxy has to intervene')
    response = failover_mode(request)
    return response


def failover_mode(request):
    headers = get_headers_and_expected_type(request)
    logger.info('Failover mode')

    ontology, _, _ = get_ontology_from_request(request)
    try:
        response = requests.get(url=ontology, headers=headers, timeout=5)
        if response.history:
            logger.debug("Request was redirected")
            for resp in response.history:
                logger.debug(f"{resp.status_code}, {resp.url}")
            logger.debug(f"Final destination: {response.status_code}, {response.url}")
        else:
            logger.debug("Request was not redirected")
        content_type = response.headers.get('Content-Type')
        logger.debug(content_type)
        if response.status_code in passthrough_status_codes_http:
                return response
        else:
            logging.info(f'Status code: {response.status_code}')
            return fetch_from_dbpedia_archivo_api(ontology)
    except (SSLError, Timeout, ConnectionError, RequestException) as e:
        return fetch_from_dbpedia_archivo_api(ontology)


def fetch_from_dbpedia_archivo_api(ontology: str, format: str = 'ttl'):
    dbpedia_url = f'{dbpedia_api}?o={ontology}&f={format}'
    try:
        logger.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
        response = requests.get(dbpedia_url, timeout=5)
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f'Exception occurred while fetching from DBpedia Archivo API: {e}')
        return mock_response_404()