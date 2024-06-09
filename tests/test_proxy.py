import pytest
import requests
import time
import proxy
import subprocess
import sys
from ontologytimemachine.custom_proxy import OntologyTimeMachinePlugin

PORT = 8899
IP = '0.0.0.0'
PROXY = f'{IP}:{PORT}'
HTTP_PROXY = f'http://{PROXY}'
HTTPS_PROXY = f'https://{PROXY}'

@pytest.fixture(scope="module", autouse=True)
def start_proxy_server():
    # Start the proxy server in a subprocess
    process = subprocess.Popen(
        [
            'python3', '-m', 'proxy', 
            '--hostname', IP, 
            '--port', str(PORT), 
            '--plugins', 'ontologytimemachine.custom_proxy.OntologyTimeMachinePlugin'
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit to ensure the server starts
    time.sleep(5)
    
    yield
    
    # Terminate the proxy server after tests
    process.terminate()
    process.wait()

def test_google_com():
    response = requests.get('http://google.com', proxies={'http': HTTP_PROXY, 'https': HTTPS_PROXY})
    assert response.status_code == 200
    assert response.text == 'This is a static response for google.com'

def test_linked_web_apis():
    iri = 'http://linked-web-apis.fit.cvut.cz/ns/core'
    response = requests.get(iri, proxies={'http': HTTP_PROXY, 'https': HTTPS_PROXY})
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/turtle'
    assert iri in response.content.decode('utf-8')

def test_ontologi_es():
    iri = 'http://ontologi.es/days#'
    response = requests.get(iri, proxies={'http': HTTP_PROXY, 'https': HTTPS_PROXY})
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/turtle'
    assert iri in response.content.decode('utf-8')

if __name__ == '__main__':
    pytest.main()
