import logging
import argparse
from werkzeug.http import parse_accept_header


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


dbpedia_api = 'https://archivo.dbpedia.org/download'
archivo_mimetypes = ['application/rdf+xml', 'application/owl+xml', 'text/turtle', 'application/n-triples']

passthrough_status_codes = [
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
    parser.add_argument('--ontoVersion', type=str, choices=['original', 'originalFailoverLiveLatest', 
                                                            'latestArchived', 'timestampArchived', 'dependencyManifest'],
                        default='originalFailoverLiveLatest', help='Version of the ontology: original, originalFailoverLive, originalFailoverArchivoMonitor, latestArchive, timestampArchive, dependencyManifest')

    # Enable/disable mode to only proxy requests to ontologies
    parser.add_argument('--restrictedAccess', type=bool, default=False,
                        help='Enable/disable mode to only proxy requests to ontologies stored in Archivo.')

    # Enable HTTPS interception for specific domains
    parser.add_argument('--httpsInterception', type=str, choices=['none', 'all', 'block'],
                        default='all', help='Enable HTTPS interception for specific domains: none, archivo, all, listfilename.')

    # Enable/disable inspecting or removing redirects
    parser.add_argument('--disableRemovingRedirects', type=bool, default=False,
                        help='Enable/disable inspecting or removing redirects.')

    # Enable/disable proxy forward headers
    parser.add_argument('--forwardHeaders', type=bool, default=True,
                        help='Enable/disable proxy forward headers.')

    args  = parser.parse_args()

    # Check the value of --ontoVersion and prompt for additional arguments if needed
    if args.ontoVersion == 'timestampArchived':
        args.timestamp = input('Please provide the timestamp (e.g., YYYY-MM-DD): ')
    elif args.ontoVersion == 'dependencyManifest':
        args.manifest = input('Please provide the manifest file path: ')
    
    # Accessing the arguments
    logger.info(f"Selected Ontology Version: {args.ontoVersion}")
    if hasattr(args, 'timestamp'):
        logger.info(f"Timestamp: {args.timestamp}")
        timestamp = args.timestamp
    else:
        timestamp = None

    if hasattr(args, 'manifest'):
        logger.info(f"Manifest File Path: {args.manifest}")
        manifest = args.manifest
    else:
        manifest = None

    ontoFormat = {
        'format': args.ontoFormat,
        'precedence': args.ontoPrecedence,
        'patchAcceptUpstream': args.patchAcceptUpstream
    }

    logger.info(f'Ontology Format: {ontoFormat}')
    logger.info(f'Ontology Version: {args.ontoVersion}')
    logger.info(f'Only Ontologies Mode: {args.restrictedAccess}')
    logger.info(f'HTTPS Interception: {args.httpsInterception}')
    logger.info(f'Inspect Redirects: {args.disableRemovingRedirects}')
    logger.info(f'Forward Headers: {args.forwardHeaders}')
    
    config = {
        "ontoFormat": ontoFormat, 
        "ontoVersion": args.ontoVersion, 
        "restrictedAccess": args.restrictedAccess, 
        "httpsInterception": args.httpsInterception, 
        "disableRemovingRedirects": args.disableRemovingRedirects, 
        "forward_headers": args.forwardHeaders, 
        "timestamp": timestamp, 
        "manifest": manifest,
    }
    
    return  config


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
    logger.info(f'Setting headers based on ontoFormat: {ontoFormat} and ontoVersion: {ontoVersion}')

    # if ontoVersion is original and patchAcceptUpstream is False nothing to do here
    if ontoVersion == 'original' and not ontoFormat['patchAcceptUpstream']:
        return
    
    # Determine the correct MIME type for the format
    mime_type = get_mime_type(ontoFormat['format'])
    logger.info(f'Requested mimetype by proxy: {mime_type}')

    # Define conditions for modifying the accept header
    request_accept_header = wrapped_request.get_request_accept_header()
    logger.info(f'Accept header by request: {request_accept_header}')
    req_headers_with_priority = parse_accept_header_with_priority(request_accept_header)
    req_headers = [x[0] for x in req_headers_with_priority]
    if not req_headers and ontoFormat['precedence'] in ['default', ['enforcedPriority']]:
        wrapped_request.set_request_accept_header(mime_type)
    elif len(req_headers) == 1 and req_headers[0] == '*/*' and ontoFormat['precedence'] in ['default', 'enforcedPriority']:
        wrapped_request.set_request_accept_header(mime_type)
    elif len(req_headers) > 1 and mime_type in req_headers and ontoFormat['precedence'] == 'enforcedPriority':
        wrapped_request.set_request_accept_header(mime_type)
    elif ontoFormat['precedence'] == 'always':
        wrapped_request.set_request_accept_header(mime_type)


def select_highest_priority_mime_from_archivo(mime_list):
    # Sort the MIME types by their priority in descending order
    sorted_mime_list = sorted(mime_list, key=lambda x: x[1], reverse=True)

    # Track the highest priority value
    highest_priority = sorted_mime_list[0][1]

    # Filter MIME types that match the highest priority
    highest_priority_mimes = [mime for mime, priority in sorted_mime_list if priority == highest_priority]

    # Check if any of the highest priority MIME types are in the archivo list
    for mime in highest_priority_mimes:
        if mime in archivo_mimetypes:
            return mime

    # If none of the preferred MIME types are present, return nothing
    return None


def map_mime_to_format(mime_type):
    # Map file extensions to formats
    mime_to_format = {
        'application/rdf+xml': 'owl',       # Common MIME type for OWL files
        'application/owl+xml': 'owl',       # Specific MIME type for OWL
        'text/turtle': 'ttl',               # MIME type for Turtle format
        'application/n-triples': 'nt',      # MIME type for N-Triples format
    }
    
    return mime_to_format.get(mime_type, None)


def parse_accept_header_with_priority(accept_header):
    logger.info('Parse accept header')
    # Parse the Accept header to extract MIME types and their priority (q values)
    parsed = parse_accept_header(accept_header)
    
    # Create a list of tuples with MIME types and their corresponding q values
    mime_types_with_priority = [(item[0], item[1]) for item in parsed]
    logger.info(f'Accept headers with priority: {mime_types_with_priority}')

    return mime_types_with_priority


def get_format_from_accept_header(headers):
    if not headers:
        return None

    # Map MIME types to formats
    accept_header = headers.get('Accept', None)
    logger.info(f'Accept header: {accept_header}')
    if not accept_header:
        return None
    
    accept_header_with_priority = parse_accept_header_with_priority(accept_header)
    
    selected_mimetype = select_highest_priority_mime_from_archivo(accept_header_with_priority)

    if not selected_mimetype:
        logger.info(f'The requested mimetype is not supported by DBpedia Archivo')
        return None
    
    format = map_mime_to_format(selected_mimetype)
    return format