import logging
import requests
import rdflib
from urllib.parse import urlparse

from ontologytimemachine.utils.utils import set_onto_format_headers, get_format_from_accept_header
from ontologytimemachine.utils.utils import parse_accept_header_with_priority
from ontologytimemachine.utils.utils import dbpedia_api, passthrough_status_codes
from ontologytimemachine.utils.mock_responses import mock_response_500
from ontologytimemachine.utils.mock_responses import mock_response_404


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def if_intercept_host(https_intercept):
    if https_intercept in ['all']:
        return True
    return False


def is_ontology_request_only_ontology(wrapped_request, only_ontologies):
    is_archivo_ontology = is_archivo_ontology_request(wrapped_request)
    if only_ontologies and not is_archivo_ontology:
        return True
    return False 


def is_archivo_ontology_request(wrapped_request):
    logger.info('Chekc if the requested ontology is in archivo')
    with open('ontologytimemachine/utils/archivo_ontologies.txt', 'r') as file:
        urls = [line.strip() for line in file]
    parsed_urls = [(urlparse(url).netloc, urlparse(url).path) for url in urls]

    _, request_host, request_path = wrapped_request.get_ontology_from_request()
    for host, path in parsed_urls:
        if request_host == host and request_path.startswith(path):
            return True
    return False


def request_ontology(url, headers, disableRemovingRedirects=False, timeout=5):
    allow_redirects = not disableRemovingRedirects
    try:
        response = requests.get(url=url, headers=headers, allow_redirects=allow_redirects, timeout=5)
        logger.info('Successfully fetched original ontology')
        return response
    except Exception as e:
        logger.error(f'Error fetching original ontology: {e}')
        return mock_response_404()


def proxy_logic(wrapped_request, ontoFormat, ontoVersion, disableRemovingRedirects, timestamp, manifest):
    logger.info('Proxy has to intervene')

    set_onto_format_headers(wrapped_request, ontoFormat, ontoVersion)

    headers = wrapped_request.get_request_headers()
    ontology, _, _ = wrapped_request.get_ontology_from_request()

    # if the requested format is not in Archivo and the ontoVersion is not original
    # we can stop because the archivo request will not go through
    format = get_format_from_accept_header(headers)
    if not format and ontoVersion != 'original':
        logger.info(f'No format can be used from Archivo')
        return mock_response_500
    
    if ontoVersion == 'original':
        response = fetch_original(ontology, headers, disableRemovingRedirects)
    elif ontoVersion == 'originalFailoverLiveLatest':
        response = fetch_failover(ontology, headers, disableRemovingRedirects)
    elif ontoVersion == 'latestArchived':
        response = fetch_latest_archived(ontology, headers)
    elif ontoVersion == 'timestampArchived':
        response = fetch_timestamp_archived(ontology, headers, timestamp)
    elif ontoVersion == 'dependencyManifest':
        response = fetch_dependency_manifest(ontology, headers, manifest)

    return response


# Fetch from the original source, no matter what
def fetch_original(ontology, headers, disableRemovingRedirects):
    logger.info(f'Fetching original ontology from URL: {ontology}')
    return request_ontology(ontology, headers, disableRemovingRedirects)


# Failover mode
def fetch_failover(ontology, headers, disableRemovingRedirects):
    logger.info(f'Fetching original ontology with failover from URL: {ontology}')
    original_response = request_ontology(ontology, headers, disableRemovingRedirects)
    if original_response.status_code in passthrough_status_codes:
        requested_mimetypes_with_priority = parse_accept_header_with_priority(headers['Accept'])
        requested_mimetypes = [x[0] for x in requested_mimetypes_with_priority]
        response_mime_type = original_response.headers.get('Content-Type', ';').split(';')[0]
        logger.info(f'Requested mimetypes: {requested_mimetypes}')
        logger.info(f'Response mimetype: {response_mime_type}')
        if response_mime_type in requested_mimetypes:
                return original_response
        else:
            logging.info(f'The returned type is not the same as the requested one')
            return fetch_latest_archived(ontology, headers)
    else:
        logger.info(f'The returend status code is not accepted: {original_response.status_code}')
        return fetch_latest_archived(ontology, headers)


# Fetch the lates version from archivo (no timestamp defined)
def fetch_latest_archived(ontology, headers):
    logger.info('Fetch latest archived')
    format = get_format_from_accept_header(headers)
    dbpedia_url = f'{dbpedia_api}?o={ontology}&f={format}'
    logger.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
    return request_ontology(dbpedia_url, headers)
    


def fetch_timestamp_archived(ontology, headers, timestamp):
    logger.info('Fetch archivo timestamp')
    format = get_format_from_accept_header(headers)
    dbpedia_url = f'{dbpedia_api}?o={ontology}&f={format}&v={timestamp}'
    logger.info(f'Fetching from DBpedia Archivo API: {dbpedia_url}')
    return request_ontology(dbpedia_url, headers)


def fetch_dependency_manifest(ontology, headers, manifest):
    logger.info(f'The dependency manifest is currently not supported')
    return mock_response_500
    # # Parse RDF data from the dependencies file
    # manifest_g = rdflib.Graph()
    # manifest_g.parse(manifest, format="turtle")

    # version_namespace = rdflib.Namespace(ontology)

    # # Extract dependencies related to the ontology link
    # ontology = rdflib.URIRef(ontology)
    
    # dependencies = manifest_g.subjects(predicate=version_namespace.dependency, object=ontology)

    # for dependency in dependencies:
    #     dep_snapshot = g.value(subject=dependency, predicate=version_namespace.snapshot)
    #     dep_file = g.value(subject=dependency, predicate=version_namespace.file)
        
    #     # Make request to DBpedia archive API
    #     if dep_file:
    #         version_param = dep_file.split('v=')[1]
    #         api_url = f"{dbpedia_api}?o={ontology}&v={version_param}"
    #     else:
    #         api_url = f"{dbpedia_api}?o={ontology}"
            
    #     response = requests.get(api_url)
    #     if response.status_code == 200:
    #         logger.info(f"Successfully fetched {api_url}")
    #         return response
    #     else:
    #         logger.error(f"Failed to fetch {api_url}, status code: {response.status_code}")
    #         return mock_response_404