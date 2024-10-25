import pytest
import requests
import logging
import csv
from typing import List, Tuple
from requests.auth import HTTPBasicAuth
from ontologytimemachine.custom_proxy import IP, PORT

# Proxy settings
PROXY = f"0.0.0.0:{PORT}"
HTTP_PROXY = f"http://{PROXY}"
HTTPS_PROXY = f"http://{PROXY}"
PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load data from the TSV file dynamically
def load_test_data(file_path):
    with open(file_path, 'r') as tsv_file:
        reader = csv.DictReader(tsv_file, delimiter='\t')
        return [row for row in reader]


def create_fake_response(status_code='error'):
    fake_response = requests.models.Response()
    fake_response.status_code = status_code  # Assign the status code you want to simulate
    fake_response._content = b'{"error": "This is a simulated error"}'  # Set some fake content
    return fake_response


def make_request_without_proxy(iri: str) -> Tuple[int, str]:
    """Make a direct request to the IRI without using the proxy."""
    headers = {
        "Content-Type": "text/turtle"
    }
    try:
        response = requests.get(iri, timeout=10, headers=headers)
        return response
    except Exception as e:
        # logger.info(f'Error: {e}')
        # logger.info('Error with the connection')
        return create_fake_response()

def make_request_with_proxy(iri: str, mode: str) -> Tuple[int, str]:
    """Make a request to the IRI using the proxy."""
    username = f"--ontoVersion {mode}"
    password = "my_password"
    headers = {
        "Content-Type": "text/turtle"
    }
    try:
        response = requests.get(iri, proxies=PROXIES, timeout=10, headers=headers, auth=HTTPBasicAuth(username, password))
        return response
    except Exception as e:
        # logger.info(f'Error: {e}')
        # logger.info('Error with the connection')
        return create_fake_response()

# Parametrize the test cases with data loaded from the TSV file
@pytest.mark.parametrize("test_case", load_test_data('tests/archivo_test_IRIs.tsv'))
def test_proxy_responses(test_case):
    iri = test_case['iri']
    error_dimension = test_case['error_dimension']
    expected_error = test_case['expected_error']
    iri_type = test_case['iri_type']
    comment = test_case['comment']

    # Make direct and proxy requests
    direct_response = make_request_without_proxy(iri)
    proxy_response = make_request_with_proxy(iri, 'original')
                    

    try:
        direct_response = requests.get(iri)
    except Exception as e:
        logger.error(f"Error making direct request to {iri}: {e}")
    
    try:
        proxy_response = requests.get(iri, proxies=PROXIES)
    except Exception as e:
        logger.error(f"Error making proxy request to {iri} using proxy {PROXY}: {e}")

    # Evaluation based on error_dimension
    if error_dimension == 'http-code':
        logger.info(f"Comparing direct response status code: expected {expected_error}, got {direct_response.status_code}")
        assert int(expected_error) == direct_response.status_code
        logger.info(f"Comparing proxy response status code: expected {expected_error}, got {proxy_response.status_code}")
        assert int(expected_error) == proxy_response.status_code

    elif error_dimension == 'None':
        logger.info(f"Comparing direct response status code for 'None' error dimension: expected 200, got {direct_response.status_code}")
        assert direct_response.status_code == 200
        logger.info(f"Comparing proxy response status code for 'None' error dimension: expected 200, got {proxy_response.status_code}")
        assert proxy_response.status_code == 200

    elif error_dimension == 'content':
        logger.info(f"Comparing direct response content length: expected 0, got {len(direct_response.content)}")
        assert len(direct_response.content) == 0
        logger.info(f"Comparing proxy response content length: expected 0, got {len(proxy_response.content)}")
        assert len(proxy_response.content) == 0

    elif error_dimension == 'dns' or error_dimension == 'transport':
        logger.info(f"Comparing direct response status code for unknown error dimension: expected 'error', got '{direct_response}'")
        assert 'error' == direct_response.status_code
        logger.info(f"Comparing proxy response status code for unknown error dimension: expected 'error', got '{proxy_response.status_code}'")
        assert 'error' == proxy_response.status_code
                    


if __name__ == "__main__":
    # You can call pytest from within the script
    pytest.main([__file__])
    
    