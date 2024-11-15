import unittest
import logging
from ontologytimemachine.utils.mock_responses import (
    mock_response_200,
    mock_response_403,
    mock_response_404,
    mock_response_500,
)

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class TestMockResponses(unittest.TestCase):

    def test_mock_response_200(self):
        response = mock_response_200()
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>To be implemented</h1>", response.text)

    def test_mock_response_403(self):
        response = mock_response_403()
        self.assertEqual(response.status_code, 403)
        self.assertIn("403 Forbidden", response.text)

    def test_mock_response_404(self):
        logger.debug("test_mock_response_404")
        logger.error("foobar")
        response = mock_response_404()
        self.assertEqual(response.status_code, 404)
        self.assertIn("404 Not Found", response.text)

    def test_mock_response_500(self):
        response = mock_response_500()
        self.assertEqual(response.status_code, 500)
        self.assertIn("500 Internal Server Error", response.text)


if __name__ == "__main__":
    unittest.main()
