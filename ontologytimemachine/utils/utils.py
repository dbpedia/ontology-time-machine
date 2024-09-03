from proxy.http.parser import HttpParser, httpParserTypes
from requests.exceptions import SSLError, Timeout, ConnectionError, RequestException
from ontologytimemachine.utils.mock_responses import mock_response_403, mock_response_404, mock_response_500, mock_response_200
from http.client import responses
from urllib.parse import urlparse
import logging
import requests
import argparse
import rdflib
import mimetypes


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


dbpedia_api = 'https://archivo.dbpedia.org/download'


passthrough_status_codes_http = [
    100, 101, 102, 103,
    200,
    300, 301, 302, 303, 304, 307, 308,
    451,
]

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process ontology format and version.')


    # Defining ontoFormat argument with nested options
    parser.add_argument('--ontoFormat', type=str, choices=['turtle', 'ntriples', 'rdfxml', 'htmldocu'],
                        default='turtle', help='Format of the ontology: turtle, ntriples, rdfxml, htmldocu')

    parser.add_argument('--ontoPrecedence', type=str, choices=['default', 'enforcedPriority', 'always'],
                        default='enforcedPriority', help='Precedence of the ontology: default, enforcedPriority, always')

    parser.add_argument('--patchAcceptUpstream', type=bool, default=False,
                        help='Defines if the Accept Header is patched upstream in original mode.')

    # Defining ontoVersion argument
    parser.add_argument('--ontoVersion', type=str, choices=['original', 'originalFailoverLive', 'originalFailoverArchivoMonitor', 
                                                            'latestArchive', 'timestampArchive', 'dependencyManifest'],
                        default='originalFailoverLive', help='Version of the ontology: original, originalFailoverLive, originalFailoverArchivoMonitor, latestArchive, timestampArchive, dependencyManifest')

    # Enable/disable mode to only proxy requests to ontologies
    parser.add_argument('--onlyOntologies', type=bool, default=False,
                        help='Enable/disable mode to only proxy requests to ontologies.')

    # Enable HTTPS interception for specific domains
    parser.add_argument('--httpsIntercept', type=str, choices=['none', 'archivo', 'all', 'listfilename'],
                        default='all', help='Enable HTTPS interception for specific domains: none, archivo, all, listfilename.')

    # Enable/disable inspecting or removing redirects
    parser.add_argument('--inspectRedirects', type=bool, default=True,
                        help='Enable/disable inspecting or removing redirects.')

    # Enable/disable proxy forward headers
    parser.add_argument('--forwardHeaders', type=bool, default=True,
                        help='Enable/disable proxy forward headers.')

    # SubjectBinarySearchThreshold
    parser.add_argument('--subjectBinarySearchThreshold', type=int, default=100,
                        help='SubjectBinarySearchThreshold value.')

    args  = parser.parse_args()
    
    ontoFormat = {
        'format': args.ontoFormat,
        'precedence': args.ontoPrecedence,
        'patchAcceptUpstream': args.patchAcceptUpstream
    }

    logger.info(f'Ontology Format: {ontoFormat}')
    logger.info(f'Ontology Version: {args.ontoVersion}')
    #logger.info(f'Only Ontologies Mode: {args.onlyOntologies}')
    #logger.info(f'HTTPS Interception: {args.httpsIntercept}')
    #logger.info(f'Inspect Redirects: {args.inspectRedirects}')
    #logger.info(f'Forward Headers: {args.forwardHeaders}')
    #logger.info(f'Subject Binary Search Threshold: {args.subjectBinarySearchThreshold}')
    return ontoFormat, args.ontoVersion, args.onlyOntologies, args.httpsIntercept, args.inspectRedirects, args.forwardHeaders, args.subjectBinarySearchThreshold


def check_if_archivo_ontology_requested(request):
    with open('ontologytimemachine/utils/archivo_ontologies.txt', 'r') as file:
        urls = [line.strip() for line in file]
    parsed_urls = [(urlparse(url).netloc, urlparse(url).path) for url in urls]

    _, request_host, request_path = get_ontology_from_request(request)
    for host, path in parsed_urls:
        if request_host == host and request_path.startswith(path):
            return True
    return False


