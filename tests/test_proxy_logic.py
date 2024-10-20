import unittest
from ontologytimemachine.utils.proxy_logic import (
    do_block_CONNECT_request,
    do_deny_request_due_non_archivo_ontology_uri,
    load_archivo_urls,
    is_archivo_ontology_request,
    proxy_logic,
    fetch_original,
)


class TestProxyLogic(unittest.TestCase):

    def test_fetch_original(self):
        url = "https://example.com"
        headers = {"Accept": "text/html"}
        response = fetch_original(url, headers, False)
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
