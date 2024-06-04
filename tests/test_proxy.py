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
    print(response.text)
    assert response.text == 'This is a static response for google.com'

def test_other_site():
    response = requests.get(PROXY_URL + '/example.com')
    assert response.status_code == 404
    print(response.text)
    assert response.text == 'Resource not found'

if __name__ == '__main__':
    pytest.main()
