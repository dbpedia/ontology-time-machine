import requests
from ontologytimemachine.utils.config import parse_arguments
from ontologytimemachine.proxy_wrapper import AbstractRequestWrapper
from ontologytimemachine.utils.config import Config, HttpsInterception
from ontologytimemachine.utils.utils import (
    set_onto_format_headers,
    get_format_from_accept_header,
)
from ontologytimemachine.utils.download_archivo_urls import load_archivo_urls
from ontologytimemachine.utils.utils import (
    parse_accept_header_with_priority,
    archivo_api,
    passthrough_status_codes,
)
from ontologytimemachine.utils.mock_responses import (
    mock_response_403,
    mock_response_404,
    mock_response_500,
)
from typing import Set, Tuple
from ontologytimemachine.utils.config import (
    OntoFormat,
    OntoFormatConfig,
    OntoPrecedence,
    OntoVersion,
    HttpsInterception,
    ClientConfigViaProxyAuth,
    logger,
)


def do_block_CONNECT_request(config: Config) -> bool:
    if config.httpsInterception == HttpsInterception.BLOCK:
        logger.info("decided to block CONNECT request due to config enum")
        return True
    return False


def do_deny_request_due_non_archivo_ontology_uri(wrapped_request, config):
    if config.restrictedAccess:
        is_archivo_ontology = is_archivo_ontology_request(wrapped_request)
        if not is_archivo_ontology:
            return True
    return False


def get_response_from_request(wrapped_request, config):
    do_deny = do_deny_request_due_non_archivo_ontology_uri(wrapped_request, config)
    if do_deny:
        logger.warning(
            "Request denied: not an ontology request and only ontologies mode is enabled"
        )
        return mock_response_403

    response = proxy_logic(wrapped_request, config)
    return response


# curl -U "--ca-key-file+ca-key.pem+--ca-cert-file+ca-cert.pem+--ca-signing-key-file+ca-signing-key.pem+--hostname+0.0.0.0+--port+%24PORT+--plugins+ontologytimemachine.custom_proxy.OntologyTimeMachinePlugin+http%3A%2F%2Fweb.de%2F%3Ffoo%3Dbar%26bar%3Dfoo%23whateversssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss:pas" -kvvvx http://localhost:8899 https:///www.example.org
# decode auth username (is in www-form encoding not to beconfused with url encoding!)
# parameters parsed into config object
# configurations merged (cmdline startup config and auth config)
# apply for current request
def evaluate_configuration(wrapped_request, config):
    authentication_str = wrapped_request.get_authentication_from_request()
    if authentication_str:
        logger.info("Authentication parameters provided, parsing the configuration.")
        username, password = authentication_str.split(":")
        logger.info(username)
        config_list = username.split(" ")
        config = parse_arguments(config_list)
        return config
    else:
        if config.clientConfigViaProxyAuth == ClientConfigViaProxyAuth.OPTIONAL:
            logger.info(
                "Client configuration via proxy auth is optional, configuration not provided."
            )
            return None
        elif config.clientConfigViaProxyAuth == ClientConfigViaProxyAuth.OPTIONAL:
            logger.info(
                "Client configuration via proxy auth is required btu configuration is not provided, return 500."
            )
            return None


def is_archivo_ontology_request(wrapped_request):
    """Check if the requested ontology is in the archivo."""
    logger.info("Check if the requested ontology is in archivo")

    # Ensure the archivo URLs are loaded
    load_archivo_urls()
    from ontologytimemachine.utils.download_archivo_urls import ARCHIVO_PARSED_URLS

    # Extract the request's host and path
    request_host = wrapped_request.get_request_host()
    request_path = wrapped_request.get_request_path()

    if (request_host, request_path) in ARCHIVO_PARSED_URLS:
        logger.info(f"Requested URL: {request_host+request_path} is in Archivo")
        return True

    # Remove last hash and check again
    if request_path.endswith("/"):
        request_path = request_path.rstrip("/")
    if (request_host, request_path) in ARCHIVO_PARSED_URLS:
        wrapped_request.set_request_path(request_path)
        logger.info(f"Requested URL: {request_host+request_path} is in Archivo")
        return True

    # Cut the last part of the path

    path_parts = request_path.split("/")
    new_path = "/".join(path_parts[:-1])

    if (request_host, new_path) in ARCHIVO_PARSED_URLS:
        wrapped_request.set_request_path(new_path)
        logger.info(f"Requested URL: {request_host+new_path} is in Archivo")
        return True

    new_path = new_path + "/"
    if (request_host, new_path) in ARCHIVO_PARSED_URLS:
        wrapped_request.set_request_path(new_path)
        logger.info(f"Requested URL: {request_host+new_path} is in Archivo")
        return True

    new_path = "/".join(path_parts[:-2])
    if (request_host, new_path) in ARCHIVO_PARSED_URLS:
        wrapped_request.set_request_path(new_path)
        logger.info(f"Requested URL: {request_host+new_path} is in Archivo")
        return True

    new_path = new_path + "/"
    if (request_host, new_path) in ARCHIVO_PARSED_URLS:
        wrapped_request.set_request_path(new_path)
        logger.info(f"Requested URL: {request_host+new_path} is in Archivo")
        return True

    logger.info(f"Requested URL: {request_host+request_path} is NOT in Archivo")
    return False


