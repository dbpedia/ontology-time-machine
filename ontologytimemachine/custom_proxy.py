from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http import httpHeaders
from proxy.http.parser import HttpParser
from proxy.common.utils import build_http_response
from ontologytimemachine.utils.mock_responses import (
    mock_response_403,
    mock_response_500,
)
from ontologytimemachine.proxy_wrapper import HttpRequestWrapper
from ontologytimemachine.utils.proxy_logic import (
    get_response_from_request,
    do_block_CONNECT_request,
    is_archivo_ontology_request,
    evaluate_configuration,
)
from ontologytimemachine.utils.config import Config, HttpsInterception, parse_arguments
from http.client import responses
import proxy
import sys
from ontologytimemachine.utils.config import (
    HttpsInterception,
    ClientConfigViaProxyAuth,
    logger,
)


default_cfg: Config = Config()
config = None

IP = default_cfg.host
PORT = default_cfg.port


class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        logger.info(f"Init - Object ID: {id(self)}")
        super().__init__(*args, **kwargs)
        self.config = config
        logger.info(f"Config: {self.config}")

    def before_upstream_connection(self, request: HttpParser) -> HttpParser | None:
        # self.client.config = None
        logger.info("Before upstream connection hook")
        logger.info(
            f"Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}"
        )
        wrapped_request = HttpRequestWrapper(request)

        if (
            self.config.clientConfigViaProxyAuth == ClientConfigViaProxyAuth.REQUIRED
            or self.config.clientConfigViaProxyAuth == ClientConfigViaProxyAuth.OPTIONAL
        ):
            config_from_auth = evaluate_configuration(wrapped_request, self.config)
            if (
                not config_from_auth
                and self.config.clientConfigViaProxyAuth
                == ClientConfigViaProxyAuth.REQUIRED
            ):
                logger.info(
                    "Client configuration via proxy auth is required btu configuration is not provided, return 500."
                )
                self.queue_response(mock_response_500)
                return None
            if (
                not config_from_auth
                and self.config.clientConfigViaProxyAuth
                == ClientConfigViaProxyAuth.OPTIONAL
            ):
                logger.info("Auth configuration is optional, not provided.")
            if config_from_auth and not hasattr(self.client, "config"):
                self.client.config = config_from_auth
                logger.info(f"New config: {config_from_auth}")
        if self.config.clientConfigViaProxyAuth == ClientConfigViaProxyAuth.IGNORE:
            logger.info("Ignore auth even if provided")

        # Check if any config was provided via the authentication parameters
        # If so, use that config
        if hasattr(self.client, "config"):
            logger.info("Using the configuration from the Auth")
            config = self.client.config
        else:
            logger.info("Using the proxy configuration")
            config = self.config

        if wrapped_request.is_connect_request():
            logger.info(
                f"Handling CONNECT request: configured HTTPS interception mode: {config.httpsInterception}"
            )

            # Check whether to allow CONNECT requests since they can impose a security risk
            if not do_block_CONNECT_request(config):
                logger.info("Allowing the CONNECT request")
                return request
            else:
                logger.info("CONNECT request was blocked due to the configuration")
                return None

        response = get_response_from_request(wrapped_request, config)
        if response:
            self.queue_response(response)
            return None

        return request

    def do_intercept(self, _request: HttpParser) -> bool:
        wrapped_request = HttpRequestWrapper(_request)

        # Check if any config was provided via the authentication parameters
        # If so, use that config
        if hasattr(self.client, "config"):
            logger.info("Using the configuration from the Auth")
            config = self.client.config
        else:
            logger.info("Using the proxy configuration")
            config = self.config

        if config.httpsInterception == HttpsInterception.ALL:
            logger.info("Intercepting all HTTPS requests")
            return True
        elif config.httpsInterception == HttpsInterception.NONE:
            logger.info("Intercepting no HTTPS requests")
            return False
        elif config.httpsInterception == HttpsInterception.BLOCK:
            logger.error(
                "Reached code block for interception decision in block mode which should have been blocked before"
            )
            # this should actually be not triggered as the CONNECT request should have been blocked before
            return False
        elif config.httpsInterception == HttpsInterception.ARCHIVO:
            if is_archivo_ontology_request(wrapped_request):
                logger.info(
                    "Intercepting HTTPS request since it is an Archivo ontology request"
                )
                return True
            logger.info(
                "No Interception of HTTPS request since it is NOT an Archivo ontology request"
            )
            return False
        else:
            logger.info(
                "Unknown Option for httpsInterception: %s -> fallback to no interception",
                self.config.httpsInterception,
            )
            return False

    def handle_client_request(self, request: HttpParser) -> HttpParser:
        logger.info("Handle client request hook")
        logger.info(
            f"Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}"
        )

        return request

    def handle_upstream_chunk(self, chunk: memoryview):
        return chunk

    def queue_response(self, response):
        self.client.queue(
            build_http_response(
                response.status_code,
                reason=bytes(responses[response.status_code], "utf-8"),
                headers={
                    b"Content-Type": bytes(
                        response.headers.get("Content-Type"), "utf-8"
                    )
                },
                body=response.content,
            )
        )


if __name__ == "__main__":

    config = parse_arguments()

    sys.argv = [sys.argv[0]]

    # check it https interception is enabled add the necessary certificates to proxypy
    if config.httpsInterception != (HttpsInterception.NONE or HttpsInterception.BLOCK):
        sys.argv += [
            "--ca-key-file", "ca-key.pem",
            "--ca-cert-file", "ca-cert.pem",
            "--ca-signing-key-file", "ca-signing-key.pem",
        ]

    sys.argv += [
        "--hostname", config.host,
        "--port", str(config.port),
        # "--log-level", config.logLevel.name,
        '--insecure-tls-interception',  # without it the proxy would not let through a response using an invalid upstream certificate in interception mode
                                        # since there currently is a bug in proxypy when a connect request uses an IP address instead of a domain name
                                        # the proxy would not be able to work corectly in transparent mode using 3proxy setup since it tries to match
                                        # the IP address as hostname with the certificate instead of the domain name in the SNI field
        "--plugins", __name__ + ".OntologyTimeMachinePlugin",
    ]

    logger.info("Starting OntologyTimeMachineProxy server...")
    logger.debug(f"starting proxypy engine with arguments: {sys.argv}")
    proxy.main()
