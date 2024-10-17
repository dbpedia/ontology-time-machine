from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.common.utils import build_http_response
from ontologytimemachine.utils.mock_responses import mock_response_403
from ontologytimemachine.proxy_wrapper import HttpRequestWrapper
from ontologytimemachine.utils.proxy_logic import (
    get_response_from_request,
    do_block_CONNECT_request,
    is_archivo_ontology_request,
)
from ontologytimemachine.utils.config import Config, HttpsInterception, parse_arguments
from http.client import responses
import proxy
import sys
import logging


IP = "0.0.0.0"
PORT = "8899"

config = None

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OntologyTimeMachinePlugin(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        logger.info("Init")
        super().__init__(*args, **kwargs)
        self.config = config

    def before_upstream_connection(self, request: HttpParser) -> HttpParser | None:
        print(config)
        logger.info("Before upstream connection hook")
        logger.info(
            f"Request method: {request.method} - Request host: {request.host} - Request path: {request.path} - Request headers: {request.headers}"
        )
        wrapped_request = HttpRequestWrapper(request)

        if wrapped_request.is_connect_request():
            logger.info(f"Handling CONNECT request: configured HTTPS interception mode: {self.config.httpsInterception}")

            # Check whether to allow CONNECT requests since they can impose a security risk
            if not do_block_CONNECT_request(self.config):
                logger.info("Allowing the CONNECT request")
                return request
            else:
                logger.info("CONNECT request was blocked due to the configuration")
                return None

        # # If only ontology mode, return None in all other cases
        logger.info(f"Config: {self.config}")
        response = get_response_from_request(wrapped_request, self.config)
        if response:
            self.queue_response(response)
            return None

        return request

    def do_intercept(self, _request: HttpParser) -> bool:
        wrapped_request = HttpRequestWrapper(_request)
        if self.config.httpsInterception in ["all"]:
            return True
        elif self.config.httpsInterception in ["none"]:
            return False
        # elif self.config.httpsInterception == HttpsInterception.BLOCK: #this should actually be not triggered
        #     return False
        elif self.config.httpsInterception in ["archivo"]:
            if is_archivo_ontology_request(wrapped_request):
                return True
            return False
        else:
            logger.info("Unknown Option for httpsInterception: %s -> fallback to no interception", self.config.httpsInterception)
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

    # check it https interception is enabled
    if config.httpsInterception != "none":
        sys.argv += [
            "--ca-key-file",
            "ca-key.pem",
            "--ca-cert-file",
            "ca-cert.pem",
            "--ca-signing-key-file",
            "ca-signing-key.pem",
        ]

    sys.argv += [
        "--hostname",
        IP,
        "--port",
        PORT,
        "--plugins",
        __name__ + ".OntologyTimeMachinePlugin",
    ]

    logger.info("Starting OntologyTimeMachineProxy server...")
    proxy.main()
