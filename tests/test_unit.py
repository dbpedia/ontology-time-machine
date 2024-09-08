import unittest
from unittest.mock import patch, Mock
import argparse
import requests

from ontologytimemachine.utils.mock_responses import (
    mock_response_200,
    mock_response_403,
    mock_response_404,
    mock_response_500
)
from ontologytimemachine.utils.utils import (
    parse_arguments, 
    map_mime_to_format, 
    get_format_from_accept_header
)

from ontologytimemachine.utils.proxy_logic import (
    fetch_latest_archived
)

class TestUtils(unittest.TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    def test_parse_arguments(self, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            ontoFormat='turtle', 
            ontoPrecedence='enforcedPriority', 
            patchAcceptUpstream=False,
            ontoVersion='originalFailoverLive',
            restrictedAccess=True,
            httpsInterception=False,
            disableRemovingRedirects=True,
            forwardHeaders=True
        )

        args = parse_arguments()

        self.assertEqual(args[0]['format'], 'turtle')
        self.assertEqual(args[0]['precedence'], 'enforcedPriority')
        self.assertFalse(args[0]['patchAcceptUpstream'])
        self.assertEqual(args[1], 'originalFailoverLive')
        self.assertTrue(args[2])
        self.assertFalse(args[3])
        self.assertTrue(args[4])
        self.assertTrue(args[5])
        
        mock_parse_args.return_value = argparse.Namespace(
            ontoFormat='ntriples', 
            ontoPrecedence='default', 
            patchAcceptUpstream=True,
            ontoVersion='latestArchive',
            restrictedAccess=False,
            httpsInterception=True,
            disableRemovingRedirects=False,
            forwardHeaders=False
        )

        args = parse_arguments()

        self.assertEqual(args[0]['format'], 'ntriples')
        self.assertEqual(args[0]['precedence'], 'default')
        self.assertTrue(args[0]['patchAcceptUpstream'])
        self.assertEqual(args[1], 'latestArchive')
        self.assertFalse(args[2])
        self.assertTrue(args[3])
        self.assertFalse(args[4])
        self.assertFalse(args[5])

        
    @patch('requests.get')
    def test_fetch_latest_archived(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        ontology = 'http://dbpedia.org/ontology/Person'
        headers = {'Accept': 'text/turtle'}
        
        response = fetch_latest_archived(ontology, headers)
        self.assertEqual(response.status_code, 200)
        
        mock_get.side_effect = requests.exceptions.RequestException
        response = fetch_latest_archived(ontology, headers)
        self.assertEqual(response.status_code, 404)
        
    def test_map_mime_to_format(self):
        self.assertEqual(map_mime_to_format('application/rdf+xml'), 'owl')
        self.assertEqual(map_mime_to_format('text/turtle'), 'ttl')
        self.assertEqual(map_mime_to_format('application/n-triples'), 'nt')
        self.assertIsNone(map_mime_to_format('unknown/mime'))
        
    def test_get_format_from_accept_header(self):
        headers = {'Accept': 'application/json'}
        format = get_format_from_accept_header(headers)
        self.assertEqual(format, None)
        
        headers = {}
        format = get_format_from_accept_header(headers)

        self.assertIsNone(format, None)

        headers = {'Accept': 'text/turtle'}
        format = get_format_from_accept_header(headers)
        self.assertEqual(format, 'ttl')


class TestMockResponses(unittest.TestCase):
    
    def test_mock_response_200(self):
        response = mock_response_200()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.url, 'https://example.com/success')
        self.assertEqual(response.headers['Content-Type'], 'text/html')
        self.assertIn(b'<h1>To be implemented</h1>', response.content)
    
    def test_mock_response_403(self):
        response = mock_response_403()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.url, 'https://example.com/forbidden')
        self.assertEqual(response.headers['Content-Type'], 'text/html')
        self.assertIn(b'<h1>403 Forbidden</h1>', response.content)
    
    def test_mock_response_404(self):
        response = mock_response_404()
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.url, 'https://example.com/resource-not-found')
        self.assertEqual(response.headers['Content-Type'], 'text/html')
        self.assertIn(b'<h1>404 Not Found</h1>', response.content)
    
    def test_mock_response_500(self):
        response = mock_response_500()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.url, 'https://example.com/internal-server-error')
        self.assertEqual(response.headers['Content-Type'], 'text/html')
        self.assertIn(b'<h1>500 Internal Server Error</h1>', response.content)