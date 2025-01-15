import pytest
import requests
import logging
import csv
from typing import List, Tuple
from unittest.mock import Mock
from requests.auth import HTTPBasicAuth
from requests.auth import _basic_auth_str
from requests.exceptions import SSLError
from ontologytimemachine.custom_proxy import IP, PORT
from urllib.parse import quote

# Proxy settings
PROXY = f"0.0.0.0:8894"
HTTP_PROXY = f"http://{PROXY}"
HTTPS_PROXY = f"http://{PROXY}"
PROXIES = {"http": HTTP_PROXY, "https": HTTPS_PROXY}
CA_CERT_PATH = "ca-cert.pem"


logging.basicConfig(
    level=logging.ERROR,
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
    try:
        response = requests.get(iri, timeout=10, allow_redirects=True)
        return response
    except SSLError as e:
        mock_response = Mock()
        mock_response.status_code = 'ssl-error'
        return mock_response
    except requests.exceptions.Timeout:
        mock_response = Mock()
        mock_response.status_code = 'timeout-error'
        return mock_response
    except requests.exceptions.ConnectionError as e:
        if 'NameResolutionError' in str(e):
            mock_response = Mock()
            mock_response.status_code = 'nxdomain-error'
            return mock_response
        elif 'Connection refused' in str(e) or 'Errno 111' in str(e):
            mock_response = Mock()
            mock_response.status_code = 'connection-refused-error'
            return mock_response
        else:
            mock_response = Mock()
            mock_response.status_code = 'error'
            return mock_response
    except Exception as e:
        mock_response = Mock()
        mock_response.status_code = 'error'
        return mock_response

def make_request_with_proxy(iri: str, mode: str) -> Tuple[int, str]:
    logger.info('Run')
    """Make a request to the IRI using the proxy."""
    username = f"--ontoVersion {mode}"
    password = "my_password"
    # Encode credentials to handle special characters
    username_encoded = quote(username)
    password_encoded = quote(password)
    proxies = {
        "http": f"http://{username_encoded}:{password_encoded}@{PROXY}", 
        "https": f"http://{username_encoded}:{password_encoded}@{PROXY}"
    }
    headers = {
        "Accept-Encoding": "identity",
    }
    try:
        # There is an issue here for https requests
        response = requests.get(iri, proxies=proxies, verify=CA_CERT_PATH, headers=headers, timeout=10)
        return response
    except SSLError as e:
        mock_response = Mock()
        mock_response.content = ''
        mock_response.status_code = 'ssl-error'
        return mock_response
    except requests.exceptions.Timeout:
        mock_response = Mock()
        mock_response.content = ''
        mock_response.status_code = 'timeout-error'
        return mock_response
    except requests.exceptions.ConnectionError as e:
        if 'NXDOMAIN' in str(e):
            mock_response = Mock()
            mock_response.content = ''
            mock_response.status_code = 'nxdomain-error'
            return mock_response
        elif 'Connection refused' in str(e) or 'Errno 111' in str(e):
            mock_response = Mock()
            mock_response.content = ''
            mock_response.status_code = 'connection-refused-error'
            return mock_response
        else:
            mock_response = Mock()
            mock_response.content = ''
            mock_response.status_code = 'error'
            return mock_response
    except Exception as e:
        mock_response = Mock()
        mock_response.content = ''
        mock_response.status_code = 'error'
        return mock_response


# Parametrize the test cases with data loaded from the TSV file
@pytest.mark.skip(reason="this test is not ready yet")
@pytest.mark.parametrize("test_case", load_test_data('tests/non_archivo_test_IRIs.tsv'))
def test_proxy_responses(test_case):
    enabled = test_case['enable_testcase']
    
    iri = test_case['iri']
    error_dimension = test_case['error_dimension']
    expected_error = test_case['expected_error']
    iri_type = test_case['iri_type']
    comment = test_case['comment']
    
    if enabled == '1':
        # Make direct and proxy requests
        direct_response = make_request_without_proxy(iri)
        proxy_original_response = make_request_with_proxy(iri, 'original')
        #proxy_failover_response = make_request_with_proxy(iri, 'originalFailoverLiveLatest')
        #proxy_archivo_latest_response = make_request_with_proxy(iri, 'latestArchived')


        # Evaluation based on error_dimension
        if error_dimension == 'http-code':
            assert int(expected_error) == direct_response.status_code
            assert int(expected_error) == proxy_original_response.status_code
            #assert int(expected_error) == proxy_failover_response.status_code
            #assert int(expected_error) == proxy_archivo_latest_response.status_code

        elif error_dimension == 'None':
            assert direct_response.status_code == 200
            assert proxy_original_response.status_code == 200
            #assert proxy_failover_response.status_code == 200
            #assert proxy_archivo_latest_response.status_code == 200

    else:
        assert True


if __name__ == "__main__":
    pytest.main([__file__])
    
