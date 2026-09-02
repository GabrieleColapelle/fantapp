import unittest

from hello import greet


class TestGreet(unittest.TestCase):
    def test_default_greeting(self):
        self.assertEqual(greet(), "Hello, World!")


if __name__ == "__main__":
    unittest.main()
