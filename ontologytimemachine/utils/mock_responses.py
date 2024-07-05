import requests


def mock_response_200():
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response.url = 'https://example.com/success'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>To be implemented</h1></body></html>'
    return mock_response


def mock_response_403():
    mock_response = requests.Response()
    mock_response.status_code = 403
    mock_response.url = 'https://example.com/forbidden'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>403 Forbidden</h1></body></html>'
    return mock_response



def mock_response_404():
    mock_response = requests.Response()
    mock_response.status_code = 404
    mock_response.url = 'https://example.com/resource-not-found'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>404 Not Found</h1></body></html>'
    return mock_response


def mock_response_500():
    mock_response = requests.Response()
    mock_response.status_code = 500
    mock_response.url = 'https://example.com/internal-server-error'
    mock_response.headers['Content-Type'] = 'text/html'
    mock_response._content = b'<html><body><h1>500 Internal Server Error</h1></body></html>'
    return mock_response