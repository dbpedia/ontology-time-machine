import unittest
import requests
import csv
from proxy.proxy import Proxy
from proxy.common.utils import new_socket_connection
from ontologytimemachine.utils.config import Config, parse_arguments
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


class OntoVersionTestCase(unittest.TestCase):
    """Test case for making requests with different OntoVersions."""

    DEFAULT_PROXY_PY_STARTUP_FLAGS = [
        '--hostname', '0.0.0.0',
        '--port', '0',  # Automatically bind to an available port
        '--num-workers', '1',
        '--num-acceptors', '1',
    ]

    PROXY: Proxy = None
    INPUT_ARGS: List[str] = None
    
    test_data = []
    plugin_config: Config = None
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources, including reading the TSV test data."""
        # Load test data from TSV file
        cls.load_test_data_from_tsv("tests/archivo_test_IRIs.tsv")

    @classmethod
    def load_test_data_from_tsv(cls, filepath: str):
        """Load test cases from a TSV file."""
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                iri = row['iri']
                error_dimension = row['error_dimension']
                expected_error = row['expected_error']
                iri_type = row['iri_type']
                comment = row['comment']
                cls.test_data.append((iri, error_dimension, expected_error, iri_type, comment))


    def setUpProxy(self) -> None:
        self.PROXY = Proxy(self.DEFAULT_PROXY_PY_STARTUP_FLAGS)
        self.PROXY.flags.plugins[b'HttpProxyBasePlugin'].append(
            OntologyTimeMachinePlugin,
        )
        self.PROXY.__enter__()
        self.wait_for_server(self.PROXY.flags.port)

    def tearDownProxy(self) -> None:
        """Tear down the proxy."""
        if self.PROXY:
            self.PROXY.__exit__(None, None, None)
            self.PROXY = None

    @staticmethod
    def wait_for_server(proxy_port: int, wait_for_seconds: float = 10.0) -> None:
        """Wait for the proxy to be available."""
        start_time = time.time()
        while True:
            try:
                new_socket_connection(('localhost', proxy_port)).close()
                break
            except ConnectionRefusedError:
                time.sleep(0.1)

            if time.time() - start_time > wait_for_seconds:
                raise TimeoutError('Timed out while waiting for proxy to start...')

    def make_request_without_proxy(self, iri: str) -> Tuple[int, str]:
        """Make a direct request to the IRI without using the proxy."""
        headers = {
            "Accept": "text/turtle"
        }
        try:
            response = requests.get(iri, timeout=10, headers=headers)
            return response
        except Exception as e:
            # logger.info(f'Error: {e}')
            # logger.info('Error with the connection')
            response.status_code = 'error'
            return response

    def make_request_with_proxy(self, iri: str, proxy_port: int, mode: str) -> Tuple[int, str]:
        """Make a request to the IRI using the proxy."""
        proxies = {
            "http": f"http://localhost:{proxy_port}",
            "https": f"https://localhost:{proxy_port}",
        }
        username = f"--ontoVersion {mode}"
        password = "my_password"
        headers = {
            "Accept": "text/turtle"
        }
        try:
            response = requests.get(iri, proxies=proxies, timeout=10, headers=headers, auth=HTTPBasicAuth(username, password))
            return response
        except Exception as e:
            # logger.info(f'Error: {e}')
            # logger.info('Error with the connection')
            return {'status_code': 'error'}
            


    def compare_responses(self, direct_response: Tuple[int, str], proxy_response: Tuple[int, str]):
        """Compare the results of the direct and proxy responses."""
        self.assertEqual(direct_response[0], proxy_response[0], "Status codes do not match.")
        self.assertEqual(direct_response[1], proxy_response[1], "Content types do not match.")

    def evaluate_results(self, direct_response, proxy_response, error_dimension, expected_error):
        error_found = False  # Flag to track if any assertion fails
        logger.info('Test without proxy results')
        try:
            if error_dimension == 'http-code':
                logger.info(f"Comparing direct response status code: expected {expected_error}, got {direct_response.status_code}")
                self.assertEqual(int(expected_error), direct_response.status_code)
            elif error_dimension == 'None':
                logger.info(f"Comparing direct response status code for 'None' error dimension: expected 200, got {direct_response.status_code}")
                self.assertEqual(200, direct_response.status_code)
            elif error_dimension == 'content':
                logger.info(f"Comparing direct response content length: expected 0, got {len(direct_response.content)}")
                self.assertEqual(0, len(direct_response.content))
            else:
                logger.info(f"Comparing direct response status code for unknown error dimension: expected 'error', got '{direct_response}'")
                self.assertEqual('error', direct_response.status_code)
        except AssertionError as e:
            logger.error(f"Direct response assertion failed: {e}")
            error_found = True  # Mark that an error occurred but continue

        # Logs before proxy response assertions
        logger.info('Test Proxy original results')
        try:
            logger.info(error_dimension)
            if error_dimension == 'http-code':
                logger.info(f"Comparing proxy response status code: expected {expected_error}, got {proxy_response.status_code}")
                self.assertEqual(int(expected_error), proxy_response.status_code)
            elif error_dimension == 'None':
                logger.info(f"Comparing proxy response status code for 'None' error dimension: expected 200, got {proxy_response.status_code}")
                self.assertEqual(200, proxy_response.status_code)
            elif error_dimension == 'content':
                logger.info(f"Comparing proxy response content length: expected 0, got {len(proxy_response.content)}")
                self.assertEqual(0, len(proxy_response.content))
            else:
                logger.info(f"Comparing proxy response status code for unknown error dimension: expected 'error', got '{proxy_response.status_code}'")
                self.assertEqual('error', proxy_response.status_code)
        except AssertionError as e:
            logger.error(f"Proxy response assertion failed: {e}")
            error_found = True  # Mark that an error occurred but continue

        # If any assertion failed, mark the test as failed
        if error_found:
            self.fail("One or more assertions failed. See logs for details.")
                

    def test_requests_with_different_onto_versions(self):
        """Test requests with different OntoVersions and compare results."""
        # Make request without proxy
        mode = 'original'
        for iri, error_dimension, expected_error, iri_type, comment in self.test_data:
            logger.info(f'IRI: {iri}')
            with self.subTest(iri=iri, expected_error=expected_error, mode=mode):
                self.setUpProxy()
                
                try:
                    # Make requests
                    direct_response = self.make_request_without_proxy(iri)
                    proxy_response = self.make_request_with_proxy(iri, self.PROXY.flags.port, mode)
                    
                    # Evaluate the results
                    logger.info('Test without proxy results')
                    if error_dimension == 'http-code':
                        logger.info(f"Comparing direct response status code: expected {expected_error}, got {direct_response.status_code}")
                        self.assertEqual(int(expected_error), direct_response.status_code)
                        logger.info(f"Comparing proxy response status code: expected {expected_error}, got {proxy_response.status_code}")
                        self.assertEqual(int(expected_error), proxy_response.status_code)
                    elif error_dimension == 'None':
                        logger.info(f"Comparing direct response status code for 'None' error dimension: expected 200, got {direct_response.status_code}")
                        self.assertEqual(200, direct_response.status_code)
                        logger.info(f"Comparing proxy response status code for 'None' error dimension: expected 200, got {proxy_response.status_code}")
                        self.assertEqual(200, proxy_response.status_code)
                    elif error_dimension == 'content':
                        logger.info(f"Comparing direct response content length: expected 0, got {len(direct_response.content)}")
                        self.assertEqual(0, len(direct_response.content))
                        logger.info(f"Comparing proxy response content length: expected 0, got {len(proxy_response.content)}")
                        self.assertEqual(0, len(proxy_response.content))
                    else:
                        logger.info(f"Comparing direct response status code for unknown error dimension: expected 'error', got '{direct_response}'")
                        self.assertEqual('error', direct_response.status_code)
                        logger.info(f"Comparing proxy response status code for unknown error dimension: expected 'error', got '{proxy_response.status_code}'")
                        self.assertEqual('error', proxy_response.status_code)
                    

                finally:
                    # Tear down the proxy after each test case
                    self.tearDownProxy()

                # Set up proxy with another OntoVersion and compare results
                # self.setUpProxy("latestArchived")
                # proxy_response_latest = self.make_request_with_proxy(iri, self.PROXY.flags.port)
                # self.compare_responses(direct_response, proxy_response_latest)
                # self.tearDownProxy()


if __name__ == "__main__":
    unittest.main()