def get_headers(request):
    headers = {}
    for k, v in request.headers.items():
        headers[v[0].decode('utf-8')] = v[1].decode('utf-8')
    return headers


def get_ontology_from_request(request):
    logger.info('Get ontology from request')
    print(f'Request protocol: {request.protocol}')
    print(f'Request host: {request.host}')
    print(f'Request _url: {request._url}')
    print(f'Request path: {request.path}')
    if (request.method == b'GET' or request.method == b'HEAD') and not request.host:
        for k, v in request.headers.items():
            if v[0].decode('utf-8') == 'Host':
                host = v[1].decode('utf-8')
                path = request.path.decode('utf-8')
        ontology = 'https://' + host + path
    else:
        host = request.host.decode('utf-8')
        path = request.path.decode('utf-8')
        ontology = str(request._url)
    logger.info(f'Ontology: {ontology}')
    return ontology, host, path


def get_mime_type(format='turtle'):
    # Define a mapping of formats to MIME types
    format_to_mime = {
        'turtle': 'text/turtle',
        'ntriples': 'application/n-triples',
        'rdfxml': 'application/rdf+xml',
        'htmldocu': 'text/html'
    }
    
    # Return the MIME type based on the format or use a generic default
    return format_to_mime.get(format, 'text/turtle')


def set_onto_format_headers(request, ontoFormat, ontoVersion):
    logger.info(f'Setting headers based on ontoFormat: {ontoFormat}')

    # Determine the correct MIME type for the format
    mime_type = get_mime_type(ontoFormat['format'])
    logger.info(f'Requested mimetype: {mime_type}')

    # Check the precedence and update the 'Accept' header if necessary
    if ontoFormat['precedence'] in ['always'] or \
       (ontoFormat['precedence'] == 'default' and request.headers[b'accept'][1] == b'*/*') or \
        request.headers[b'accept'][1] == b'*/*':
        # Needed to make sure the accept header is define
        # TODO: Clean up the conditions
        request.headers[b'accept'] = (b'Accept', mime_type.encode('utf-8'))
        logger.info(f'Accept header set to: {request.headers[b"accept"][1]}')

    # Check if patchAcceptUpstream is true and ontoVersion is 'original'
    if ontoFormat['patchAcceptUpstream'] and ontoVersion == 'original':
        request.headers[b'accept'] = (b'Accept', mime_type.encode('utf-8'))
        logger.info(f'Accept header patched upstream: {request.headers[b"accept"][1]}')


def proxy_logic(request: HttpParser, ontoFormat, ontoVersion):
    logger.info('Proxy has to intervene')
    set_onto_format_headers(request, ontoFormat, ontoVersion)
    headers = get_headers(request)
    logger.info(f'Updated headers: {request.headers}')
    ontology, _, _ = get_ontology_from_request(request)
    if ontoVersion == 'original':
        response = fetch_original(ontology, headers)
    elif ontoVersion == 'originalFailoverLive':
        response = fetch_failover(ontology, headers, live=True)
    elif ontoVersion == 'originalFailoverArchivoontoVersionMonitor':
        response = fetch_failover(ontology, headers, monitor=True)
    elif ontoVersion == 'latestArchive':
        response = fetch_latest_archive(ontology, headers)
    elif ontoVersion == 'timestampArchive':
        response = fetch_timestamp_archive(ontology, headers)
    elif ontoVersion == 'dependencyManifest':
        response = fetch_dependency_manifest(ontology, headers)

    return response


# Fetch from the original source, no matter what
def fetch_original(ontology, headers):
    logger.info(f'Fetching original ontology from URL: {ontology}')
    try:
        response = requests.get(url=ontology, headers=headers, timeout=5)
        logger.info('Successfully fetched original ontology')
        return response
    except Exception as e:
        logger.error(f'Error fetching original ontology: {e}')
        return mock_response_500()


