import unittest
from ontologytimemachine.utils.proxy_logic import (
    if_not_block_host,
    do_deny_request_due_non_archivo_ontology_uri,
    load_archivo_urls,
    is_archivo_ontology_request,
    proxy_logic,
    fetch_original,
)


class TestProxyLogic(unittest.TestCase):

    def test_do_deny_request_due_non_archivo_ontology_uri(self):
        # Assuming we are using some sample data structure
        class WrappedRequest:
            def __init__(self, request):
                self.request = {"host": request[0], "path": request[1]}

            def get_request_host(self) -> str:
                return self.request["host"].decode("utf-8")

            def get_request_path(self) -> str:
                return self.request["path"].decode("utf-8")

        request = WrappedRequest((b"example.com", b"/ontology"))
        self.assertTrue(do_deny_request_due_non_archivo_ontology_uri(request, True))
        self.assertFalse(do_deny_request_due_non_archivo_ontology_uri(request, False))

    def test_fetch_original(self):
        url = "https://example.com"
        headers = {"Accept": "text/html"}
        response = fetch_original(url, headers, False)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
