import logging
import argparse
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

    args  = parser.parse_args()
    
    ontoFormat = {
        'format': args.ontoFormat,
        'precedence': args.ontoPrecedence,
        'patchAcceptUpstream': args.patchAcceptUpstream
    }

    logger.info(f'Ontology Format: {ontoFormat}')
    logger.info(f'Ontology Version: {args.ontoVersion}')
    logger.info(f'Only Ontologies Mode: {args.onlyOntologies}')
    logger.info(f'HTTPS Interception: {args.httpsIntercept}')
    logger.info(f'Inspect Redirects: {args.inspectRedirects}')
    logger.info(f'Forward Headers: {args.forwardHeaders}')
    return ontoFormat, args.ontoVersion, args.onlyOntologies, args.httpsIntercept, args.inspectRedirects, args.forwardHeaders


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


def set_onto_format_headers(wrapped_request, ontoFormat, ontoVersion):
    logger.info(f'Setting headers based on ontoFormat: {ontoFormat}')

    # Determine the correct MIME type for the format
    mime_type = get_mime_type(ontoFormat['format'])
    logger.info(f'Requested mimetype: {mime_type}')

    logger.info(f'Wrapper isconnect: {wrapped_request.is_connect_request()}')

    request_accept_header = wrapped_request.get_request_accept_header()

    # Check the precedence and update the 'Accept' header if necessary
    # Redefine the condition
    if ontoFormat['precedence'] in ['always'] or \
       (ontoFormat['precedence'] == 'default' and request_accept_header == '*/*') or \
        request_accept_header == '*/*':
        # Needed to make sure the accept header is define
        wrapped_request.set_request_accept_header(mime_type)

    # Check if patchAcceptUpstream is true and ontoVersion is 'original'
    if ontoFormat['patchAcceptUpstream'] and ontoVersion == 'original':
        wrapped_request.set_request_accept_header(mime_type)



# def failover_mode(request):
#     headers = get_headers(request)
#     logger.info('Failover mode')

#     ontology, _, _ = get_ontology_from_request(request)
#     try:
#         response = requests.get(url=ontology, headers=headers, timeout=5)
#         if response.history:
#             logger.debug("Request was redirected")
#             for resp in response.history:
#                 logger.debug(f"{resp.status_code}, {resp.url}")
#             logger.debug(f"Final destination: {response.status_code}, {response.url}")
#         else:
#             logger.debug("Request was not redirected")
#         content_type = response.headers.get('Content-Type')
#         logger.debug(content_type)
#         if response.status_code in passthrough_status_codes_http:
#                 return response
#         else:
#             logging.info(f'Status code: {response.status_code}')
#             return fetch_from_dbpedia_archivo_api(ontology, headers)
#     except (SSLError, Timeout, ConnectionError, RequestException) as e:
#         return fetch_from_dbpedia_archivo_api(ontology, headers)


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