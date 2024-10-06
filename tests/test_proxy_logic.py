import unittest
from ontologytimemachine.utils.proxy_logic import (
    if_intercept_host,
    do_deny_request_due_non_archivo_ontology_uri,
    load_archivo_urls,
    is_archivo_ontology_request,
    proxy_logic,
    fetch_original,
)


class TestProxyLogic(unittest.TestCase):

    def test_if_intercept_host(self):
        self.assertTrue(if_intercept_host("all"))
        self.assertFalse(if_intercept_host("block"))
        self.assertTrue(if_intercept_host("none"))

    def test_do_deny_request_due_non_archivo_ontology_uri(self):
        # Assuming we are using some sample data structure
        class WrappedRequest:
            def __init__(self, host, path):
                self.host = host
                self.path = path

            def get_request(self):
                return self

        request = WrappedRequest(b"example.com", b"/ontology")
        self.assertTrue(do_deny_request_due_non_archivo_ontology_uri(request, True))
        self.assertFalse(do_deny_request_due_non_archivo_ontology_uri(request, False))

    def test_fetch_original(self):
        url = "https://example.com"
        headers = {"Accept": "text/html"}
        response = fetch_original(url, headers, False)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