# Failover mode
def fetch_failover(ontology, headers, live=False, monitor=False):
    try:
        logger.info(f'Fetching original ontology with failover from URL: {ontology}')
        response = requests.get(url=ontology, headers=headers, timeout=5)
        logger.info('Successfully fetched original ontology')
        requested_mime_type = headers.get('Accept', None)  # Assuming you set the requested MIME type in the 'Accept' header
        response_mime_type = response.headers.get('Content-Type', '').split(';')[0]
        logger.info(f'Requested mimetype: {requested_mime_type}')
        logger.info(f'Response mimetype: {response_mime_type}')
        if response.status_code in passthrough_status_codes_http and requested_mime_type == response_mime_type:
                return response
        else:
            logging.info(f'Status code: {response.status_code}')
            return fetch_from_dbpedia_archivo_api(ontology, headers)
    except Exception as e:
        logger.error(f'Error fetching original ontology: {e}')
        if live:
            logger.info('Attempting to fetch live version due to failover')
            return fetch_from_dbpedia_archivo_api(ontology, headers)
        elif monitor:
            logger.info('Attempting to fetch archive monitor version due to failover')
            # TODO
            return mock_response_404
        else:
            return mock_response_500


# Fetch the lates version from archivo (no timestamp defined)
def fetch_latest_archive(ontology, headers):
    logger.info(f'Fetching latest archive ontology from URL: {ontology}/latest')
    try:
        response = requests.get(url=ontology, headers=headers, timeout=5)
        logger.info('Successfully fetched latest archive ontology')
        return response
    except Exception as e:
        logger.error(f'Error fetching latest archive ontology: {e}')
        return mock_response_500


def fetch_timestamp_archive(ontology, headers):
    return mock_response_404


def fetch_dependency_manifest(ontology, headers):
    dependencies_file = "ontologytimemachine/utils/dependency.ttl"
    # Parse RDF data from the dependencies file
    g = rdflib.Graph()
    g.parse(dependencies_file, format="turtle")

    version_namespace = rdflib.Namespace("https://example.org/versioning/")

    # Extract dependencies related to the ontology link
    ontology = rdflib.URIRef(ontology)
    
    dependencies = g.subjects(predicate=version_namespace.dependency, object=ontology)

    for dependency in dependencies:
        dep_snapshot = g.value(subject=dependency, predicate=version_namespace.snapshot)
        dep_file = g.value(subject=dependency, predicate=version_namespace.file)
        
        # Make request to DBpedia archive API
        base_api_url = "https://archivo.dbpedia.org/download"
        
        if dep_file:
            version_param = dep_file.split('v=')[1]
            api_url = f"{base_api_url}?o={ontology}&v={version_param}"
        else:
            api_url = f"{base_api_url}?o={ontology}"
            
        response = requests.get(api_url)
        if response.status_code == 200:
            logger.info(f"Successfully fetched {api_url}")
            return response
        else:
            logger.error(f"Failed to fetch {api_url}, status code: {response.status_code}")
            return mock_response_404


def failover_mode(request):
    headers = get_headers(request)
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
            return fetch_from_dbpedia_archivo_api(ontology, headers)
    except (SSLError, Timeout, ConnectionError, RequestException) as e:
        return fetch_from_dbpedia_archivo_api(ontology, headers)


def fetch_from_dbpedia_archivo_api(ontology, headers):
    format, version, versionMatching = get_parameters_from_headers(headers)
    dbpedia_url = f'{dbpedia_api}?o={ontology}&f={format}'
    try:
        logger.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
        response = requests.get(dbpedia_url, timeout=5)
        print(response)
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f'Exception occurred while fetching from DBpedia Archivo API: {e}')
        return mock_response_404()
    

def map_mime_to_format(mime_type):
    # Map file extensions to formats
    mime_to_format = {
        'application/rdf+xml': 'owl',       # Common MIME type for OWL files
        'application/owl+xml': 'owl',       # Specific MIME type for OWL
        'text/turtle': 'ttl',               # MIME type for Turtle format
        'application/n-triples': 'nt',      # MIME type for N-Triples format
    }
    
    return mime_to_format.get(mime_type, None)


def get_parameters_from_headers(headers):
    # Map MIME types to formats
    mime_type = headers.get('Accept', None)
    format = map_mime_to_format(mime_type)

    version = headers.get('Version', None)
    versionMatching = headers.get('VersionMatching', None)
    return format, version, versionMatching