def request_ontology(
    wrapped_request, url, headers, disableRemovingRedirects=False, timeout=5
):
    allow_redirects = not disableRemovingRedirects
    try:
        if wrapped_request.is_head_request():
            response = requests.head(
                url=url, headers=headers, allow_redirects=allow_redirects, timeout=5
            )
        else:
            response = requests.get(
                url=url, headers=headers, allow_redirects=allow_redirects, timeout=5
            )
        logger.info("Successfully fetched ontology")
        return response
    except Exception as e:
        logger.error(f"Error fetching original ontology: {e}")
        return mock_response_404()


# change the function definition and pass only the config
def proxy_logic(wrapped_request, config):
    logger.info("Proxy has to intervene")

    set_onto_format_headers(wrapped_request, config)

    headers = wrapped_request.get_request_headers()

    # if the requested format is not in Archivo and the ontoVersion is not original
    # we can stop because the archivo request will not go through
    format = get_format_from_accept_header(headers)
    if not format and config.ontoVersion != OntoVersion.ORIGINAL:
        logger.info(f"No format can be used from Archivo")
        return mock_response_500

    if config.ontoVersion == OntoVersion.ORIGINAL:
        ontology, _, _ = wrapped_request.get_request_url_host_path()
        response = fetch_original(wrapped_request, ontology, headers, config)
    elif config.ontoVersion == OntoVersion.ORIGINAL_FAILOVER_LIVE_LATEST:
        response = fetch_failover(
            wrapped_request, headers, config.disableRemovingRedirects
        )
    elif config.ontoVersion == OntoVersion.LATEST_ARCHIVED:
        response = fetch_latest_archived(wrapped_request, ontology, headers)
    elif config.ontoVersion == OntoVersion.LATEST_ARCHIVED:
        response = fetch_timestamp_archived(wrapped_request, headers, config)
    # Commenting the manifest related part because it is not supported in the current version
    # elif ontoVersion == 'dependencyManifest':
    #     response = fetch_dependency_manifest(ontology, headers, manifest)

    return response


# Fetch from the original source, no matter what
def fetch_original(wrapped_request, ontology, headers, disableRemovingRedirects):
    logger.info(f"Fetching original ontology from URL: {ontology}")
    return request_ontology(
        wrapped_request, ontology, headers, disableRemovingRedirects
    )


# Failover mode
def fetch_failover(wrapped_request, headers, disableRemovingRedirects):
    ontology, _, _ = wrapped_request.get_request_url_host_path()
    logger.info(f"Fetching original ontology with failover from URL: {ontology}")
    original_response = request_ontology(
        wrapped_request, ontology, headers, disableRemovingRedirects
    )
    if original_response.status_code in passthrough_status_codes:
        requested_mimetypes_with_priority = parse_accept_header_with_priority(
            headers["Accept"]
        )
        requested_mimetypes = [x[0] for x in requested_mimetypes_with_priority]
        response_mime_type = original_response.headers.get("Content-Type", ";").split(
            ";"
        )[0]
        logger.info(f"Requested mimetypes: {requested_mimetypes}")
        logger.info(f"Response mimetype: {response_mime_type}")
        if response_mime_type in requested_mimetypes:
            return original_response
        else:
            logging.info(f"The returned type is not the same as the requested one")
            return fetch_latest_archived(wrapped_request, headers)
    else:
        logger.info(
            f"The returend status code is not accepted: {original_response.status_code}"
        )
        return fetch_latest_archived(wrapped_request, headers)


# Fetch the lates version from archivo (no timestamp defined)
def fetch_latest_archived(wrapped_request, headers):
    if not is_archivo_ontology_request(wrapped_request):
        logger.info(
            "Data needs to be fetched from Archivo, but ontology is not available on Archivo."
        )
        return mock_response_404()
    logger.info("Fetch latest archived")
    format = get_format_from_accept_header(headers)
    ontology, _, _ = wrapped_request.get_request_url_host_path()
    dbpedia_url = f"{archivo_api}?o={ontology}&f={format}"
    logger.info(f"Fetching from DBpedia Archivo API: {dbpedia_url}")
    return request_ontology(wrapped_request, dbpedia_url, headers)


def fetch_timestamp_archived(wrapped_request, headers, config):
    if not is_archivo_ontology_request(wrapped_request):
        logger.info(
            "Data needs to be fetched from Archivo, but ontology is not available on Archivo."
        )
        return mock_response_404()
    logger.info("Fetch archivo timestamp")
    format = get_format_from_accept_header(headers)
    ontology, _, _ = wrapped_request.get_request_url_host_path()
    dbpedia_url = f"{archivo_api}?o={ontology}&f={format}&v={config.timestamp}"
    logger.info(f"Fetching from DBpedia Archivo API: {dbpedia_url}")
    return request_ontology(wrapped_request, dbpedia_url, headers)


def fetch_dependency_manifest(ontology, headers, manifest):
    logger.info(f"The dependency manifest is currently not supported")
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
    #         api_url = f"{archivo_api}?o={ontology}&v={version_param}"
    #     else:
    #         api_url = f"{archivo_api}?o={ontology}"

    #     response = requests.get(api_url)
    #     if response.status_code == 200:
    #         logger.info(f"Successfully fetched {api_url}")
    #         return response
    #     else:
    #         logger.error(f"Failed to fetch {api_url}, status code: {response.status_code}")
    #         return mock_response_404
