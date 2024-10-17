import unittest
from ontologytimemachine.utils.config import parse_arguments, Config
import sys


class TestConfig(unittest.TestCase):

    def test_parse_arguments(self):
        test_args = [
            "test",
            "--ontoFormat",
            "turtle",
            "--ontoPrecedence",
            "enforcedPriority",
            "--patchAcceptUpstream",
            "False",
            "--ontoVersion",
            "original",
            "--httpsInterception",
            "none",
            "--disableRemovingRedirects",
            "False",
            "--logLevel",
            "info",
        ]
        sys.argv = test_args
        config = parse_arguments()
        self.assertIsInstance(config, Config)
        self.assertEqual(config.ontoFormat["format"], "turtle")
        self.assertEqual(config.ontoVersion, "original")
        self.assertEqual(config.restrictedAccess, False)
        self.assertEqual(config.httpsInterception, "none")


if __name__ == "__main__":
    unittest.main()
