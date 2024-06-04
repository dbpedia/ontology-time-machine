import pytest
import requests
from ontologytimemachine.proxy import start_proxy, PORT

PROXY_URL = f'http://localhost:{PORT}'

@pytest.fixture(scope="module", autouse=True)
def start_proxy_server():
    start_proxy()
    import time
    time.sleep(1)

def test_google_com():
    response = requests.get(PROXY_URL + '/google.com')
    assert response.status_code == 200
    assert response.text == 'This is a static response for google.com'

def test_linked_web_apis():
    response = requests.get(PROXY_URL + '/http://linked-web-apis.fit.cvut.cz/ns/core')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/turtle'

def test_ontologi_es():
    response = requests.get(PROXY_URL + '/http%3A//ontologi.es/days%23')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/turtle'


if __name__ == '__main__':
    pytest.main()
