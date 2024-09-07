import logging
import requests
import rdflib
from urllib.parse import urlparse

from ontologytimemachine.utils.utils import set_onto_format_headers, get_parameters_from_headers
from ontologytimemachine.utils.utils import dbpedia_api, passthrough_status_codes_http
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
    with open('ontologytimemachine/utils/archivo_ontologies.txt', 'r') as file:
        urls = [line.strip() for line in file]
    parsed_urls = [(urlparse(url).netloc, urlparse(url).path) for url in urls]

    _, request_host, request_path = wrapped_request.get_ontology_from_request()
    for host, path in parsed_urls:
        if request_host == host and request_path.startswith(path):
            return True
    return False


def proxy_logic(wrapped_request, ontoFormat, ontoVersion):
    logger.info('Proxy has to intervene')

    set_onto_format_headers(wrapped_request, ontoFormat, ontoVersion)

    headers = wrapped_request.get_request_headers()
    logger.info(f'Updated headers: {headers}')
    ontology, _, _ = wrapped_request.get_ontology_from_request()
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