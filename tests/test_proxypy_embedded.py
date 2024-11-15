import unittest
from proxy import TestCase
import pytest
import requests
import csv
from proxy.proxy import Proxy
from proxy.common.utils import new_socket_connection
from ontologytimemachine.utils.config import Config, parse_arguments , logger
from ontologytimemachine.custom_proxy import OntologyTimeMachinePlugin
from typing import List, Tuple
from requests.auth import HTTPBasicAuth
import time
import logging


logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level to DEBUG
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ProxyAutoStartUpTestCase(TestCase):
    """This test case is a demonstration of proxy.TestCase and also serves as
    integration test suite for proxy.py."""

    PROXY_PY_STARTUP_FLAGS = TestCase.DEFAULT_PROXY_PY_STARTUP_FLAGS + [
        '--enable-web-server',
        '--port', '8866',
        '--plugins','ontologytimemachine.custom_proxy.OntologyTimeMachinePlugin'
    ]
    
    CA_CERT_PATH = "ca-cert.pem"

    # @classmethod
    # def get_additional_plugins(cls) -> List[Type]:
    #     """Subclasses can override this method to add additional plugins."""
    #     return []


    @classmethod
    def setUpClass(cls) -> None:
        cls.INPUT_ARGS = getattr(cls, 'PROXY_PY_STARTUP_FLAGS', cls.DEFAULT_PROXY_PY_STARTUP_FLAGS)
        cls.PROXY = Proxy(cls.INPUT_ARGS)
        # Add default plugin
        cls.PROXY.flags.plugins[b'HttpProxyBasePlugin'].append(
            OntologyTimeMachinePlugin,
        )
        # Add additional plugins from subclass
        # additional_plugins = cls.get_additional_plugins()
        # cls.PROXY.flags.plugins[b'HttpProxyBasePlugin'].extend(additional_plugins)
        # Start the proxy server
        cls.PROXY.__enter__()
        assert cls.PROXY.acceptors
        cls.wait_for_server(cls.PROXY.flags.port)


    def make_request_with_proxy(self, iri: str, proxy_port: int, mode: str) -> Tuple[int, str]:
        """Make a request to the IRI using the proxy."""
        proxies = {
            "http": f"http://localhost:{proxy_port}",
            "https": f"http://localhost:{proxy_port}",
        }
        username = f"--ontoVersion {mode}"
        password = "my_password"
        headers = {
            "Accept": "text/turtle"
        }
        try:
            response = requests.get(iri, proxies=proxies, verify=self.CA_CERT_PATH, timeout=300, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Request exception: {e}", exc_info=True)
            return {'status_code': 'error'}

    def test_function1(self) -> None:
        logger.debug("~~~~~~~~~~~~~~~~~~~~~~~______________________________#Debug message from imported time machine logger")
        logger.debug(vars(logger))
        logger2 = logging.getLogger("ontologytimemachine.tests.test_logging")
        logger2.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~______________________________#Debug message from test logger2")
        assert True
        #logger.warning(vars(self.make_request_with_proxy("https://data.europa.eu/esco/flow", 8894, 'latestArchived')))
        assert 200 == self.make_request_with_proxy("http://data.europa.eu/esco/flow	", 8866, 'latestArchived').status_code
        # self.assertEqual(self.make_request_with_proxy("http://data.europa.eu/esco/flow	",8866, 'latestArchived').status_code,200)

            

    # def make_request_with_proxy(self, iri: str, mode: str) -> Tuple[int, str]:
    #     logger.warn('Run')
    #     proxies = {
    #         "http": f"http://localhost:{proxy_port}",
    #         "https": f"https://localhost:{proxy_port}",
    #     }
    #     """Make a request to the IRI using the proxy."""
    #     username = f"--ontoVersion {mode}"
    #     password = "my_password"
    #     headers = {
    #         "Accept": "text/turtle",
    #         "Accept-Encoding": "identity",
    #         "Proxy-Authorization": _basic_auth_str(username, password)
    #     }
    #     try:
    #         # There is an issue here for https requests
    #         response = requests.get(iri, proxies=proxies, headers=headers, timeout=10)
    #         return response
    #     except SSLError as e:
    #         mock_response = Mock()
    #         mock_response.content = ''
    #         mock_response.status_code = 'ssl-error'
    #         return mock_response
    #     except requests.exceptions.Timeout:
    #         mock_response = Mock()
    #         mock_response.content = ''
    #         mock_response.status_code = 'timeout-error'
    #         return mock_response
    #     except requests.exceptions.ConnectionError as e:
    #         if 'NXDOMAIN' in str(e):
    #             mock_response = Mock()
    #             mock_response.content = ''
    #             mock_response.status_code = 'nxdomain-error'
    #             return mock_response
    #         elif 'Connection refused' in str(e) or 'Errno 111' in str(e):
    #             mock_response = Mock()
    #             mock_response.content = ''
    #             mock_response.status_code = 'connection-refused-error'
    #             return mock_response
    #         else:
    #             mock_response = Mock()
    #             mock_response.content = ''
    #             mock_response.status_code = 'error'
    #             return mock_response
    #     except Exception as e:
    #         mock_response = Mock()
    #         mock_response.content = ''
    #         mock_response.status_code = 'error'
    #         return mock_response


    # Parametrize the test cases with data loaded from the TSV file
    # @pytest.mark.parametrize("test_case", load_test_data('tests/archivo_test_IRIs.tsv'))
    # def test_proxy_responses(self,test_case):
    #     enabled = test_case['enable_testcase']
        
    #     iri = test_case['iri']
    #     error_dimension = test_case['error_dimension']
    #     expected_error = test_case['expected_error']
    #     iri_type = test_case['iri_type']
    #     comment = test_case['comment']
        
    #     if enabled == '1':
    #         # Make direct and proxy requests
    #         direct_response = make_request_without_proxy(iri)
    #         proxy_original_response = make_request_with_proxy(iri, 'original')
    #         proxy_failover_response = make_request_with_proxy(iri, 'originalFailoverLiveLatest')
    #         proxy_archivo_laest_response = make_request_with_proxy(iri, 'latestArchived')

    #         # Evaluation based on error_dimension
    #         if error_dimension == 'http-code':
    #             assert int(expected_error) == direct_response.status_code
    #             assert int(expected_error) == proxy_original_response.status_code
                

    #         elif error_dimension == 'None':
    #             assert direct_response.status_code == 200
    #             assert proxy_original_response.status_code == 200

    #         elif error_dimension == 'content':
    #             if expected_error == 'text_html':
    #                 assert direct_response.headers.get('Content-Type') == 'text/html'
    #                 assert proxy_original_response.headers.get('Content-Type') == 'text/html'
    #             elif expected_error == '0-bytes':
    #                 assert len(direct_response.content) == 0
    #                 assert len(proxy_original_response.content) == 0

    #         elif error_dimension == 'dns':
    #             if expected_error == 'nxdomain':
    #                 assert direct_response.status_code == 'nxdomain-error'
    #                 assert proxy_original_response.status_code == 502
                            
    #         elif error_dimension == 'transport':
    #             if expected_error == 'cert-expired':
    #                 assert direct_response.status_code == 'ssl-error'
    #                 assert proxy_original_response.status_code == 'ssl-error'
    #             elif expected_error == 'connect-timeout':
    #                 assert direct_response.status_code == 'timeout-error'
    #                 assert proxy_original_response.status_code == 'timeout-error'
    #             elif expected_error == 'connect-refused':
    #                 assert direct_response.status_code == 'connection-refused-error'
    #                 assert proxy_original_response.status_code == 'connection-refused-error'
                
    #         assert 200 == proxy_failover_response.status_code
    #         assert 200 == proxy_archivo_laest_response.status_code
        
    #     else:
            # assert True

