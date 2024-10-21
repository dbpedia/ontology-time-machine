import unittest
from ontologytimemachine.utils.config import parse_arguments, Config
import sys
from ontologytimemachine.utils.config import OntoVersion, HttpsInterception


class TestConfig(unittest.TestCase):

    def test_parse_arguments(self):
        test_args = [
            "test",
            "--ontoFormat",
            "turtle",
            "--ontoVersion",
            "original",
            "--httpsInterception",
            "none",
        ]
        sys.argv = test_args
        config = parse_arguments()
        self.assertIsInstance(config, Config)
        self.assertEqual(config.ontoFormatConf.format.value, "turtle")
        self.assertEqual(config.ontoVersion, OntoVersion.ORIGINAL)
        self.assertEqual(config.restrictedAccess, False)
        self.assertEqual(config.httpsInterception, HttpsInterception.NONE)


if __name__ == "__main__":
    unittest.main()
