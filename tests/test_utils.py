import unittest
from unittest.mock import patch, Mock
import argparse
import requests

from ontologytimemachine.utils.utils import (
    get_mime_type,
    map_mime_to_format,
    get_format_from_accept_header,
    select_highest_priority_mime_from_archivo,
    parse_accept_header_with_priority,
    set_onto_format_headers,
)


class TestUtils(unittest.TestCase):

    def test_get_mime_type(self):
        self.assertEqual(get_mime_type("turtle"), "text/turtle")
        self.assertEqual(get_mime_type("rdfxml"), "application/rdf+xml")
        self.assertEqual(get_mime_type("ntriples"), "application/n-triples")
        self.assertEqual(get_mime_type("htmldocu"), "text/html")
        self.assertEqual(get_mime_type("unknown"), "text/turtle")  # Default

    def test_map_mime_to_format(self):
        self.assertEqual(map_mime_to_format("application/rdf+xml"), "owl")
        self.assertEqual(map_mime_to_format("application/owl+xml"), "owl")
        self.assertEqual(map_mime_to_format("text/turtle"), "ttl")
        self.assertEqual(map_mime_to_format("application/n-triples"), "nt")
        self.assertIsNone(map_mime_to_format("unknown/mime"))

    def test_select_highest_priority_mime_from_archivo(self):
        archivo_mime_types = [
            ("application/rdf+xml", 1.0),
            ("text/turtle", 0.8),
            ("application/n-triples", 1.0),
        ]
        result = select_highest_priority_mime_from_archivo(archivo_mime_types)
        self.assertEqual(result, "application/rdf+xml")

        archivo_mime_types = [
            ("text/html", 0.8),  # Unsupported type
        ]
        result = select_highest_priority_mime_from_archivo(archivo_mime_types)
        self.assertIsNone(result)

    def test_parse_accept_header_with_priority(self):
        accept_header = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        )
        parsed_result = parse_accept_header_with_priority(accept_header)
        expected_result = [
            ("text/html", 1),
            ("application/xhtml+xml", 1),
            ("image/webp", 1),
            ("application/xml", 0.9),
            ("*/*", 0.8),
        ]
        print(parsed_result)
        print(expected_result)
        self.assertEqual(parsed_result, expected_result)

    def test_get_format_from_accept_header(self):
        headers = {"Accept": "application/rdf+xml,text/turtle;q=0.9,*/*;q=0.8"}
        format_result = get_format_from_accept_header(headers)
        self.assertEqual(format_result, "owl")

        headers_empty = {}
        format_result = get_format_from_accept_header(headers_empty)
        self.assertIsNone(format_result)

    @patch("requests.get")
    def test_fetch_latest_archived(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        ontology = "http://dbpedia.org/ontology/Person"
        headers = {"Accept": "text/turtle"}

    def test_map_mime_to_format(self):
        self.assertEqual(map_mime_to_format("application/rdf+xml"), "owl")
        self.assertEqual(map_mime_to_format("text/turtle"), "ttl")
        self.assertEqual(map_mime_to_format("application/n-triples"), "nt")
        self.assertIsNone(map_mime_to_format("unknown/mime"))

    def test_get_format_from_accept_header(self):
        headers = {"Accept": "application/json"}
        format = get_format_from_accept_header(headers)
        self.assertEqual(format, None)

        headers = {}
        format = get_format_from_accept_header(headers)

        self.assertIsNone(format, None)

        headers = {"Accept": "text/turtle"}
        format = get_format_from_accept_header(headers)
        self.assertEqual(format, "ttl")


if __name__ == "__main__":
    unittest.main()
